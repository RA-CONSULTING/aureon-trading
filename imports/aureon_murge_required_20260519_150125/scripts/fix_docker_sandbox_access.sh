#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/home/l/CodexPROsSparrow"
TARGET_USER="l"
LOG_DIR="$PROJECT_DIR/logs"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
LOG_FILE="$LOG_DIR/fix-docker-sandbox-$TIMESTAMP.log"

mkdir -p "$LOG_DIR"
exec > >(tee -a "$LOG_FILE") 2>&1

usage() {
  cat <<'USAGE'
Usage:
  bash scripts/fix_docker_sandbox_access.sh
  sudo bash scripts/fix_docker_sandbox_access.sh

What this script does:
  1. Runs Docker + session diagnostics.
  2. Starts Docker daemon if needed.
  3. Ensures docker group exists.
  4. Ensures user "l" is in docker group.
  5. Tries to use docker group in current shell via sg/newgrp strategy.
  6. Runs project checks: npm run check, npm run sandbox:build.
  7. Verifies sandbox API endpoint with curl and JSON assertions.
  8. Writes full report to logs/fix-docker-sandbox-<timestamp>.log.

When to run with sudo:
  - If your shell cannot run privileged commands (systemctl/usermod/groupadd).
  - Script uses sudo automatically when not root, so you can also run it as normal user.

If re-login is still required:
  - run: newgrp docker
  - if that still fails: log out and log back in, then rerun this script.
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ ! -d "$PROJECT_DIR" ]]; then
  echo "FAIL: project directory does not exist: $PROJECT_DIR"
  exit 1
fi

SUDO=()
if [[ "$EUID" -ne 0 ]]; then
  SUDO=(sudo)
fi

declare -a BLOCKERS=()
declare -a WARNINGS=()
declare -a NEXT_STEPS=()

log_step() {
  echo
  echo "==== $1 ===="
}

add_blocker() {
  BLOCKERS+=("$1")
}

add_warning() {
  WARNINGS+=("$1")
}

add_next_step() {
  NEXT_STEPS+=("$1")
}

run_or_note() {
  local desc="$1"
  shift
  echo "-- $desc"
  if "$@"; then
    echo "   OK"
    return 0
  fi
  echo "   FAILED"
  return 1
}

run_as_docker_context() {
  local command="$1"
  if docker info >/dev/null 2>&1; then
    bash -lc "$command"
    return $?
  fi
  if command -v sg >/dev/null 2>&1; then
    if sg docker -c "docker info >/dev/null 2>&1"; then
      sg docker -c "$command"
      return $?
    fi
  fi
  return 1
}

log_step "Environment"
echo "Project: $PROJECT_DIR"
echo "Target user: $TARGET_USER"
echo "Current user: $(id -u -n)"
echo "Current groups: $(id -nG)"
echo "Log file: $LOG_FILE"

log_step "Diagnostics"
if ! command -v docker >/dev/null 2>&1; then
  add_blocker "docker binary is missing. Install docker.io first."
  echo "docker not found in PATH"
else
  echo "docker binary: $(command -v docker)"
fi

if command -v systemctl >/dev/null 2>&1; then
  echo "docker service status:"
  systemctl status docker --no-pager --lines=5 || true
else
  add_warning "systemctl not found; service checks are limited."
fi

echo "id -u -n: $(id -u -n)"
echo "id -nG: $(id -nG)"
echo "getent group docker:"
getent group docker || true
echo "ls -l /var/run/docker.sock:"
ls -l /var/run/docker.sock || true

DOCKER_INFO_OUTPUT="$(docker info 2>&1 || true)"
echo "docker info output:"
echo "$DOCKER_INFO_OUTPUT"

log_step "Automatic repair"
if command -v systemctl >/dev/null 2>&1; then
  if ! systemctl is-active --quiet docker; then
    if ! run_or_note "Enable and start docker service" "${SUDO[@]}" systemctl enable --now docker; then
      add_blocker "Could not start docker service."
    fi
  else
    echo "docker service already active."
  fi
fi

if ! getent group docker >/dev/null 2>&1; then
  if ! run_or_note "Create docker group" "${SUDO[@]}" groupadd docker; then
    add_blocker "Could not create docker group."
  fi
else
  echo "docker group already exists."
fi

if ! getent group docker | cut -d: -f4 | tr ',' '\n' | grep -qx "$TARGET_USER"; then
  if ! run_or_note "Add user '$TARGET_USER' to docker group" "${SUDO[@]}" usermod -aG docker "$TARGET_USER"; then
    add_blocker "Could not add user '$TARGET_USER' to docker group."
  fi
else
  echo "user '$TARGET_USER' already present in docker group entry."
fi

echo "Post-repair docker group entry:"
getent group docker || true
echo "Post-repair socket info:"
ls -l /var/run/docker.sock || true

