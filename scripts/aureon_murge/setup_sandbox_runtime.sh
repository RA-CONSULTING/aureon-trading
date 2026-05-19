#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE_NAME="${SANDBOX_IMAGE:-flameborn-runtime:24.04}"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is not installed."
  echo "Install Docker first, then rerun this script."
  echo "Ubuntu/Debian example:"
  echo "  sudo apt-get update"
  echo "  sudo apt-get install -y docker.io"
  echo "  sudo usermod -aG docker \"$USER\""
  echo "Then log out and back in so the docker group applies."
  exit 1
fi

DOCKER_INFO_OUTPUT="$(docker info 2>&1 || true)"
if [[ "$DOCKER_INFO_OUTPUT" == *"permission denied"* ]]; then
  echo "Docker daemon is running, but this shell has no permission to /var/run/docker.sock."
  echo "Run:"
  echo "  sudo usermod -aG docker \"$USER\""
  echo "  newgrp docker"
  echo "Then rerun: npm run sandbox:build"
  exit 1
fi

if [[ "$DOCKER_INFO_OUTPUT" == *"Cannot connect to the Docker daemon"* ]] || [[ "$DOCKER_INFO_OUTPUT" == *"Is the docker daemon running"* ]]; then
  echo "Docker is installed but the daemon is not reachable."
  echo "Try:"
  echo "  sudo systemctl enable --now docker"
  exit 1
fi

if [[ "$DOCKER_INFO_OUTPUT" != *"Server:"* ]]; then
  echo "Docker check returned an unexpected response:"
  echo "$DOCKER_INFO_OUTPUT"
  exit 1
fi

docker build -t "$IMAGE_NAME" "$PROJECT_DIR/runtime"
echo "Built sandbox image: $IMAGE_NAME"
