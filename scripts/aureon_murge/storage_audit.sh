#!/usr/bin/env bash
set -euo pipefail

echo "== Filesystem =="
df -h / /home/l

echo
echo "== Top user directories =="
du -sh "$HOME/.cache" "$HOME/.npm" "$HOME/.local" "$HOME/Desktop" "$HOME/CodexPROsSparrow" 2>/dev/null | sort -h

echo
echo "== Largest project paths =="
du -sh "$HOME/CodexPROsSparrow/desktop" "$HOME/CodexPROsSparrow/node_modules" "$HOME/CodexPROsSparrow/logs" 2>/dev/null | sort -h

echo
echo "== Desktop hotspots =="
du -sh "$HOME/Desktop"/* 2>/dev/null | sort -h | tail -n 20

echo
echo "== Cache hotspots =="
du -sh "$HOME/.cache"/* 2>/dev/null | sort -h | tail -n 20

echo
echo "== Candidate offload targets =="
for path in \
  "$HOME/Desktop/prace dark neutrino " \
  "$HOME/Desktop/gary repo nexus" \
  "$HOME/CodexPROsSparrow/desktop/dist" \
  "$HOME/.cache/google-chrome"; do
  if [ -e "$path" ]; then
    du -sh "$path" 2>/dev/null || true
  fi
done
