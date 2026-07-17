#!/usr/bin/env bash
# Aureon — show process + health status (Linux).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
export PATH="$ROOT/.venv/bin:$PATH"

echo "── processes ─────────────────────────────────────────────"
if [ -S state/supervisor.sock ]; then
  .venv/bin/supervisorctl -c deploy/supervisord.linux.conf status || true
else
  echo "supervisor not running (no state/supervisor.sock)"
fi

echo "── health ────────────────────────────────────────────────"
for probe in "operator http://localhost:8790/healthz" "pro-dashboard http://localhost:8080/health"; do
  name="${probe%% *}"; url="${probe##* }"
  code="$(curl -fsS -o /dev/null -w '%{http_code}' --max-time 3 "$url" 2>/dev/null || echo 000)"
  echo "  $name  $url  → $code"
done
