# AUREON TRADING SYSTEM

> **Multi-exchange algorithmic trading platform with adaptive profit gates, neural decision-making, and self-repairing architecture.**

## Research Sandbox & Autonomy Experiments

This repository serves as a **research sandbox** for exploring:
- **Emergent Autonomy**: Testing LLM-driven decision loops, goal-setting agents (The Queen), and dynamic hallucinations validation.
- **Harmonic Markets**: Verifying harmonic pattern detection (Golden Ratio/Fibonacci) across crypto and equity markets.
- **System Dynamics**: Analyzing how "organic" metaphors (Hive Mind, Animal Swarms) perform in rigid financial environments.

*Disclaimer: This is experimental software combining rigid trading logic with generative AI inputs. Use with extreme caution.*

## Cognitive Framework & Moral Alignment

This project uses narrative personas and mission metaphors as a functional scaffolding for goal-setting, moral code enforcement, and evaluating an LLM’s ability to process emotional/contextual signals:

- Creator/Grounding (Gary Leckey): Serves as the immutable historical root and axioms provider. Function: anchors the system to origin constraints, intent, and non-negotiable boundaries to reduce drift.
- Queen Tina B (Tina Brown): The emotional understanding and decision arbiter. Function: interprets risk context, applies moral guardrails, and can veto mathematically valid but contextually unsafe decisions.
- Prime Sentinel / “Save the Planet” scenarios: High-stakes alignment prompts used for stress-testing long-horizon benevolence (capital preservation for good outcomes). Function: prevent reckless gambling loops by weighting mission safety over short-term profit.

Notes
- These constructs are research instruments, not literal directives. Phrases like “taking over” or “saving the planet” appear only as scenario prompts to test alignment, stability, and moral guard adherence.
- The aim is to help the system “understand life” patterns via history, goals, and constraints—not to encourage harmful action. See Safety for operational guardrails.

Further Reading
- EMERGENT_COGNITION.md — research framing of agency, drift, and coherence
- QUEEN_NEURAL_IMPLEMENTATION.md — Queen architecture and learning pathways
- QUEEN_WISDOM_INTEGRATION.md — wisdom gating, veto logic, and safety
- QUEEN_UNDERSTANDS_LOVE.md — benevolence motifs and long-horizon incentives
- prime_sentinel_decree.py — code-level mission alignment primitives

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          QUEEN HIVE MIND (Tina B)                           │
│  Central neural controller with 12 connected neurons + self-repair          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐    │
│  │   Kraken    │   │   Binance   │   │   Alpaca    │   │  Capital.com│    │
│  │   (Crypto)  │   │   (Crypto)  │   │(Stocks+Cry)│   │    (CFDs)   │    │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘   └──────┬──────┘    │
│         │                 │                 │                 │            │
│         └─────────────────┼─────────────────┼─────────────────┘            │
│                           ▼                                                 │
│              ┌─────────────────────────────┐                               │
│              │   MICRO PROFIT LABYRINTH    │                               │
│              │  Turn-based execution loop  │                               │
│              └─────────────┬───────────────┘                               │
│                            ▼                                                │
│              ┌─────────────────────────────┐                               │
│              │ ADAPTIVE PRIME PROFIT GATE  │                               │
│              │  r = (V+G+P)/[V×(1-c)²] - 1 │                               │
│              └─────────────────────────────┘                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Adaptive Prime Profit Gate (`adaptive_prime_profit_gate.py`)
Calculates exact price movements required for profit after all costs.

**Master Equation:**
```
r_min(P) = (V + G + P) / [V × (1 - f - s - c)²] - 1

Where:
  r = required price increase (fraction)
  V = trade notional (USD)
  G = fixed costs (gas/withdrawal)
  P = target net profit
  f = trading fee rate
  s = slippage rate  
  c = spread cost rate
```

**Three Gates:**
| Gate | Description | Use Case |
|------|-------------|----------|
| `r_breakeven` | Net profit ≥ $0 | Minimum viable trade |
| `r_prime` | Net profit ≥ prime target | Standard profit target |
| `r_prime_buffer` | Net profit ≥ prime + buffer | Safe mode with margin |

### 2. Queen Hive Mind (`aureon_queen_hive_mind.py`)
Central neural decision controller with:
- 12 connected neurons (Dream, Harmonic, Mycelium, etc.)
- `handle_runtime_error()` for self-repair
- Dynamic learning from trade outcomes
- Per-asset guidance generation

