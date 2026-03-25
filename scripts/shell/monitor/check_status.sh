#!/bin/bash
# Unified runtime status check for DigitalOcean + local process orchestration

set -u

echo "🦆⚔️ AUREON RUNTIME STATUS ⚔️🦆"
echo ""

echo "== Process status (aureon/orca/queen/ws/truth/deploy) =="
if pgrep -af "(aureon|orca|queen|ws_market_data_feeder|aureon_live_tv_station|deploy_digital_ocean)" >/tmp/aureon_proc_status.$$ 2>/dev/null; then
    cat /tmp/aureon_proc_status.$$
else
    echo "No matching runtime processes found"
fi
rm -f /tmp/aureon_proc_status.$$ >/dev/null 2>&1 || true

echo ""
echo "== Supervisor status =="
if [ -S "/workspaces/aureon-trading/supervisor.sock" ]; then
    supervisorctl -c supervisord.conf status 2>/dev/null || echo "Supervisor socket exists but status command failed"
else
    echo "Supervisor socket missing (/workspaces/aureon-trading/supervisor.sock)"
fi

echo ""
echo "== Docker status =="
if command -v docker >/dev/null 2>&1; then
    docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' 2>/dev/null || echo "Docker CLI available but daemon unreachable"
else
    echo "Docker CLI not installed"
fi

echo ""
echo "== Local health files =="
for f in orca_trade_history.json cost_basis_history.json active_position.json; do
    if [ -f "$f" ]; then
        echo "FOUND: $f ($(stat -c%s "$f" 2>/dev/null || echo '?') bytes)"
    else
        echo "MISSING: $f"
    fi
done

echo ""
echo "== Focused log activity (last 5 matching lines/file) =="
LOG_CANDIDATES="buyer1.log buyer2.log seller1.log seller2.log watcher.log logs/orca_trader.out.log logs/queen_eternal_machine.log logs/deployment_coordinator.log"
for log in $LOG_CANDIDATES; do
    if [ -f "$log" ]; then
        echo "=== $log ==="
        tail -n 50 "$log" | grep -E "(💰|💎|👁️|ENTERING|SOLD|Profit|Trades|ERROR|WARN|healthy|started|executed)" | tail -n 5 || echo "  No recent matching activity"
    fi
done
