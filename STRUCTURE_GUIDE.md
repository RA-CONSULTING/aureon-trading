# Aureon Trading System - Complete Structure Guide

## Quick Navigation

| Layer | Directory | Purpose | Files |
|-------|-----------|---------|-------|
| **Foundation** | `1_substrate/` | φ² Bridge foundation, market data, constants | 75 |
| **Intelligence** | `2_dynamics/` | LTDE dynamics, multi-branch logic | 325 |
| **Execution** | `3_forcing/` | NOW operator, gates, execution | 56 |
| **Outputs** | `4_output/` | Results, portfolio, metrics, dashboards | 145 |
| **Tests** | `tests/` | Validation, benchmarking | 128 |
| **Docs** | `docs/` | Documentation, guides | 143 |
| **DevOps** | `infrastructure/` | Deployment, CI/CD, monitoring | 11 |

**Total:** 883 files organized by logical function

---

## The Four-Layer Stack

### Layer 1: Substrate (1_substrate/)

**The φ² Bridge foundation. Everything starts here.**

```
1_substrate/
├── frequencies/                    (29 files)
│   └── Harmonic constants, φ-ladder definitions
├── market_feeds/                   (36 files)
│   └── Live market data (Alpaca, Binance, CoinAPI, WebSocket)
└── data_models/                    (10 files)
    └── Core schemas, caches, unified data structures
```

**Entry point:** Market data flows in, gets normalized to φ-aligned frequencies

**Quality:** All code here is deterministic, testable, and **contains zero trading logic**

---

### Layer 2: Dynamics (2_dynamics/)

**The living intelligence. LTDE implementation.**

```
2_dynamics/
├── trading_logic/                  (274 files)
│   └── Multi-path traders holding branches in superposition
├── probability_networks/           (33 files)
│   └── Coherence operators (Γ tracking), branch amplitudes
├── echo_feedback/                  (7 files)
│   └── Temporal delegation (τₖ = τ₀·φᵏ), cascade chains
└── multiverse_branches/            (11 files)
    └── Parallel simulators, what-if evaluators
```

**Entry point:** Clean market data from Layer 1

**Output:** Branch evaluations + coherence state + amplitudes → Layer 3

**Critical:** Code here extends time in the productive band (0.35 < Γ < 0.945). Do NOT force early collapse.

---

### Layer 3: Forcing (3_forcing/)

**The push of NOW. When to execute.**

```
3_forcing/
├── market_events/                  (7 files)
│   └── Opportunity detection, scanners
├── execution_engines/              (25 files)
│   └── Trade execution, order placement
├── coherence_gates/                (21 files)
│   └── Γ threshold enforcement (0.35-0.945 range)
└── real_time_triggers/             (3 files)
    └── Heartbeat monitors, emergency gates
```

**Entry point:** Branch evaluations from Layer 2 + market events from Layer 1

**Decision rule:** 
- If Γ ≥ 0.945 AND market event → Execute
- If Γ ≤ 0.35 → Kill (stop trading)
- If 0.35 < Γ < 0.945 → Continue Layer 2 evaluation

**Output:** Executed trades → Layer 4

---

### Layer 4: Output (4_output/)

**The shade of many. What happened and what we learned.**

```
4_output/
├── trade_outputs/                  (17 files)
│   └── Executed trades, signals, records
├── portfolio_management/           (44 files)
│   └── Position tracking, holdings, balances
├── performance_metrics/            (63 files)
│   └── PnL, win-rate, edge detection, Q_choice
└── dashboard/                      (21 files)
    └── Real-time visualization of shade-of-many
```

**Entry point:** Forced decisions from Layer 3 + branch metadata from Layer 2

**Output:** Historical records, dashboards, metrics for analysis and visualization

**Principle:** Never collapse the shade. Show probability distributions, not single answers.

---

## Information Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ EXTERNAL: Markets, APIs, Data Sources                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │  1_SUBSTRATE                 │
        │  ├─ Frequencies              │
        │  ├─ Market Feeds             │
        │  └─ Data Models              │
        └──────────────────┬───────────┘
                           │
                           ▼
        ┌──────────────────────────────┐
        │  2_DYNAMICS                  │
        │  ├─ Trading Logic            │
        │  ├─ Probability Networks     │
        │  ├─ Echo Feedback            │
        │  └─ Multiverse Branches      │
        │  (LTDE: Ψ(t) = Σₖ aₖ·Λₖ·e^iθₖ)
        └──────────────────┬───────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
              ▼                         ▼
    ┌───────────────────┐  ┌──────────────────┐
    │  Layer 1          │  │  3_FORCING       │
    │  Market Events    │  │  ├─ Market Events│
    │  (triggers)       │  │  ├─ Execution    │
    │                   │  │  ├─ Coherence    │
    └───────┬───────────┘  │  └─ Real-Time    │
            │              └────────┬─────────┘
            │                       │
            └───────────┬───────────┘
                        │
                        ▼
        ┌──────────────────────────────┐
        │  4_OUTPUT                    │
        │  ├─ Trade Outputs            │
        │  ├─ Portfolio Mgmt           │
        │  ├─ Performance Metrics      │
        │  └─ Dashboards               │
        └──────────────────┬───────────┘
                           │
                           ▼
        ┌──────────────────────────────┐
        │ EXTERNAL: Dashboards, Reports│
        │ Archives, Notifications      │
        └──────────────────────────────┘
