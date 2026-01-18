# Aureon Trading System - AI Agent Instructions

## System Architecture (Orion/Batten Matrix Pipeline)

This is a **multi-exchange algorithmic trading system** with three primary layers:

```
Ecosystem (Feed Layer) → Scanner (Validation Layer) → Queen Hive (Execution Layer)
```

### 1. **Ecosystem Layer** - Reality Branch Universe
- Each symbol/pair on each exchange = one "reality branch"
- Files: `aureon_unified_ecosystem.py`, `global_financial_feed.py`
- **Key concept**: Treats trading pairs as parallel reality branches to scan
- Emits: Market data feeds, candle freshness, spread/volatility snapshots

### 2. **Scanner Layer** - Batten Matrix (3 Validations → Act on 4th)
- Files: `aureon_probability_nexus.py`, `aureon_global_wave_scanner.py`
- **Core logic**: Each branch undergoes 3 validation passes, execution on 4th confirmation
- **Metrics computed**:
  - **PIP score**: Net move after fees (target: 0.07–1.4 pips post-profit)
  - **Coherence score** $C_b$: Agreement across 3 validators (high = tight consensus)
  - **LAMBDA (Λ) stability**: $Λ_b(t) = e^{-α D_b(t)}$ (penalizes drift over time)
  - **Drift score** $D_b(t)$: How fast the branch state changes before execution
- **Decision formula**: $S_b(t) = \bar{p}_b \cdot P_b \cdot C_b \cdot Λ_b(t)$

### 3. **Queen Hive Layer** - Execution & Orchestration
- Files: `aureon_queen_hive_mind.py`, `micro_profit_labyrinth.py`
- **Tina B** ("The Intelligent Neural Arbiter Bee"): Central neural controller with 12 neurons
- Enforces 4th-pass execution gate, risk management, turn-based order routing
- Integration: Queen receives PIP predictions, validation probabilities, drift features

### 4. **Stargate Protocol Layer** - Quantum Mirror & Timeline Activation 🌌
- Files: `aureon_stargate_protocol.py`, `aureon_quantum_mirror_scanner.py`, `aureon_timeline_anchor_validator.py`
- **Planetary Node Network**: Historical sacred sites (Giza, Stonehenge, etc.) as resonance nodes
- **Quantum Mirror Pull**: Identifies and anchors high-coherence "timelines" (beneficial outcome states)
- **Integration**: Couples Schumann resonance (7.83 Hz), Solfeggio frequencies, and golden ratio (φ) harmonics

#### Stargate Protocol Components:
```python
# 1. Planetary Stargates - 12 global nodes with resonance frequencies
PLANETARY_STARGATES = {
    "giza": StargateNode(freq=432.0, casimir=0.95),
    "stonehenge": StargateNode(freq=396.0, casimir=0.88),
    "machu_picchu": StargateNode(freq=528.0, casimir=0.90),
    # ... more nodes
}

# 2. Quantum Mirrors - Potential timelines with coherence scores
quantum_mirrors = {
    "golden_age": QuantumMirror(coherence=0.95, beneficial=0.98),
    "unity_timeline": QuantumMirror(coherence=0.92, beneficial=0.97),
}

# 3. Human Resonance - Conscious nodes contributing to global coherence
conscious_nodes = register_conscious_node(stargate_id, intention)
```

#### Quantum Mirror Scanner Integration:
- **Reality Branches**: Market symbols scanned as parallel timeline possibilities
- **Validation Passes**: Same 3-pass Batten Matrix applied to timeline coherence
- **Convergence Detection**: Multiple branches aligning = manifestation window
- **4th Pass Execution**: Timeline anchor when coherence exceeds φ threshold (0.618)

#### Timeline Anchor Validator:
- **7-Day Validation Window**: Extended validation across prime/Fibonacci intervals
- **Hourly/Daily/Weekly Cycles**: Multi-scale coherence verification
- **Anchor Strength**: Accumulated score from successful validations
- **Persistence**: `7day_pending_validations.json`, `7day_anchored_timelines.json`

