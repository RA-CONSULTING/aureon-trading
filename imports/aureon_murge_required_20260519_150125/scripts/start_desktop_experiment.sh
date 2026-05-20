#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$APP_DIR"
if [[ ! -d desktop/node_modules/electron ]]; then
  echo "Installing desktop dependencies first..."
  npm --prefix desktop install
fi

echo "Starting FlameBorn desktop experiment..."
exec npm --prefix desktop start
