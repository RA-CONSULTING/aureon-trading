# Aureon Trading System - Complete Structure Guide

## Quick Navigation

| Layer | Directory | Purpose | Files |
|-------|-----------|---------|-------|
| **Foundation** | `1_substrate/` | φ² Bridge foundation, market data, constants | 403 |
| **Intelligence** | `2_dynamics/` | LTDE dynamics, multi-branch logic | 514 |
| **Execution** | `3_forcing/` | NOW operator, gates, execution | 85 |
| **Outputs** | `4_output/` | Results, portfolio, metrics, dashboards | 187 |
| **Tests** | `tests/` | Validation, benchmarking | 130 |
| **Docs** | `docs/` | Documentation, research, archives | 201 |
| **DevOps** | `infrastructure/` | Deployment, CI/CD, production, config | 52 |
| **Scripts** | `scripts/` | Entry points, utilities, management | 148 |
| **Assets** | `Assets/` | Images, scientific data (CSV, BSP) | 28 |
| **State** | `state/` | Runtime state, logs, JSONL, backups | 22 |

**Total organized:** 2,681 files (including web stack)

---

## The Four-Layer Stack

### Layer 1: Substrate (1_substrate/)

**The φ² Bridge foundation. Everything starts here.**

```
1_substrate/
├── frequencies/                    (32 files)
│   ├── Harmonic constants, φ-ladder definitions
│   └── cache/   (harmonic cache)
├── market_feeds/                   (57 files)
│   └── Live market data (Alpaca, Binance, CoinAPI, Kraken, WebSocket)
└── data_models/                    (313 files)
    ├── Core schemas, caches, unified data structures
    ├── queen_configs/  (state configuration)
    ├── memory/  (CIA declassified references)
    └── wisdom/  (wisdom data & cache)
```

**Entry point:** Market data flows in, gets normalized to φ-aligned frequencies

**Quality:** All code here is deterministic, testable, and **contains zero trading logic**

---

### Layer 2: Dynamics (2_dynamics/)

**The living intelligence. LTDE implementation.**

```
2_dynamics/
├── trading_logic/                  (460 files)
│   └── Multi-path traders holding branches in superposition
├── probability_networks/           (34 files)
│   └── Coherence operators (Γ tracking), branch amplitudes
├── echo_feedback/                  (8 files)
│   └── Temporal delegation (τₖ = τ₀·φᵏ), cascade chains
└── multiverse_branches/            (12 files)
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
├── market_events/                  (19 files)
│   └── Opportunity detection, scanners, whale trackers
├── execution_engines/              (39 files)
│   └── Trade execution, order placement, smoke tests
├── coherence_gates/                (22 files)
│   └── Γ threshold enforcement (0.35-0.945 range)
└── real_time_triggers/             (4 files)
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
├── trade_outputs/                  (32 files)
│   └── Executed trades, signals, records, history
├── portfolio_management/           (47 files)
│   └── Position tracking, holdings, balances
├── performance_metrics/            (83 files)
│   ├── PnL, win-rate, edge detection, Q_choice
│   └── benchmarks/   (reports & benchmark runs)
└── dashboard/                      (23 files)
    └── Real-time visualization of shade-of-many
```

**Entry point:** Forced decisions from Layer 3 + branch metadata from Layer 2

**Output:** Historical records, dashboards, metrics for analysis and visualization

**Principle:** Never collapse the shade. Show probability distributions, not single answers.

---

## Python Import Path Setup

### Why This Matters

The codebase was reorganized into PEFCφS layers, but **629+ files still use flat module imports** like:

```python
from aureon_baton_link import link_system
from aureon_advanced_intelligence import AdvancedIntelligence
```

To make these work across the new layer structure, the repo ships with:

**`bootstrap_paths.py`** — adds all layer directories to `sys.path`

**`conftest.py`** — auto-imports `bootstrap_paths` for pytest

### Usage

