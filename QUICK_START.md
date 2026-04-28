# Aureon Trading System — Quick Start

> **For complete, verified setup and run instructions, see [`RUNNING.md`](RUNNING.md).**
> This page is a quick reference for finding files and running commands.

---

## Run the System (One Command)

```bash
# Safe dry-run mode (default — no real trades)
python scripts/aureon_ignition.py
```

**Need full instructions?** → See [`RUNNING.md`](RUNNING.md) for setup, testnet, and live trading.

---

## Where Things Live

The active codebase lives in the `aureon/` package. The numbered top-level folders (`1_substrate/`, `2_dynamics/`, `3_forcing/`, `4_output/`) reflect the conceptual PEFCφS architecture but are **not** where most active Python files live.

### Actual File Locations

| Subsystem | Location |
|-----------|----------|
| Master launcher | `scripts/aureon_ignition.py` |
| HNC interactive terminal | `run_hnc_live.py` |
| Trade executor | `aureon/trading/aureon_queen_trade_executor.py` |
| Historical backtests | `aureon/analytics/aureon_historical_backtest.py` |
| Portfolio tracker | `aureon/portfolio/live_portfolio_growth_tracker.py` |
| Bot intelligence | `aureon/bots_intelligence/` |
| Harmonic / FFT modules | `aureon/harmonic/` |
| Queen AI layer | `aureon/queen/` |
| Exchange adapters | `aureon/exchanges/` |
| Wisdom traditions | `research/wisdom_traditions/` |
| Sacred frequencies | `research/harmonic_frequencies/` |

For a full module map, see [`docs/MODULES_AT_A_GLANCE.md`](docs/MODULES_AT_A_GLANCE.md) and [`docs/SCRIPTS_INDEX.md`](docs/SCRIPTS_INDEX.md).

---

## Common Tasks

### Run Paper Trading (Dry-Run)

```bash
# Default mode is dry-run — no real money
python scripts/aureon_ignition.py
```

See [`RUNNING.md`](RUNNING.md#a-test-the-system-safe-no-money-at-risk) for details.

### Run Backtesting

```bash
# Spot trading historical backtest
python aureon/analytics/aureon_historical_backtest.py
```

### Boot All Systems Without Trading

```bash
# Verify connectivity to exchanges, no orders placed
python scripts/aureon_ignition.py --live --no-trade
```

### Run Interactive HNC Terminal

```bash
python run_hnc_live.py
```

### Live Trading (Real Money)

⚠️ **Read [`RUNNING.md`](RUNNING.md#d-live-trade-with-real-money-️) and [`docs/LIVE_TRADING_RUNBOOK.md`](docs/LIVE_TRADING_RUNBOOK.md) before running with real funds.**

```bash
python scripts/aureon_ignition.py --live
```

---

## Documentation Map

| What you want | Where to look |
|---------------|---------------|
| **How to run the system** | [`RUNNING.md`](RUNNING.md) |
| **One-page synthesis of the project** | [`docs/THE_SYNTHESIS.md`](docs/THE_SYNTHESIS.md) |
| **Architecture & code organization** | [`docs/NAVIGATION_GUIDE.md`](docs/NAVIGATION_GUIDE.md) |
| **HNC theory and mathematics** | [`docs/HNC_UNIFIED_WHITE_PAPER.md`](docs/HNC_UNIFIED_WHITE_PAPER.md) |
| **All claims and evidence** | [`docs/CLAIMS_AND_EVIDENCE.md`](docs/CLAIMS_AND_EVIDENCE.md) |
| **Live trading checklist** | [`docs/LIVE_TRADING_RUNBOOK.md`](docs/LIVE_TRADING_RUNBOOK.md) |
| **Full module reference** | [`docs/MODULES_AT_A_GLANCE.md`](docs/MODULES_AT_A_GLANCE.md) |
| **All scripts catalog** | [`docs/SCRIPTS_INDEX.md`](docs/SCRIPTS_INDEX.md) |
| **Research papers** | [`docs/research/READING_PATHS.md`](docs/research/READING_PATHS.md) |

---

## Getting Help

- **Setup problems?** See [`RUNNING.md`](RUNNING.md#common-issues--fixes)
- **What does this system do?** See [`docs/THE_SYNTHESIS.md`](docs/THE_SYNTHESIS.md)
- **Can I trust the results?** See [`docs/CLAIMS_AND_EVIDENCE.md`](docs/CLAIMS_AND_EVIDENCE.md)
- **AI assistant landing here?** Read [`CLAUDE.md`](CLAUDE.md) first

---

**For run instructions, always defer to [`RUNNING.md`](RUNNING.md).** This file gets out of date faster than the canonical run guide.
