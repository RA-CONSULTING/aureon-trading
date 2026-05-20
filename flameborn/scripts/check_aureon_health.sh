#!/usr/bin/env bash
set -euo pipefail

WEB_URL="${FLAMEBORN_WEB_URL:-http://127.0.0.1:4174}"
AUREON_URL="${FLAMEBORN_AUREON_URL:-http://127.0.0.1:5566}"

echo "Checking flAmeBorn app: $WEB_URL"
curl -fsS "$WEB_URL/api/aureon/status"
echo

echo "Checking Aureon bridge: $AUREON_URL"
if curl -fsS "$AUREON_URL/api/status"; then
  echo
  echo "Aureon bridge is live."
else
  echo "Aureon bridge is not reachable. The app should use local vault fallback."
fi
echo
