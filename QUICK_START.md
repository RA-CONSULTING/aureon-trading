# Aureon Trading System — Quick Start Guide

**Find what you need fast. All key functionality with file locations and commands.**

---

## I Want To... → Go To

### See Live Proof
- **"I want to see the actual trading results"**  
  → [`LIVE_PROOF.md`](LIVE_PROOF.md)  
  Shows backtests (+$97K), paper trades, live accounts, and verification

### Understand the Architecture
- **"How does this system work?"**  
  → [`ARCHITECTURE.md`](ARCHITECTURE.md)  
  Complete PEFCφS formalism explanation

- **"Where do I find specific files?"**  
  → [`STRUCTURE_GUIDE.md`](STRUCTURE_GUIDE.md)  
  Navigation guide for all 4 trading layers

- **"What are the 6 domains?"**  
  → [`META/DOMAIN_MAP.md`](META/DOMAIN_MAP.md)  
  Overview of Ancient Research, Financial Exposure, Bot Intelligence, Trading, HNC, and Platform

### Run Paper Trading
```bash
# Start a paper trading session
npm run paper-trade
# or
python3 scripts/paperTradeSimulation.ts

# Monitor trades in real-time
python3 4_output/portfolio_management/live_portfolio_growth_tracker.py

# View paper trade history
cat 4_output/trade_outputs/paper_trade_history.json
```

**Files:**
- Execution: `scripts/paperTradeSimulation.ts`
- Results: `4_output/trade_outputs/paper_trade_history.json`
- Monitoring: `4_output/portfolio_management/live_portfolio_growth_tracker.py`

### Run Backtesting
```bash
# Backtest with spot trading (no leverage)
python3 4_output/performance_metrics/aureon_historical_backtest.py

# Backtest with margin trading (leverage, shorts)
python3 4_output/performance_metrics/super_intelligence_backtest.py

# View spot results
cat 4_output/performance_metrics/backtest_spot_results.json

# View margin results
cat 4_output/performance_metrics/backtest_margin_results.json
```

**Files:**
- Spot backtest script: `4_output/performance_metrics/aureon_historical_backtest.py`
- Margin backtest script: `4_output/performance_metrics/super_intelligence_backtest.py`
- Spot results: `4_output/performance_metrics/backtest_spot_results.json`
- Margin results: `4_output/performance_metrics/backtest_margin_results.json`

### Check Live Portfolio
```bash
# See current account balances
python3 4_output/portfolio_management/check_portfolio.py

# View recent trades
python3 4_output/portfolio_management/check_recent_trades.py

# Full portfolio analysis
python3 4_output/portfolio_management/analyze_portfolio_stats.py

# View portfolio truth state
cat 4_output/portfolio_management/portfolio_truth.json
```

**Files:**
- Portfolio checker: `4_output/portfolio_management/check_portfolio.py`
- Recent trades: `4_output/portfolio_management/check_recent_trades.py`
- Current state: `4_output/portfolio_management/portfolio_truth.json`

### Execute Live Trades
```bash
# Execute trades against real exchange
python3 3_forcing/execution_engines/aureon_queen_trade_executor.py

# Execute with specific strategy
python3 3_forcing/execution_engines/execute_real_trades.py

# Execute with force (override limits)
python3 3_forcing/execution_engines/force_trade.py
```

**Files:**
- Main executor: `3_forcing/execution_engines/aureon_queen_trade_executor.py`
- Real trade executor: `3_forcing/execution_engines/execute_real_trades.py`
- Force trade: `3_forcing/execution_engines/force_trade.py`

### Validate & Verify Trades
```bash
# Validate trade profitability
python3 4_output/performance_metrics/trade_profit_validator.py

# View complete trade audit
cat 4_output/performance_metrics/trade_history_audit.json

# Check ETA prediction accuracy
cat 4_output/trade_outputs/eta_verification_history.json
```

**Files:**
- Validator: `4_output/performance_metrics/trade_profit_validator.py`
- Audit trail: `4_output/performance_metrics/trade_history_audit.json`
- ETA verification: `4_output/trade_outputs/eta_verification_history.json`

