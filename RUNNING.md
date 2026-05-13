# Running Aureon

Last updated: 2026-05-13

This is the canonical runbook for the current Aureon runtime. The recommended full-organism terminal entrypoint is the production wake-up launcher, not individual exchange bots.

For a plain-English map of every major subsystem and what it can do, read [SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md).

The launcher starts the production supervisor, market runtime, status/telemetry server, mind hub, self-questioning loop, organism observer, manifest refresh, and unified frontend console.

## Current Entrypoints

| Purpose | Command |
|---|---|
| Full Windows production supervisor | `.\AUREON_PRODUCTION_LIVE.cmd -WaitForRefresh -MarketStatusPort 8791` |
| Validate launcher and flags without opening services | `.\AUREON_PRODUCTION_LIVE.cmd -ValidateOnly -NoOpen -MarketStatusPort 8791` |
| Dev/audit ignition path | `python scripts/aureon_ignition.py --audit-only` |
| Standalone runtime status server | `python aureon/exchanges/unified_market_status_server.py --port 8791` |
| Frontend development server | `cd frontend; npm run dev` |

Use port `8791` for the current runtime feed when older local sessions may still own `8790`.

## Run The Whole Organism

Open PowerShell:

```powershell
cd C:\Users\user\aureon-trading-integrated-main-20260508
.\AUREON_PRODUCTION_LIVE.cmd -WaitForRefresh -MarketStatusPort 8791
```

Leave this terminal open. It is the production supervisor. A healthy launch prints:

```text
Mode: LIVE_TRADING_OPERATOR_CONFIRMED + COGNITIVE_ORDER_INTENT_AUTHORITY + PRODUCTION_SUPERVISOR
LLM/cognitive order-intent authority: ON
Production supervisor attached
```

## Safe Validation

Run this before a live session, after pulling updates, or after editing launch docs:

```powershell
.\AUREON_PRODUCTION_LIVE.cmd -ValidateOnly -NoOpen -MarketStatusPort 8791
```

Validation checks the launcher profile and command wiring without starting the full console stack.

## Watch The Runtime

Open the unified console:

```text
http://127.0.0.1:8081/
```

Watch local endpoints from a second PowerShell window:

```powershell
Invoke-RestMethod http://127.0.0.1:8791/api/terminal-state | ConvertTo-Json -Depth 8
Invoke-RestMethod http://127.0.0.1:8791/api/flight-test | ConvertTo-Json -Depth 8
Invoke-RestMethod http://127.0.0.1:8791/api/reboot-advice | ConvertTo-Json -Depth 8
Invoke-RestMethod http://127.0.0.1:13002/api/thoughts | ConvertTo-Json -Depth 8
```

The console also reads the wake-up manifest from:

```text
state/aureon_wake_up_manifest.json
frontend/public/aureon_wake_up_manifest.json
```

## What The Launcher Starts

| Surface | Active path |
|---|---|
| Production wrapper | `AUREON_PRODUCTION_LIVE.cmd` |
| Full wake-up launcher | `AUREON_WAKE_UP_FULL_AUTONOMOUS.ps1` |
| Market runtime | `aureon/exchanges/unified_market_trader.py` |
| Runtime status server | `aureon/exchanges/unified_market_status_server.py` |
| Kraken client | `aureon/exchanges/kraken_client.py` |
| Binance client | `aureon/exchanges/binance_client.py` |
| Alpaca client | `aureon/exchanges/alpaca_client.py` |
| Capital client | `aureon/exchanges/capital_client.py` |
| Self-questioning loop | `aureon/autonomous/aureon_self_questioning_ai.py` |
| Mind hub | `aureon/autonomous/aureon_mind_thought_action_hub.py` |
| Organism observer | `aureon/autonomous/aureon_organism_runtime_observer.py` |
| Readiness audit | `aureon/autonomous/aureon_system_readiness_audit.py` |
| Capability switchboard | `aureon/autonomous/aureon_autonomous_capability_switchboard.py` |
| Repo self-catalog | `aureon/autonomous/aureon_repo_self_catalog.py` |
| Mind wiring audit | `aureon/autonomous/mind_wiring_audit.py` |
| Cognitive trade evidence | `aureon/autonomous/aureon_cognitive_trade_evidence.py` |
| Harmonic affect state | `aureon/autonomous/aureon_harmonic_affect_state.py` |
| Live cognition benchmark | `aureon/autonomous/aureon_live_cognition_benchmark.py` |
| Frontend shell | `frontend/src/App.tsx` |
| Frontend autonomous service | `frontend/src/services/aureonAutonomousFrontend.ts` |
| Terminal sync hook | `frontend/src/hooks/useTerminalSync.ts` |
| Accounting pack generator | `Kings_Accounting_Suite/tools/generate_statutory_filing_pack.py` |
| Accounting context bridge | `aureon/queen/accounting_context_bridge.py` |

