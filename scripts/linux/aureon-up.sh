#!/usr/bin/env bash
# Aureon — bring up the whole system on Linux (one command).
# Default: full stack, DRY/PAPER (safe). Flags:
#   --live           arm live trading (AUREON_LIVE_TRADING=1) — the hard gates still hold
#   --organism-only  start only hnc + organism + operator (+ frontend), skip the swarm
#   --no-frontend    skip the Vite frontend
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

LIVE=0; ORGANISM_ONLY=0; NO_FRONTEND=0
for arg in "$@"; do
  case "$arg" in
    --live) LIVE=1 ;;
    --organism-only) ORGANISM_ONLY=1 ;;
    --no-frontend) NO_FRONTEND=1 ;;
    -h|--help) grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown flag: $arg" >&2; exit 2 ;;
  esac
done

if [ ! -x ".venv/bin/python" ]; then
  echo "No .venv found — run scripts/linux/install-linux.sh first." >&2
  exit 1
fi
export PATH="$ROOT/.venv/bin:$PATH"
export AUREON_PYTHON="$ROOT/.venv/bin/python"
mkdir -p state/logs

# Safe by default; --live only arms the runtime gate (conscience/gates still apply).
if [ "$LIVE" = "1" ]; then
  export AUREON_LIVE_TRADING=1
  echo "⚠️  LIVE trading armed (AUREON_LIVE_TRADING=1) — hard boundaries still hold."
else
  export AUREON_LIVE_TRADING=0
  export DRY_RUN=true
  echo "🛡️  Dry/paper mode (default). Pass --live to arm live trading."
fi

# Which groups autostart (the config gates swarm/frontend on these env vars).
export AUREON_START_SWARM=true
export AUREON_START_FRONTEND=true
[ "$ORGANISM_ONLY" = "1" ] && export AUREON_START_SWARM=false
[ "$NO_FRONTEND" = "1" ] && export AUREON_START_FRONTEND=false

echo "🌱 Aureon — bringing up the organism"
echo "   operator       http://localhost:8790   (/healthz)"
if [ "$ORGANISM_ONLY" != "1" ]; then
  echo "   pro-dashboard  http://localhost:8080    (/health)"
  echo "   market status  http://localhost:8791"
  echo "   mind hub       http://localhost:13002"
fi
[ "$NO_FRONTEND" != "1" ] && echo "   frontend       http://localhost:8081"

exec .venv/bin/supervisord -n -c deploy/supervisord.linux.conf
