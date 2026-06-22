#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKIP_DOCKER="false"
SKIP_VALIDATION="false"

for arg in "$@"; do
  case "$arg" in
    --skip-docker)
      SKIP_DOCKER="true"
      ;;
    --skip-validation)
      SKIP_VALIDATION="true"
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      echo "Usage: scripts/reset-demo-environment.sh [--skip-docker] [--skip-validation]" >&2
      exit 2
      ;;
  esac
done

run_step() {
  local title="$1"
  local directory="$2"
  shift 2
  printf '\n==> %s\n' "$title"
  (cd "$directory" && "$@")
}

ensure_env_file() {
  local directory="$1"
  if [[ ! -f "$directory/.env" && -f "$directory/.env.example" ]]; then
    cp "$directory/.env.example" "$directory/.env"
  fi
}

ensure_env_file "$REPO_ROOT"

if [[ "$SKIP_DOCKER" != "true" ]]; then
  run_step "Start PostgreSQL, pgvector, and Neo4j services" "$REPO_ROOT" docker compose up -d
fi

ensure_env_file "$REPO_ROOT/database-layer"
run_step "Generate Prisma client" "$REPO_ROOT/database-layer" npm run db:generate
run_step "Apply Prisma schema" "$REPO_ROOT/database-layer" npm run db:push
run_step "Enable pgvector" "$REPO_ROOT/database-layer" npm run db:enable-vector
run_step "Reset PostgreSQL demo rows" "$REPO_ROOT/database-layer" npm run reset:demo
run_step "Ingest deterministic fixtures" "$REPO_ROOT/database-layer" npm run ingest
run_step "Validate concurrency behavior" "$REPO_ROOT/database-layer" npm run validate:concurrency

ensure_env_file "$REPO_ROOT/agent-brain"
run_step "Reset Neo4j demo graph" "$REPO_ROOT/agent-brain" python scripts/reset_graph.py --yes
run_step "Project PostgreSQL records into Neo4j" "$REPO_ROOT/agent-brain" python -m agent_brain.cli.project_graph

ensure_env_file "$REPO_ROOT/mock-pricing-api"
run_step "Reset mock pricing fixture" "$REPO_ROOT/mock-pricing-api" python scripts/reset_pricing_fixture.py

if [[ "$SKIP_VALIDATION" != "true" ]]; then
  run_step "Run vector retrieval smoke test" "$REPO_ROOT/agent-brain" python -m agent_brain.cli.search_vectors "cross-border processing subprocessors outside the EU" --top-k 5
  run_step "Run graph traversal smoke test" "$REPO_ROOT/agent-brain" python -m agent_brain.cli.traverse_graph --risk-category DATA_RESIDENCY --limit 10
  run_step "Run hybrid retrieval smoke test" "$REPO_ROOT/agent-brain" python -m agent_brain.cli.hybrid_retrieve "cross-border processing subprocessors outside the EU" --top-k 5 --graph-limit 25
  run_step "Run curated demo assertions" "$REPO_ROOT/agent-brain" python -m agent_brain.cli.run_curated_demo
fi

printf '\nDemo environment reset complete.\n'