---

## Critical Workflows

### Trading Execution Flow
```python
# 1. Scan opportunities across exchanges
opportunities = find_opportunities_for_exchange(exchange)

# 2. Validate via 3-pass pipeline (aureon_probability_nexus.py)
validation_passes = [validate_pass_1(), validate_pass_2(), validate_pass_3()]
coherence = compute_coherence(validation_passes)

# 3. Check drift/lambda stability
drift = compute_drift(current_state, scan_state)
lambda_score = math.exp(-alpha * drift)

# 4. Execute on 4th confirmation (Queen Hive enforces)
if all_passes_validated and coherence > threshold and lambda_score > min_stability:
    execute_conversion(branch)
```

### Profit Gate Equation
From `adaptive_prime_profit_gate.py`:
```python
r_min = (V + G + P) / (V × (1 - f - s - c)²) - 1
# V=notional, G=fixed costs, P=target profit, f=fee, s=slippage, c=spread
```
Three gates: `r_breakeven` (profit ≥ $0), `r_prime` (≥ target), `r_prime_buffer` (safe margin)

### Debugging Commands
```bash
# Live trading (dry-run mode)
python micro_profit_labyrinth.py --dry-run

# Check system health
python check_system_logs.py
python comprehensive_diagnostic.py

# Exchange balance verification
python check_all_balances.py
python verify_platform_connectivity.py
```

---

## Code Patterns & Conventions

### 1. **Windows UTF-8 Fix** (MANDATORY at top of every `.py` file)
```python
import sys, os
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import io
        def _is_utf8_wrapper(stream):
            """Check if stream is already a UTF-8 TextIOWrapper."""
            return (isinstance(stream, io.TextIOWrapper) and 
                    hasattr(stream, 'encoding') and stream.encoding and
                    stream.encoding.lower().replace('-', '') == 'utf8')
        # Only wrap if not already UTF-8 wrapped (prevents re-wrapping on import)
        if hasattr(sys.stdout, 'buffer') and not _is_utf8_wrapper(sys.stdout):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        if hasattr(sys.stderr, 'buffer') and not _is_utf8_wrapper(sys.stderr):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except Exception:
        pass
```

### 2. **Data Structures: Always Use `@dataclass`**
```python
from dataclasses import dataclass, field
from typing import List, Optional, Dict

@dataclass
class BranchValidation:
    symbol: str
    timestamp: float
    pip_score: float
    validation_passes: List[float] = field(default_factory=list)
    coherence: float = 0.0
    lambda_stability: float = 1.0
    drift: float = 0.0
```
**Pattern**: Define as dataclass → Serialize to JSON for persistence → Load in related modules. See examples in `aureon_probability_nexus.py`, `aureon_timeline_oracle.py`, `queen_loss_learning.py`.

### 3. **Exchange Client Pattern**
All exchange wrappers (`kraken_client.py`, `binance_client.py`, `alpaca_client.py`) implement:
- `get_balance()` → Dict[asset, amount]
- `get_ticker(symbol)` → {bid, ask, last}
- `execute_trade(symbol, side, quantity)` → order result
- Fee profiles stored in `DEFAULT_FEE_PROFILES` dict

### 4. **Queen Hive Decision Pattern**
```python
# Ask Queen before execution
guidance = queen_hive.ask_queen_will_we_win(
    asset=asset,
    exchange=exchange,
    opportunity_score=score,
    context={"coherence": C_b, "lambda": lambda_score}
)
if guidance.confidence > threshold:
    execute()
```

