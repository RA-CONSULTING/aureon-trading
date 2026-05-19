#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$PROJECT_DIR/.env"
DO_DEPLOY="${1:-}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Brak pliku .env w $PROJECT_DIR"
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

if [[ -z "${CLOUDFLARE_API_TOKEN:-}" ]]; then
  echo "Brak CLOUDFLARE_API_TOKEN w .env"
  exit 1
fi

cd "$PROJECT_DIR"

echo "Instaluję zależności npm..."
npm install

echo "Buduję assets dla Workers..."
npm run cf:build

echo "Sprawdzam autoryzację Wrangler..."
if ! npx wrangler whoami; then
  if [[ -n "${CLOUDFLARE_ACCOUNT_ID:-}" ]]; then
    echo "whoami nie zwrocil kont, ale CLOUDFLARE_ACCOUNT_ID jest ustawione - kontynuuje."
  else
  echo
  echo "Autoryzacja nie jest kompletna dla deployu Workers."
  echo "Uzupełnij w .env:"
  echo "  CLOUDFLARE_ACCOUNT_ID=<twoje_account_id>"
  echo "albo zaloguj OAuth:"
  echo "  npx wrangler login"
  exit 2
  fi
fi

if [[ "$DO_DEPLOY" == "--deploy" ]]; then
  echo "Wdrażam na workers.dev..."
  npm run cf:deploy
else
  echo "Bootstrap gotowy. Aby wdrożyć, uruchom:"
  echo "  bash scripts/workers_dev_bootstrap.sh --deploy"
fi