## Runtime Modes

| Mode | Meaning |
|---|---|
| `safe_observation` | Runtime or feed is offline, or live environment is not enabled. |
| `guarded_observe_plan` | Live runtime is enabled, but action blockers such as stale ticks, open-position restart windows, or booting state remain active. |
| `guarded_live_action` | Runtime is fresh, live environment is enabled, real order capability is enabled, and guards are clear. |

The guard layer is not a separate trading strategy. It is the runtime evidence layer that prevents stale data, duplicate supervisors, unsafe reboot timing, credential mistakes, API-rate overload, payment/filing automation, and unowned security mutation from being treated as live action.

## Live Trading Preconditions

Before live operation, confirm:

- Exchange credentials are present in `.env` for Kraken, Binance, Alpaca, and Capital as applicable.
- Withdrawal permissions are disabled on exchange keys.
- The launcher validation command passes.
- `http://127.0.0.1:8791/api/terminal-state` reports `trading_ready: true` and `data_ready: true`.
- `stale` is `false`, or the console clearly shows a guarded state while waiting.
- `http://127.0.0.1:8791/api/flight-test` allows reboot only when the runtime is in a safe downtime window.

## Dev And Audit Paths

Use ignition for local audit and dry-run checks:

```powershell
python scripts/aureon_ignition.py --audit-only
python scripts/aureon_ignition.py --no-trade
python scripts/aureon_ignition.py --accounts-status
```

The production launcher remains the recommended full Windows organism entrypoint.

## Legacy Or Dev-Only Commands

Do not use old root scripts as the main run path. These are obsolete, deprecated, or dev-only references:

- `python aureon_live.py`
- `python aureon_unified_ecosystem.py`
- `python3 scripts/paperTradeSimulation.ts`
- `.\scripts\runners\run_unified_live.cmd`

Use the production launcher for full operation and `scripts/aureon_ignition.py --audit-only` for dev/audit checks.

## Verification

```powershell
.\AUREON_PRODUCTION_LIVE.cmd -ValidateOnly -NoOpen -MarketStatusPort 8791
.\.venv\Scripts\python.exe -m pytest tests/test_ignition_live_profile.py tests/test_unified_market_status_server.py tests/test_aureon_organism_runtime_observer.py -q
```

Verify the active OS/LLM/task/code/skill surfaces:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_safe_code_control.py tests/test_inhouse_llm_adapter_audit_mode.py tests/test_goal_capability_map.py tests/test_capability_growth_loop.py tests/vault/test_skill_executor_bridge.py -q
```

Frontend build check:

```powershell
cd frontend
npm run build
```

## Stop And Recovery

Press `Ctrl+C` in the production supervisor terminal to stop supervising. Background services keep their own process state.

To relaunch cleanly, close older elevated terminals that may still own ports `8081`, `8790`, or `8791`, then run the production launcher once. Do not force-kill the market runtime while positions are open; use the flight-test and reboot-advice endpoints to wait for a safe downtime window.