### 5. **Thought Bus Communication** (Loosely-Coupled Pub/Sub)
```python
from aureon_thought_bus import ThoughtBus, Thought

# Emit signal
bus.emit(Thought(
    source="Scanner",
    type="validation_complete",
    data={"symbol": "BTC/USD", "coherence": 0.82}
))

# Subscribe to events
def on_queen_decision(thought: Thought):
    if thought.type == "4th_decision":
        handle_execution_gate(thought.data)
```
**Pattern**: Check `THOUGHT_BUS_AVAILABLE` before use. Enables cross-module signaling without tight coupling.

### 5.1 **Whale Sonar (Mycelium Sonar)** 🐋🔊
Treat each subsystem (each Python process / component) as a *whale* that sings short, frequency-like signals to the Queen via `ThoughtBus` and the Enigma integration. The sonar is intentionally compact (minimal text / morse-like codes) to validate cognitive activity with small payloads and to enable "data packers" for streamlined streaming.

Core behavior:
- Each subsystem publishes regular Thoughts (health, opportunity, execution, drift, PnL).
- `mycelium_whale_sonar.py` subscribes to a light set of topics (`system.*`, `execution.*`, `market.*`, `mycelium.*`, `*`), aggregates per-source event rates, amplitude and pattern strength, and computes a normalized `whale_signal_score` (0–1).
- Emits compact sonar Thoughts: `topic = 'whale.sonar.<whale_name>'` with payload `{'code': 'S0', 'pack': {...}}` where `code` is a 2-3 char morse-like summary and `pack` is a minimal data pack (score, rate, amp, critical flag, ts).
- Sonar forwards compact InterceptedSignal objects to Enigma (`aureon_enigma.decode`) for decoding into short intelligence thoughts (published under `enigma.whale.<name>`).
- Queen subscribes to `whale.sonar.*` and `enigma.whale.*` for quick gating decisions (raise confidence, flag critical whales, block paths).

Operational notes:
- Keep sonar aggregation lightweight (default 1s aggregation interval, 5s window) to avoid load.
- Use Enigma + Auris (if available) for richer decoding: `EnigmaIntegration` already wires Enigma and Auris nodes — sonar feeds can be decoded and graded by Enigma rotors.
- Sonar outputs are minimal by design to keep network and logging overhead low; full packs are persisted only to ThoughtBus memory and optional logs.

Metrics & Alerts (best-effort):
- Expose `whale_signal_strength{whale="<name>"}` and `whale_event_rate` via telemetry (OpenTelemetry / Prometheus).
- Alerting rule ideas:
  - `whale_signal_strength > 0.8` → Alert: whale singing loudly (inspect subsystem)
  - `whale_critical_total > 0` → Alert: immediate Queen attention

Example usage:
```python
from mycelium_whale_sonar import create_and_start_sonar
sonar = create_and_start_sonar()
# Sonar will publish 'whale.sonar.<name>' Thoughts and 'enigma.whale.<name>' when decoded
```

### 6. **Sacred Constants** (Never Hardcode These)
```python
import math

PHI = (1 + math.sqrt(5)) / 2           # 1.618 Golden ratio
LOVE_FREQUENCY = 528                   # Hz DNA repair frequency
SCHUMANN_BASE = 7.83                   # Hz Earth resonance
PRIMES = [2, 3, 5, 7, 11, 13, 17, ...]  # Prime sequences
```
**Usage**: Use for weighting, thresholds, phase calculations. These constants appear throughout—import from a central location when possible.

### 7. **Validation Storage** (JSON state files)
- `7day_pending_validations.json`: Branches awaiting 4th pass
- `coherence_history.json`: Per-branch coherence over time
- `adaptive_learning_history.json`: Drift patterns learned
- `aureon_memory_spiral.json`: Persistent memory patterns
- `queen_weights.json`: Neural network weights (if using `queen_neuron.py`)

**Atomic writes**: Write to temp file → atomic rename (avoid partial reads on crashes).

---

## Integration Points

### Multi-Exchange Architecture
- **Kraken**: Primary crypto (WebSocket + REST), multi-hop conversions
- **Binance**: UK restrictions, tiered fee handling
- **Alpaca**: Stocks + crypto, fractional shares, SSE feeds (`alpaca_sse_client.py`)
- **Capital.com**: CFDs (separate risk profile)