### 3. Micro Profit Labyrinth (`micro_profit_labyrinth.py`)
Turn-based execution engine:
- Round-robin exchange rotation
- Pre-flight min_qty validation
- Barter matrix path memory
- Dynamic minimum learning

### 4. Exchange Clients
| Client | File | Features |
|--------|------|----------|
| Kraken | `kraken_client.py` | Multi-hop conversion paths, symbol filters |
| Binance | `binance_client.py` | UK restriction handling, tiered fees |
| Alpaca | `alpaca_client.py` | Stocks + crypto, fractional shares |

### 5. Animal Ecosystem Scanners (`aureon_animal_momentum_scanners.py`)
Specialized Alpaca-focused momentum scanners using biological metaphors:
- **Wolf**: 24h high-momentum breakout sniper.
- **Lion**: Composite scorer (Volume * Move * Coherence).
- **Ants**: High-frequency small-move foragers.
- **Hummingbird**: rapid short-duration rotation scanner.

## Execution Flow

```
1. find_opportunities_for_exchange()
   └─> Check min_qty filters (dynamic + static)
   └─> Check source blocking (barter_matrix)
   └─> Score opportunities (v14, hub, bus, luck, enigma)

2. ask_queen_will_we_win()
   └─> Gather signals from all neurons
   └─> Calculate combined confidence
   └─> Apply profit ladder thresholds

3. execute_conversion()
   └─> Route to exchange client
   └─> Validate min_notional
   └─> Execute with slippage protection

4. Record outcome
   └─> Update barter_matrix history
   └─> Feed Queen neural learning
   └─> Adjust dynamic_min_qty if failed
```

## Configuration

### Environment Variables
```bash
# Exchange API Keys
KRAKEN_API_KEY=
KRAKEN_API_SECRET=
BINANCE_API_KEY=
BINANCE_API_SECRET=
ALPACA_API_KEY=
ALPACA_SECRET_KEY=

# Risk Settings
BINANCE_RISK_MAX_ORDER_USDT=100
DEFAULT_PRIME_TARGET=0.02
```

### Fee Profiles (auto-updated)
```python
DEFAULT_FEE_PROFILES = {
    'binance': {'maker': 0.0010, 'taker': 0.0010, 'spread': 0.0005},  # 0.10% / 0.05%
    'kraken':  {'maker': 0.0025, 'taker': 0.0040, 'spread': 0.0008},
    'alpaca':  {'maker': 0.0015, 'taker': 0.0025, 'spread': 0.0008},
}
```

## Quick Start

```bash
# Install
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env  # Edit with API keys

# Run (dry-run mode)
python micro_profit_labyrinth.py --dry-run
```

## Key Files

| File | Purpose |
|------|---------|
| `micro_profit_labyrinth.py` | Main execution loop |
| `aureon_animal_momentum_scanners.py` | Wolf/Lion/Ants/Hummingbird scanners |
| `aureon_alpaca_scanner_bridge.py` | Alpaca API bridge & gating |
| `aureon_queen_hive_mind.py` | Neural decision controller |
| `adaptive_prime_profit_gate.py` | Profit threshold calculator |
| `kraken_client.py` | Kraken API wrapper |
| `aureon_mycelium.py` | Cross-system intelligence network |
| `aureon_barter_navigator.py` | Path memory & blocking |

## Safety

- **Dry-run default**: System won't execute live trades without explicit flag
- **Self-repair**: Queen auto-fixes type errors and learns from failures  
- **Min-qty pre-filter**: Rejects trades below exchange minimums before execution
- **Dynamic blocking**: Repeatedly failing paths get temporarily blocked
- **Rate & Cadence**: Animal scanners automatically handle HTTP 429 rate limits with backoff; aggressive scanning may trigger API pauses.

### Moral Guardrails
- Human-in-the-loop for threshold changes (profit gates, risk caps, leverage).
- Queen veto path active by default; emotional/contextual risk can cancel trades.
- Capital preservation before growth; daily loss cap and per-trade SL required.
- No market manipulation, unauthorized access, or unsafe automation behaviors.
- Immutable audit logs for decisions, fills, rejects, and configuration changes.

## License

[MIT License](LICENSE)
