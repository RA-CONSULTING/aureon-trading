#!/usr/bin/env bash
set -euo pipefail

# ═══════════════════════════════════════════════════════════════════════════════
# FLAMEBORN + AUREON INTEGRATION HEALTH CHECK
# ═══════════════════════════════════════════════════════════════════════════════

AUREON_URL="${FLAMEBORN_AUREON_URL:-http://127.0.0.1:5566}"
FLAMEBORN_URL="${FLAMEBORN_WEB_URL:-http://127.0.0.1:4173}"
RUNTIME_URL="${FLAMEBORN_RUNTIME_URL:-http://127.0.0.1:7331}"

ERRORS=0

check_http() {
  local name="$1" url="$2" path="$3"
  local full_url="${url}${path}"
  echo -n "Checking $name ... "
  if curl -fsS "$full_url" >/dev/null 2>&1; then
    echo "OK ($full_url)"
    return 0
  else
    echo "FAIL ($full_url)"
    return 1
  fi
}

echo "═══════════════════════════════════════════════════════════════════════════════"
echo "  FLAMEBORN + AUREON INTEGRATION HEALTH CHECK"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""

# ── Aureon Vault UI ──
if ! check_http "Aureon Vault UI" "$AUREON_URL" "/api/status"; then
  ERRORS=$((ERRORS + 1))
fi

# ── Flameborn Web App ──
if ! check_http "Flameborn Web App" "$FLAMEBORN_URL" "/api/aureon/status"; then
  ERRORS=$((ERRORS + 1))
fi

# ── Flameborn Runtime (optional, only if port is listening) ──
if curl -fsS "${RUNTIME_URL}/health" >/dev/null 2>&1; then
  echo "Checking Flameborn Runtime ... OK ($RUNTIME_URL/health)"
else
  echo "Checking Flameborn Runtime ... NOT RUNNING (optional)"
fi

# ── Cross-connectivity: Flameborn → Aureon ──
echo -n "Checking Flameborn → Aureon bridge ... "
if curl -fsS -X POST "$AUREON_URL/api/message" \
  -H "Content-Type: application/json" \
  -d '{"text":"ping","voice":"queen","fast":true}' >/dev/null 2>&1; then
  echo "OK"
else
  # A 400 or 422 is also acceptable if the endpoint exists but rejects the payload
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$AUREON_URL/api/message" \
    -H "Content-Type: application/json" \
    -d '{"text":"ping","voice":"queen","fast":true}' 2>/dev/null || echo "000")
  if [[ "$STATUS" == "400" || "$STATUS" == "422" || "$STATUS" == "200" || "$STATUS" == "201" ]]; then
    echo "OK (HTTP $STATUS)"
  else
    echo "FAIL (HTTP $STATUS)"
    ERRORS=$((ERRORS + 1))
  fi
fi

echo ""
if [[ "$ERRORS" -eq 0 ]]; then
  echo "✓ All required services are healthy."
  exit 0
else
  echo "✗ $ERRORS service(s) failed health check."
  exit 1
fi