### External Dependencies
- `aureon_memory_core.py`: Persistent memory spiral for pattern recall
- `aureon_thought_bus.py`: Cross-module consciousness sharing
- `aureon_immune_system.py`: Self-healing on runtime errors
- `probability_ultimate_intelligence.py`: 95% accuracy ML predictions (if available)

### State Persistence
JSON files in root:
- `active_position.json`: Current open positions
- `aureon_kraken_state.json`: Kraken-specific runtime state
- `elephant_*.json`: Elephant memory (historical pattern learning)
- `barter_graph_cache.json`: Conversion path optimization

---

## Metrics & Observability

### 1. Repo / Engineering Metrics (GitHub-level)
These tell you if the codebase is healthy + used:

- **GitHub Insights + Traffic**: Views, clones, unique cloners
- **GitHub Actions**: Build/test status, runtime, failure rate
- **Code Coverage**: Codecov or Coveralls badge
- **Security Scanning**: CodeQL + Dependabot alerts
- **Quality Gates**: Lint + type-check in CI (Python: `ruff`, `mypy`; TS: `eslint`, `tsc`)
- **Release Metrics**: Tags/releases + changelog automation

**Outcome**: "Is the repo growing + is it stable + is it safe?"

### 2. Runtime / Trading-System Metrics (Orion Pipeline - CRITICAL)

**Observability Stack** (standard, works everywhere):
- **OpenTelemetry (OTel)** for instrumentation (metrics + traces + logs)
- **Prometheus** to scrape/store metrics
- **Grafana** dashboards + alerting
- **Optional but great**: Loki for logs + Tempo for traces

This gives you a clean **"single pane"** for the full chain.

#### What to Measure per Layer

**Ecosystem (Feed Layer)**:
```python
# In aureon_unified_ecosystem.py or global_financial_feed.py
feed_latency_ms.observe(latency)
dropped_messages_total.inc()
candle_freshness_seconds.set(age)
symbol_universe_size.set(len(branches))
scan_frequency_hz.set(scans_per_second)
spread_snapshot.observe(spread)
volatility_snapshot.observe(volatility)
```

**Scanner (Validation Layer)**:
```python
# In aureon_probability_nexus.py
pip_score_distribution.observe(pip_score)  # 0.07–1.4 band hit-rate
validation_pass_count.labels(pass_num=1).inc()  # Track p1, p2, p3 outcomes
validation_pass_count.labels(pass_num=2).inc()
validation_pass_count.labels(pass_num=3).inc()
coherence_score_per_branch.observe(C_b)
coherence_rejection_total.inc()  # When coherence < threshold
lambda_stability.observe(Lambda_b)
drift_speed.observe(D_b)
time_to_4th_decision_seconds.observe(duration)  # Validation 1 → execution
```

**Queen Hive (Execution / Orchestration)**:
```python
# In micro_profit_labyrinth.py or aureon_queen_hive_mind.py
order_latency_ms.observe(exec_time)
fill_ratio.observe(filled / requested)
slippage_pips.observe(executed_price - expected_price)
realized_pnl_usd.inc(profit_after_fees)
win_rate.set(wins / total_trades)
drawdown_usd.set(current_drawdown)
exposure_per_exchange.set(exposure, labels={"exchange": "kraken"})
signal_to_execution_decay.observe(drift_at_execution)  # Did drift invalidate before 4th?
```

#### Critical Alerts (so it doesn't "drift off" silently)
- **`drift_spike`**: Drift > 0.3 (signal decaying too fast → re-scan needed)
- **`coherence_collapse`**: Coherence < 0.5 (validators disagree → skip trade)
- **`execution_latency_high`**: Latency > 2s (too slow for drift regime → market moved)
- **`slippage_exceeds_pip_edge`**: Slippage/fees ate the expected pip edge → unprofitable execution

