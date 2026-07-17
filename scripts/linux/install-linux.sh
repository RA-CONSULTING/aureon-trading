#!/usr/bin/env bash
# Aureon — bare-metal Linux installer (from source; not Docker).
# Creates a project venv, installs the organism core + the Linux-safe full deps,
# seeds .env, builds the frontend if Node is present. Idempotent.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

# ── Python 3.11+ ───────────────────────────────────────────────────────────────
PY="${PYTHON:-python3}"
if ! command -v "$PY" >/dev/null 2>&1; then
  echo "python3 not found. Install Python 3.11+ first." >&2; exit 1
fi
ver="$("$PY" -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
"$PY" - <<'PY' || { echo "Python 3.11+ required (found '"$ver"')." >&2; exit 1; }
import sys; raise SystemExit(0 if sys.version_info[:2] >= (3, 11) else 1)
PY
echo "🐍 Python $ver"

# ── venv + deps ──────────────────────────────────────────────────────────────
if [ ! -d .venv ]; then
  echo "📦 creating .venv"; "$PY" -m venv .venv
fi
# shellcheck disable=SC1091
. .venv/bin/activate
python -m pip install --upgrade pip
echo "📦 installing the organism core (pip install -e '.[operator]')"
pip install -e '.[operator]'
echo "📦 installing the Linux-safe full stack (requirements-linux.txt)"
pip install -r requirements-linux.txt

# ── .env ───────────────────────────────────────────────────────────────────────
if [ ! -f .env ] && [ -f .env.example ]; then
  cp .env.example .env
  echo "📝 seeded .env from .env.example — add your keys (optional; the system runs degraded without them)."
fi

# ── frontend (optional; only if Node is present) ─────────────────────────────────
if command -v npm >/dev/null 2>&1; then
  echo "🖥️  building the frontend (npm ci && npm run build)"
  ( cd frontend && npm ci && npm run build )
else
  echo "ℹ️  Node/npm not found — skipping the frontend build. Install Node 20+ to serve the dashboards."
fi

mkdir -p state/logs
cat <<'EOF'

✅ Aureon installed.
   Start the whole system:   scripts/linux/aureon-up.sh
   Organism only:            scripts/linux/aureon-up.sh --organism-only
   Arm live trading:         scripts/linux/aureon-up.sh --live   (still runtime-gated)
   Status / stop:            scripts/linux/aureon-status.sh  /  scripts/linux/aureon-down.sh
   Run as a service:         see deploy/systemd/ and docs/linux/LINUX_SETUP_GUIDE.md
EOF
