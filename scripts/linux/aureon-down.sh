#!/usr/bin/env bash
# Aureon — stop the whole system (Linux).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
export PATH="$ROOT/.venv/bin:$PATH"

if [ -S state/supervisor.sock ]; then
  .venv/bin/supervisorctl -c deploy/supervisord.linux.conf shutdown || true
  echo "🌙 Aureon shutdown signalled."
elif [ -f state/supervisord.pid ]; then
  kill "$(cat state/supervisord.pid)" 2>/dev/null || true
  echo "🌙 Sent SIGTERM to supervisord (pid $(cat state/supervisord.pid))."
else
  echo "Aureon does not appear to be running (no supervisor socket/pid)."
fi