### 3. Model/Experiment Metrics (if training/optimizing)

If iterating models/params for coherence/lambda/drift:
- **MLflow**: Experiments, params, artifacts
- **DVC**: Dataset/version control if tracking training data
- **Evidently**: Data drift / model drift reports

### Recommended "Minimum That Works"

For fastest path that still looks professional:
1. **GitHub Actions + CodeQL + Dependabot + Coverage**
2. **OpenTelemetry → Prometheus → Grafana** (+ Loki if you want)

**Instrumentation Example**:
```python
# In any Python file (e.g., aureon_probability_nexus.py)
from opentelemetry import metrics
meter = metrics.get_meter(__name__)

# Create instruments
coherence_gauge = meter.create_gauge("aureon.scanner.coherence")
pip_histogram = meter.create_histogram("aureon.scanner.pip_score")

# Record metrics
coherence_gauge.set(C_b, {"branch": branch_id, "exchange": "kraken"})
pip_histogram.record(pip_score)
```

---

## Project-Specific Quirks

1. **"Reality branches"**: Trading pairs are conceptualized as parallel realities; code uses this metaphor extensively
2. **Sacred numbers**: System references Schumann Resonance (7.83 Hz), golden ratio (φ), harmonic frequencies—these are functional, not decorative
3. **4th-pass execution**: NEVER execute on 1st/2nd/3rd validation—Queen Hive enforces 4th confirmation gate
4. **PIP targeting**: All profit calculations in pips after fees, not raw price moves
5. **Turn-based execution**: `micro_profit_labyrinth.py` uses round-robin exchange rotation (prevents API rate limits)
6. **Barter matrix**: Conversion paths cached/scored; avoid re-trying failed source assets within cooldown

---

## File Navigation Quick Reference

| Purpose | Key Files |
|---------|-----------|
| Main entry point | `micro_profit_labyrinth.py`, `aureon_unified_ecosystem.py` |
| Validation logic | `aureon_probability_nexus.py` |
| Profit calculations | `adaptive_prime_profit_gate.py` |
| Decision controller | `aureon_queen_hive_mind.py` |
| Exchange APIs | `kraken_client.py`, `binance_client.py`, `alpaca_client.py` |
| Brain/ML | `aureon_miner_brain.py`, `probability_ultimate_intelligence.py` |
| Historical learning | `aureon_elephant_learning.py` |
| **Stargate Protocol** | `aureon_stargate_protocol.py` |
| **Quantum Mirror Scanner** | `aureon_quantum_mirror_scanner.py` |
| **Timeline Anchoring** | `aureon_timeline_anchor_validator.py` |
| State files | `*.json` in repo root |

---

## Common Development Patterns

### Implementing a New Validation System
```python
# 1. Define dataclass for validation result
@dataclass
class NewValidationResult:
    symbol: str
    probability: float  # 0-1
    confidence: float
    reasoning: str

# 2. Create validator function
async def new_validation_pass(branch: Dict) -> float:
    """Validation pass N for Batten Matrix."""
    features = extract_features(branch)
    score = compute_validation_logic(features)
    return clip(score, 0.0, 1.0)

# 3. Integrate into probability nexus
# In aureon_probability_nexus.py:
p1 = await harmonic_validation(branch)
p2 = await coherence_validation(branch)
p3 = await new_validation_pass(branch)  # <-- Add here

# 4. Update coherence calculation
coherence = 1 - (max(p1, p2, p3) - min(p1, p2, p3))
```

