#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_HOST="${FLAMEBORN_RUNTIME_HOST:-127.0.0.1}"
RUNTIME_PORT="${FLAMEBORN_RUNTIME_PORT:-7331}"

cd "$APP_DIR"
echo "Starting flameborn-runtime on http://${RUNTIME_HOST}:${RUNTIME_PORT}"
echo "If Docker sandbox reports EACCES, restart this runtime from a shell refreshed with: newgrp docker"
exec node runtime/server.mjs