### Access Harmonic Analysis
```bash
# Run harmonic frequency scanning
python3 1_substrate/frequencies/aureon_planetary_harmonic_sweep.py

# Check sacred frequency database
cat 1_substrate/frequencies/sacred_frequencies.json

# View planet harmonic network
cat 1_substrate/frequencies/planetary_harmonic_network.json
```

**Files:**
- Harmonic sweep: `1_substrate/frequencies/aureon_planetary_harmonic_sweep.py`
- Frequency constants: `1_substrate/frequencies/`
- Harmonic networks: `1_substrate/frequencies/planetary_harmonic_network.json`

### Detect Bot Manipulation
```bash
# Scan for bot activity patterns
python3 2_dynamics/trading_logic/aureon_bot_intelligence_profiler.py

# Ocean wave scanner (price action analysis)
python3 2_dynamics/trading_logic/aureon_ocean_wave_scanner.py

# View detected bots
cat 2_dynamics/trading_logic/bot_census_registry.json

# View bot attribution
cat 2_dynamics/trading_logic/bot_cultural_attribution.json
```

**Files:**
- Bot profiler: `2_dynamics/trading_logic/aureon_bot_intelligence_profiler.py`
- Ocean scanner: `2_dynamics/trading_logic/aureon_ocean_wave_scanner.py`
- Bot registry: `2_dynamics/trading_logic/bot_census_registry.json`
- Bot attribution: `2_dynamics/trading_logic/bot_cultural_attribution.json`

### Analyze Historical Market Manipulation
```bash
# Hunt for historical manipulation patterns
python3 2_dynamics/trading_logic/aureon_historical_manipulation_hunter.py

# View financial extraction analysis
cat 4_output/performance_metrics/deep_money_flow_analysis.json

# View extraction timeline
cat 1_substrate/data_models/money_flow_timeline.json
```

**Files:**
- Manipulation hunter: `2_dynamics/trading_logic/aureon_historical_manipulation_hunter.py`
- Money flow analysis: `4_output/performance_metrics/deep_money_flow_analysis.json`
- Timeline: `1_substrate/data_models/money_flow_timeline.json`

### Explore Ancient Wisdom
```bash
# View 12 civilizations' wisdom entries
ls research/wisdom_traditions/

# Example: Aztec wisdom
cat research/wisdom_traditions/aztec_wisdom.json

# Star chart decoders
cat public/aztec-star-glyphs.json
cat public/celtic-ogham-feda.json
cat public/egyptian-hieroglyphs.json
```

**Files:**
- Wisdom databases: `research/wisdom_traditions/` (12 files)
- Star charts: `public/` (7 decoder files)
- Sacred sites: `research/sacred_sites/`

### Understand HNC Theory
```bash
# Read the theoretical foundation
cat docs/HNC_UNIFIED_WHITE_PAPER.md

# View validation research
ls docs/research/validation_framework/
```

**Files:**
- HNC paper: `docs/HNC_UNIFIED_WHITE_PAPER.md`
- Validation: `docs/research/validation_framework/` (14 PDFs)

### Find Files by Name
```bash
# Resolve old README-cited paths
python3 META/PATH_REGISTRY.py stargate_grid.py
# → 3_forcing/coherence_gates/stargate_grid.py

python3 META/PATH_REGISTRY.py aztec_wisdom.json
# → research/wisdom_traditions/aztec_wisdom.json

# List all README-critical files
python3 META/PATH_REGISTRY.py
```

**Files:**
- Path resolver: `META/PATH_REGISTRY.py`
- File catalog: `META/CATALOG.json`
- Mapping: `META/CROSS_REFERENCES.md`

---

## File Locations Reference

### Core Trading System (PEFCφS Layers)

```
1_substrate/                 Foundation (frequencies, data models, market feeds)
├─ frequencies/              Harmonic constants, φ-ladder
├─ market_feeds/             Exchange connections (Alpaca, Binance, Kraken)
└─ data_models/              Schemas, caches, configs

2_dynamics/                  Intelligence (trading logic, probability networks)
├─ trading_logic/            Multi-branch traders (LTDE)
├─ probability_networks/     Γ coherence operators
├─ echo_feedback/            Temporal delegation τₖ = τ₀·φᵏ
└─ multiverse_branches/      Parallel scenario evaluators

3_forcing/                   Execution (gates, order placement, triggers)
├─ coherence_gates/          Γ threshold enforcement
├─ execution_engines/        Order placement, trade emission
├─ market_events/            Scanners, whale trackers
└─ real_time_triggers/       Heartbeat monitors

4_output/                    Results (trades, portfolio, metrics, dashboards)
├─ trade_outputs/            Executed signals, records
├─ portfolio_management/     Position tracking, accounting
├─ performance_metrics/      PnL, win-rate, backtests
└─ dashboard/                Real-time visualisation
```

