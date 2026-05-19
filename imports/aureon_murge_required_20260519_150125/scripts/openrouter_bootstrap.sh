#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT_DIR/.env"
PORT="${PORT:-4173}"
DEFAULT_MODEL="${DEFAULT_MODEL:-openrouter/free}"
BROWSER_URL="http://127.0.0.1:${PORT}/?provider=openrouter&model=${DEFAULT_MODEL}"

has_env_key() {
  local key="$1"
  if command -v rg >/dev/null 2>&1; then
    rg -q "^${key}=" "$ENV_FILE"
    return
  fi
  grep -q "^${key}=" "$ENV_FILE"
}

ensure_env_line() {
  local key="$1"
  local value="$2"
  if [[ -f "$ENV_FILE" ]] && has_env_key "$key"; then
    sed -i "s#^${key}=.*#${key}=${value}#" "$ENV_FILE"
  else
    printf '%s=%s\n' "$key" "$value" >> "$ENV_FILE"
  fi
}

port_in_use() {
  if command -v ss >/dev/null 2>&1; then
    ss -ltn 2>/dev/null | grep -q ":${PORT} "
    return
  fi
  return 1
}

if [[ -z "${OPENROUTER_API_KEY:-}" ]]; then
  if [[ -f "$ENV_FILE" ]]; then
    set +u
    source "$ENV_FILE"
    set -u
  fi
fi

if [[ -z "${OPENROUTER_API_KEY:-}" ]]; then
  read -r -s -p "Podaj OPENROUTER_API_KEY: " OPENROUTER_API_KEY
  echo
fi

if [[ -z "${OPENROUTER_API_KEY:-}" ]]; then
  echo "Brak OPENROUTER_API_KEY. Przerywam."
  exit 1
fi

: > "$ENV_FILE.tmp"
if [[ -f "$ENV_FILE" ]]; then
  cat "$ENV_FILE" > "$ENV_FILE.tmp"
fi
mv "$ENV_FILE.tmp" "$ENV_FILE"
ensure_env_line "OPENROUTER_API_KEY" "$OPENROUTER_API_KEY"
ensure_env_line "PORT" "$PORT"
ensure_env_line "SPARROW_DEFAULT_PROVIDER" "openrouter"
ensure_env_line "SPARROW_DEFAULT_OPENROUTER_MODEL" "$DEFAULT_MODEL"

cd "$ROOT_DIR"
echo "Uruchamiam CodexPROsSparrow na ${BROWSER_URL}"
echo "Domyślny model OpenRouter: ${DEFAULT_MODEL}"

if port_in_use; then
  echo "Port ${PORT} jest już zajęty. Najpewniej serwer Sparrow już działa."
  echo "Otwórz w przeglądarce: ${BROWSER_URL}"
  exit 0
fi

node server.mjs
