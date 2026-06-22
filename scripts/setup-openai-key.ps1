<#
.SYNOPSIS
Securely configures OpenAI API key in local .env files without exposing the key.

.DESCRIPTION
Prompts the user for their OpenAI API key using a secure masked input, then
writes it to the three local .env files (root, agent-brain, database-layer).
The key is never printed, logged, or transmitted anywhere except the local .env
files which are gitignored.

The script also optionally switches the provider configuration from placeholder
to openai in each .env file.
#>

param(
  [switch]$SwitchToOpenAI
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
    # File doesn't exist — create it with just this key
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

Write-Host "=== Secure OpenAI API Key Setup ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "This script will:" -ForegroundColor White
Write-Host "  1. Prompt you for your OpenAI API key (input will be masked)" -ForegroundColor White
Write-Host "  2. Write the key to .env, agent-brain/.env, and database-layer/.env" -ForegroundColor White
Write-Host "  3. The key is NEVER printed, logged, or transmitted" -ForegroundColor White
Write-Host "  4. All .env files are gitignored and will never be committed" -ForegroundColor White
Write-Host ""

if ($SwitchToOpenAI) {
  Write-Host "The --SwitchToOpenAI flag is set." -ForegroundColor Yellow
  Write-Host "Provider settings will be switched from placeholder to openai." -ForegroundColor Yellow
  Write-Host ""
}

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
Write-Host "Writing API key to .env files..." -ForegroundColor Cyan

$envFiles = @(
  @{ Path = Join-Path $RepoRoot ".env"; Label = "root .env" }
  @{ Path = Join-Path $RepoRoot "agent-brain\.env"; Label = "agent-brain/.env" }
  @{ Path = Join-Path $RepoRoot "database-layer\.env"; Label = "database-layer/.env" }
)

foreach ($envFile in $envFiles) {
  Set-EnvValue -FilePath $envFile.Path -Key "OPENAI_API_KEY" -Value $apiKey
  Write-Host "  Updated: $($envFile.Label)" -ForegroundColor Green

  if ($SwitchToOpenAI) {
    Set-EnvValue -FilePath $envFile.Path -Key "EMBEDDING_PROVIDER" -Value "openai"
    Set-EnvValue -FilePath $envFile.Path -Key "EMBEDDING_MODEL" -Value "text-embedding-3-small"
    Set-EnvValue -FilePath $envFile.Path -Key "EMBEDDING_DIMENSION" -Value "1536"
    Set-EnvValue -FilePath $envFile.Path -Key "MODEL_PROVIDER" -Value "openai"
    Set-EnvValue -FilePath $envFile.Path -Key "OPENAI_MODEL" -Value "gpt-4o-mini"
    Write-Host "    (provider switched to openai)" -ForegroundColor DarkGreen
  }
}

Write-Host ""
Write-Host "Done. Your API key has been written to the local .env files." -ForegroundColor Green
Write-Host "The key was NOT printed, logged, or transmitted anywhere else." -ForegroundColor Green
Write-Host ""

if (-not $SwitchToOpenAI) {
  Write-Host "To switch from placeholder to OpenAI providers, either:" -ForegroundColor White
  Write-Host "  - Re-run this script with -SwitchToOpenAI" -ForegroundColor White
  Write-Host "  - Or manually edit the .env files:" -ForegroundColor White
  Write-Host "      EMBEDDING_PROVIDER=openai" -ForegroundColor DarkGray
  Write-Host "      EMBEDDING_MODEL=text-embedding-3-small" -ForegroundColor DarkGray
  Write-Host "      EMBEDDING_DIMENSION=1536" -ForegroundColor DarkGray
  Write-Host "      MODEL_PROVIDER=openai" -ForegroundColor DarkGray
  Write-Host "      OPENAI_MODEL=gpt-4o-mini" -ForegroundColor DarkGray
  Write-Host ""
}

Write-Host "IMPORTANT: Verify .env files are gitignored before committing:" -ForegroundColor Yellow
Write-Host "  git status --short" -ForegroundColor DarkGray
Write-Host "  (no .env files should appear)" -ForegroundColor DarkGray