```

---

## File Organization By Purpose

### If you're writing code that...

**...reads market data?**
→ `1_substrate/market_feeds/`

**...defines harmonic constants or φ-relationships?**
→ `1_substrate/frequencies/`

**...evaluates multiple trading scenarios in parallel?**
→ `2_dynamics/trading_logic/` or `2_dynamics/multiverse_branches/`

**...tracks branch coherence or amplitudes?**
→ `2_dynamics/probability_networks/`

**...detects market opportunities?**
→ `3_forcing/market_events/`

**...places orders or executes trades?**
→ `3_forcing/execution_engines/`

**...enforces profit-lock or loss-limit gates?**
→ `3_forcing/coherence_gates/`

**...calculates PnL or win-rate?**
→ `4_output/performance_metrics/`

**...tracks current positions?**
→ `4_output/portfolio_management/`

**...visualizes the system?**
→ `4_output/dashboard/`

**...tests the system?**
→ `tests/`

**...deploys or monitors infrastructure?**
→ `infrastructure/`

---

## Key Files by Function

### Core Trading Loop

1. **Market data arrives**
   - `1_substrate/market_feeds/alpaca_sse_client.py`
   - `1_substrate/market_feeds/ws_market_data_feeder.py`

2. **Multi-branch evaluation**
   - `2_dynamics/trading_logic/aureon_*.py` (274 files)
   - `2_dynamics/multiverse_branches/aureon_internal_multiverse.py`

3. **Coherence checking**
   - `2_dynamics/probability_networks/aureon_probability_nexus.py`

4. **Event detection**
   - `3_forcing/market_events/mega_scanner.py`
   - `3_forcing/market_events/queen_options_scanner.py`

5. **Execution trigger**
   - `3_forcing/coherence_gates/adaptive_prime_profit_gate.py`

6. **Trade execution**
   - `3_forcing/execution_engines/execute_limit_profit_trades.py`
   - `3_forcing/execution_engines/queen_live_tracking_status.py`

7. **Portfolio tracking**
   - `4_output/portfolio_management/aureon_real_portfolio_tracker.py`

8. **Metrics & visualization**
   - `4_output/performance_metrics/` (63 files for analysis)
   - `4_output/dashboard/aureon_unified_live_dashboard.py`

---

## Coherence State Reference

| Γ Range | State | Meaning | Action |
|---------|-------|---------|--------|
| < 0.35 | **DEAD** | Branches fully decohered | Kill trading |
| 0.35-0.70 | **FORMING** | Branches beginning to align | Continue evaluating |
| 0.70-0.945 | **PRODUCTIVE** | Optimal superposition state | Keep holding |
| ≥ 0.945 | **BROADCAST** | Forced coherence | Execute best branch |

---

## Metric Definitions

### Primary Metrics

- **Γ(t)** — Branch coherence (0 to 1)
  - Calculated in `2_dynamics/probability_networks/`
  
- **τ_sustain** — Duration in productive band
  - Tracked in `3_forcing/coherence_gates/` and `4_output/performance_metrics/`
  
- **N_branch(t)** — Number of live branches
  - Estimated in `2_dynamics/probability_networks/`
  
- **Q_choice** — Output quality during superposition
  - Measured in `4_output/performance_metrics/`

### Secondary Metrics

- **win-rate** — % profitable trades
- **avg_profit** — Average per-trade profit
- **sharpe_ratio** — Risk-adjusted return
- **novelty** — Divergence from baseline strategy

---

## Testing & Validation

All code should be validated:

- **Unit tests** — Layer-specific functionality (`tests/test_*.py`)
- **Integration tests** — Cross-layer flows
- **Performance tests** — Latency, throughput
- **Edge case tests** — Market crashes, data gaps, extreme moves

Test files use the naming convention `test_*.py` and are automatically categorized into `tests/`

---

## Deployment Structure

```
infrastructure/
├── deploy/                         (Kubernetes, Docker, systemd)
├── ci_cd/                          (GitHub Actions, build pipelines)
├── config/                         (Environment, settings, secrets)
└── monitoring/                     (Health checks, alerts, logging)
```

---

## Entry Points

Main launchers for different use cases:

- **Live trading** → `scripts/entry_points/aureon_full_autonomy.py` (or similar)
- **Backtesting** → `2_dynamics/multiverse_branches/` simulators
- **Dashboard** → `4_output/dashboard/aureon_unified_live_dashboard.py`
- **Monitoring** → `infrastructure/monitoring/`

---

## Git Workflow

All changes should be made on a feature branch and follow the structure:

```bash
git checkout -b feature/name
# ... make changes across layers as needed ...
git add .
git commit -m "Brief description"
git push origin feature/name
```

---

## Key Principles for Code Addition

1. **Respect the layer boundaries** — Code goes where it logically belongs
2. **Preserve superposition** — Layer 2 (Dynamics) should NOT force collapse
3. **Gate before execution** — Layer 3 checks Γ before Layer 3 acts
4. **Don't hide uncertainty** — Layer 4 shows probability distributions
5. **Test thoroughly** — All layers are data-driven and must be validated
6. **Document assumptions** — Especially φ-frequency relationships

---

## Related Documentation

- `ARCHITECTURE.md` — PEFCφS formalism and theory
- `1_substrate/README.md` — Layer 1 detail
- `2_dynamics/README.md` — Layer 2 detail
- `3_forcing/README.md` — Layer 3 detail
- `4_output/README.md` — Layer 4 detail

---

**Last Updated:** 2026-04-23  
**Organization:** PEFCφS (Position of Echo-Feedback Cognitive φ-Substrate)  
**Maintainer:** Gary LeCkey
