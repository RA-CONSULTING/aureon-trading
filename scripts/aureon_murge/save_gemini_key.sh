#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT_DIR/.env"
PROJECT_VALUE="projects/49803487925"

update_env_line() {
  local key="$1"
  local value="$2"
  if grep -q "^${key}=" "$ENV_FILE" 2>/dev/null; then
    sed -i "s#^${key}=.*#${key}=${value}#" "$ENV_FILE"
  else
    printf '%s=%s\n' "$key" "$value" >> "$ENV_FILE"
  fi
}

mkdir -p "$ROOT_DIR"
touch "$ENV_FILE"
chmod 600 "$ENV_FILE"

if [[ -z "${GEMINI_API_KEY:-}" ]]; then
  read -r -s -p "Podaj GEMINI_API_KEY: " GEMINI_API_KEY
  echo
fi

if [[ -z "${GEMINI_API_KEY:-}" ]]; then
  echo "Brak GEMINI_API_KEY. Przerywam."
  exit 1
fi

update_env_line "GEMINI_API_KEY" "$GEMINI_API_KEY"
update_env_line "GOOGLE_API_KEY" "$GEMINI_API_KEY"
update_env_line "GEMINI_PROJECT" "$PROJECT_VALUE"

printf 'Zapisano konfiguracje w %s\n' "$ENV_FILE"
printf 'GEMINI_PROJECT=%s\n' "$PROJECT_VALUE"
printf 'GEMINI_API_KEY=***SET***\n'
