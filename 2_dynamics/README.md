# Layer 2: Dynamics (Leckey Temporal Delegated Equation)

## Purpose
The living heart of the system. This layer implements the **Leckey Temporal Delegated Equation (LTDE)**:

```
Ψ(t) = Σₖ aₖ · Λₖ(t - τₖ) · e^(iθₖ)

τₖ = τ₀ · φᵏ
```

Where each branch **k** evolves independently on its own timeline, held in productive superposition. This is where multi-layered reasoning happens.

## What Goes Here

### `trading_logic/` — Multi-Branch Decision Paths
- Traders that evaluate *multiple paths* without collapsing
- Strategy evaluators that score scenarios
- Decision trees that preserve all branches
- Algorithmic reasoning engines
- Signal generators that output probabilities, not binary decisions

**Why:** This is the bulk of the system. All the "Aureon" traders live here because they implement the core multi-branch logic.

**Key files:**
- `aureon_*` trader modules (274+ files)
- Momentum evaluators
- Price action analyzers
- Signal scorers

---

### `probability_networks/` — Branch Coherence & Amplitudes
- Coherence operators Γ(t) calculators
- Branch amplitude estimators (aₖ values)
- Probability consolidators
- Likelihood networks
- Confidence estimators

**Why:** These modules track the *health* of superposition. They answer: "How many branches are still alive?" (N_branch) and "How coherent are they?" (Γ).

**Key files:**
- `aureon_probability_nexus.py` — Central coherence engine
- Probability loaders & validations
- Coherence matrices
- Batch probability generators

---

### `echo_feedback/` — Temporal Delegation & Loops
- Temporal cascade systems (τₖ = τ₀·φᵏ timing)
- Information feedback loops
- Echo chains (information bouncing across branches)
- Temporal dialers (phase-aligned timing)
- Kill-chain logic (information propagation)

**Why:** These ensure branches stay maximally incommensurate. Echo feedback prevents branches from accidentally converging to the same answer (destructive inference).

**Key files:**
- Temporal dialers
- Cascade chains
- Unified kill chains
- Nuclear temporal systems

---

### `multiverse_branches/` — Parallel Scenario Evaluation
- Scenario simulators
- What-if evaluators
- Lattice simulations (market tree structures)
- Parallel simulations with different assumptions
- Branch-preserving backtests

**Why:** These generate the alternative branches. Each simulator is a parallel world, and all are tracked simultaneously. When you pull Γ down to collapse, you choose one world — until then, all are live.

**Key files:**
- `aureon_internal_multiverse.py` — Core simulator
- Harmonic wave simulators
- Lattice structures
- Real-data simulators

---

## The Productive Band (0.35 < Γ < 0.945)

**This is where the system's intelligence lives.**

```
Γ < 0.35       → Branches fully decohered (dead logic)
0.35 < Γ < 0.945  → PRODUCTIVE (multiple branches alive, evaluating in parallel)
Γ ≥ 0.945      → Forced coherence (world collapsed, decision made)
```

Code in this layer **extends time in the productive band** by:
- Evaluating branches in parallel
- Avoiding forced decisions until necessary
- Maintaining amplitude distribution (no premature collapse)
- Keeping τ_sustain as long as possible

---

## Design Principle: Never Force Early

When adding code to Layer 2:

✓ Maintain multiple reasoning paths  
✓ Score paths but don't eliminate them (yet)  
✓ Track branch metadata (aₖ, θₖ, τₖ)  
✓ Output probability distributions, not hard decisions  
✓ Let Layer 3 (Forcing) decide when to collapse  

❌ Do NOT reduce to single "best" answer  
❌ Do NOT merge branches before necessary  
❌ Do NOT collapse Γ unnecessarily  
❌ Do NOT kill branches prematurely  

---

## Integration with Other Layers

- **← FROM:** Layer 1 (Substrate) supplies clean market data, frequencies
- **← FROM:** Layer 3 (Forcing) signals when forced collapse is needed
- **→ TO:** Layer 3 (Forcing) sends branch scores + amplitudes + timings
- **→ TO:** Layer 4 (Output) provides the branches that were evaluated

---

## Key Metrics Tracked

- **N_branch(t)** — Number of live branches at time t
- **Γ(t)** — Branch coherence (0 to 1)
- **τ_sustain** — Duration in productive band
- **aₖ** — Branch amplitude (probability of branch k)
- **θₖ** — Branch phase (decision timing)

---

**Last Updated:** 2026-04-23