### Research & Intelligence (Domains I-III)

```
research/                    Domain I: Ancient Convergence
├─ wisdom_traditions/        12 civilisation databases
├─ star_chart_decoders/      7 decoder systems
├─ sacred_sites/             24 sites, 10 ley lines
├─ harmonic_frequencies/     Solfeggio, Schumann, φ
└─ convergence_analysis/     47+ proven connections

                            Domain II: Financial Exposure
1_substrate/data_models/    Money flow timeline, extraction evidence
4_output/performance_metrics/ Deep flow analysis

                            Domain III: Bot Intelligence
2_dynamics/trading_logic/   Bot census, attribution, scanners
1_substrate/frequencies/    Harmonic network coordination
```

### Platform Infrastructure (Domain VI)

```
frontend/                    React UI, dashboards
api/, server/, functions/    Backend, endpoints
supabase/                    Database migrations
infrastructure/              Docker, CI/CD, deployment
scripts/                     Entry points, utilities
```

---

## Common Workflows

### "I want to validate a trading hypothesis"

1. Read [`LIVE_PROOF.md`](LIVE_PROOF.md) to understand performance baseline
2. Review backtesting results in `4_output/performance_metrics/`
3. Run paper trading with your hypothesis
4. Compare results to baseline

**Commands:**
```bash
python3 scripts/paperTradeSimulation.ts
python3 4_output/portfolio_management/live_portfolio_growth_tracker.py
```

### "I want to find a specific file"

1. Use [`META/PATH_REGISTRY.py`](META/PATH_REGISTRY.py) to resolve old paths
2. Check [`META/DOMAIN_MAP.md`](META/DOMAIN_MAP.md) for domain breakdown
3. Use [`STRUCTURE_GUIDE.md`](STRUCTURE_GUIDE.md) for layer navigation

**Command:**
```bash
python3 META/PATH_REGISTRY.py <filename>
```

### "I want to understand the complete system"

1. Start with [`LIVE_PROOF.md`](LIVE_PROOF.md) — see it working
2. Read [`ARCHITECTURE.md`](ARCHITECTURE.md) — understand the formalism
3. Explore [`META/DOMAIN_MAP.md`](META/DOMAIN_MAP.md) — understand scope
4. Deep dive into specific domain or layer via [`STRUCTURE_GUIDE.md`](STRUCTURE_GUIDE.md)

### "I want to replicate trading results"

1. Start with backtesting (fastest, historical):
   ```bash
   python3 4_output/performance_metrics/aureon_historical_backtest.py
   ```

2. Move to paper trading (real-time, risk-free):
   ```bash
   python3 scripts/paperTradeSimulation.ts
   ```

3. Deploy live trading (real capital):
   ```bash
   python3 3_forcing/execution_engines/aureon_queen_trade_executor.py
   ```

---

## Getting Help

- **"How are trades executed?"** → `ARCHITECTURE.md` + `3_forcing/execution_engines/`
- **"What's the signal algorithm?"** → `2_dynamics/trading_logic/` + HNC paper
- **"How do I know it works?"** → `LIVE_PROOF.md`
- **"Where's file X?"** → `META/PATH_REGISTRY.py filename`
- **"What can this system do?"** → `META/DOMAIN_MAP.md`

---

## Key Statistics

```
Repository:           2,694 files, 6 domains, 4 trading layers
Backtesting:          629 trades, 92.4% win rate, +$97,475 PnL
Paper Trading:        24 trades, 66.7% win rate, +$2.00 PnL
Live Trading:         Multi-exchange portfolio management
Unique Features:      Harmonic analysis, HNC theory, bot detection
```

---

**Want to dive in? Start here:** [`LIVE_PROOF.md`](LIVE_PROOF.md)
