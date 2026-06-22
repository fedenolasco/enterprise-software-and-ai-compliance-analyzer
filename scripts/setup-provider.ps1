<#
.SYNOPSIS
Securely configures OpenAI API key in local .env files and optionally switches provider settings.

.DESCRIPTION
Prompts the user for their OpenAI API key using a secure masked input, then
writes it to the three local .env files (root, agent-brain, database-layer).
The key is never printed, logged, or transmitted anywhere except the local .env
files which are gitignored.

The script can also switch provider configuration between placeholder,
microsoft-foundry-local, and openai modes.

Usage:
  .\scripts\setup-openai-key.ps1                              # Set key only
  .\scripts\setup-openai-key.ps1 -SwitchTo openai             # Set key + switch to OpenAI
  .\scripts\setup-openai-key.ps1 -SwitchTo foundry            # Switch to Foundry Local (no key needed)
  .\scripts\setup-openai-key.ps1 -SwitchTo placeholder        # Switch back to placeholder
  .\scripts\setup-openai-key.ps1 -SwitchTo openai -SkipKey    # Switch to OpenAI without prompting for key
#>

param(
  [ValidateSet("openai", "foundry", "placeholder", "none")]
  [string]$SwitchTo = "none",
  [switch]$SkipKey
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot

function Read-MaskedInput {
  param([string]$Prompt)

  Write-Host $Prompt -NoNewline
  $input = ""
  while ($true) {
    $key = [System.Console]::ReadKey($true)
    if ($key.Key -eq "Enter") {
      Write-Host ""
      break
    }
    if ($key.Key -eq "Escape") {
      Write-Host ""
      return $null
    }
    $input += $key.KeyChar
    Write-Host "*" -NoNewline
  }
  return $input
}

function Set-EnvValue {
  param(
    [string]$FilePath,
    [string]$Key,
    [string]$Value
  )

  if (-not (Test-Path $FilePath)) {
    "$Key=$Value" | Out-File -FilePath $FilePath -Encoding utf8 -Append
    return
  }

  $lines = Get-Content -Path $FilePath -Encoding utf8
  $found = $false
  $updatedLines = @()

  foreach ($line in $lines) {
    if ($line -match "^#?\s*$Key\s*=") {
      $updatedLines += "$Key=$Value"
      $found = $true
    } else {
      $updatedLines += $line
    }
  }

  if (-not $found) {
    $updatedLines += "$Key=$Value"
  }

  $updatedLines | Out-File -FilePath $FilePath -Encoding utf8
}

function Get-ProviderConfig {
  param([string]$Provider)

  switch ($Provider) {
    "openai" {
      return @{
        EMBEDDING_PROVIDER = "openai"
        EMBEDDING_MODEL = "text-embedding-3-small"
        EMBEDDING_DIMENSION = "1536"
        MODEL_PROVIDER = "openai"
        OPENAI_MODEL = "gpt-4o-mini"
      }
    }
    "foundry" {
      return @{
        EMBEDDING_PROVIDER = "microsoft-foundry-local"
        EMBEDDING_MODEL = "all-MiniLM-L6-v2"
        EMBEDDING_DIMENSION = "384"
        MODEL_PROVIDER = "microsoft-foundry-local"
        LOCAL_MODEL_NAME = "Phi-3.5-mini-instruct"
      }
    }
    "placeholder" {
      return @{
        EMBEDDING_PROVIDER = "placeholder"
        EMBEDDING_MODEL = "deterministic-placeholder"
        EMBEDDING_DIMENSION = "8"
        MODEL_PROVIDER = "placeholder"
        LOCAL_MODEL_NAME = "deterministic-placeholder-local-model"
      }
    }
    default {
      return @{}
    }
  }
}

Write-Host "=== Secure OpenAI API Key and Provider Setup ===" -ForegroundColor Cyan
Write-Host ""

# Show current provider mode
if ($SwitchTo -ne "none") {
  Write-Host "Switching provider to: $SwitchTo" -ForegroundColor Yellow
  $config = Get-ProviderConfig -Provider $SwitchTo
  Write-Host "  EMBEDDING_PROVIDER=$($config['EMBEDDING_PROVIDER'])" -ForegroundColor DarkGray
  Write-Host "  EMBEDDING_MODEL=$($config['EMBEDDING_MODEL'])" -ForegroundColor DarkGray
  Write-Host "  EMBEDDING_DIMENSION=$($config['EMBEDDING_DIMENSION'])" -ForegroundColor DarkGray
  Write-Host "  MODEL_PROVIDER=$($config['MODEL_PROVIDER'])" -ForegroundColor DarkGray
  if ($config.ContainsKey('OPENAI_MODEL')) {
    Write-Host "  OPENAI_MODEL=$($config['OPENAI_MODEL'])" -ForegroundColor DarkGray
  }
  if ($config.ContainsKey('LOCAL_MODEL_NAME')) {
    Write-Host "  LOCAL_MODEL_NAME=$($config['LOCAL_MODEL_NAME'])" -ForegroundColor DarkGray
  }
  Write-Host ""
}

# Prompt for API key unless skipped or switching to non-OpenAI provider
$apiKey = $null
if (-not $SkipKey -and $SwitchTo -ne "foundry" -and $SwitchTo -ne "placeholder") {
  Write-Host "This script will prompt for your OpenAI API key (input will be masked)." -ForegroundColor White
  Write-Host "The key is NEVER printed, logged, or transmitted." -ForegroundColor White
  Write-Host "All .env files are gitignored and will never be committed." -ForegroundColor White
  Write-Host ""
  Write-Host "Press ESC at any time to cancel without saving." -ForegroundColor DarkGray
  Write-Host ""

  $apiKey = Read-MaskedInput -Prompt "Enter your OpenAI API key: "

  if (-not $apiKey -or $apiKey.Trim() -eq "") {
    Write-Host "No API key entered. Exiting without changes." -ForegroundColor Yellow
    exit 0
  }

  $apiKey = $apiKey.Trim()

  if (-not $apiKey.StartsWith("sk-")) {
    Write-Host ""
    Write-Host "Warning: The key does not start with 'sk-'. This may not be a valid OpenAI API key." -ForegroundColor Yellow
    $continue = Read-Host "Continue anyway? (y/N)"
    if ($continue -ne "y" -and $continue -ne "Y") {
      Write-Host "Cancelled. No changes made." -ForegroundColor Yellow
      exit 0
    }
  }
  Write-Host ""
} elseif ($SkipKey) {
  Write-Host "Skipping API key prompt (-SkipKey flag set)." -ForegroundColor DarkGray
  Write-Host ""
}

Write-Host "Updating .env files..." -ForegroundColor Cyan

$envFiles = @(
  @{ Path = Join-Path $RepoRoot ".env"; Label = "root .env" }
  @{ Path = Join-Path $RepoRoot "agent-brain\.env"; Label = "agent-brain/.env" }
  @{ Path = Join-Path $RepoRoot "database-layer\.env"; Label = "database-layer/.env" }
)

foreach ($envFile in $envFiles) {
  # Write API key if provided
  if ($apiKey) {
    Set-EnvValue -FilePath $envFile.Path -Key "OPENAI_API_KEY" -Value $apiKey
    Write-Host "  Updated OPENAI_API_KEY in: $($envFile.Label)" -ForegroundColor Green
  }

  # Switch provider settings if requested
  if ($SwitchTo -ne "none") {
    foreach ($key in $config.Keys) {
      Set-EnvValue -FilePath $envFile.Path -Key $key -Value $config[$key]
    }
    Write-Host "  Switched provider to $SwitchTo in: $($envFile.Label)" -ForegroundColor Green
  }

  if (-not $apiKey -and $SwitchTo -eq "none") {
    Write-Host "  No changes needed in: $($envFile.Label)" -ForegroundColor DarkGray
  }
}

Write-Host ""
Write-Host "Done." -ForegroundColor Green

if ($apiKey) {
  Write-Host "Your API key has been written to the local .env files." -ForegroundColor Green
  Write-Host "The key was NOT printed, logged, or transmitted anywhere else." -ForegroundColor Green
}

Write-Host ""
Write-Host "IMPORTANT: Verify .env files are gitignored before committing:" -ForegroundColor Yellow
Write-Host "  git status --short" -ForegroundColor DarkGray
Write-Host "  (no .env files should appear)" -ForegroundColor DarkGray

if ($SwitchTo -ne "none" -and $SwitchTo -ne "placeholder") {
  Write-Host ""
  Write-Host "NOTE: Switching embedding model changes the vector dimension." -ForegroundColor Yellow
  Write-Host "You must reset and re-ingest demo data after switching:" -ForegroundColor Yellow
  Write-Host "  .\scripts\reset-demo-environment.ps1" -ForegroundColor DarkGray
}
