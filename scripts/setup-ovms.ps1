<#
.SYNOPSIS
Sets up, starts, stops, and checks native Windows OpenVINO Model Server (OVMS).

.DESCRIPTION
Runs OVMS as a bare-metal Windows process instead of a Docker Compose service so
OVMS can access Intel NPU/GPU/CPU devices directly. The script assumes the OVMS
package is installed and `ovms.exe` is available on PATH, or that -OvmsPath points
to the installed executable.

Download the native Windows package from the OpenVINO Model Server bare-metal
deployment guide: https://docs.openvino.ai/2026/model-server/ovms_docs_deploying_server_baremetal.html

Examples:
  .\scripts\setup-ovms.ps1 -Status
  .\scripts\setup-ovms.ps1 -Start
  .\scripts\setup-ovms.ps1 -Start -Device GPU -Port 8100
  .\scripts\setup-ovms.ps1 -Start -Task embeddings -Model OpenVINO/Qwen3-Embedding-0.6B-int8-ov
  .\scripts\setup-ovms.ps1 -Stop
#>

param(
  [switch]$Start,
  [switch]$Stop,
  [switch]$Status,
  [switch]$MultiModel,
  [switch]$ForceRestart,
  [string]$OvmsPath = $(if ($env:OPENVINO_OVMS_PATH) { $env:OPENVINO_OVMS_PATH } else { "ovms.exe" }),
  [string]$Model = $env:OPENVINO_MODEL,
  [string]$EmbeddingModel = $env:OPENVINO_EMBEDDING_MODEL,
  [ValidateSet("text_generation", "embeddings")]
  [string]$Task = "text_generation",
  [ValidateSet("NPU", "GPU", "CPU")]
  [string]$Device = $(if ($env:OPENVINO_DEVICE) { $env:OPENVINO_DEVICE } else { "NPU" }),
  [int]$Port = $(if ($env:OPENVINO_PORT) { [int]$env:OPENVINO_PORT } else { 8100 }),
  [string]$ModelRepositoryPath,
  [string]$ConfigPath,
  [string]$CacheDir,
  [string]$LogDir,
  [int]$MaxPromptLen = 2000,
  [int]$CacheSize = 2
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot

function Import-EnvFile {
  param([string]$Path)

  if (-not (Test-Path $Path)) {
    return
  }

  Get-Content -Path $Path | ForEach-Object {
    $line = $_.Trim()
    if (-not $line -or $line.StartsWith("#") -or -not $line.Contains("=")) {
      return
    }

    $parts = $line.Split("=", 2)
    $name = $parts[0].Trim()
    $value = $parts[1].Trim().Trim('"').Trim("'")
    if ($name -and -not [Environment]::GetEnvironmentVariable($name, "Process")) {
      [Environment]::SetEnvironmentVariable($name, $value, "Process")
    }
  }
}

Import-EnvFile -Path (Join-Path $RepoRoot ".env")

if (-not $Model) { $Model = "OpenVINO/Qwen3-8B-int4-cw-ov" }
if (-not $EmbeddingModel) { $EmbeddingModel = "OpenVINO/Qwen3-Embedding-0.6B-int8-ov" }
if (-not $ModelRepositoryPath) { $ModelRepositoryPath = $(if ($env:OPENVINO_MODEL_REPOSITORY_PATH) { $env:OPENVINO_MODEL_REPOSITORY_PATH } else { Join-Path $RepoRoot ".openvino\models" }) }
if (-not $ConfigPath) { $ConfigPath = Join-Path $ModelRepositoryPath "config.json" }
if (-not $CacheDir) { $CacheDir = $(if ($env:OPENVINO_CACHE_DIR) { $env:OPENVINO_CACHE_DIR } else { Join-Path $RepoRoot ".openvino\cache" }) }
if (-not $LogDir) { $LogDir = $(if ($env:OPENVINO_LOG_DIR) { $env:OPENVINO_LOG_DIR } else { Join-Path $RepoRoot ".openvino" }) }

function Resolve-OvmsPath {
  param([string]$Candidate)

  if (Test-Path $Candidate) {
    return (Resolve-Path $Candidate).Path
  }

  $command = Get-Command $Candidate -ErrorAction SilentlyContinue
  if ($command) {
    return $command.Source
  }

  Write-Host "OVMS executable not found." -ForegroundColor Red
  Write-Host "Install the OpenVINO Model Server Windows package, then either:" -ForegroundColor Yellow
  Write-Host "  1. Add the folder containing ovms.exe to PATH and restart the UI backend; or" -ForegroundColor Yellow
  Write-Host "  2. Start manually with: .\scripts\setup-ovms.ps1 -Start -OvmsPath C:\Path\To\ovms.exe" -ForegroundColor Yellow
  Write-Host "Download/deployment guide: https://docs.openvino.ai/2026/model-server/ovms_docs_deploying_server_baremetal.html" -ForegroundColor Yellow
  exit 3
}

function Initialize-OvmsEnvironment {
  param([string]$ResolvedOvmsPath)

  $ovmsDirectory = Split-Path -Parent $ResolvedOvmsPath
  $setupVarsPath = Join-Path $ovmsDirectory "setupvars.ps1"

  if (Test-Path $setupVarsPath) {
    Write-Host "Loading OVMS environment: $setupVarsPath" -ForegroundColor DarkGray
    . $setupVarsPath | Out-Null
  } else {
    Write-Host "OVMS setupvars.ps1 not found next to ovms.exe. Continuing with current environment." -ForegroundColor Yellow
  }

  return $ovmsDirectory
}

function Get-LogTail {
  param(
    [string]$Path,
    [int]$LineCount = 30
  )

  if (-not (Test-Path $Path)) {
    return "Log not found: $Path"
  }

  $content = Get-Content -Path $Path -Tail $LineCount -ErrorAction SilentlyContinue
  if (-not $content) {
    return "Log is empty: $Path"
  }
  return ($content -join [Environment]::NewLine)
}

function Test-OvmsEndpoint {
  param([int]$RestPort)

  foreach ($path in @("/v1/models", "/v2/health/ready")) {
    try {
      $response = Invoke-WebRequest -Uri "http://localhost:$RestPort$path" -UseBasicParsing -TimeoutSec 5
      if ($response.StatusCode -eq 200 -or $response.StatusCode -eq 204) {
        return $true
      }
    } catch {
      # Try the next health path.
    }
  }
  return $false
}

function Get-OvmsProcesses {
  param([int]$RestPort)

  Get-CimInstance Win32_Process |
    Where-Object {
      $_.Name -match "^ovms(\.exe)?$" -and
      ($_.CommandLine -match "--rest_port\s+$RestPort" -or $_.CommandLine -match "--rest_port=$RestPort")
    }
}

function Stop-Ovms {
  param([int]$RestPort)

  $processes = @(Get-OvmsProcesses -RestPort $RestPort)
  if ($processes.Count -eq 0) {
    Write-Host "No native OVMS process found for REST port $RestPort." -ForegroundColor Yellow
    return
  }

  foreach ($process in $processes) {
    Write-Host "Stopping OVMS process $($process.ProcessId) on REST port $RestPort..." -ForegroundColor Cyan
    Stop-Process -Id $process.ProcessId -Force
  }
}

function Stop-DuplicateOvmsProcesses {
  param([int]$RestPort)

  $processes = @(Get-OvmsProcesses -RestPort $RestPort | Sort-Object CreationDate -Descending)
  if ($processes.Count -le 1) {
    return
  }

  $keeper = $processes[0]
  Write-Host "Multiple OVMS processes found for REST port $RestPort. Keeping process $($keeper.ProcessId) and stopping duplicates..." -ForegroundColor Yellow
  foreach ($process in $processes | Select-Object -Skip 1) {
    Write-Host "Stopping duplicate OVMS process $($process.ProcessId) on REST port $RestPort..." -ForegroundColor Yellow
    Stop-Process -Id $process.ProcessId -Force
  }
}

function Convert-ModelIdToName {
  param([string]$ModelId)
  # Keep the public model ID as the served model name so OpenAI-compatible
  # clients can keep using OPENVINO_MODEL / OPENVINO_EMBEDDING_MODEL unchanged.
  return $ModelId
}

function Convert-ModelIdToRepoPath {
  param([string]$ModelId)
  return $ModelId.Replace("/", "\")
}

function Invoke-OvmsPull {
  param(
    [string]$ResolvedOvmsPath,
    [string]$SourceModel,
    [string]$TaskName,
    [string]$TargetDevice,
    [string]$RepositoryPath
  )

  $pullArgs = @(
    "--pull",
    "--model_repository_path", $RepositoryPath,
    "--source_model", $SourceModel,
    "--task", $TaskName,
    "--target_device", $TargetDevice
  )
  if ($TaskName -eq "embeddings") {
    $pullArgs += @("--pooling", "LAST")
  }
  Write-Host "Pulling/preparing $TaskName model: $SourceModel" -ForegroundColor Cyan
  & $ResolvedOvmsPath @pullArgs
  if ($LASTEXITCODE -ne 0) {
    throw "OVMS pull failed for $SourceModel with exit code $LASTEXITCODE."
  }
}

function Add-OvmsModelToConfig {
  param(
    [string]$ResolvedOvmsPath,
    [string]$ConfigFile,
    [string]$ModelId
  )

  $modelName = Convert-ModelIdToName -ModelId $ModelId
  $modelPath = Convert-ModelIdToRepoPath -ModelId $ModelId
  Write-Host "Adding model to OVMS config: $modelName -> $modelPath" -ForegroundColor Cyan
  & $ResolvedOvmsPath --add_to_config --config_path $ConfigFile --model_name $modelName --model_path $modelPath
  if ($LASTEXITCODE -ne 0) {
    throw "OVMS add_to_config failed for $ModelId with exit code $LASTEXITCODE."
  }
}

if (-not $Start -and -not $Stop -and -not $Status) {
  $Status = $true
}

if ($Status) {
  $running = Test-OvmsEndpoint -RestPort $Port
  if ($running) {
    Write-Host "OVMS is responding at http://localhost:$Port" -ForegroundColor Green
    exit 0
  }
  Write-Host "OVMS is not responding at http://localhost:$Port" -ForegroundColor Yellow
  exit 1
}

if ($Stop) {
  Stop-Ovms -RestPort $Port
  Start-Sleep -Seconds 2
  if (Test-OvmsEndpoint -RestPort $Port) {
    Write-Host "Stop command completed, but OVMS is still responding on http://localhost:$Port." -ForegroundColor Yellow
    exit 1
  }
  Write-Host "OVMS stopped on http://localhost:$Port." -ForegroundColor Green
  exit 0
}

if ($Start) {
  Stop-DuplicateOvmsProcesses -RestPort $Port
  if (Test-OvmsEndpoint -RestPort $Port) {
    if ($ForceRestart) {
      Write-Host "OVMS is already responding at http://localhost:$Port. Restarting because -ForceRestart was requested..." -ForegroundColor Yellow
      Stop-Ovms -RestPort $Port
      Start-Sleep -Seconds 2
    } else {
      Write-Host "OVMS is already responding at http://localhost:$Port" -ForegroundColor Green
      exit 0
    }
  }

  $staleProcesses = @(Get-OvmsProcesses -RestPort $Port)
  if ($staleProcesses.Count -gt 0) {
    Write-Host "OVMS processes exist on REST port $Port but endpoint is not ready. Stopping stale processes before starting a single instance..." -ForegroundColor Yellow
    Stop-Ovms -RestPort $Port
    Start-Sleep -Seconds 2
  }

  $resolvedOvms = Resolve-OvmsPath -Candidate $OvmsPath
  $ovmsWorkingDirectory = Initialize-OvmsEnvironment -ResolvedOvmsPath $resolvedOvms
  New-Item -ItemType Directory -Force -Path $ModelRepositoryPath | Out-Null
  New-Item -ItemType Directory -Force -Path $CacheDir | Out-Null
  New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

  $selectedModel = if ($Task -eq "embeddings") { $EmbeddingModel } else { $Model }
  $modelName = $selectedModel.Replace("/", "_").Replace("\\", "_")
  # OVMS writes --cache_dir into a JSON plugin_config inside graph.pbtxt.
  # Raw Windows backslashes can become invalid JSON escapes after protobuf
  # string handling, causing "Plugin config is in wrong format" at startup.
  # Keep filesystem paths as normal Windows paths, but pass a JSON-safe
  # forward-slash cache path to OVMS.
  # PowerShell does not use backslash as an escape character in strings; "\"
  # is the single backslash path separator we need to replace.
  $ovmsCacheDir = $CacheDir.Replace("\", "/")
  $logPath = Join-Path $LogDir "ovms-$Task-$Port.log"
  $errorLogPath = Join-Path $LogDir "ovms-$Task-$Port.err.log"
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $logPath) | Out-Null

  if ($MultiModel) {
    Invoke-OvmsPull -ResolvedOvmsPath $resolvedOvms -SourceModel $Model -TaskName "text_generation" -TargetDevice $Device -RepositoryPath $ModelRepositoryPath
    Invoke-OvmsPull -ResolvedOvmsPath $resolvedOvms -SourceModel $EmbeddingModel -TaskName "embeddings" -TargetDevice $Device -RepositoryPath $ModelRepositoryPath
    if (Test-Path $ConfigPath) { Remove-Item -Force $ConfigPath }
    Add-OvmsModelToConfig -ResolvedOvmsPath $resolvedOvms -ConfigFile $ConfigPath -ModelId $Model
    Add-OvmsModelToConfig -ResolvedOvmsPath $resolvedOvms -ConfigFile $ConfigPath -ModelId $EmbeddingModel
    $arguments = @(
      "--rest_port", "$Port",
      "--config_path", $ConfigPath
    )
  } else {
    $arguments = @(
      "--rest_port", "$Port",
      "--source_model", $selectedModel,
      "--model_repository_path", $ModelRepositoryPath,
      "--model_name", $modelName,
      "--task", $Task,
      "--target_device", $Device,
      "--cache_size", "$CacheSize",
      "--cache_dir", $ovmsCacheDir
    )

    if ($Task -eq "embeddings") {
      $arguments += @("--pooling", "LAST")
    } else {
      $arguments += @("--enable_prefix_caching", "true", "--max_prompt_len", "$MaxPromptLen")
    }
  }

  Write-Host "Starting native OVMS..." -ForegroundColor Cyan
  Write-Host "  Executable: $resolvedOvms" -ForegroundColor DarkGray
  Write-Host "  Endpoint:   http://localhost:$Port" -ForegroundColor DarkGray
  Write-Host "  Task:       $Task" -ForegroundColor DarkGray
  Write-Host "  MultiModel: $MultiModel" -ForegroundColor DarkGray
  Write-Host "  Model:      $selectedModel" -ForegroundColor DarkGray
  if ($MultiModel) { Write-Host "  Embeddings: $EmbeddingModel" -ForegroundColor DarkGray }
  Write-Host "  Device:     $Device" -ForegroundColor DarkGray
  Write-Host "  Repository: $ModelRepositoryPath" -ForegroundColor DarkGray
  if ($MultiModel) { Write-Host "  Config:     $ConfigPath" -ForegroundColor DarkGray }
  Write-Host "  Compile cache: $CacheDir" -ForegroundColor DarkGray
  Write-Host "  OVMS cache arg: $ovmsCacheDir" -ForegroundColor DarkGray
  Write-Host "  Log:        $logPath" -ForegroundColor DarkGray
  Write-Host "  Error log:  $errorLogPath" -ForegroundColor DarkGray

  $process = Start-Process -FilePath $resolvedOvms -ArgumentList $arguments -PassThru -RedirectStandardOutput $logPath -RedirectStandardError $errorLogPath -WindowStyle Hidden -WorkingDirectory $ovmsWorkingDirectory
  Write-Host "Started OVMS process $($process.Id). Waiting for readiness..." -ForegroundColor Cyan

  for ($attempt = 1; $attempt -le 30; $attempt++) {
    Start-Sleep -Seconds 2
    if (Test-OvmsEndpoint -RestPort $Port) {
      Write-Host "OVMS is responding at http://localhost:$Port" -ForegroundColor Green
      exit 0
    }
    if ($process.HasExited) {
      Write-Host "OVMS process exited before readiness. Exit code: $($process.ExitCode)" -ForegroundColor Red
      Write-Host "STDOUT tail:" -ForegroundColor Yellow
      Write-Host (Get-LogTail -Path $logPath)
      Write-Host "STDERR tail:" -ForegroundColor Yellow
      Write-Host (Get-LogTail -Path $errorLogPath)
      exit 4
    }
  }

  Write-Host "OVMS was started but did not become ready within 60 seconds. It may still be downloading or compiling the model. Check: $logPath and $errorLogPath" -ForegroundColor Yellow
  Write-Host "STDOUT tail:" -ForegroundColor Yellow
  Write-Host (Get-LogTail -Path $logPath)
  Write-Host "STDERR tail:" -ForegroundColor Yellow
  Write-Host (Get-LogTail -Path $errorLogPath)
  exit 2
}

