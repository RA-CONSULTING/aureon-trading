#!/usr/bin/env bash
set -euo pipefail

# ═══════════════════════════════════════════════════════════════════════════════
# AUREON + FLAMEBORN UNIFIED LAUNCHER
# Starts the Aureon skeleton (vault UI) and the Flameborn frontend together.
# ═══════════════════════════════════════════════════════════════════════════════

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FLAMEBORN_DIR="${REPO_ROOT}/flameborn"
AUREON_PORT="${AUREON_PORT:-5566}"
FLAMEBORN_PORT="${FLAMEBORN_PORT:-4173}"
RUNTIME_PORT="${FLAMEBORN_RUNTIME_PORT:-7331}"
FLAMEBORN_RUNTIME_ENABLED="${FLAMEBORN_RUNTIME_ENABLED:-false}"
VAULT_DIR="${AUREON_OBSIDIAN_VAULT_PATH:-$FLAMEBORN_DIR/logs/aureon-obsidian-vault}"

mkdir -p "$REPO_ROOT/logs" "$VAULT_DIR"

# ── Load shared environment ──
if [[ -f "$REPO_ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$REPO_ROOT/.env"
  set +a
fi

# ── Discover Python ──
AUREON_PYTHON="${AUREON_PYTHON:-}"
if [[ -z "$AUREON_PYTHON" ]]; then
  if [[ -x "$REPO_ROOT/.venv/Scripts/python.exe" ]]; then
    AUREON_PYTHON="$REPO_ROOT/.venv/Scripts/python.exe"
  elif [[ -x "$REPO_ROOT/.venv/bin/python" ]]; then
    AUREON_PYTHON="$REPO_ROOT/.venv/bin/python"
  else
    AUREON_PYTHON="$(command -v python3 || command -v python)"
  fi
fi

# ── Discover Node ──
if ! command -v node >/dev/null 2>&1; then
  echo "ERROR: node is not installed or not in PATH." >&2
  exit 1
fi

# ── Cleanup trap ──
cleanup() {
  echo ""
  echo "Shutting down unified services..."
  if [[ -n "${AUREON_PID:-}" ]] && kill -0 "$AUREON_PID" 2>/dev/null; then
    kill "$AUREON_PID" 2>/dev/null || true
    wait "$AUREON_PID" 2>/dev/null || true
  fi
  if [[ -n "${FLAMEBORN_PID:-}" ]] && kill -0 "$FLAMEBORN_PID" 2>/dev/null; then
    kill "$FLAMEBORN_PID" 2>/dev/null || true
    wait "$FLAMEBORN_PID" 2>/dev/null || true
  fi
  if [[ -n "${RUNTIME_PID:-}" ]] && kill -0 "$RUNTIME_PID" 2>/dev/null; then
    kill "$RUNTIME_PID" 2>/dev/null || true
    wait "$RUNTIME_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

# ═══════════════════════════════════════════════════════════════════════════════
# 1. Start Aureon Vault UI (skeleton backend)
# ═══════════════════════════════════════════════════════════════════════════════
echo "[1/3] Starting Aureon Vault UI on port $AUREON_PORT ..."
cd "$REPO_ROOT"
export AUREON_OBSIDIAN_VAULT_PATH="$VAULT_DIR"
export AUREON_VOICE_BACKEND="${AUREON_VOICE_BACKEND:-local}"
export AUREON_LLM_OFFLINE="${AUREON_LLM_OFFLINE:-0}"
export AUREON_LLM_BASE_URL="${AUREON_LLM_BASE_URL:-https://openrouter.ai/api/v1}"
export AUREON_LLM_MODEL="${AUREON_LLM_MODEL:-qwen/qwen-2.5-7b-instruct}"
if [[ -z "${AUREON_LLM_API_KEY:-}" && -n "${OPENROUTER_API_KEY:-}" ]]; then
  export AUREON_LLM_API_KEY="$OPENROUTER_API_KEY"
fi

"$AUREON_PYTHON" scripts/runners/run_vault_ui.py \
  --host 127.0.0.1 \
  --port "$AUREON_PORT" \
  --no-signals \
  --no-ollama \
  --obsidian-vault-path "$VAULT_DIR" \
  > "$REPO_ROOT/logs/aureon-vault-ui.log" 2>&1 &
AUREON_PID=$!

for _ in {1..30}; do
  if curl -fsS "http://127.0.0.1:$AUREON_PORT/api/status" >/dev/null 2>&1; then
    echo "      ✓ Aureon Vault UI ready: http://127.0.0.1:$AUREON_PORT"
    break
  fi
  sleep 1
done

if ! curl -fsS "http://127.0.0.1:$AUREON_PORT/api/status" >/dev/null 2>&1; then
  echo "      ✗ Aureon Vault UI failed to start. Log tail:" >&2
  tail -40 "$REPO_ROOT/logs/aureon-vault-ui.log" >&2 || true
  exit 1
fi

# ═══════════════════════════════════════════════════════════════════════════════
# 2. Start Flameborn Runtime (optional)
# ═══════════════════════════════════════════════════════════════════════════════
if [[ "$FLAMEBORN_RUNTIME_ENABLED" == "true" ]]; then
  echo "[2/3] Starting Flameborn Runtime on port $RUNTIME_PORT ..."
  cd "$FLAMEBORN_DIR"
  export FLAMEBORN_RUNTIME_HOST="127.0.0.1"
  export FLAMEBORN_RUNTIME_PORT="$RUNTIME_PORT"
  node runtime/server.mjs > "$REPO_ROOT/logs/flameborn-runtime.log" 2>&1 &
  RUNTIME_PID=$!

  for _ in {1..20}; do
    if curl -fsS "http://127.0.0.1:$RUNTIME_PORT/health" >/dev/null 2>&1; then
      echo "      ✓ Flameborn Runtime ready: http://127.0.0.1:$RUNTIME_PORT"
      break
    fi
    sleep 1
  done
else
  echo "[2/3] Flameborn Runtime skipped (set FLAMEBORN_RUNTIME_ENABLED=true to enable)"
fi

# ═══════════════════════════════════════════════════════════════════════════════
# 3. Start Flameborn Web App (frontend)
# ═══════════════════════════════════════════════════════════════════════════════
echo "[3/3] Starting Flameborn Web App on port $FLAMEBORN_PORT ..."
cd "$FLAMEBORN_DIR"
export AUREON_API_BASE_URL="${AUREON_API_BASE_URL:-http://127.0.0.1:$AUREON_PORT}"
export AUREON_CHAT_PATH="${AUREON_CHAT_PATH:-/api/message}"
export AUREON_VAULT_PATH="${AUREON_VAULT_PATH:-$FLAMEBORN_DIR/logs/aureon-vault}"
export AUREON_ENV_PATH="${AUREON_ENV_PATH:-$REPO_ROOT/.env}"
export PORT="$FLAMEBORN_PORT"
export GARY_AUREON_ROOT="$REPO_ROOT"
export LOCAL_TERMINAL_ENABLED="${LOCAL_TERMINAL_ENABLED:-true}"
export TERMINAL_ALLOW_REMOTE="${TERMINAL_ALLOW_REMOTE:-false}"
export SANDBOX_TERMINAL_ENABLED="${SANDBOX_TERMINAL_ENABLED:-true}"
export FLAMEBORN_RUNTIME_HOST="${FLAMEBORN_RUNTIME_HOST:-127.0.0.1}"
export FLAMEBORN_RUNTIME_PORT="${FLAMEBORN_RUNTIME_PORT:-$RUNTIME_PORT}"

node server.mjs > "$REPO_ROOT/logs/flameborn-aureon-app.log" 2>&1 &
FLAMEBORN_PID=$!

for _ in {1..20}; do
  if curl -fsS "http://127.0.0.1:$FLAMEBORN_PORT/api/aureon/status" >/dev/null 2>&1; then
    echo "      ✓ Flameborn Web App ready: http://127.0.0.1:$FLAMEBORN_PORT"
    break
  fi
  sleep 1
done

if ! curl -fsS "http://127.0.0.1:$FLAMEBORN_PORT/api/aureon/status" >/dev/null 2>&1; then
  echo "      ✗ Flameborn Web App failed to start. Log tail:" >&2
  tail -40 "$REPO_ROOT/logs/flameborn-aureon-app.log" >&2 || true
  exit 1
fi

# ═══════════════════════════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════════════════════════
echo ""
echo "═══════════════════════════════════════════════════════════════════════════════"
echo "  AUREON + FLAMEBORN UNIFIED SYSTEM IS ONLINE"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo "  Aureon Vault UI:  http://127.0.0.1:$AUREON_PORT"
echo "  Flameborn Web:    http://127.0.0.1:$FLAMEBORN_PORT"
if [[ "$FLAMEBORN_RUNTIME_ENABLED" == "true" ]]; then
  echo "  Flameborn Runtime: http://127.0.0.1:$RUNTIME_PORT"
fi
echo ""
echo "  Logs:"
echo "    - $REPO_ROOT/logs/aureon-vault-ui.log"
echo "    - $REPO_ROOT/logs/flameborn-aureon-app.log"
if [[ "$FLAMEBORN_RUNTIME_ENABLED" == "true" ]]; then
  echo "    - $REPO_ROOT/logs/flameborn-runtime.log"
fi
echo ""
echo "  Press Ctrl-C to stop all services."
echo "═══════════════════════════════════════════════════════════════════════════════"

# Wait for the web app (the primary foreground process)
wait "$FLAMEBORN_PID"
