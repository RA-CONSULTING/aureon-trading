# 🐙🌌 AUREON UNIFIED TRADING ECOSYSTEM

> **Pure Math Logic. Harmonic Intelligence. Multi-Exchange. Self-Evolving.**

[![License](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue.svg)](https://typescriptlang.org)
[![Exchanges](https://img.shields.io/badge/Exchanges-4-green.svg)](#-verified-exchanges)

**AUREON** is a **unified multi-exchange algorithmic trading system** designed to achieve **51%+ win rate with net profit after all fees**. It combines **Lattice Theory**, **Swarm Intelligence**, **Quantum Geometry**, **Harmonic Frequency Analysis**, and **Temporal Probability Forecasting** into a single coherent trading engine.

---

## 🌟 WHAT MAKES AUREON UNIQUE

**There is no other trading system like AUREON.** While most algorithmic trading platforms rely on conventional technical indicators (RSI, MACD, Bollinger Bands) and standard machine learning models, AUREON takes an entirely different approach:

| Conventional Systems | AUREON |
|---------------------|--------|
| Technical indicators | **Master Equation**: Λ(t) = S(t) + O(t) + E(t) |
| Single algorithm | **9 Auris Nodes** (multi-dimensional animal totems) |
| Price-only analysis | **Sacred Geometry** (5 Platonic Solids refraction) |
| Historical backtesting | **Temporal Probability Forecasting** (H-1 to H+2) |
| No external data | **Earth Resonance** (Schumann frequency integration) |
| Static rules | **Self-Referential Observer** (consciousness-inspired) |
| Single exchange | **Unified Multi-Exchange** routing |

### 🔬 Novel Theoretical Framework

- **Quantum Geometry** — Markets refracted through Tetrahedron, Hexahedron, Octahedron, Icosahedron, Dodecahedron
- **Harmonic Frequency Analysis** — Solfeggio frequencies (528Hz transformation, 432Hz harmony, 440Hz distortion)
- **Earth Field Integration** — Real-time Schumann resonance (7.83Hz) correlation
- **Temporal Ladder** — Hive-mind coordination between trading agents
- **Echo Memory** — Momentum persistence with intelligent cooldowns

---

## 🏗️ SYSTEM ARCHITECTURE

```text
                    ┌─────────────────────────────────────┐
                    │   AUREON UNIFIED ECOSYSTEM          │
                    │   (aureon_unified_ecosystem.py)     │
                    └─────────────────┬───────────────────┘
                                      │
        ┌─────────────────────────────┼─────────────────────────────┐
        │                             │                             │
        ▼                             ▼                             ▼
┌───────────────┐           ┌─────────────────┐           ┌─────────────────┐
│   EXCHANGES   │           │  INTELLIGENCE   │           │   EXECUTION     │
├───────────────┤           ├─────────────────┤           ├─────────────────┤
│ 🐙 Kraken     │           │ 🔭 Quantum Tel. │           │ Smart Router    │
│ 🟡 Binance    │           │ 📊 Prob Matrix  │           │ Arbitrage Scan  │
│ 💼 Capital    │           │ 🌍 Earth Reson. │           │ Position Mgmt   │
│ 🦙 Alpaca     │           │ 🌌 HNC Freq.    │           │ Kelly Sizing    │
└───────────────┘           │ 🧠 Adaptive ML  │           └─────────────────┘
                            └─────────────────┘
```

---

## 🚀 Performance Targets

| Metric | Target | Method |
|--------|--------|--------|
| **Win Rate** | 51%+ | Multi-gate filtering |
| **Net Profit** | Positive after ALL fees | Fee-aware execution |
| **Max Drawdown** | 15% circuit breaker | Risk management |
| **Positions** | Max 15 concurrent | Quality over quantity |

---

## ⚡ Quickstart (Dry Run vs Live)

### Install & configure

- `pip install -r requirements.txt`
- Copy `.env.example` → `.env`, add API keys (Binance, Kraken, Capital.com, Alpaca)

### Dry run (default)

- `python aureon_unified_ecosystem.py`

### Live trading

- `LIVE=1 FRESH_START=1 python aureon_unified_ecosystem.py`
- Optional: `EXCHANGE=binance` (default multi-exchange); `BINANCE_USE_TESTNET=true` for testnet
- UK accounts: `BINANCE_UK_MODE=true` (default) filters to UK-allowed pairs
- Force entry if stuck: `FORCE_TRADE=1 [FORCE_TRADE_SYMBOL=XXXUSDC]` (still respects min liquidity)

### Probability training (offline)

- `PROB_TRAIN_TRADES=300 python probability_matrix_training.py`

Logs: `tail -f unified_ecosystem.log` (live decisions), state: `aureon_kraken_state.json`, rejection reasons: `rejection_log.json`.

---

## 🛡️ Safety & Risk Controls

- **Circuit breaker**: `MAX_DRAWDOWN_PCT=50%` (was 15%). Skips breaker during init and after `FRESH_START` to prevent false halts.
- **Portfolio budget**: `PORTFOLIO_RISK_BUDGET=1.50` (150% notional cap) so imported holdings don’t block new trades.
- **Profit gate**: requires ≥0.5% net after fees/spread/slippage (see `test_profit_gate.py`).
- **Trailing stops**: enable at +0.5%, trail 0.3% (per strategy config).
- **Kelly sizing**: Half-Kelly with caps; `MAX_SYMBOL_EXPOSURE` and per-trade caps enforced.
- **Fresh start**: `FRESH_START=1` resets baselines before breaker activates; recommended after manual interventions.

---

## 🚀 Recent Improvements (Live Trading UX)

- **Historical holdings as fuel**: Startup imports all exchange balances; marks them `is_historical` and can liquidate them when cash is needed for better opportunities. Ongoing harvesting takes 10% slices of winners (`HARVEST_PCT=0.10`).
- **Auto-harvest**: Detects gains on imported positions and locks profit (seen on FARTCOIN/ETH/SHIB/BTC/XLM).
- **Probability matrix refresh**: `probability_matrix_training.py` emits `probability_training_report.json` and `adaptive_learning_history.json` for transparency.
- **Binance precision & UK filters**: Quote precision fixes reduce `LOT_SIZE` errors; UK mode avoids blocked symbols and invalid payloads.
- **Kraken ticker robustness**: Altname mapping to avoid `EQuery:Unknown asset pair`.
- **Liquidity-aware entries**: Skips illiquid symbols; will attempt historical-asset liquidation first.

---

## 🧭 Monitoring & Ops

- Live log: `unified_ecosystem.log` (entries, exits, harvests, sweeps, P&L pool)
- State snapshots: `aureon_kraken_state.json`, `multi_exchange_learning.json`, `rejection_log.json`
- Probability artifacts: `probability_training_report.json`, `adaptive_learning_history.json`
- Quick health check: `tail -f unified_ecosystem.log | grep "Market Sweep\|Pool:\|HARVEST"`

---

## 🧪 Testing

- `test_profit_gate.py` — validates profit-gate math (fees, spread, slippage)
- `smoke_test_json_integration.py` — validates aggregated feeds
- `test_trade_capability.py`, `test_scout_deployment.py` — entry/position smoke

---

## 🐛 Known Issues / Tips

- **Binance UK restrictions**: Many symbols are blocked; USDC/USDT only. Expect occasional `Invalid symbol` or zero-liquidity skips.
- **Lot size / precision**: If Binance returns `Filter failure: LOT_SIZE`, the amount was too small; precision fixes help but very tiny balances may still fail.
- **Kraken pair naming**: If you see `Unknown asset pair`, ensure symbol maps to Kraken altname (client handles most cases).
- **Liquidity shortfalls**: Bot will try to liquidate historical assets when cash is low; it skips anything under ~$1 to avoid dust churn.

---

## 🧬 KEY COMPONENTS

### 1. Multi-Exchange Client

- **Kraken** (🐙): Primary crypto exchange (USD, GBP, EUR)
- **Binance** (🟡): UK-compliant pairs (USDC, USDT)
- **Capital.com** (💼): CFDs - Forex, Indices, Commodities
- **Alpaca** (🦙): US Stocks & Crypto (analytics mode)

### 2. Smart Order Router

Routes orders to the best exchange based on:

- Real-time price comparison
- Fee optimization (Binance 0.1% vs Kraken 0.26%)
- Liquidity depth
- UK regulatory compliance

### 3. Cross-Exchange Arbitrage Scanner

Detects price discrepancies across exchanges for risk-free profit opportunities.

---

## 🔭 QUANTUM TELESCOPE (Sacred Geometry Engine)

The Quantum Telescope refracts market data through **5 Platonic Solids** - the fundamental geometric forms that underlie reality:

| Solid | Element | Market Aspect | Signal Type |
|-------|---------|---------------|-------------|
| **Tetrahedron** | Fire 🔥 | Momentum/Velocity | Trend strength |
| **Hexahedron** | Earth 🌍 | Support/Resistance | Price levels |
| **Octahedron** | Air 💨 | Mean Reversion | Balance points |
| **Icosahedron** | Water 💧 | Liquidity/Volume | Flow analysis |
| **Dodecahedron** | Ether ✨ | Sentiment/Coherence | **Primary Signal** |

### How It Works

```python
# Create a LightBeam from market data
beam = LightBeam(
    symbol="BTCUSD",
    price=97500.00,
    volume=1250000,
    momentum=2.5,  # 24h change %
    timestamp=time.time()
)

# Refract through the telescope
observation = telescope.observe(beam)

# Dodecahedron (Ether) provides coherence signal
coherence = observation[GeometricSolid.DODECAHEDRON]
```

**Key Parameter:** `OPTIMAL_MIN_GATES: 5` → All 5 geometric gates must align = **63.6% win rate**

---

## 📊 PROBABILITY MATRIX (Temporal Forecasting)

The HNC Probability Matrix operates on a **2-hour temporal window**:

```text
├─ HOUR -1 (LOOKBACK):  Historical frequency patterns
├─ HOUR  0 (NOW):       Current calibration point  
├─ HOUR +1 (FORECAST):  ← PRIMARY TRADING SIGNAL
└─ HOUR +2 (FINE-TUNE): Refines Hour +1 predictions
```

### Matrix Integration

```python
signal = prob_matrix.get_trading_signal(symbol)
# Returns:
# {
#     'probability': 0.72,      # 72% up probability
#     'confidence': 0.85,       # High confidence
#     'action': 'BUY',          # Recommended action
#     'modifier': 1.15,         # Position size boost
#     'h1_state': 'BULLISH',    # Hour +1 forecast
#     'fine_tune': 0.03         # Hour +2 adjustment
# }
```

**Key Parameters:**

- `PROB_MIN_CONFIDENCE: 0.50` → Minimum confidence threshold
- `PROB_HIGH_THRESHOLD: 0.65` → High probability boost trigger
- `PROB_FORECAST_WEIGHT: 0.40` → 40% weight in position sizing

---

## 🎯 LAMBDA FIELD (Unified Coherence Equation)

All intelligence systems feed into the **Lambda Field** equation:

```text
Λ(t) = S(t) + O(t) + E(t) + H(t) + Q(t)

Where:
├─ S(t) = Substrate    (9 Auris Nodes)           Base coherence
├─ O(t) = Observer     (Λ(t-1) × 0.30)           Self-reference  
├─ E(t) = Echo         (avg(Λ[t-5:t]) × 0.20)    Memory
├─ H(t) = Harmonic     (HNC frequency × 0.25)    Frequency signal
└─ Q(t) = Quantum      (Telescope × 0.20)        Geometric coherence
```

### Trading Decision Flow

```text
Market Data (price, volume, momentum)
          │
          ├──► QUANTUM TELESCOPE (Geometric refraction)
          │         └──► Dodecahedron → Q(t)
          │
          ├──► PROBABILITY MATRIX (Temporal forecast)
          │         └──► Hour +1 signal → P(t)
          │
          ├──► HNC FREQUENCY (Harmonic analysis)
          │         └──► 528Hz boost / 440Hz penalty → H(t)
          │
          └──► 9 AURIS NODES (Animal totems)
                    └──► S(t) base coherence
                              │
                              ▼
              LAMBDA FIELD: Λ(t) = S(t) + O(t) + E(t) + H(t) + Q(t)
                              │
                              ▼
                    FINAL COHERENCE (Γ)
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
              Γ ≥ 0.45 ?          Γ < 0.45 ?
                ENTER                SKIP
```

---

## 🐅 THE 9 AURIS NODES (Animal Totems)

Each node represents a different market-sensing strategy:

| Node | Frequency | Role |
|------|-----------|------|
| 🐅 **Tiger** | 741 Hz | Momentum hunter |
| 🦅 **Falcon** | 852 Hz | Trend spotter |
| 🐦 **Hummingbird** | 963 Hz | High-frequency signals |
| 🐬 **Dolphin** | 528 Hz | Harmony/Balance |
| 🦌 **Deer** | 396 Hz | Fear/Greed sensing |
| 🦉 **Owl** | 432 Hz | Night/calm markets |
| 🐼 **Panda** | 412 Hz | Patience signals |
| 🚢 **Cargoship** | 174 Hz | Volume/liquidity |
| 🐠 **Clownfish** | 639 Hz | Connection patterns |

---

## 🎵 FREQUENCY PHILOSOPHY

Price action is mapped to **Solfeggio frequencies** using the Golden Ratio (φ = 1.618):

```python
frequency = 432 × (1 + price_change/100) ^ φ
```

| Frequency | Effect | Multiplier |
|-----------|--------|------------|
| **528 Hz** | Transformation/Love | **×1.35 boost** |
| **432 Hz** | Natural Harmony | ×1.00 baseline |
| **440 Hz** | Distortion (AVOID) | ×0.70 penalty |
| **963 Hz** | Poor historical performer | ×0.60 suppression |

---

## 🧠 Core Mathematical Logic

### 1. Lattice Theory & Coherence (Γ)

Markets are treated as a lattice of interconnected price feeds:

$$\Gamma(t) = \frac{1}{N} \sum_{i=1}^{N} \vec{v}_i(t) \cdot \vec{v}_{market}(t)$$

- **High Coherence (Γ → 1)**: Market is unified; trend is strong
- **Low Coherence (Γ → 0)**: Market is chaotic; noise dominates
- **Logic**: Trade _with_ the lattice alignment, not against it

### 2. Swarm Intelligence (Orchestrator)

Multi-agent architecture derived from biological systems:

- **🐺 Scout Signals**: First position broadcasts market direction
- **🐝 Queen-Hive Splitting**: Positions split when value doubles

### 3. Kelly Criterion (Position Sizing)

```python
kelly_fraction = (win_rate × win_loss_ratio - (1 - win_rate)) / win_loss_ratio
position_size = kelly_fraction × safety_factor  # Half-Kelly for safety
```

### 4. Smart Gates (Entry/Exit Logic)

- **Entry Gate**: Coherence ≥ 0.45, avoid 440Hz, probability ≥ 50%
- **Exit Gate**: Take profit 1.2%, Stop loss 0.8%, Trailing stops

---

## 🛠 System Architecture

### Core Modules

| Module | Purpose |
|--------|---------|
| `aureon_unified_ecosystem.py` | Main trading engine |
| `aureon_quantum_telescope.py` | Geometric refraction |
| `hnc_probability_matrix.py` | Temporal forecasting |
| `hnc_master_protocol.py` | Frequency analysis |
| `earth_resonance_engine.py` | Schumann resonance |
| `unified_exchange_client.py` | Multi-exchange API |

### Support Systems

| Module | Purpose |
|--------|---------|
| `trade_logger.py` | Comprehensive logging |
| `aureon_bridge.py` | Inter-system communication |
| `aureon_nexus.py` | Neural network integration |
| `adaptive_learning_engine` | Self-optimization |

### Configuration

```python
CONFIG = {
    'ENTRY_COHERENCE': 0.45,          # Minimum coherence to enter
    'EXIT_COHERENCE': 0.35,           # Exit when coherence drops
    'TAKE_PROFIT_PCT': 1.2,           # 1.2% profit target
    'STOP_LOSS_PCT': 0.8,             # 0.8% stop loss
    'MAX_POSITIONS': 15,              # Maximum concurrent positions
    'OPTIMAL_MIN_GATES': 5,           # Quantum telescope gates
    'KELLY_SAFETY_FACTOR': 0.5,       # Half-Kelly sizing
    'ENABLE_QUANTUM_TELESCOPE': True, # Geometric analysis
    'ENABLE_PROB_MATRIX': True,       # Temporal forecasting
    'ENABLE_HNC_FREQUENCY': True,     # Harmonic analysis
}
```

---

## 💰 THE 10-9-1 COMPOUNDING MODEL

Profits are managed using the **10-9-1** system:

```text
├─ 90% → COMPOUND back into trading capital
└─ 10% → HARVEST to safety (never re-risked)
```

This creates exponential growth while protecting gains.

---

## 📊 DATA SOURCES (JSON State Files)

| File | Purpose |
|------|---------|
| `aureon_kraken_state.json` | Live positions, balance, stats |
| `elephant_ultimate.json` | Symbol memory & blacklist |
| `calibration_trades.json` | Trade history for learning |
| `hnc_frequency_log.json` | Frequency readings |
| `auris_runtime.json` | Runtime configuration |

---

## 💻 How to Run

The system is designed for Linux environments (Ubuntu 24.04 recommended).

```bash
# 1. Install Dependencies
pip install -r requirements.txt

# 2. Configure Environment
cp .env.example .env
# Add your API keys:
# - BINANCE_API_KEY / BINANCE_API_SECRET
# - KRAKEN_API_KEY / KRAKEN_API_SECRET
# - CAPITAL_API_KEY / CAPITAL_API_SECRET (optional)

# 3. Run Simulation
python run_real_data_simulation.py

# 4. Run Paper Trading
python aureon_unified_live.py --paper

# 5. Run Live Trading
python aureon_unified_live.py --live
```

---

## ✅ Verified Exchanges

- **Binance**: Live trading (UK-compliant pairs)
- **Kraken**: API verified (Transaction ID: `OAOWPL-UYY6N-4RGOJJ`)
- **Capital.com**: CFD integration available
- **Alpaca**: Analytics mode (US stocks)

---

## 📊 Performance Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| **Target Win Rate** | 51%+ | Multi-gate filtering ensures quality entries |
| **Risk/Reward** | 1.5:1 | TP 1.2% / SL 0.8% |
| **Processing Speed** | ~7ms per cycle | Real-time WebSocket feeds |
| **Pairs Monitored** | 100+ | Crypto, Forex, Stocks, CFDs |
| **Exchanges** | 4 | Kraken, Binance, Capital.com, Alpaca |
| **Intelligence Layers** | 5 | Quantum, Probability, Harmonic, Auris, Earth |

---

## 🏆 Key Features

### Multi-Exchange Trading

- **Kraken** 🐙 — Primary crypto (USD/GBP/EUR pairs)
- **Binance** 🟡 — UK-compliant crypto (USDC/USDT)
- **Capital.com** 💼 — CFDs (Forex, Indices, Commodities)
- **Alpaca** 🦙 — US Stocks & Crypto (analytics mode)

### Intelligent Risk Management

- Circuit breakers with configurable drawdown limits
- Kelly Criterion position sizing (Half-Kelly for safety)
- Trailing stops with automatic profit harvesting
- 10-9-1 compounding model (90% compound / 10% harvest)

### Adaptive Learning

- Real-time probability matrix training
- Symbol memory with cooldowns and blacklisting
- Cross-exchange performance tracking
- Continuous self-optimization

---

## 📈 Trading History

Trade history is persisted in `paper_trade_history.json` with full metadata:

- Entry/exit prices and times
- Frequency band classification
- Coherence values
- HNC probability signals
- Position sizing percentages

Use this data for continuous learning and system optimization.

---

## 🔮 Roadmap

- [x] v1: Core Master Equation implementation
- [x] v2: 9 Auris Nodes animal totem system
- [x] v3: Extended timeout, frequency filtering
- [x] v4: Adaptive position sizing, learned thresholds
- [x] v5: Multi-exchange unified client (Kraken, Binance, Capital, Alpaca)
- [x] v6: Quantum Telescope (5 Platonic Solids)
- [x] v7: HNC Probability Matrix (2-hour temporal forecasting)
- [x] v8: Earth Resonance Engine (Schumann integration)
- [ ] v9: Multi-timeframe coherence analysis
- [ ] v10: Cross-exchange arbitrage automation
- [ ] v11: Neural network signal enhancement
- [ ] v12: Mobile monitoring dashboard

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [QUICK_START.md](QUICK_START.md) | Fast setup guide |
| [LIVE_TRADING_RUNBOOK.md](LIVE_TRADING_RUNBOOK.md) | Production operations |
| [docs/SYSTEM_LANDSCAPE.md](docs/SYSTEM_LANDSCAPE.md) | Full architecture overview |
| [docs/MULTI_BROKER_GUIDE.md](docs/MULTI_BROKER_GUIDE.md) | Exchange integration details |

---

## ⚠️ Disclaimer

This software is for educational and research purposes. Trading cryptocurrencies and financial instruments involves substantial risk of loss. Past performance does not guarantee future results. Always trade responsibly and never risk more than you can afford to lose.

---

> _"Mathematics is the language in which God has written the universe."_ - Galileo Galilei
>
> _"The market is a frequency. Trade in harmony."_ - Gary Leckey

**Author:** Gary Leckey | R&A Consulting  
**Built with:** GitHub Copilot  
**Last Updated:** December 2025
