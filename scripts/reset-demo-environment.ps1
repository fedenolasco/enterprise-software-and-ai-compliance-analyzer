<#
.SYNOPSIS
Resets the local demo environment from committed fixtures on Windows.

.DESCRIPTION
Runs the repeatable demo reset path: start services, reset PostgreSQL rows,
re-ingest deterministic fixtures, reset/rebuild Neo4j graph state, reset the
mock pricing fixture, and optionally run smoke validation commands.
#>

param(
  [switch]$SkipDocker,
  [switch]$SkipValidation
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot

function Invoke-Step {
  param(
    [string]$Title,
    [string]$WorkingDirectory,
    [scriptblock]$Command
  )

  Write-Host "`n==> $Title" -ForegroundColor Cyan
  Push-Location $WorkingDirectory
  try {
    & $Command
  }
  finally {
    Pop-Location
  }
}

if (-not (Test-Path (Join-Path $RepoRoot ".env")) -and (Test-Path (Join-Path $RepoRoot ".env.example"))) {
  Copy-Item (Join-Path $RepoRoot ".env.example") (Join-Path $RepoRoot ".env")
}

if (-not $SkipDocker) {
  Invoke-Step "Start PostgreSQL, pgvector, and Neo4j services" $RepoRoot {
    docker compose up -d
  }
}

Invoke-Step "Reset and ingest PostgreSQL demo data" (Join-Path $RepoRoot "database-layer") {
  if (-not (Test-Path ".env") -and (Test-Path ".env.example")) {
    Copy-Item ".env.example" ".env"
  }
  npm run db:generate
  npm run db:push
  npm run db:enable-vector
  npm run reset:demo
  npm run ingest
  npm run validate:concurrency
}

Invoke-Step "Reset and rebuild Neo4j graph projection" (Join-Path $RepoRoot "agent-brain") {
  if (-not (Test-Path ".env") -and (Test-Path ".env.example")) {
    Copy-Item ".env.example" ".env"
  }
  python scripts/reset_graph.py --yes
  python -m agent_brain.cli.project_graph
}

Invoke-Step "Reset mock pricing fixture" (Join-Path $RepoRoot "mock-pricing-api") {
  if (-not (Test-Path ".env") -and (Test-Path ".env.example")) {
    Copy-Item ".env.example" ".env"
  }
  python scripts/reset_pricing_fixture.py
}

if (-not $SkipValidation) {
  Invoke-Step "Run retrieval smoke tests" (Join-Path $RepoRoot "agent-brain") {
    python -m agent_brain.cli.search_vectors "cross-border processing subprocessors outside the EU" --top-k 5
    python -m agent_brain.cli.traverse_graph --risk-category DATA_RESIDENCY --limit 10
    python -m agent_brain.cli.hybrid_retrieve "cross-border processing subprocessors outside the EU" --top-k 5 --graph-limit 25
    python -m agent_brain.cli.run_curated_demo
  }
}

Write-Host "`nDemo environment reset complete." -ForegroundColor Green
