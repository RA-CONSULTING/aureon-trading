# Aureon Quick Start

Use this when you only need the current commands. For the full runbook, see [RUNNING.md](RUNNING.md). For the full subsystem map, see [SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md).

## 1. Install

```powershell
cd C:\Users\user\aureon-trading-integrated-main-20260508
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

Manifest files:

```text
state/aureon_wake_up_manifest.json
frontend/public/aureon_wake_up_manifest.json
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
| Market runtime | `aureon/exchanges/unified_market_trader.py`, `aureon/exchanges/unified_market_status_server.py` |
| Exchange clients | `aureon/exchanges/kraken_client.py`, `aureon/exchanges/binance_client.py`, `aureon/exchanges/alpaca_client.py`, `aureon/exchanges/capital_client.py` |
| Cognitive runtime | `aureon/autonomous/aureon_self_questioning_ai.py`, `aureon/autonomous/aureon_mind_thought_action_hub.py` |
| Observer and audits | `aureon/autonomous/aureon_organism_runtime_observer.py`, `aureon/autonomous/aureon_system_readiness_audit.py`, `aureon/autonomous/aureon_autonomous_capability_switchboard.py`, `aureon/autonomous/aureon_repo_self_catalog.py`, `aureon/autonomous/mind_wiring_audit.py` |
| HNC evidence | `aureon/autonomous/aureon_cognitive_trade_evidence.py`, `aureon/autonomous/aureon_harmonic_affect_state.py`, `aureon/autonomous/aureon_live_cognition_benchmark.py` |
| Frontend | `frontend/src/App.tsx`, `frontend/src/services/aureonAutonomousFrontend.ts`, `frontend/src/hooks/useTerminalSync.ts` |
| Accounting | `Kings_Accounting_Suite/tools/generate_statutory_filing_pack.py`, `aureon/queen/accounting_context_bridge.py` |

## Safety Notes

Live trading requires configured exchange credentials and clear runtime gates. The runtime keeps stale-data, reboot-window, open-position, API-rate, credential, filing, payment, and security boundaries visible. Validation and audit commands do not place orders.
