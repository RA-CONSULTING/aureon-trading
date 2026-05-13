# Aureon Current Capabilities

This document describes the current public runtime surfaces and capability map. For commands, see [RUNNING.md](RUNNING.md) and [QUICK_START.md](QUICK_START.md). For a deeper end-user explanation of how all subsystems connect, see [SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md).

## Current Full-System Entrypoint

```powershell
.\AUREON_PRODUCTION_LIVE.cmd -WaitForRefresh -MarketStatusPort 8791
```

Safe launcher validation:

```powershell
.\AUREON_PRODUCTION_LIVE.cmd -ValidateOnly -NoOpen -MarketStatusPort 8791
```

Dev/audit ignition:

```powershell
python scripts/aureon_ignition.py --audit-only
```

## Capability Table

| Capability | What it does | Primary surfaces |
|---|---|---|
| Live/safe runtime supervision | Starts and supervises the organism from one terminal, publishes manifests, and keeps reboot timing visible. | `AUREON_PRODUCTION_LIVE.cmd`, `AUREON_WAKE_UP_FULL_AUTONOMOUS.ps1` |
| Multi-exchange market coverage | Runs unified market telemetry and exchange readiness for Kraken, Binance, Alpaca, and Capital. | `aureon/exchanges/unified_market_trader.py`, `aureon/exchanges/unified_market_status_server.py` |
| Spot/margin observation and trading readiness | Tracks runtime state, open positions, stale ticks, and flight-test reboot decisions before action. | `/api/terminal-state`, `/api/flight-test`, `/api/reboot-advice` |
| Exchange clients | Provides exchange-specific adapters for market data, balances, and order paths through the runtime gates. | `kraken_client.py`, `binance_client.py`, `alpaca_client.py`, `capital_client.py` |
| Cognitive order-intent path | Lets the cognitive layer observe, ask, reason, and emit order-intent evidence into the runtime rather than bypassing exchange gates. | `aureon/autonomous/aureon_self_questioning_ai.py`, `aureon/autonomous/aureon_mind_thought_action_hub.py` |
| HNC/Auris harmonic affect reporting | Produces timestamped cognitive trade evidence, harmonic affect state, and benchmark reporting. | `aureon_cognitive_trade_evidence.py`, `aureon_harmonic_affect_state.py`, `aureon_live_cognition_benchmark.py` |
| Self-questioning and mind hub | Runs the local thought/action hub and self-questioning loop for operator-visible reasoning. | `http://127.0.0.1:13002/api/thoughts` |
| Unified autonomous console | Shows organism pulse, runtime mirror, blockers, exchange state, evolution queue, audits, and current capability modes. | `frontend/src/App.tsx`, `frontend/src/services/aureonAutonomousFrontend.ts`, `frontend/src/hooks/useTerminalSync.ts` |
| Accounting/HMRC support pack tooling | Generates statutory support packs, CT support notes, and accounting evidence while keeping filing manual. | `Kings_Accounting_Suite/tools/generate_statutory_filing_pack.py`, `aureon/queen/accounting_context_bridge.py` |
| SaaS/security/local authorized audit tooling | Catalogs SaaS/frontend surfaces, security blockers, authorized local findings, and migration work orders. | `aureon/autonomous/aureon_saas_system_inventory.py`, `aureon/autonomous/hnc_authorized_attack_lab.py` |
| Continuous self-audit | Rebuilds readiness, switchboard, catalog, and mind-wiring reports for the console and operator review. | `aureon_organism_runtime_observer.py`, `aureon_system_readiness_audit.py`, `aureon_autonomous_capability_switchboard.py`, `aureon_repo_self_catalog.py`, `mind_wiring_audit.py` |

## Subsystem Atlas

| Subsystem | End-user purpose | Where to start |
|---|---|---|
| Launcher/supervisor | Start the whole organism once and know what is alive. | `AUREON_PRODUCTION_LIVE.cmd`, wake-up manifests |
| Exchange runtime | Bring Kraken, Binance, Alpaca, and Capital into one market state. | `aureon/exchanges/`, `/api/terminal-state` |
| Trading/portfolio/risk | Convert market state into readiness, intent, position, and execution evidence. | `aureon/trading/`, `aureon/portfolio/`, `aureon/strategies/` |
| Scanners/analytics | Find movement, anomalies, backtest context, and opportunity candidates. | `aureon/scanners/`, `aureon/analytics/` |
| Cognition/agents | Ask questions, route goals, choose capabilities, and expose thought/action state. | `aureon/autonomous/`, `/api/thoughts` |
| HNC/Auris evidence | Timestamp coherence, cognitive trade evidence, harmonic affect, and benchmark state. | `docs/audits/`, `aureon/autonomous/aureon_live_cognition_benchmark.py` |
| Frontend console | Give the operator a single live surface for runtime, blockers, audits, and capability modes. | `frontend/src/App.tsx`, `frontend/public/` |
| Accounting/HMRC support | Build evidence packs and manual filing support without changing accounts totals silently. | `Kings_Accounting_Suite/tools/`, `aureon/queen/accounting_context_bridge.py` |
| SaaS/security audit | Show frontend/SaaS blockers, owned-scope security findings, and migration work. | `aureon_saas_system_inventory.py`, `hnc_authorized_attack_lab.py` |
| Vault/research/memory | Keep local knowledge, learning history, research context, and voice/persona state. | `aureon/vault/`, `docs/`, `queen_research/` |
| Self-improvement | Catalog what exists, what is stale, and what can safely be improved next. | readiness audit, repo catalog, growth loop, self-enhancement lifecycle |

## Public Local Interfaces

| Interface | URL or file |
|---|---|
| Unified autonomous console | `http://127.0.0.1:8081/` |
| Runtime terminal state | `http://127.0.0.1:8791/api/terminal-state` |
| Flight test | `http://127.0.0.1:8791/api/flight-test` |
| Reboot advice | `http://127.0.0.1:8791/api/reboot-advice` |
| Mind thoughts | `http://127.0.0.1:13002/api/thoughts` |
| Wake-up manifest | `state/aureon_wake_up_manifest.json` |
| Frontend manifest mirror | `frontend/public/aureon_wake_up_manifest.json` |
| Cognitive trade evidence | `docs/audits/aureon_cognitive_trade_evidence.json` |
| Harmonic affect state | `docs/audits/aureon_harmonic_affect_state.json` and `frontend/public/aureon_harmonic_affect_state.json` |

## Runtime Modes

| Mode | Meaning |
|---|---|
| `safe_observation` | Runtime/feed is offline, or the environment is not in live mode. |
| `guarded_observe_plan` | Runtime is live but action is blocked by evidence such as stale data, booting state, open-position reboot timing, or unavailable downtime window. |
| `guarded_live_action` | Runtime is fresh, live mode is enabled, real order capability is enabled, and all runtime gates are clear. |

## Exchange Coverage

| Exchange | Current role |
|---|---|
| Kraken | Spot/margin-capable client path under unified exchange runtime. |
| Binance | Market and trade adapter with symbol normalization and account readiness checks. |
| Alpaca | Stocks/crypto adapter with account and position readiness checks. |
| Capital | CFD account and position adapter integrated into unified runtime state. |

The unified runtime is responsible for coordinating these clients. Individual exchange bots are not the recommended public run path.

## Manual Boundaries

Aureon can generate evidence, reports, runtime state, order intent, and accounting support packs. It does not remove the need for configured credentials, runtime freshness, safe reboot windows, valid exchange permissions, or manual review of filings/payments. Official filings, payments, credential reveal, and unowned security mutation remain manual or explicitly authorized operations.
