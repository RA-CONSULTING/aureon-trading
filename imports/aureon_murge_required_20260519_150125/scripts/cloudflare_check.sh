#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$PROJECT_DIR/.env"

SHOW_ZONES=false
if [[ "${1:-}" == "--zones" ]]; then
  SHOW_ZONES=true
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Brak pliku .env w: $PROJECT_DIR"
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

token="${CLOUDFLARE_API_TOKEN:-}"
if [[ -z "$token" ]]; then
  echo "Brak CLOUDFLARE_API_TOKEN w .env"
  exit 1
fi

echo "Sprawdzam token Cloudflare..."
verify_json="$(curl -sS --fail-with-body \
  -H "Authorization: Bearer $token" \
  -H "Content-Type: application/json" \
  "https://api.cloudflare.com/client/v4/user/tokens/verify")"

if ! printf '%s' "$verify_json" | grep -q '"success"[[:space:]]*:[[:space:]]*true'; then
  echo "Weryfikacja tokenu nie powiodła się."
  printf '%s\n' "$verify_json"
  exit 1
fi

status="$(printf '%s' "$verify_json" | sed -n 's/.*"status":"\([^"]*\)".*/\1/p')"
token_id="$(printf '%s' "$verify_json" | sed -n 's/.*"id":"\([^"]*\)".*/\1/p')"
echo "Token OK. Status: ${status:-unknown}, id: ${token_id:-unknown}"

if [[ "$SHOW_ZONES" == "true" ]]; then
  echo "Pobieram listę stref (zones)..."
  zones_json="$(curl -sS --fail-with-body \
    -H "Authorization: Bearer $token" \
    -H "Content-Type: application/json" \
    "https://api.cloudflare.com/client/v4/zones?per_page=50")"

  if ! printf '%s' "$zones_json" | grep -q '"success"[[:space:]]*:[[:space:]]*true'; then
    echo "Nie udało się pobrać zones (sprawdź uprawnienia tokenu)."
    printf '%s\n' "$zones_json"
    exit 1
  fi

  total_count="$(printf '%s' "$zones_json" | sed -n 's/.*"total_count":\([0-9][0-9]*\).*/\1/p')"
  if [[ "${total_count:-0}" == "0" ]]; then
    echo "Brak stref na koncie Cloudflare (total_count=0)."
    exit 0
  fi

  echo "Zones (name | id):"
  printf '%s\n' "$zones_json" | tr '{' '\n' | grep '"name":"\|"id":"' | sed -n 'N;s/.*"name":"\([^"]*\)".*"id":"\([^"]*\)".*/- \1 | \2/p' || true
fi
