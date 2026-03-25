#!/usr/bin/env bash
# Simple restart loop for environments without systemd (dev/containers)
# Usage: ./scripts/run_micro_forever.sh [--env-file .env]

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE=""

if [[ "$1" == "--env-file" && -n "${2-}" ]]; then
  ENV_FILE="$2"
fi

if [[ -n "$ENV_FILE" && -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$ENV_FILE"
fi

cd "$REPO_ROOT"

while true; do
  echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] Starting Micro Profit Labyrinth (stocks enabled)"
  # Unbuffered Python output for real-time logs
  PYTHONUNBUFFERED=1 python3 micro_profit_labyrinth.py --duration 0 --yes || true
  echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] Process exited — restarting in 5s"
  sleep 5
done
