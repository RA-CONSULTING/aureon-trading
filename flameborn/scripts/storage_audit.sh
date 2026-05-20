#!/usr/bin/env bash
set -euo pipefail

echo "== Filesystem =="
df -h / /c

echo
echo "== Top user directories =="
du -sh "$HOME/.cache" "$HOME/.npm" "$HOME/.local" "$HOME/Desktop" "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)" 2>/dev/null | sort -h

echo
echo "== Largest project paths =="
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
du -sh "$APP_DIR/desktop" "$APP_DIR/node_modules" "$APP_DIR/logs" 2>/dev/null | sort -h

echo
echo "== Desktop hotspots =="
du -sh "$HOME/Desktop"/* 2>/dev/null | sort -h | tail -n 20

echo
echo "== Cache hotspots =="
du -sh "$HOME/.cache"/* 2>/dev/null | sort -h | tail -n 20

echo
echo "== Candidate offload targets =="
for path in \
  "$HOME/Desktop" \
  "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)" \
  "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/desktop/dist" \
  "$HOME/.cache/google-chrome"; do
  if [ -e "$path" ]; then
    du -sh "$path" 2>/dev/null || true
  fi
done
