#!/usr/bin/env bash
#
# Securely configures OpenAI API key in local .env files and optionally
# switches provider settings between placeholder, foundry, and openai.
#
# Usage:
#   bash scripts/setup-openai-key.sh                              # Set key only
#   bash scripts/setup-openai-key.sh --switch-to openai           # Set key + switch to OpenAI
#   bash scripts/setup-openai-key.sh --switch-to foundry          # Switch to Foundry Local
#   bash scripts/setup-openai-key.sh --switch-to placeholder      # Switch back to placeholder
#   bash scripts/setup-openai-key.sh --switch-to openai --skip-key # Switch to OpenAI without key prompt
#

set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SWITCH_TO="none"
SKIP_KEY="false"

for arg in "$@"; do
  case "$arg" in
    --switch-to)
      shift
      SWITCH_TO="${1:-none}"
      shift || true
      ;;
    --switch-to=*)
      SWITCH_TO="${arg#--switch-to=}"
      ;;
    --skip-key)
      SKIP_KEY="true"
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      echo "Usage: scripts/setup-openai-key.sh [--switch-to openai|foundry|placeholder] [--skip-key]" >&2
      exit 2
      ;;
  esac
done

case "$SWITCH_TO" in
  openai|foundry|placeholder|none) ;;
  *)
    echo "Invalid --switch-to value: $SWITCH_TO" >&2
    echo "Valid values: openai, foundry, placeholder, none" >&2
    exit 2
    ;;
esac

set_env_value() {
  local file_path="$1"
  local key="$2"
  local value="$3"

  if [[ ! -f "$file_path" ]]; then
    echo "${key}=${value}" > "$file_path"
    return
  fi

  local tmp_file
  tmp_file="$(mktemp)"
  local found="false"

  while IFS= read -r line || [[ -n "$line" ]]; do
    if [[ "$line" =~ ^#?[[:space:]]*${key}[[:space:]]*= ]]; then
      echo "${key}=${value}" >> "$tmp_file"
      found="true"
    else
      echo "$line" >> "$tmp_file"
    fi
  done < "$file_path"

  if [[ "$found" == "false" ]]; then
    echo "${key}=${value}" >> "$tmp_file"
  fi

  mv "$tmp_file" "$file_path"
}

get_provider_config() {
  local provider="$1"
  case "$provider" in
    openai)
      echo "EMBEDDING_PROVIDER=openai"
      echo "EMBEDDING_MODEL=text-embedding-3-small"
      echo "EMBEDDING_DIMENSION=1536"
      echo "MODEL_PROVIDER=openai"
      echo "OPENAI_MODEL=gpt-4o-mini"
      ;;
    foundry)
      echo "EMBEDDING_PROVIDER=microsoft-foundry-local"
      echo "EMBEDDING_MODEL=all-MiniLM-L6-v2"
      echo "EMBEDDING_DIMENSION=384"
      echo "MODEL_PROVIDER=microsoft-foundry-local"
      echo "LOCAL_MODEL_NAME=Phi-3.5-mini-instruct"
      ;;
    placeholder)
      echo "EMBEDDING_PROVIDER=placeholder"
      echo "EMBEDDING_MODEL=deterministic-placeholder"
      echo "EMBEDDING_DIMENSION=8"
      echo "MODEL_PROVIDER=placeholder"
      echo "LOCAL_MODEL_NAME=deterministic-placeholder-local-model"
      ;;
  esac
}

read_masked_input() {
  local prompt="$1"
  local input=""

  printf "%s" "$prompt" >&2

  if command -v stty &> /dev/null; then
    stty -echo 2> /dev/null || true
  fi

  while IFS= read -r -n1 -s char; do
    if [[ "$char" == "" ]]; then
      break
    fi
    input += "$char"
    printf "*" >&2
  done

  if command -v stty &> /dev/null; then
    stty echo 2> /dev/null || true
  fi

  printf "\n" >&2
  printf "%s" "$input"
}

echo "=== Secure OpenAI API Key and Provider Setup ==="
echo ""

# Show provider switch info
if [[ "$SWITCH_TO" != "none" ]]; then
  echo "Switching provider to: $SWITCH_TO"
  while IFS= read -r config_line; do
    echo "  $config_line"
  done < <(get_provider_config "$SWITCH_TO")
  echo ""
fi

# Prompt for API key unless skipped or switching to non-OpenAI provider
API_KEY=""
if [[ "$SKIP_KEY" == "false" && "$SWITCH_TO" != "foundry" && "$SWITCH_TO" != "placeholder" ]]; then
  echo "This script will prompt for your OpenAI API key (input will be masked)."
  echo "The key is NEVER printed, logged, or transmitted."
  echo "All .env files are gitignored and will never be committed."
  echo ""

  API_KEY=$(read_masked_input "Enter your OpenAI API key: ")

  if [[ -z "$API_KEY" || -z "$(echo "$API_KEY" | tr -d '[:space:]')" ]]; then
    echo "No API key entered. Exiting without changes."
    exit 0
  fi

  API_KEY="$(echo "$API_KEY" | tr -d '[:space:]')"

  if [[ "$API_KEY" != sk-* ]]; then
    echo ""
    echo "Warning: The key does not start with 'sk-'. This may not be a valid OpenAI API key."
    read -p "Continue anyway? (y/N) " continue
    if [[ "$continue" != "y" && "$continue" != "Y" ]]; then
      echo "Cancelled. No changes made."
      exit 0
    fi
  fi
  echo ""
elif [[ "$SKIP_KEY" == "true" ]]; then
  echo "Skipping API key prompt (--skip-key flag set)."
  echo ""
fi

echo "Updating .env files..."

ENV_FILES=(
  "${REPO_ROOT}/.env"
  "${REPO_ROOT}/agent-brain/.env"
  "${REPO_ROOT}/database-layer/.env"
)

ENV_LABELS=(
  "root .env"
  "agent-brain/.env"
  "database-layer/.env"
)

for i in "${!ENV_FILES[@]}"; do
  # Write API key if provided
  if [[ -n "$API_KEY" ]]; then
    set_env_value "${ENV_FILES[$i]}" "OPENAI_API_KEY" "$API_KEY"
    echo "  Updated OPENAI_API_KEY in: ${ENV_LABELS[$i]}"
  fi

  # Switch provider settings if requested
  if [[ "$SWITCH_TO" != "none" ]]; then
    while IFS= read -r config_line; do
      key="${config_line%%=*}"
      value="${config_line#*=}"
      set_env_value "${ENV_FILES[$i]}" "$key" "$value"
    done < <(get_provider_config "$SWITCH_TO")
    echo "  Switched provider to $SWITCH_TO in: ${ENV_LABELS[$i]}"
  fi

  if [[ -z "$API_KEY" && "$SWITCH_TO" == "none" ]]; then
    echo "  No changes needed in: ${ENV_LABELS[$i]}"
  fi
done

echo ""
echo "Done."

if [[ -n "$API_KEY" ]]; then
  echo "Your API key has been written to the local .env files."
  echo "The key was NOT printed, logged, or transmitted anywhere else."
fi

echo ""
echo "IMPORTANT: Verify .env files are gitignored before committing:"
echo "  git status --short"
echo "  (no .env files should appear)"

if [[ "$SWITCH_TO" != "none" && "$SWITCH_TO" != "placeholder" ]]; then
  echo ""
  echo "NOTE: Switching embedding model changes the vector dimension."
  echo "You must reset and re-ingest demo data after switching:"
  echo "  bash scripts/reset-demo-environment.sh"
fi
