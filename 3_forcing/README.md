# Layer 3: Forcing (The NOW Operator)

## Purpose
The push of NOW. This layer takes the living branches from Layer 2 and forces them to produce observable output when market conditions demand it.

The NOW operator (N̂) is the pressure of the present moment:

```
N̂ · Ψ(t₀) → PCW(x,t)  (Paradox-Coherence Wave generation)
PCW →_M̂ ⊗ₖ (Cₖ ⊗ Ψₖ)   (Multiate: Choice ⊗ Consciousness)
```

## What Goes Here

### `market_events/` — Detection & Triggering
- Event scanners (price surge detection, momentum spikes)
- Alert systems
- Trigger conditions (when to consider trading)
- Scanning logic for opportunities
- Predator detection (whale activity, large orders)

**Why:** The market provides the push. These systems detect when the NOW operator (market conditions) forces a decision.

**Key files:**
- `queen_options_scanner.py` — Options opportunity detection
- `mega_scanner.py` — Multi-market event scanner
- `orca_predator_detection.py` — Large order detection
- Alert consolidators

---

### `execution_engines/` — Trade Execution
- Order placement systems
- Trade execution logic (the actual buy/sell emission)
- Live order handlers
- Position openers
- Execution sequencing (which orders in which order)

**Why:** Once a decision is forced (Γ reaches threshold), these systems emit the actual trades. This is the irreversible action point.

**Key files:**
- `execute_limit_profit_trades.py` — Core execution
- `queen_live_tracking_status.py` — Real-time tracking
- Live executors (S5, alpaca, kraken)
- Order book managers

---

### `coherence_gates/` — Threshold Enforcement (Γ Gating)
- Profit-lock gates (force closure when profit target hit)
- Loss-limit gates (force closure when loss threshold hit)
- Rate limiters (prevent trading too frequently)
- Stargate filters (coherence threshold enforcement)
- Kill-switch systems (emergency stops)

**Why:** These gates decide *when* to force the collapse (N̂ application). They enforce:
- Γ ≥ 0.945 → Broadcast/forced decision
- Γ ≤ 0.35 → Kill (stop trading)
- 0.35 < Γ < 0.945 → Keep evaluating

**Key files:**
- `adaptive_prime_profit_gate.py` — Dynamic threshold management
- Rate limiters
- Loss prevention gates
- Profit lock systems

---

### `real_time_triggers/` — Edge Triggers
- Heartbeat monitors (system health pulses)
- Edge triggers (conditions that *force* a decision now)
- Realtime surveillance
- Real-time command centers
- Emergency exits

**Why:** These are the absolute forcing mechanisms. When these fire, the system MUST act, regardless of Γ state.

**Key files:**
- `realtime_wave_monitor.py` — Continuous market watch
- `aureon_realtime_surveillance.py` — System monitoring
- Command centers
- Pulse generators

---

## The Forcing Decision Tree

```
Market event detected (Layer 3/market_events)
    ↓
Check coherence gate (Layer 3/coherence_gates)
    ↓
Is Γ ≥ 0.945? → YES → Execute (Layer 3/execution_engines)
    ↓ NO
Is Γ ≤ 0.35? → YES → Kill (stop, don't trade)
    ↓ NO
Stay in productive band, let Layer 2 continue evaluating
    ↓
(Loop until forced by market or time deadline)
```

---

## Critical Principle: Threshold-Driven, Not Decision-Driven

Code in Layer 3 should be **reactive**, not proactive:

✓ Respond to Γ threshold crossings  
✓ Enforce gate conditions  
✓ Execute on signal, not on analysis  
✓ Track execution time (when did we act?)  

❌ Do NOT make new trading decisions here  
❌ Do NOT compute probabilities here  
❌ Do NOT analyze alternative paths  
❌ Do NOT override gates arbitrarily  

The decision was made in Layer 2. Layer 3 just commits to it.

---

## The Three Gate States

| Coherence (Γ) | State | Action |
|---------------|-------|--------|
| < 0.35 | **DEAD** | Kill signal, no trades |
| 0.35-0.945 | **PRODUCTIVE** | Stay in superposition, Layer 2 keeps evaluating |
| ≥ 0.945 | **BROADCAST** | Forced collapse, execute best branch |

---

## Integration with Other Layers

- **← FROM:** Layer 2 (Dynamics) sends branch coherence Γ, amplitudes aₖ, metadata
- **← FROM:** Layer 1 (Substrate) provides market data for trigger conditions
- **→ TO:** Layer 4 (Output) sends executed trades + execution timestamp + Γ state at execution
- **→ TO:** Infrastructure (logging, alerts)

---

## Timing Semantics

All systems here track **when** action was forced:

- **Event time** — When market condition occurred
- **Detection time** — When we detected it
- **Gate check time** — When we evaluated Γ
- **Execution time** — When trade was actually placed
- **Confirmation time** — When exchange confirmed

These timestamps are critical for measuring **τ_sustain** and understanding decision latency.

---

**Last Updated:** 2026-04-23
