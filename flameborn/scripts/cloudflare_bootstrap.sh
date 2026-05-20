#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$PROJECT_DIR/.env"
DEFAULT_TOKEN_FILE="$HOME/Desktop/CloudFlareAPI"

TOKEN_FILE="${1:-$DEFAULT_TOKEN_FILE}"
VERIFY="${2:-}"

if [[ ! -f "$TOKEN_FILE" ]]; then
  echo "Brak pliku z tokenem: $TOKEN_FILE"
  exit 1
fi

first_line="$(sed -n '/\S/{p;q}' "$TOKEN_FILE")"
if [[ -z "${first_line:-}" ]]; then
  echo "Plik tokenu jest pusty: $TOKEN_FILE"
  exit 1
fi

if [[ "$first_line" == *"="* ]]; then
  token="${first_line#*=}"
else
  token="$first_line"
fi

token="$(printf '%s' "$token" | tr -d '[:space:]')"
if [[ -z "$token" ]]; then
  echo "Nie udało się odczytać tokenu z: $TOKEN_FILE"
  exit 1
fi

touch "$ENV_FILE"
tmp_file="$(mktemp)"
grep -v '^CLOUDFLARE_API_TOKEN=' "$ENV_FILE" > "$tmp_file" || true
printf 'CLOUDFLARE_API_TOKEN=%s\n' "$token" >> "$tmp_file"
mv "$tmp_file" "$ENV_FILE"

echo "Zapisano CLOUDFLARE_API_TOKEN do $ENV_FILE"
echo "Prefix tokenu: ${token:0:8}... (ukryty)"

if [[ "$VERIFY" == "--verify" ]]; then
  "$SCRIPT_DIR/cloudflare_check.sh" --zones
fi
