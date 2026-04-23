# Aureon Trading System

> **Multi-dimensional financial intelligence platform exposing systematic market manipulation through spectral analysis, historical pattern recognition, and ancestral wisdom integration.**

---

## This Repository Is Six Domains, Not One

| # | Domain | What It Contains | Entry Point |
|---|--------|-----------------|-------------|
| **I** | [Ancient Convergence Research](META/DOMAIN_MAP.md#i-ancient-convergence-research) | 12 civilisations, 1,190 wisdom entries, 3,603 decoder points, 47+ convergence proofs | [`research/`](research/), [`public/`](public/), [`docs/README.md`](docs/README.md) |
| **II** | [Financial Exposure](META/DOMAIN_MAP.md#ii-financial-exposure) | $33.5T extraction across 109 years, 34-node perpetrator network, 11 events | `deep_money_flow_analysis.json`, `money_flow_timeline.json` |
| **III** | [Bot Intelligence](META/DOMAIN_MAP.md#iii-bot-intelligence) | 23 exposed algorithms, 37 firms, 44,000+ live bots, $13T+ tracked | `bot_census_registry.json`, `aureon_ocean_wave_scanner.py` |
| **IV** | [Trading System (PEFCφS)](META/DOMAIN_MAP.md#iv-trading-system-pefcφs-architecture) | 4-layer operational engine (substrate/dynamics/forcing/output) | [`ARCHITECTURE.md`](ARCHITECTURE.md), [`STRUCTURE_GUIDE.md`](STRUCTURE_GUIDE.md) |
| **V** | [Harmonic Nexus Core](META/DOMAIN_MAP.md#v-harmonic-nexus-core-hnc) | HNC theory, Master Formula, Tree of Light, Auris Conjecture | [`docs/HNC_UNIFIED_WHITE_PAPER.md`](docs/HNC_UNIFIED_WHITE_PAPER.md), `docs/research/validation_framework/` |
| **VI** | [Platform Infrastructure](META/DOMAIN_MAP.md#vi-platform-infrastructure) | Frontend (React), backend (API+server), databases (Supabase), deployment | `frontend/`, `api/`, `server/`, `supabase/`, `infrastructure/` |

**Full domain detail:** [`META/DOMAIN_MAP.md`](META/DOMAIN_MAP.md)

---

## The Main README

For the complete research narrative, convergence proofs, extraction timeline, and bot intelligence details, read the main README:

**→ [`docs/README.md`](docs/README.md)**

The main README references many files by their original flat paths (pre-reorganisation). Those paths are still valid logically — use the **path registry** to resolve them to their current locations.

---

## Path Registry (README Citations)

The main README cites files like `stargate_grid.py` and `wisdom_data/aztec_wisdom.json` using original flat paths. These are now in PEFCφS layers and domain folders.

**Resolve any README citation:**
```bash
python3 META/PATH_REGISTRY.py stargate_grid.py
# → 3_forcing/coherence_gates/stargate_grid.py (domain: research/sacred_sites)

python3 META/PATH_REGISTRY.py aztec_wisdom.json
# → research/wisdom_traditions/aztec_wisdom.json (domain: research/wisdom_traditions)
```

**Full cross-reference:** [`META/CROSS_REFERENCES.md`](META/CROSS_REFERENCES.md)

---

## Structure Summary

```
aureon-trading/
│
├── META/                         Metadata catalog & path registry
│   ├── CATALOG.json              Machine-readable file catalog (2,694 files)
│   ├── DOMAIN_MAP.md             Six-domain overview
│   ├── PATH_REGISTRY.py          Lookup utility for README citations
│   ├── CROSS_REFERENCES.md       Old-path → new-path mapping
│   └── FILE_INDEX.md             Alphabetical file index by domain
│
├── research/                     DOMAIN I: Ancient Convergence
│   ├── wisdom_traditions/        12 civilisation JSON databases
│   ├── star_chart_decoders/      7 decoder systems
│   ├── sacred_sites/             24 sites, 10 ley lines
│   ├── harmonic_frequencies/     Solfeggio, Schumann, φ
│   ├── convergence_analysis/     47+ proven connections
│   └── harmonic_nexus_core/      HNC theoretical modules
│
├── 1_substrate/                  DOMAIN IV: Trading System - Foundation
│   ├── frequencies/              Harmonic constants, φ-ladder
│   ├── market_feeds/             Alpaca, Binance, CoinAPI, Kraken
│   └── data_models/              Schemas, caches, configs
│
├── 2_dynamics/                   DOMAIN IV: Trading System - Intelligence
│   ├── trading_logic/            Multi-branch traders (LTDE)
│   ├── probability_networks/     Γ coherence operators
│   ├── echo_feedback/            Temporal delegation τₖ = τ₀·φᵏ
│   └── multiverse_branches/      Parallel scenario evaluators
│
├── 3_forcing/                    DOMAIN IV: Trading System - Execution
│   ├── market_events/            Scanners, whale trackers
│   ├── execution_engines/        Order placement, trade emission
│   ├── coherence_gates/          Γ threshold enforcement (incl. stargate_grid.py)
│   └── real_time_triggers/       Heartbeat monitors, emergency handlers
│
├── 4_output/                     DOMAIN IV: Trading System - Results
│   ├── trade_outputs/            Executed signals, records
│   ├── portfolio_management/     Position tracking
│   ├── performance_metrics/      PnL, win-rate, Q_choice
│   └── dashboard/                Real-time visualisation (shade of many)
│
├── frontend/                     DOMAIN VI: Platform - React UI
├── public/                       DOMAIN I+VI: Star-chart decoders + static assets
├── api/, server/, functions/     DOMAIN VI: Platform - Backend
├── supabase/                     DOMAIN VI: Platform - Database
├── infrastructure/               DOMAIN VI: Platform - Deployment
├── scripts/                      DOMAIN VI: Platform - Entry points + utilities
│
├── aureon/                       Python package (civilizational_dna, harmonic_nexus_bridge)
├── Assets/                       Images (PNG, SVG), scientific data (CSV, BSP)
├── state/                        Runtime state (logs, JSONL, backups)
├── tests/                        Validation & benchmarking
├── docs/                         Documentation + research archives
│
├── ARCHITECTURE.md               PEFCφS formalism (Layer IV detail)
├── STRUCTURE_GUIDE.md            Trading system layer navigation
├── bootstrap_paths.py            Python path helper for flat imports
├── conftest.py                   Pytest bootstrap
├── Dockerfile, Procfile, app.yaml Deployment configs
└── LICENSE
```

---

## File Statistics

| Domain | Critical Files | Total Files |
|--------|---------------|-------------|
| I. Ancient Convergence Research | 22 | 157 |
| II. Financial Exposure | 4 | 10 |
| III. Bot Intelligence | 7 | 55 |
| IV. Trading System (PEFCφS) | 1 | 1,069 |
| V. HNC (in research/platform) | — | ~50 |
| VI. Platform Infrastructure | — | 1,197 |
| Documentation | — | 188 |
| **Total indexed** | **34** | **2,694** |

---

## Verification Commands

### Verify the research data (updated paths)

```bash
# Count wisdom entries across all 12 civilisations
python3 -c "
import json, os
root = 'research/wisdom_traditions'
total = 0
for f in sorted(os.listdir(root)):
    if not f.endswith('.json'): continue
    data = json.load(open(f'{root}/{f}'))
    subs = 0
    for entry in (data if isinstance(data, list) else data.values()):
        if isinstance(entry, dict):
            for v in entry.values():
                if isinstance(v, (list, dict)): subs += len(v)
    print(f'{f}: {len(data)} categories, {subs} entries')
    total += subs
print(f'TOTAL: {total} entries across 12 civilisations')
"

# Verify PHI (1.618) across decoders
grep -l "1.618" public/*.json research/wisdom_traditions/*.json

# Run tests
pytest tests/ -q --tb=line
```

### Using the path registry in code

```python
from META.PATH_REGISTRY import resolve_absolute
import json

# Look up any README-cited file
wisdom_path = resolve_absolute("aztec_wisdom.json")
with open(wisdom_path) as f:
    data = json.load(f)
```

### Running the trading system

```bash
# Bootstrap Python paths (one-time per session)
python3 -c "import bootstrap_paths; print('paths ready')"

# Run any entry-point script
python3 scripts/entry_points/run_queen_hive_mind.py
```

---

## Documentation Index

**For the full narrative:**
- [`docs/README.md`](docs/README.md) — Main README (convergence proofs, extraction timeline, bot intelligence)

**For the architecture:**
- [`ARCHITECTURE.md`](ARCHITECTURE.md) — PEFCφS formalism
- [`STRUCTURE_GUIDE.md`](STRUCTURE_GUIDE.md) — Trading system layer guide

**For domain navigation:**
- [`META/DOMAIN_MAP.md`](META/DOMAIN_MAP.md) — Six domains, overview
- [`META/CROSS_REFERENCES.md`](META/CROSS_REFERENCES.md) — Old paths → new paths
- [`META/FILE_INDEX.md`](META/FILE_INDEX.md) — Alphabetical file index
- [`META/CATALOG.json`](META/CATALOG.json) — Machine-readable catalog

**For research:**
- [`docs/HNC_UNIFIED_WHITE_PAPER.md`](docs/HNC_UNIFIED_WHITE_PAPER.md) — HNC theory
- [`docs/research/validation_framework/`](docs/research/validation_framework/) — 14 validation PDFs

---

**Repository:** gary-leckey/aureon-trading
**Architect:** Gary LeCkey
**Model:** PEFCφS (Position of Echo-Feedback Cognitive φ-Substrate)
**Last reorganisation:** 2026-04-23
