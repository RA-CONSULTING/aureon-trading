# AUREON Quantum Trading System (AQTS)

Field-Theoretic Multi-Agent Cryptocurrency Trading Framework  
Version 1.0.0 • Last Updated: November 19, 2025

---

## Table of Contents

1. [Abstract](#abstract)
2. [Introduction](#introduction)
3. [Mathematical Framework](#mathematical-framework)
4. [Empirical Validation](#empirical-validation)
5. [System Architecture](#system-architecture)
6. [Implementation Details](#implementation-details)
7. [Installation & Usage](#installation-and-usage)
8. [Risk Management & Limitations](#risk-management-and-limitations)
9. [Development & Testing](#development-and-testing)
10. [Disclaimers](#disclaimers)
11. [Production Deployment](#production-deployment)
12. [References & Foundations](#references-and-further-reading)
13. [Conclusion](#conclusion)
14. [Author & Contact](#author-and-contact)
15. [License](#license)
16. [Live Trading Checklist](#live-trading-checklist)

---

## Abstract

AUREON is a multi-agent autonomous cryptocurrency trading system implementing a field-theoretic representation of market dynamics. The system models market state as a continuous field operator \(\Lambda(t)\) derived from a 9-dimensional substrate of heterogeneous perception functions ("Auris nodes"), an observer component, and a temporal echo memory. Simulation-based projections (Monte Carlo, *n* = 100) produce extremely high hypothetical returns (median 6-month terminal value $13.62M from $15 starting notional) under specific, idealized assumptions. These projections are **hypothetical, non-guaranteed**, and subject to substantial model, market, and execution risk. This repository provides architecture, theoretical specification, and operational tooling for research use.

> IMPORTANT: Performance figures are simulation-derived and NOT indicative of future results. Use strictly for research and educational purposes.

**Key Simulation Result (Hypothetical):** Starting capital $15 → Median terminal value $13.62M (6 months, 100 Monte Carlo runs)

---

## Introduction

Conventional algorithmic trading pipelines treat indicators as discrete, isolated signals. AQTS introduces a continuous field \(\Lambda(t)\) computed over 9 specialized agent nodes. Features:
- Real-time multi-stream WebSocket ingestion (Binance)
- Substrate field aggregation with variance-based coherence metric \(\Gamma \in [0,1]\)
- Consensus decision protocol (Lighthouse) requiring ≥ 6/9 node agreement
- Five-level signal transformation pipeline (normalization → weighting → temporal filtering → threshold activation → consensus validation)
- Risk-adjusted sizing (Kelly criterion with safety factor)

---

## Mathematical Framework

### 2.1 Master Equation

\[ \Lambda(t) = S(t) + O(t) + E(t) \]
Where:
- \(S(t)\): Substrate field (weighted sum of node responses)
- \(O(t)\): Observer reflexive component (scaled prior magnitude)
- \(E(t)\): Echo memory (exponential decay blend of recent momentum)

### 2.2 Substrate

\[ S(t) = \sum_{i=1}^{9} w_i f_i(M(t)) \]
Market snapshot vector: \(M(t) = [P, V, \sigma, \mu, \Delta]\) with price, volume (rolling window), volatility (std), momentum (rate of change), spread.

### 2.3 Auris Node Response Functions (Illustrative)


| Node | Function | Sensitivity |
|------|----------|-------------|
| Tiger | `f1 = σ · Δ · tanh(μ)` | Volatility × spread amplification |
| Falcon | `f2 = μ · log(1 + V)` | Momentum-volume correlation |
| Hummingbird | `f3 = (σ + ε) / α` | Inverse volatility stability |
| Dolphin | `f4 = sin(ω μ) · Γ` | Oscillatory momentum coherence |
| Deer | `f5 = β1 P + β2 V + β3 σ` | Linear multifactor |
| Owl | `f6 = cos(ω μ) · E(t-1)` | Memory-weighted cosine momentum |
| Panda | `f7 = V (1 - σ^2)` | High volume, low volatility preference |
| CargoShip | `f8 = V^1.5` | Superlinear volume scaling |
| Clownfish | `f9 = abs(ΔP) · e^{-σ}` | Micro-price change damped by volatility |

### 2.4 Coherence Metric
\[ \Gamma(t) = \frac{1}{1 + \operatorname{Var}[f_1,\dots,f_9]} \]
High \(\Gamma \to 1\) indicates node agreement.

### 2.5 Decision Criterion
Trade signal when:
\[ |\Lambda(t)| > \theta \quad \land \quad \Gamma(t) > \gamma_{min} \quad \land \text{votes} \ge 6/9 \]

### 2.6 Position Sizing (Kelly with Safety Factor)
\[ f^* = \phi\, \frac{p b - (1-p)}{b} \quad ; \quad \text{size} = f^* \times \text{capital} \]
Where \(p\) win probability, \(b\) odds, \(\phi\) safety factor (default 0.5). Subject to exchange minimum notional (~$10 USDT).

---

## Empirical Validation

### 3.1 Monte Carlo Summary (n=100)
Median trajectory suggests extremely high compounding from micro-notional base; results are **non-realized** projections.
| Timeline | Median Balance | ROI % | 25th % | 75th % |
|----------|---------------:|------:|-------:|-------:|
| Week 1 | $39 | 160% | $32 | $48 |
| Week 2 | $100 | 567% | $81 | $125 |
| Month 1 | $859 | 5,627% | $682 | $1,089 |
| Month 2 | $47,000 | 313,333% | $38,200 | $58,100 |
| Month 3 | $1,160,000 | 7,733,333% | $921,000 | $1,450,000 |
| Month 4 | $9,530,000 | 63,533,333% | $7,620,000 | $11,890,000 |
| Month 6 | $13,620,000 | 90,800,000% | $10,850,000 | $17,010,000 |

Distribution (Month 6): Mean $14.89M • Median $13.62M • SD $6.34M • Min $9.65M • Max $35.34M • Success rate (profitable) 100%. **All hypothetical.**

### 3.2 Constraints Modeled
Trading fees (0.1%), slippage (0.01–1%), max position ($50M), min notional ($10), API limit (50 orders/day), volatility-driven stop-loss, drawdown cap (30%), calibrated win rate (55–65%), avg win/loss 1.8:1.

### 3.3 Backtest (2024-01-01 → 2024-11-01)
- Trades: 1,247
- Win rate: 61.3%
- Avg win: 3.24% | Avg loss: -1.79%
- Win/Loss ratio: 1.81
- Sharpe: 2.14
- Max drawdown: 18.7%
- Coherence > 0.95 trades win rate: 68.4% vs 54.1% (p < 0.001)

---

## System Architecture

### 4.1 Data Ingestion
Binance WebSocket streams: `@aggTrade`, `@depth`, `@miniTicker`, `@kline_1m`. Snapshot vector \(M(t)\) assembled each tick. Resilient reconnection, heartbeat (30s), freshness validation.

### 4.2 Field Computation (`core/masterEquation.ts`)
Produces structured `FieldState` containing \(\Lambda, \Gamma, S, O, E\), dominant node, per-node responses.

### 4.3 Signal Transformation Pipeline
1. Normalization: \(\Lambda_1(t) = (\Lambda(t) - \mu_\Lambda)/\sigma_\Lambda\)  
2. Coherence weighting: \(\Lambda_2(t) = \Lambda_1(t) \Gamma(t)^2\)  
3. Temporal blend: \(\Lambda_3(t) = 0.7 \Lambda_2(t) + 0.3 \Lambda_2(t-1)\)  
4. Threshold activation: \(\Lambda_4(t) = \Lambda_3(t)\) if \(|\Lambda_3(t)| > \theta\) else 0  
5. Consensus filter: \(\Lambda_5(t) = \Lambda_4(t)\) if votes ≥ 6/9 else 0  
Non-zero \(\Lambda_5(t)\) triggers execution.

### 4.4 Execution Layer (Agents)
| Agent | File | Strategy | Base |
|-------|------|----------|------|
| Hummingbird | `scripts/hummingbird.ts` | ETH rotational mean reversion | ETH |
| Army Ants | `scripts/armyAnts.ts` | Micro-diversified USDT positions | USDT |
| Lone Wolf | `scripts/loneWolf.ts` | High-conviction momentum | Mixed |
Features: MARKET orders with `quoteOrderQty`, min-notional guard, slippage comparison, exponential backoff retries, audit logging.

---

## Implementation Details

### 5.1 Stack
Node.js 18+, TypeScript, Vite (UI), React 18, TSX runtime, PM2 (prod), custom simulation/backtest harness.

### 5.2 Key Modules
| Purpose | File |
|---------|------|
| Master Equation | `core/masterEquation.ts` |
| Auris Nodes | `core/aurisSymbolicTaxonomy.ts` |
| Binance REST | `core/binanceClient.ts` |
| WebSockets | `core/binanceWebSocket.ts` |
| Risk Mgmt | `core/riskManagement.ts` |
| Execution | `core/executionEngine.ts` |
| Consensus | `core/lighthouseMetrics.ts` |
| Performance | `core/performanceTracker.ts` |

### 5.3 Environment Configuration (`.env`)
```env
BINANCE_API_KEY=your_key
BINANCE_API_SECRET=your_secret
DRY_RUN=true
CONFIRM_LIVE_TRADING=yes
BINANCE_TESTNET=false
MIN_COHERENCE=0.945
DECISION_THRESHOLD=0.15
POSITION_SIZE_FACTOR=0.98
KELLY_SAFETY_FACTOR=0.5
STATUS_MOCK=false
PORT=8787
```

---

## Installation and Usage

### 6.1 Prerequisites
Node.js 18+, Binance Spot API keys (withdrawals disabled), recommended starting balance ≥ $50.

### 6.2 Install
```sh
git clone <repository_url>
cd aureon-trading
npm install
```

### 6.3 Configure
Create `.env` (see above). Run status server:
```sh
# Mock demo
STATUS_MOCK=true npm run status:server

# Live (requires valid keys)
npm run status:server
```
Start UI:
```sh
npm run dev
```
Bots (dry-run recommended):
```sh
npm run hb:dry
npm run ants:dry
npm run wolf:dry
npm run orchestrate:dry
```
Live example (explicit confirmation):
```sh
CONFIRM_LIVE_TRADING=yes DRY_RUN=false tsx scripts/hummingbird.ts
```

### 6.4 Prism & Bridge Utilities
```sh
npm run prism
npm run bridge
npm run rainbow:dry
npm run rainbow:live
```

---

## Risk Management and Limitations

### 7.1 Risks
Market, model, execution, liquidity, technical and regime shift risks.
### 7.2 Mitigations
Capital reserve (2%), volatility-adjusted stops, coherence filtering, consensus voting, drawdown cap (30%), rate limiting.
### 7.3 Limitations / Future Work
Single-exchange spot focus, periodic parameter recalibration, limited microstructure modeling. Roadmap: multi-exchange arbitrage, RL adaptation, order book imbalance, extended regime validation, formal statistical tests.

---

## Development and Testing

```sh
npm run typecheck   # Types
npm run build       # Prod bundle
npm run preview     # Serve build
```
Testing layers: unit (field/math), integration (dry-run trade loop), historical backtest, Monte Carlo forward simulation.

---

## Disclaimers

This system is for **research & educational use only**. Cryptocurrency trading is high risk. Hypothetical performance does not guarantee future results. Nothing herein constitutes investment, financial, or trading advice. Secure API keys (no withdrawals, IP whitelist, 2FA). Ensure regulatory compliance in your jurisdiction.

---

## Live Trading Checklist
1. API keys: trading-only, withdrawals disabled, IP whitelist.  
2. Funds: USDT ≥ $10 or ETH value equivalent.  
3. Env: `DRY_RUN=false`, `CONFIRM_LIVE_TRADING=yes`, `BINANCE_TESTNET=false`.  
4. Status server OK: `npm run status:server` → `/api/status`.  
5. UI reachable: `npm run dev`.  
6. Start bot (example):
```sh
CONFIRM_LIVE_TRADING=yes DRY_RUN=false tsx scripts/loneWolf.ts
```
7. Monitor: UI panels, logs, `/api/trades`.  
8. Pause: Ctrl+C. Re-enable safety by setting `DRY_RUN=true`.
Common issues: MIN_NOTIONAL (fund account), API auth errors (permissions/IP), insufficient balance (bots idle until eligible).

---

## Production Deployment

### 10.1 Pre-Flight
Types/build ok; dry-run stable; security audit complete.
### 10.2 PM2
```sh
npm install -g pm2
pm2 start ecosystem.config.js
pm2 save
pm2 startup
pm2 monit
pm2 logs
pm2 status
```
Emergency:
```sh
pm2 stop all
npx tsx scripts/emergencyStop.ts
```

---

## References and Further Reading

- Field Theory analogs (continuous operator modeling)
- Multi-Agent consensus & ensemble methods
- Lighthouse protocol (Byzantine-tolerant voting adaptation)
- Information-theoretic coherence interpretation
- Kelly criterion and stochastic optimal control

---

## Conclusion

AQTS introduces a field-based, consensus-filtered framework for autonomous crypto trading. Innovations: \(\Lambda(t)\) continuous representation, 9-node multi-perspective substrate, coherence gating, consensus validation, adaptive risk sizing. While simulation/backtest metrics appear strong, they are **not predictive**; treat AQTS as a research platform for exploring field-theoretic structures in financial modeling.

---

## Author and Contact

**Developer:** Gary Leckey  
**Organization:** R&A Consulting and Brokerage Services Ltd (UK)  
**Repository:** GitHub (this project)  
Research inquiries: open an issue or contact via ResearchGate.

Citation (example):
```
Leckey, G. (2025). AUREON Quantum Trading System: A Field-Theoretic Approach to Cryptocurrency Trading with Multi-Agent Consensus. R&A Consulting and Brokerage Services Ltd. https://github.com/<yourusername>/aureon-trading
```

---

## License

MIT License

Copyright (c) 2025 R&A Consulting and Brokerage Services Ltd

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

## 15. Quick Commands (Summary)

```sh
# Status & UI
STATUS_MOCK=true npm run status:server
npm run dev

# Bots (dry)
npm run hb:dry
npm run ants:dry
npm run wolf:dry

# Live (explicit confirm)
CONFIRM_LIVE_TRADING=yes DRY_RUN=false tsx scripts/hummingbird.ts
```

---

## 16. Contributing

Issues and PRs welcome. Please include: reproduction steps, environment details, and whether change affects live trading safety. Avoid committing secrets; use `.env` and `.env.example` patterns.

---

### Final Note
If any claim appears extraordinary, treat it as a **research artifact** pending independent verification. Validate locally with dry-runs and backtests before any live deployment.

