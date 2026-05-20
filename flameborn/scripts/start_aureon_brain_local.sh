#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AUREON_DIR="${AUREON_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
AUREON_PORT="${AUREON_PORT:-5566}"
APP_PORT="${PORT:-4173}"
VAULT_DIR="${AUREON_OBSIDIAN_VAULT_PATH:-$APP_DIR/logs/aureon-obsidian-vault}"
FLAMEBORN_SKIP_WEB_SERVER="${FLAMEBORN_SKIP_WEB_SERVER:-false}"
BRIDGE_ENABLED="true"

if [[ ! -d "$AUREON_DIR" ]]; then
  BRIDGE_ENABLED="false"
  echo "Nie znaleziono repo Aureon: $AUREON_DIR" >&2
  echo "Uruchamiam tylko appke flAmeBornLLC z lokalnym fallbackiem Aureon." >&2
fi

mkdir -p "$APP_DIR/logs" "$VAULT_DIR"

if [[ -f "$APP_DIR/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$APP_DIR/.env"
  set +a
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "Brak python3." >&2
  exit 1
fi
if ! command -v node >/dev/null 2>&1; then
  echo "Brak node." >&2
  exit 1
fi

if command -v docker >/dev/null 2>&1; then
  if docker info >/dev/null 2>&1; then
    DOCKER_SANDBOX_STATUS="ready"
  else
    DOCKER_SANDBOX_STATUS="stale-session"
  fi
else
  DOCKER_SANDBOX_STATUS="missing"
fi

if [[ "$BRIDGE_ENABLED" == "true" ]]; then
  AUREON_PYTHON="${AUREON_PYTHON:-$AUREON_DIR/.venv-bridge/bin/python}"
  if [[ ! -x "$AUREON_PYTHON" ]]; then
    AUREON_PYTHON="$(command -v python3)"
  fi
fi

cleanup() {
  if [[ -n "${AUREON_PID:-}" ]] && kill -0 "$AUREON_PID" 2>/dev/null; then
    kill "$AUREON_PID" 2>/dev/null || true
  fi
  if [[ -n "${APP_PID:-}" ]] && kill -0 "$APP_PID" 2>/dev/null; then
    kill "$APP_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

if [[ "$BRIDGE_ENABLED" == "true" ]]; then
  cd "$AUREON_DIR"
  export AUREON_VOICE_BACKEND="${AUREON_VOICE_BACKEND:-local}"
  export AUREON_LLM_OFFLINE="${AUREON_LLM_OFFLINE:-0}"
  export AUREON_LLM_BASE_URL="${AUREON_LLM_BASE_URL:-https://openrouter.ai/api/v1}"
  export AUREON_LLM_MODEL="${AUREON_LLM_MODEL:-qwen/qwen-2.5-7b-instruct}"
  if [[ -z "${AUREON_LLM_API_KEY:-}" && -n "${OPENROUTER_API_KEY:-}" ]]; then
    export AUREON_LLM_API_KEY="$OPENROUTER_API_KEY"
  fi
  export AUREON_OBSIDIAN_VAULT_PATH="$VAULT_DIR"
  "$AUREON_PYTHON" scripts/runners/run_vault_ui.py \
    --host 127.0.0.1 \
    --port "$AUREON_PORT" \
    --no-signals \
    --no-ollama \
    --obsidian-vault-path "$VAULT_DIR" \
    > "$APP_DIR/logs/aureon-vault-ui.log" 2>&1 &
  AUREON_PID=$!

  for _ in {1..30}; do
    if curl -fsS "http://127.0.0.1:$AUREON_PORT/api/status" >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done

  if ! curl -fsS "http://127.0.0.1:$AUREON_PORT/api/status" >/dev/null 2>&1; then
    echo "Aureon Phi Bridge nie wystartował. Log:" >&2
    tail -80 "$APP_DIR/logs/aureon-vault-ui.log" >&2 || true
    exit 1
  fi
else
  AUREON_PORT=""
fi

if [[ "$FLAMEBORN_SKIP_WEB_SERVER" != "true" ]]; then
  cd "$APP_DIR"
  if [[ -n "$AUREON_PORT" ]]; then
    export AUREON_API_BASE_URL="${AUREON_API_BASE_URL:-http://127.0.0.1:$AUREON_PORT}"
  fi
  export AUREON_CHAT_PATH="${AUREON_CHAT_PATH:-/api/message}"
  export AUREON_VAULT_PATH="$APP_DIR/logs/aureon-vault"
  export PORT="$APP_PORT"
  node server.mjs > "$APP_DIR/logs/flameborn-aureon-app.log" 2>&1 &
  APP_PID=$!

  for _ in {1..20}; do
    if curl -fsS "http://127.0.0.1:$APP_PORT/api/aureon/status" >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done
fi

cat <<MSG
Aureon Phi Bridge: $([[ -n "$AUREON_PORT" ]] && echo "http://127.0.0.1:$AUREON_PORT" || echo "not started")
flAmeBorn app:      http://127.0.0.1:$APP_PORT
Obsidian vault:     $VAULT_DIR

Provider w apce: Aureon Brain
Model/głos: aureon-queen, aureon-council, aureon-architect, aureon-lover, aureon-vault
Aureon voice backend: $AUREON_VOICE_BACKEND
Aureon LLM endpoint:   $AUREON_LLM_BASE_URL
Aureon LLM model:      $AUREON_LLM_MODEL
Docker sandbox:        $DOCKER_SANDBOX_STATUS
Web server started:    $([[ "$FLAMEBORN_SKIP_WEB_SERVER" == "true" ]] && echo "no" || echo "yes")

$(if [[ "$DOCKER_SANDBOX_STATUS" == "stale-session" ]]; then
  cat <<'EOF'
Uwaga: Docker jest zainstalowany, ale ten proces appki nie ma jeszcze odświeżonych uprawnień do /var/run/docker.sock.
Jeśli sandbox ma działać, uruchom apkę z odświeżonej sesji:
  newgrp docker
  cd "$APP_DIR"
  bash scripts/start_aureon_brain_local.sh
EOF
fi)

Logi:
- $APP_DIR/logs/aureon-vault-ui.log
$(if [[ "$FLAMEBORN_SKIP_WEB_SERVER" != "true" ]]; then echo "- $APP_DIR/logs/flameborn-aureon-app.log"; fi)

Ctrl-C zatrzyma uruchomione procesy.
MSG

if [[ "$FLAMEBORN_SKIP_WEB_SERVER" == "true" ]]; then
  if [[ "$BRIDGE_ENABLED" == "true" && -n "${AUREON_PID:-}" ]]; then
    wait "$AUREON_PID"
  fi
  exit 0
fi

wait "$APP_PID"
