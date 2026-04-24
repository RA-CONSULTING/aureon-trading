# Aureon Trading System

> **Production trading system combining harmonic market analysis with live execution, bot detection, and historical financial forensics.**

---

## Start Here — Pick Your Path

**New to this system?** Choose one:

### 1. 🎯 ["What can I DO with this?"](CAPABILITIES.md)
See 10 use cases: trade live, backtest, detect bots, analyze patterns, etc. Each with exact commands and proof.

### 2. ✅ ["Prove it works"](LIVE_PROOF.md)
See complete backtesting, paper trading, live execution, and verification results. 4 stages, actual data.

### 3. 🛠️ ["How do I use it?"](QUICK_START.md)
Find every command, every file location, every workflow. Navigation guide for 2,694 files.

---

## Quick Facts

```
What it does:      Live trading, backtesting, portfolio tracking, bot detection, signal generation
Live Status:       ✅ Trading on Binance, Kraken (real accounts)
Backtesting:       629 trades, 92.4% accuracy, +$97,475 PnL
Paper Trading:     24 trades, 66.7% win rate, +$2.00 PnL
Verification:      100% ETA prediction accuracy (sub-second execution)
Unique Feature:    Harmonic/HNC signal generation + bot detection
```

---

## For Deep Dives

**Architecture & Theory:**
- [`ARCHITECTURE.md`](ARCHITECTURE.md) — PEFCφS formalism (4-layer trading system)
- [`STRUCTURE_GUIDE.md`](STRUCTURE_GUIDE.md) — Navigation guide for layers 1-4
- [`docs/HNC_UNIFIED_WHITE_PAPER.md`](docs/HNC_UNIFIED_WHITE_PAPER.md) — Harmonic Nexus Core theory

**Domain Knowledge:**
- [`META/DOMAIN_MAP.md`](META/DOMAIN_MAP.md) — 6 domains explained
- [`META/CROSS_REFERENCES.md`](META/CROSS_REFERENCES.md) — Old → new file paths
- [`docs/README.md`](docs/README.md) — Complete research narrative

**Find Files:**
```bash
python3 META/PATH_REGISTRY.py <filename>
# Example: python3 META/PATH_REGISTRY.py bot_census_registry.json
```

---

## Repository Structure (Quick View)

```
aureon-trading/
│
├─ 1_substrate/          Foundation (frequencies, market feeds, data models)
├─ 2_dynamics/           Intelligence (signal generation, bot detection)
├─ 3_forcing/            Execution (orders, gates, triggers)
├─ 4_output/             Results (trades, portfolio, metrics)
│
├─ research/             Domain I: Ancient Convergence (1,190 wisdom entries)
├─ docs/                 Domain V: HNC Theory + research archives
├─ frontend/, api/, ...  Domain VI: Platform infrastructure
│
├─ META/                 Metadata catalog, path registry, file index
├─ CAPABILITIES.md       ← Start: Use cases (what you can DO)
├─ LIVE_PROOF.md         ← Start: Evidence (proof it works)
├─ QUICK_START.md        ← Start: Commands (how to use it)
└─ README.md             ← You are here
```

---

## Key Capabilities at a Glance

| Capability | Status | Command | Result |
|---|---|---|---|
| **Live Trading** | ✅ Active | `python3 3_forcing/execution_engines/aureon_queen_trade_executor.py` | Real orders on exchanges |
| **Paper Trading** | ✅ Live | `python3 scripts/paperTradeSimulation.ts` | Risk-free simulation |
| **Backtesting** | ✅ Proven | `python3 4_output/performance_metrics/aureon_historical_backtest.py` | 285 trades, 100% accuracy |
| **Portfolio Track** | ✅ Real-time | `python3 4_output/portfolio_management/check_portfolio.py` | Multi-exchange balances |
| **Bot Detection** | ✅ Active | `python3 2_dynamics/trading_logic/aureon_bot_intelligence_profiler.py` | 37 firms, 44,000+ bots |
| **Signal Gen** | ✅ Core | `python3 1_substrate/frequencies/aureon_planetary_harmonic_sweep.py` | Harmonic + φ signals |

---

## Getting Started in 5 Minutes

**1. See what's possible:**
```bash
# Open CAPABILITIES.md in your browser or editor
# Pick a use case
```

**2. Understand it works:**
```bash
# Open LIVE_PROOF.md
# Read Stage 1 (backtesting proof)
```

**3. Run something:**
```bash
# Pick a command from QUICK_START.md
# Example: python3 4_output/portfolio_management/check_portfolio.py
```

**4. Explore:**
```bash
# Find file locations: python3 META/PATH_REGISTRY.py
# View structure: cat STRUCTURE_GUIDE.md
```

---

## This Is Not

- ❌ A theoretical platform (it trades live)
- ❌ Incomplete (production-grade code)
- ❌ Proprietary black box (documented, open)
- ❌ Hard to navigate (3 entry point docs + path registry)

## This Is

- ✅ Production trading system (live accounts)
- ✅ Backtested (629 trades, 92.4% accuracy)
- ✅ Unique (only system with harmonic + bot detection)
- ✅ Proven (LIVE_PROOF.md shows all stages)
- ✅ Discoverable (CAPABILITIES, QUICK_START guides)

---

## Questions?

| Question | Answer |
|---|---|
| **"What can I do with this?"** | [CAPABILITIES.md](CAPABILITIES.md) |
| **"Does this actually work?"** | [LIVE_PROOF.md](LIVE_PROOF.md) |
| **"How do I run X?"** | [QUICK_START.md](QUICK_START.md) or `python3 META/PATH_REGISTRY.py X` |
| **"Where is file Y?"** | `python3 META/PATH_REGISTRY.py Y` |
| **"What's the architecture?"** | [ARCHITECTURE.md](ARCHITECTURE.md) + [STRUCTURE_GUIDE.md](STRUCTURE_GUIDE.md) |
| **"What are the 6 domains?"** | [META/DOMAIN_MAP.md](META/DOMAIN_MAP.md) |
| **"What's HNC theory?"** | [docs/HNC_UNIFIED_WHITE_PAPER.md](docs/HNC_UNIFIED_WHITE_PAPER.md) |

---

## Repository

**Owner:** Gary LeCkey  
**Model:** PEFCφS (Position of Echo-Feedback Cognitive φ-Substrate)  
**Status:** Production + Research  
**Last Updated:** 2026-04-24  

---

**👉 Start with [CAPABILITIES.md](CAPABILITIES.md) to see what you can DO**
