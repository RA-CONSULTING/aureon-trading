# Aureon Quick Start

Use this when you only need the current commands. For the full runbook, see [RUNNING.md](RUNNING.md). For the full subsystem map, see [SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md).

## 1. Install

```powershell
cd C:\path\to\aureon-trading
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Frontend dependencies:

```powershell
cd frontend
npm install
cd ..
```

## 2. Validate The Launcher

```powershell
.\AUREON_PRODUCTION_LIVE.cmd -ValidateOnly -NoOpen -MarketStatusPort 8791
```

Use this command after pulling from `main`, before a live session, or after any launcher/doc change.

## 3. Run The Full Organism

```powershell
.\AUREON_PRODUCTION_LIVE.cmd -WaitForRefresh -MarketStatusPort 8791
```

Leave the terminal open. It supervises the live runtime, market feed, frontend console, mind hub, self-questioning loop, observer, and manifest refresh.

## 4. Open The Console

```text
http://127.0.0.1:8081/
```

Runtime endpoints:

```text
http://127.0.0.1:8791/api/terminal-state
http://127.0.0.1:8791/api/flight-test
http://127.0.0.1:8791/api/reboot-advice
http://127.0.0.1:13002/api/thoughts
```

If `terminal-state` returns `ok:false` but the status file and heartbeat are fresh, treat it as connected-but-guarded. Check `stale_reason`, `runtime_watchdog`, `executor_route_state`, and `/api/reboot-advice` before restarting. Do not restart the market runtime while open positions exist unless the flight-test reports `can_reboot_now: true`.

Manifest files:

```text
state/aureon_wake_up_manifest.json
frontend/public/aureon_wake_up_manifest.json
```

## 5. Optional Data Ocean

Run this in a second low-priority terminal when you want Aureon to widen live/history/context coverage without blocking the trading runtime:

```powershell
.\AUREON_DATA_OCEAN.cmd -Adaptive -CoverageProfile LicensedReachable
```

If Kraken or another private account endpoint starts rate-limiting, keep the public/context ocean running without private account-history sync:

```powershell
.\AUREON_DATA_OCEAN.cmd -Adaptive -CoverageProfile LicensedReachable -SkipAccountSync
```

The data ocean uses `aureon/core/exchange_rate_limit_registry.py` to expose official provider limits and cash-aware call budgets. Check `state/aureon_data_ocean_status.json` for each live exchange row's `official_rate_limit`, `cash_aware_call_plan`, and `rate_budget`.

Validation-only:

```powershell
.\AUREON_DATA_OCEAN.cmd -ValidateOnly -DryRun -RunOnce -NoIngest
```

## Dev And Audit Mode

```powershell
python scripts/aureon_ignition.py --audit-only
```

This is the development/audit ignition path. The production launcher is the full-organism entrypoint.

## Active File Map

| Area | Paths |
|---|---|
| Production launcher | `AUREON_PRODUCTION_LIVE.cmd`, `AUREON_WAKE_UP_FULL_AUTONOMOUS.ps1` |
| Data ocean | `AUREON_DATA_OCEAN.cmd`, `aureon/autonomous/aureon_data_ocean.py`, `aureon/autonomous/aureon_global_financial_coverage_map.py` |
| Official exchange rate budgets | `aureon/core/exchange_rate_limit_registry.py` |
| Market runtime | `aureon/exchanges/unified_market_trader.py`, `aureon/exchanges/unified_market_status_server.py` |
| Exchange clients | `aureon/exchanges/kraken_client.py`, `aureon/exchanges/binance_client.py`, `aureon/exchanges/alpaca_client.py`, `aureon/exchanges/capital_client.py` |
| Cognitive runtime | `aureon/autonomous/aureon_self_questioning_ai.py`, `aureon/autonomous/aureon_mind_thought_action_hub.py` |
| Observer and audits | `aureon/autonomous/aureon_organism_runtime_observer.py`, `aureon/autonomous/aureon_system_readiness_audit.py`, `aureon/autonomous/aureon_autonomous_capability_switchboard.py`, `aureon/autonomous/aureon_repo_self_catalog.py`, `aureon/autonomous/mind_wiring_audit.py` |
| HNC evidence | `aureon/autonomous/aureon_cognitive_trade_evidence.py`, `aureon/autonomous/aureon_harmonic_affect_state.py`, `aureon/autonomous/aureon_live_cognition_benchmark.py` |
| Frontend | `frontend/src/App.tsx`, `frontend/src/services/aureonAutonomousFrontend.ts`, `frontend/src/hooks/useTerminalSync.ts` |
| Accounting | `Kings_Accounting_Suite/tools/generate_statutory_filing_pack.py`, `aureon/queen/accounting_context_bridge.py` |

## Safety Notes

Live trading requires configured exchange credentials and clear runtime gates. The runtime keeps stale-data, reboot-window, open-position, API-rate, credential, filing, payment, and security boundaries visible. Validation and audit commands do not place orders.