### Adding a New Exchange Client
```python
# 1. Create client file: {exchange}_client.py
class NewExchangeClient:
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
    
    def get_balance(self) -> Dict[str, float]:
        """Return {asset: amount}"""
        pass
    
    def get_ticker(self, symbol: str) -> Dict:
        """Return {bid, ask, last, timestamp}"""
        pass
    
    def execute_trade(self, symbol: str, side: str, quantity: float) -> Dict:
        """Execute trade, return order result"""
        pass

# 2. Add fee profile to adaptive_prime_profit_gate.py
DEFAULT_FEE_PROFILES = {
    'newexchange': {
        'maker': 0.001,  # 0.1%
        'taker': 0.0015,  # 0.15%
        'spread': 0.0005  # 0.05%
    }
}

# 3. Register in micro_profit_labyrinth.py turn rotation
exchanges = ["kraken", "binance", "alpaca", "newexchange"]
```

### Logging Best Practices
```python
import logging
logger = logging.getLogger(__name__)

# Structured logging with context
logger.info("Branch validation complete", extra={
    "branch_id": branch_id,
    "symbol": symbol,
    "coherence": coherence,
    "lambda": lambda_val,
    "pass_count": 3,
    "ready_for_4th": ready
})

# Error handling with Queen immune system
try:
    result = execute_trade(symbol, side, quantity)
except Exception as e:
    logger.error(f"Trade execution failed: {e}", exc_info=True)
    if hasattr(self, 'immune_system'):
        self.immune_system.handle_error('execution', e)
```

### Async/Await Pattern (Market Data)
```python
import asyncio
from typing import List, Dict

async def fetch_multi_exchange_data(symbols: List[str]) -> Dict:
    """Fetch data from multiple exchanges in parallel."""
    tasks = [
        fetch_kraken(symbols),
        fetch_binance(symbols),
        fetch_alpaca(symbols)
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return merge_results(results)

# Usage
async def main():
    data = await fetch_multi_exchange_data(["BTC/USD", "ETH/USD"])
    # Process data...
```

---

## Troubleshooting Guide

### High Drift / Low Lambda Stability
**Symptom**: Execution rejected with "drift_too_high"  
**Cause**: Time between scan and 4th decision exceeded stability threshold  
**Fix**: 
- Reduce validation latency (parallelize passes)
- Increase drift decay constant α in lambda calculation
- Check network/API latency to exchanges

### Low Coherence Scores
**Symptom**: Validations (p₁, p₂, p₃) widely disagree  
**Cause**: Validators seeing different market states  
**Fix**:
- Synchronize data timestamps across validators
- Check if one validator is lagging (stale data)
- Investigate if market is genuinely volatile (no fix—wait for clarity)

### 4th Decision Never Triggers
**Symptom**: Branches stuck in `7day_pending_validations.json`  
**Cause**: Score S = p̄ · P · C · Λ below threshold  
**Debug**:
```bash
# Check pending validations
jq '.[] | {symbol, coherence, lambda, score}' 7day_pending_validations.json

# Lower threshold temporarily (TEST ONLY)
# In aureon_probability_nexus.py:
BRANCH_CONFIDENCE_THRESHOLD = 0.5  # Was 0.618 (golden ratio)
```

### Exchange API Rate Limits
**Symptom**: 429 errors from exchange  
**Cause**: Too many requests in turn-based loop  
**Fix**:
- Increase sleep interval in `micro_profit_labyrinth.py`
- Check `min_qty` filters to reduce rejected orders
- Verify turn rotation is working (not hammering one exchange)

### Queen Neural Weights Diverging
**Symptom**: Queen confidence always 0.0 or 1.0 (saturated)  
**Cause**: Learning rate too high or too many bad outcomes  
**Fix**:
```python
# In queen_neuron.py, adjust learning rate:
self.learning_rate = 0.001  # Was 0.01 (too high)
```

### JSON Corruption (State Files)
**Symptom**: `JSONDecodeError` on startup  
**Cause**: Crash during write left partial file  
**Fix**:
```bash
# Restore from backup (atomic writes create .tmp files)
mv 7day_pending_validations.json.tmp 7day_pending_validations.json

# Or reset state (CAUTION: loses history)
echo '{}' > 7day_pending_validations.json
```

---

## When Making Changes

