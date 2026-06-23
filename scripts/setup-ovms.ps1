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
  .\scripts\setup-ovms.ps1 -Start -Task embeddings -Model OpenVINO/Qwen3-Embedding-0.6B
  .\scripts\setup-ovms.ps1 -Stop
#>

param(
  [switch]$Start,
  [switch]$Stop,
  [switch]$Status,
  [string]$OvmsPath = $(if ($env:OPENVINO_OVMS_PATH) { $env:OPENVINO_OVMS_PATH } else { "ovms.exe" }),
  [string]$Model = $env:OPENVINO_MODEL,
  [string]$EmbeddingModel = $env:OPENVINO_EMBEDDING_MODEL,
  [ValidateSet("text_generation", "embeddings")]
  [string]$Task = "text_generation",
  [ValidateSet("NPU", "GPU", "CPU")]
  [string]$Device = $(if ($env:OPENVINO_DEVICE) { $env:OPENVINO_DEVICE } else { "NPU" }),
  [int]$Port = $(if ($env:OPENVINO_PORT) { [int]$env:OPENVINO_PORT } else { 8100 }),
  [string]$ModelRepositoryPath,
  [string]$CacheDir,
  [int]$MaxPromptLen = 2000,
  [int]$CacheSize = 2
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot

if (-not $Model) { $Model = "OpenVINO/Qwen3-8B-int4-cw-ov" }
if (-not $EmbeddingModel) { $EmbeddingModel = "OpenVINO/Qwen3-Embedding-0.6B" }
if (-not $ModelRepositoryPath) { $ModelRepositoryPath = Join-Path $RepoRoot ".openvino\models" }
if (-not $CacheDir) { $CacheDir = Join-Path $RepoRoot ".openvino\cache" }

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
  if (Test-OvmsEndpoint -RestPort $Port) {
    Write-Host "OVMS is already responding at http://localhost:$Port" -ForegroundColor Green
    exit 0
  }

  $resolvedOvms = Resolve-OvmsPath -Candidate $OvmsPath
  $ovmsWorkingDirectory = Initialize-OvmsEnvironment -ResolvedOvmsPath $resolvedOvms
  New-Item -ItemType Directory -Force -Path $ModelRepositoryPath | Out-Null
  New-Item -ItemType Directory -Force -Path $CacheDir | Out-Null

  $selectedModel = if ($Task -eq "embeddings") { $EmbeddingModel } else { $Model }
  $modelName = $selectedModel.Replace("/", "_").Replace("\\", "_")
  $logPath = Join-Path $RepoRoot ".openvino\ovms-$Task-$Port.log"
  $errorLogPath = Join-Path $RepoRoot ".openvino\ovms-$Task-$Port.err.log"
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $logPath) | Out-Null

  $arguments = @(
    "--rest_port", "$Port",
    "--source_model", $selectedModel,
    "--model_repository_path", $ModelRepositoryPath,
    "--model_name", $modelName,
    "--task", $Task,
    "--target_device", $Device,
    "--cache_size", "$CacheSize",
    "--cache_dir", $CacheDir
  )

  if ($Task -eq "embeddings") {
    $arguments += @("--pooling", "LAST")
  } else {
    $arguments += @("--enable_prefix_caching", "true", "--max_prompt_len", "$MaxPromptLen")
  }

  Write-Host "Starting native OVMS..." -ForegroundColor Cyan
  Write-Host "  Executable: $resolvedOvms" -ForegroundColor DarkGray
  Write-Host "  Endpoint:   http://localhost:$Port" -ForegroundColor DarkGray
  Write-Host "  Task:       $Task" -ForegroundColor DarkGray
  Write-Host "  Model:      $selectedModel" -ForegroundColor DarkGray
  Write-Host "  Device:     $Device" -ForegroundColor DarkGray
  Write-Host "  Repository: $ModelRepositoryPath" -ForegroundColor DarkGray
  Write-Host "  Compile cache: $CacheDir" -ForegroundColor DarkGray
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
