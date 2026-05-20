#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SECRETS_DIR="${SECRETS_DIR:-$HOME/.config/codex-secrets}"
ENV_FILE="${ENV_FILE:-$APP_DIR/.env}"

mkdir -p "$SECRETS_DIR"
chmod 700 "$SECRETS_DIR"

usage() {
  cat <<'EOF'
Usage:
  scripts/setup_git_zenodo_secrets.sh --github-token TOKEN --zenodo-token TOKEN
  scripts/setup_git_zenodo_secrets.sh --prompt

Options:
  --github-token TOKEN   GitHub personal access token
  --zenodo-token TOKEN   Zenodo access token
  --prompt               Read tokens interactively from stdin

What it does:
  - stores tokens in ~/.config/codex-secrets/
  - writes/updates GITHUB_TOKEN and ZENODO_TOKEN in the repo .env
  - creates a timestamped backup of .env before editing
EOF
}

github_token="${GITHUB_TOKEN:-}"
zenodo_token="${ZENODO_TOKEN:-}"
prompt_mode=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --github-token)
      [[ $# -ge 2 ]] || { echo "Missing value for --github-token" >&2; exit 1; }
      github_token="$2"
      shift 2
      ;;
    --zenodo-token)
      [[ $# -ge 2 ]] || { echo "Missing value for --zenodo-token" >&2; exit 1; }
      zenodo_token="$2"
      shift 2
      ;;
    --prompt)
      prompt_mode=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ $prompt_mode -eq 1 ]]; then
  if [[ -z "$github_token" ]]; then
    read -r -p "GitHub token: " github_token
  fi
  if [[ -z "$zenodo_token" ]]; then
    read -r -p "Zenodo token: " zenodo_token
  fi
fi

if [[ -z "$github_token" || -z "$zenodo_token" ]]; then
  echo "Error: both GitHub and Zenodo tokens are required." >&2
  usage
  exit 1
fi

timestamp="$(date +%Y%m%d-%H%M%S)"
if [[ -f "$ENV_FILE" ]]; then
  cp "$ENV_FILE" "$ENV_FILE.bak-$timestamp"
fi

store_secret() {
  local name="$1"
  local value="$2"
  local file="$SECRETS_DIR/${name,,}"
  printf '%s' "$value" > "$file"
  chmod 600 "$file"
}

store_secret "GITHUB_TOKEN" "$github_token"
store_secret "ZENODO_TOKEN" "$zenodo_token"

tmp_env="$(mktemp)"
if [[ -f "$ENV_FILE" ]]; then
  GITHUB_TOKEN_VALUE="$github_token" ZENODO_TOKEN_VALUE="$zenodo_token" awk '
    BEGIN { seen_github=0; seen_zenodo=0 }
    /^GITHUB_TOKEN=/ { seen_github=1; next }
    /^ZENODO_TOKEN=/ { seen_zenodo=1; next }
    { print }
    END {
      if (!seen_github) print "GITHUB_TOKEN=" ENVIRON["GITHUB_TOKEN_VALUE"]
      if (!seen_zenodo) print "ZENODO_TOKEN=" ENVIRON["ZENODO_TOKEN_VALUE"]
    }
  ' "$ENV_FILE" > "$tmp_env"
else
  {
    printf 'GITHUB_TOKEN=%s\n' "$github_token"
    printf 'ZENODO_TOKEN=%s\n' "$zenodo_token"
  } > "$tmp_env"
fi
mv "$tmp_env" "$ENV_FILE"
chmod 600 "$ENV_FILE"

if command -v gh >/dev/null 2>&1; then
  printf '%s' "$github_token" | gh auth login --with-token >/dev/null 2>&1 || true
fi

cat <<EOF
Configured local secrets:
- $SECRETS_DIR/github_token
- $SECRETS_DIR/zenodo_token
- $ENV_FILE

Next step:
  source "$ENV_FILE"
EOF
