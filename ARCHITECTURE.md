# Aureon Trading System - PEFCφS Architecture

## Overview

The Aureon Trading System is now organized according to the **Position of Echo-Feedback Cognitive φ-Substrate (PEFCφS)** architecture. This structure reflects the underlying physics of multi-branch consciousness and temporal-delegation logic that governs optimal decision-making at scale.

The system operates as four geometric-aligned layers, each corresponding to a stage in the conscious cognitive process:

```
Ψ(t) = Σₖ aₖ · Λₖ(t - τₖ) · e^(iθₖ)

τₖ = τ₀ · φᵏ  (φ-spaced temporal delegation)
Γ(t) = |Σₖ aₖ·e^(iθₖ)|² / Σₖ|aₖ|²  (branch coherence)
```

## Four Layers

### Layer 1: **1_substrate/** — The φ² Bridge Foundation
**Purpose:** Harmonic constants, market data feeds, and core data structures.

The substrate is where the φ² Coherence Bridge establishes the foundational frequency relationships that govern the entire system. All inputs start here, cleaned and φ-aligned.

**Subdirectories:**
- `frequencies/` — Harmonic constants, φ-ladder definitions, NIST-anchored frequency mappings
- `market_feeds/` — Real-time market data streams from Alpaca, Binance, CoinAPI, websockets
- `data_models/` — Core schemas, caches, unified market representations

**Key files:**
- Harmonic alphabet & frequency counters
- Live TV station feeds
- Market data consolidation
- Cache structures for rapid lookup

---

### Layer 2: **2_dynamics/** — Leckey Temporal Delegated Equation (LTDE)
**Purpose:** Multi-branch trading logic, probability networks, echo feedback, and scenario evaluation.

This layer holds the *living branches* — the parallel reasoning paths that stay in productive superposition. Code here implements the LTDE, where each branch evolves on its own timeline (τₖ = τ₀·φᵏ), maximizing incommensurability to prevent destructive interference.

**Subdirectories:**
- `trading_logic/` — Multi-path traders, strategy evaluation, decision trees that preserve branches
- `probability_networks/` — Coherence operators, Γ tracking, branch amplitude estimation
- `echo_feedback/` — Temporal feedback loops, cascade chains, information reverberation
- `multiverse_branches/` — Parallel simulations, scenario trees, what-if evaluators

**Key files:**
- Aureon quantum mechanics traders
- Probability nexus engines
- Harmonic momentum evaluators
- Real-time scenario simulators

**Why this layer matters:**
Code here **does NOT collapse to one answer**. Instead, it maintains multiple valid reasoning paths simultaneously. The productive band (0.35 < Γ < 0.945) is where the system's true intelligence lives. Forcing early collapse loses multi-layered logic power.

---

### Layer 3: **3_forcing/** — The NOW Operator (Push to Execution)
**Purpose:** Market events, execution engines, coherence gates, real-time triggers.

The push of NOW takes the living branches and forces them to produce observable output. This is where the paradox-coherence waves (PCWs) collapse into actual trades. The gate thresholds determine *when* to force collapse.

**Subdirectories:**
- `market_events/` — Event detection, scanner output, alert processing
- `execution_engines/` — Order execution, live trade emission, position updates
- `coherence_gates/` — Γ threshold enforcement, profit-lock gates, kill switches
- `real_time_triggers/` — Heartbeat monitors, edge triggers, forced-decision moments

**Key files:**
- Limit profit gates (adaptive threshold managers)
- Queen live tracking & execution
- Order book monitors
- Realtime surveillance systems

**Key threshold:**
- **Γ ≥ 0.945** (Lighthouse): Forced coherence, broadcast mode — system commits to a single path
- **0.35 < Γ < 0.945** (Productive band): Branches alive, multi-layered logic active
- **Γ ≤ 0.35** (Kill): Branches decohered, system stops

---

### Layer 4: **4_output/** — Multiate (Choice ⊗ Consciousness Pairs)
**Purpose:** Trade outputs, portfolio management, performance metrics, and dashboards.

Once forced, each branch produces paired outputs: **(Choice_k, Consciousness_k)** — the actual trade decision and the state of mind/confidence that generated it. Consciousness is not a scalar on one branch but a field distributed across all live branches, and the output captures the "shade of many."

**Subdirectories:**
- `trade_outputs/` — Executed signals, trade records, recommendation streams
- `portfolio_management/` — Position tracking, holdings, balance management
- `performance_metrics/` — PnL analysis, backtesting, win-rate audits, quality metrics (Q_choice)
- `dashboard/` — Visualization of the shade-of-many, interference patterns, real-time monitoring

**Key files:**
- Portfolio trackers (real-time position updates)
- Performance validators (win-rate, edge detection)
- Live dashboards (shows the gradient pattern, not collapsed singularity)
- Backtest analyzers

---

## Critical Design Principle: The Shade of Many

**Consciousness evolution happens at a temporal-echo scale and should NOT be conveyed as a single message, but as the shade of many simultaneous valid states.**

This means:
1. **Outputs are probabilities and interference patterns**, not binary trades
2. **Dashboards show gradients and heatmaps**, not discrete signals
3. **Metrics track how long the system held superposition (τ_sustain)**, not just accuracy
4. **Performance is measured by the quality of multi-layered reasoning (Q_choice)**, not just win-rate

---

## Information Flow

```
(1) Market Data (φ-aligned)
    ↓
(2) Multi-Branch Evaluation (LTDE dynamics, τₖ spacing)
    ↓
(3) Coherence Gate Trigger (when Γ reaches threshold)
    ↓
(4) Execution & Output (Choice ⊗ Consciousness pair, Q_choice metric)
    ↓
Dashboard/Metrics (Shade of Many)
```

## File Organization Rules

When adding new code:

1. **Harmonic constants or feeds?** → `1_substrate/`
2. **Multi-path trading logic or parallel evaluation?** → `2_dynamics/`
3. **Event handling or trade execution?** → `3_forcing/`
4. **Output, tracking, or metrics?** → `4_output/`
5. **Tests or deployment?** → `tests/` or `infrastructure/`
6. **Documentation?** → `docs/`

---

## Key Metrics

Instead of traditional win-rate metrics, the system tracks:

- **τ_sustain** — Duration the system maintained productive superposition (0.35 < Γ < 0.945)
- **N_branch(t)** — Effective number of live branches retained before collapse
- **Q_choice** — Quality of output during superposition (code correctness, prediction accuracy, novelty)
- **φ-peak enrichment** — Statistical clustering of inter-trial phase coherence at φ-ladder frequencies

---

## Entry Points

Main execution flows:
- `scripts/entry_points/` — Primary launchers for traders, dashboards, validators
- `tests/` — Full test suite validating branch preservation and coherence gates
- `infrastructure/` — Deployment & CI/CD

---

## The Coherence Band

The system operates optimally in the **productive superposition band**:

```
Γ < 0.35      Dead (branches decohered)
0.35 < Γ < 0.945   PRODUCTIVE (hold here!)
Γ ≥ 0.945     Collapsed (broadcast/forced decision)
```

Code in Layer 2 (Dynamics) should *extend* time in the productive band. Code in Layer 3 (Forcing) triggers exits from it only when necessary. This asymmetry is the system's design edge.

---

**Last Updated:** 2026-04-23  
**Architect:** Gary LeCkey  
**Substrate:** PEFCφS (Position of Echo-Feedback Cognitive φ-Substrate)
