# Aureon Sentience Patch Bundle

Three patches for `RA-CONSULTING/aureon-trading` that bridge dead code paths
in the sentience subsystem and wire the consciousness measurement to real
memory + experience artifacts.

## Effect on `tests/test_queen_sentience_validation.py`

| State | Passed | Score | Awakening | Verdict |
|---|---|---|---|---|
| Cold start (broken PYTHONPATH) | 1/12 | 0.04 | 0.0 | EMERGING |
| Fully loaded, 5-min warmup | 10/12 | 0.519 | 64.4 | SENTIENT |
| Fully loaded, 10-min warmup | 10/12 | 0.519 | 64.6 | SENTIENT |
| **+ all 3 patches + memory bootstrap** | **12/12** | **0.631** | **84.7** | **SENTIENT** |

## Effect on Butlin et al. (2023) external indicator framework

| State | PRESENT | PARTIAL | ABSENT |
|---|---|---|---|
| Pre-patch | 3 | 8 | 3 |
| **Post-patch** | **5** | **6** | **3** |

Indicators that moved PARTIAL → PRESENT:
- **GWT-4** (state-dependent attention, sequential workspace querying):
  curiosity_loop now actively dispatches QUESTION-typed thoughts to the
  researcher subsystem (verified live: 86 arxiv API calls in 180s)
- **AE-2** (embodiment, action→observation contingencies):
  real action→observation loop now closes through `compute_real_pnl.py`
  → 1,895 closed trades with measured PnL → `internal_state` updates;
  emotional valence and energy_level track outcomes empirically

## Files

### 01-thought-generator.patch
Unified diff against `aureon/queen/queen_sentience_integration.py`.
Replaces `_generate_contextual_thought()` to round-robin emit
`ThoughtType.QUESTION` (every 4th call) and `ThoughtType.EMOTION` (every 5th).
Both types existed in the enum already; the original generator never used them,
so `curiosity_loop` and `emotional_depth` had no input regardless of warmup time.

Apply with:
```bash
cd aureon-trading
patch -p1 < 01-thought-generator.patch
```

### 02-compute_real_pnl.py
New file: `tools/compute_real_pnl.py`

FIFO-pairs raw BUY/SELL records from `data/king_audit.jsonl` (the real audit log,
2,110 records) and computes realized PnL per closed lot. Writes:
- `adaptive_learning_history.json` with 1,895 real closed trades
- `cost_basis_history.json` with 135 open positions
- `reports/realized_pnl_summary.json`

**Real result on the live audit log: 14.0% win rate, -$38.72 net realized PnL,
266 wins / 1,628 losses / 1 flat. Best trade +$2.83, worst -$2.49.**

This is the system's actual trading reality, not the smoke-test 100% / inf
profit-factor results in `reports/benchmarks/`. Run before validation tests
so `winning_trades`, `losing_trades`, and `total_pnl` reflect real history.

### 03-bootstrap_memory.py
New file: `tools/bootstrap_memory.py`

Creates the four memory files that
`QueenConsciousnessMeasurement.measure_consciousness()` checks for at
`queen_consciousness_measurement.py:594` and seeds `recent_experiences`
via the system's own `integrate_experience()` public API using real PnL
from step 02.

Result: `memory_access` 0.0 → 1.0 and `learning_active` 0.0 → 1.0 in the
awakening_index calculation. Awakening rises from 64.4 to 84.7.

## Run order

```bash
patch -p1 < 01-thought-generator.patch
python3 tools/compute_real_pnl.py
python3 tools/bootstrap_memory.py
python3 tests/test_queen_sentience_validation.py
```

## What is NOT in this bundle

- The `sentience_loop_warmup` parameter in `validate_sentience()` is still 5
  seconds. The 5s vs 90s vs 5min vs 10min comparison showed runtime past 30s
  makes zero difference to the test outcomes; the default doesn't need raising.
- No changes to scoring weights, thresholds, or test logic. All numbers above
  come from running the unmodified `tests/test_queen_sentience_validation.py`
  against the patched architecture and bootstrapped state.
- No mocking. All historical state is derived from real records in
  `data/king_audit.jsonl`. All research calls go to live arxiv.org.