**Running a script directly:**
```bash
cd /home/user/aureon-trading
python -c "import bootstrap_paths; import your_module"
```

**In a script:**
```python
import bootstrap_paths  # Add at the top of entry scripts
# Now all flat imports work
from aureon_baton_link import link_system
```

**Running pytest:**
```bash
# conftest.py handles it automatically — no changes needed
pytest tests/
```

**Setting PYTHONPATH (persistent):**
```bash
export PYTHONPATH="$PYTHONPATH:/path/to/aureon-trading/1_substrate/frequencies"
# ... or use bootstrap_paths.py instead
```

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
    │  Market Events    │  │  3_FORCING       │
    │  (triggers)       │  │  ├─ Market Events│
    │                   │  │  ├─ Execution    │
    └───────┬───────────┘  │  ├─ Coherence    │
            │              │  └─ Real-Time    │
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

## Supporting Directories

```
aureon-trading/
├── 1_substrate/          PEFCφS foundation layer
├── 2_dynamics/           PEFCφS intelligence layer
├── 3_forcing/            PEFCφS execution layer
├── 4_output/             PEFCφS results layer
│
├── aureon/               Main Python package (decoders, forensics)
├── Assets/               Images (PNG, SVG) & scientific data (CSV, BSP)
├── docs/                 Documentation, research, validation framework, archives
├── frontend/             React UI source
├── infrastructure/       Deployment (Docker, systemd), CI/CD, config, production
├── scripts/              Entry points, utilities, management, CLI, aureon_launcher
├── skills/               Claude Code custom skills
├── state/                Runtime state (logs, JSONL, backups)
├── tests/                Validation & benchmarking
│
├── api/                  Web API endpoint (RSS)
├── functions/            Cloudflare functions
├── netlify/              Netlify functions
├── public/               Static web assets (codex, oracle cards, glyphs)
├── server/               Node.js servers (earth-live-data, nexus-command)
├── static/               Static HTML (geometric glyphs)
├── supabase/             Database migrations & edge functions
├── templates/            HTML templates (queen dashboards)
│
├── ARCHITECTURE.md       Full PEFCφS formalism and design
├── STRUCTURE_GUIDE.md    This file — navigation guide
├── bootstrap_paths.py    Python path setup for flat imports
├── conftest.py           Pytest bootstrap
├── Dockerfile            Main container definition
├── Dockerfile.ephemeris  Ephemeris container
├── Procfile              Heroku-style process spec
├── app.yaml              Google App Engine config
└── LICENSE
```

---

## File Organization By Purpose

### If you're writing code that...

**...reads market data?**
→ `1_substrate/market_feeds/`

**...defines harmonic constants or φ-relationships?**
→ `1_substrate/frequencies/`

**...stores cached or unified data?**
→ `1_substrate/data_models/`

**...evaluates multiple trading scenarios in parallel?**
→ `2_dynamics/trading_logic/` or `2_dynamics/multiverse_branches/`

**...tracks branch coherence or amplitudes?**
→ `2_dynamics/probability_networks/`

**...detects market opportunities (scanning, whale tracking)?**
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

**...provides a CLI entry point?**
→ `scripts/entry_points/`

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

- **Γ(t)** — Branch coherence (0 to 1) — calculated in `2_dynamics/probability_networks/`
- **τ_sustain** — Duration in productive band — tracked in `3_forcing/coherence_gates/` and `4_output/performance_metrics/`
- **N_branch(t)** — Number of live branches — estimated in `2_dynamics/probability_networks/`
- **Q_choice** — Output quality during superposition — measured in `4_output/performance_metrics/`

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
- `docs/research/` — Research documents (validation framework, queen research)
- `docs/archives/` — Historical zips, RAINBOW-main, patches

---

**Last Updated:** 2026-04-23
**Organization:** PEFCφS (Position of Echo-Feedback Cognitive φ-Substrate)
**Maintainer:** Gary LeCkey