SOCK_GROUP="$(stat -c '%G' /var/run/docker.sock 2>/dev/null || true)"
SOCK_MODE="$(stat -c '%a' /var/run/docker.sock 2>/dev/null || true)"
if [[ -n "$SOCK_GROUP" && "$SOCK_GROUP" != "docker" ]]; then
  add_warning "docker.sock group is '$SOCK_GROUP' (expected 'docker')."
fi
if [[ -n "$SOCK_MODE" && "$SOCK_MODE" != "660" && "$SOCK_MODE" != "666" ]]; then
  add_warning "docker.sock permissions are '$SOCK_MODE' (expected 660 or 666)."
fi

log_step "Docker context check (current shell)"
if docker info >/dev/null 2>&1; then
  echo "docker info works in current shell."
  DOCKER_CONTEXT_OK=1
else
  echo "docker info still fails in current shell."
  if run_as_docker_context "docker info >/dev/null 2>&1"; then
    echo "docker works via sg/newgrp context in this script."
    DOCKER_CONTEXT_OK=1
    add_warning "Current shell still not refreshed; script is using sg/newgrp context."
  else
    DOCKER_CONTEXT_OK=0
    add_blocker "Docker context still unavailable. Run 'newgrp docker' or re-login, then rerun script."
  fi
fi

log_step "Project verification"
if [[ "$DOCKER_CONTEXT_OK" -eq 1 ]]; then
  if ! run_as_docker_context "cd '$PROJECT_DIR' && npm run check"; then
    add_blocker "npm run check failed."
  fi
  if ! run_as_docker_context "cd '$PROJECT_DIR' && npm run sandbox:build"; then
    add_blocker "npm run sandbox:build failed."
  fi
else
  add_blocker "Skipped project verification because Docker context is not usable."
fi

log_step "API verification"
SANDBOX_JSON="$(curl -s http://127.0.0.1:4173/api/sandbox/status || true)"
if [[ -z "$SANDBOX_JSON" ]]; then
  add_blocker "Sandbox status endpoint did not return data. Ensure app server is running."
  echo "curl returned empty response."
else
  echo "sandbox status JSON:"
  echo "$SANDBOX_JSON"
  if command -v jq >/dev/null 2>&1; then
    docker_available="$(jq -r '.dockerAvailable // false' <<<"$SANDBOX_JSON")"
    docker_cli_available="$(jq -r '.dockerCliAvailable // false' <<<"$SANDBOX_JSON")"
    image_available="$(jq -r '.imageAvailable // false' <<<"$SANDBOX_JSON")"
  else
    docker_available=false
    docker_cli_available=false
    image_available=false
    grep -q '"dockerAvailable":true' <<<"$SANDBOX_JSON" && docker_available=true
    grep -q '"dockerCliAvailable":true' <<<"$SANDBOX_JSON" && docker_cli_available=true
    grep -q '"imageAvailable":true' <<<"$SANDBOX_JSON" && image_available=true
  fi

  [[ "$docker_available" == "true" ]] || add_blocker "sandbox status: dockerAvailable is not true."
  [[ "$docker_cli_available" == "true" ]] || add_blocker "sandbox status: dockerCliAvailable is not true."
  [[ "$image_available" == "true" ]] || add_blocker "sandbox status: imageAvailable is not true."

  if [[ "$DOCKER_CONTEXT_OK" -eq 1 && "$docker_available" != "true" ]] && grep -q 'EACCES /var/run/docker.sock' <<<"$SANDBOX_JSON"; then
    add_warning "Docker works in the repaired shell context, but the running app process still has stale group permissions."
    add_next_step "newgrp docker"
    add_next_step "cd $PROJECT_DIR"
    add_next_step "pkill -f 'node server.mjs' || true"
    add_next_step "pkill -f 'run_vault_ui.py' || true"
    add_next_step "bash scripts/start_aureon_brain_local.sh"
    add_next_step "curl -s http://127.0.0.1:4173/api/sandbox/status"
  fi
fi

log_step "Final summary"
if [[ "${#WARNINGS[@]}" -gt 0 ]]; then
  echo "Warnings:"
  for warning in "${WARNINGS[@]}"; do
    echo " - $warning"
  done
fi

if [[ "${#BLOCKERS[@]}" -gt 0 ]]; then
  echo "FAIL: unresolved blockers detected."
  for blocker in "${BLOCKERS[@]}"; do
    echo " - $blocker"
  done
  echo
  echo "Next manual commands to try:"
  if [[ "${#NEXT_STEPS[@]}" -gt 0 ]]; then
    for step in "${NEXT_STEPS[@]}"; do
      echo "  $step"
    done
  else
    echo "  newgrp docker"
    echo "  cd $PROJECT_DIR"
    echo "  npm run sandbox:build"
    echo "  curl -s http://127.0.0.1:4173/api/sandbox/status"
  fi
  echo
  echo "Full log: $LOG_FILE"
  exit 1
fi

echo "PASS: Docker sandbox access and project checks validated."
echo "Full log: $LOG_FILE"
