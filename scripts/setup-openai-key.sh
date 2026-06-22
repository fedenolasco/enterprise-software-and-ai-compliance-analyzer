#!/usr/bin/env bash
#
# Securely configures OpenAI API key in local .env files without exposing the key.
#
# Prompts the user for their OpenAI API key using a masked input, then writes
# it to the three local .env files (root, agent-brain, database-layer). The key
# is never printed, logged, or transmitted anywhere except the local .env files
# which are gitignored.
#
# Usage:
#   bash scripts/setup-openai-key.sh [--switch-to-openai]
#

set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SWITCH_TO_OPENAI="false"

for arg in "$@"; do
  case "$arg" in
    --switch-to-openai)
      SWITCH_TO_OPENAI="true"
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      echo "Usage: scripts/setup-openai-key.sh [--switch-to-openai]" >&2
      exit 2
      ;;
  esac
done

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

read_masked_input() {
  local prompt="$1"
  local input=""

  printf "%s" "$prompt" >&2

  # Disable echo and read character by character
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

echo "=== Secure OpenAI API Key Setup ==="
echo ""
echo "This script will:"
echo "  1. Prompt you for your OpenAI API key (input will be masked)"
echo "  2. Write the key to .env, agent-brain/.env, and database-layer/.env"
echo "  3. The key is NEVER printed, logged, or transmitted"
echo "  4. All .env files are gitignored and will never be committed"
echo ""

if [[ "$SWITCH_TO_OPENAI" == "true" ]]; then
  echo "The --switch-to-openai flag is set."
  echo "Provider settings will be switched from placeholder to openai."
  echo ""
fi

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
echo "Writing API key to .env files..."

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
  set_env_value "${ENV_FILES[$i]}" "OPENAI_API_KEY" "$API_KEY"
  echo "  Updated: ${ENV_LABELS[$i]}"

  if [[ "$SWITCH_TO_OPENAI" == "true" ]]; then
    set_env_value "${ENV_FILES[$i]}" "EMBEDDING_PROVIDER" "openai"
    set_env_value "${ENV_FILES[$i]}" "EMBEDDING_MODEL" "text-embedding-3-small"
    set_env_value "${ENV_FILES[$i]}" "EMBEDDING_DIMENSION" "1536"
    set_env_value "${ENV_FILES[$i]}" "MODEL_PROVIDER" "openai"
    set_env_value "${ENV_FILES[$i]}" "OPENAI_MODEL" "gpt-4o-mini"
    echo "    (provider switched to openai)"
  fi
done

echo ""
echo "Done. Your API key has been written to the local .env files."
echo "The key was NOT printed, logged, or transmitted anywhere else."
echo ""

if [[ "$SWITCH_TO_OPENAI" == "false" ]]; then
  echo "To switch from placeholder to OpenAI providers, either:"
  echo "  - Re-run this script with --switch-to-openai"
  echo "  - Or manually edit the .env files:"
  echo "      EMBEDDING_PROVIDER=openai"
  echo "      EMBEDDING_MODEL=text-embedding-3-small"
  echo "      EMBEDDING_DIMENSION=1536"
  echo "      MODEL_PROVIDER=openai"
  echo "      OPENAI_MODEL=gpt-4o-mini"
  echo ""
fi

echo "IMPORTANT: Verify .env files are gitignored before committing:"
echo "  git status --short"
echo "  (no .env files should appear)"