1. **Preserve the 3-validate-4th-execute pattern** (Batten Matrix core)
2. **Always update coherence/lambda metrics** when touching validation code
3. **Test with `--dry-run` flag** before live execution
4. **Check Queen Hive guidance** before modifying execution logic
5. **Update JSON state schemas carefully** (many modules read these)
6. **Run `python check_system_health.py`** after structural changes
7. **Use `@dataclass` for new data structures** (enables JSON serialization)
8. **Instrument new code paths with metrics** (OpenTelemetry)
9. **Feed outcomes to Queen neural learning** (`queen_neuron.py`)
10. **Document sacred number usage** (PHI, LOVE_FREQUENCY, etc.)

---

## Common Development Patterns

### Implementing a New Validation System
```python
# 1. Define dataclass for validation result
@dataclass
class NewValidationResult:
    symbol: str
    probability: float  # 0-1
    confidence: float
    reasoning: str

# 2. Create validator function
async def new_validation_pass(branch: Dict) -> float:
    """Validation pass N for Batten Matrix."""
    features = extract_features(branch)
    score = compute_validation_logic(features)
    return clip(score, 0.0, 1.0)

# 3. Integrate into probability nexus
# In aureon_probability_nexus.py:
p1 = await harmonic_validation(branch)
p2 = await coherence_validation(branch)
p3 = await new_validation_pass(branch)  # <-- Add here

# 4. Update coherence calculation
coherence = 1 - (max(p1, p2, p3) - min(p1, p2, p3))
```

### Adding a New Exchange Client
```python
# 1. Create client file: {exchange}_client.py
class NewExchangeClient:
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
    
    def get_balance(self) -> Dict[str, float]:
        """Return {asset: amount}"""
        pass
    
    def get_ticker(self, symbol: str) -> Dict:
        """Return {bid, ask, last, timestamp}"""
        pass
    
    def execute_trade(self, symbol: str, side: str, quantity: float) -> Dict:
        """Execute trade, return order result"""
        pass

# 2. Add fee profile to adaptive_prime_profit_gate.py
DEFAULT_FEE_PROFILES = {
    'newexchange': {
        'maker': 0.001,  # 0.1%
        'taker': 0.0015,  # 0.15%
        'spread': 0.0005  # 0.05%
    }
}

# 3. Register in micro_profit_labyrinth.py turn rotation
exchanges = ["kraken", "binance", "alpaca", "newexchange"]
```

### Logging Best Practices
```python
import logging
logger = logging.getLogger(__name__)

# Structured logging with context
logger.info("Branch validation complete", extra={
    "branch_id": branch_id,
    "symbol": symbol,
    "coherence": coherence,
    "lambda": lambda_val,
    "pass_count": 3,
    "ready_for_4th": ready
})

# Error handling with Queen immune system
try:
    result = execute_trade(symbol, side, quantity)
except Exception as e:
    logger.error(f"Trade execution failed: {e}", exc_info=True)
    if hasattr(self, 'immune_system'):
        self.immune_system.handle_error('execution', e)
```

### Async/Await Pattern (Market Data)
```python
import asyncio
from typing import List, Dict

async def fetch_multi_exchange_data(symbols: List[str]) -> Dict:
    """Fetch data from multiple exchanges in parallel."""
    tasks = [
        fetch_kraken(symbols),
        fetch_binance(symbols),
        fetch_alpaca(symbols)
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return merge_results(results)

# Usage
async def main():
    data = await fetch_multi_exchange_data(["BTC/USD", "ETH/USD"])
    # Process data...
```

---

## References
- **Harmonic Nexus Core**: Frequency-based market analysis (400–520 Hz golden zone)
- **10-9-1 Model**: Compounding strategy (10% → 9% retained → 1% reinvested)
- **Elephant Memory**: Never forgets historical patterns (`aureon_elephant_learning.py`)
- **Prime Sentinel Decree**: Gary Leckey (02.11.1991) authentication module
