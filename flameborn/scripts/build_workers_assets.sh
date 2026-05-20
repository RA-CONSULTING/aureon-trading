#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DIST_DIR="$PROJECT_DIR/dist-workers"

mkdir -p "$DIST_DIR"
mkdir -p "$DIST_DIR/assets"
cp "$PROJECT_DIR/index.html" "$DIST_DIR/index.html"
cp "$PROJECT_DIR/script.js" "$DIST_DIR/script.js"
cp "$PROJECT_DIR/style.css" "$DIST_DIR/style.css"
cp "$PROJECT_DIR/assets/flameborn-llm-academy.jpg" "$DIST_DIR/assets/flameborn-llm-academy.jpg"
cp "$PROJECT_DIR/assets/flameborn-logo-current.jpg" "$DIST_DIR/assets/flameborn-logo-current.jpg"

cat > "$DIST_DIR/.assetsignore" <<'EOF'
_worker.js
wrangler.jsonc
EOF

echo "Zbudowano assets do: $DIST_DIR"
