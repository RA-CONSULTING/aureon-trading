# Cognitive Flow — Live Data Checklist

**Status as of**: 2026-04-29 (Stage AP, commit `d3cf7c17`)
**Branch**: `claude/organize-repo-fYIx7`

---

## TL;DR

After 12 stages of sweeping (Stage AE → AP), every production trade-decision
path in Aureon either reads real live data through a verified chain, or
explicitly surfaces a missing-data sentinel (`None`, `no_real_data: True`,
`[insufficient-data]` warning) so callers can skip the cycle rather than
treat fake-neutral values as real signal.

This document is the **operator's checklist**. It tells you, layer by layer,
which cognitive functions produce live fresh data today and which still
fall back to defaults that need wiring before they carry full trust.

Status icons used throughout:

| Icon | Meaning |
|---|---|
| ✅ FIXED | Produces live fresh data; verified |
| ⚠️ PARTIAL | Partially wired; some defaults remain (reason given) |
| 🔍 GATED | Refuses to fire fake data in production; opt-in via `AUREON_ALLOW_SIM_FALLBACK=1` |
| ❌ NOT FIXED | Still uses fake/hardcoded defaults; needs wiring |

---

## Cognitive Flow Diagram

```
                            ┌──────────────────────────────────────┐
                            │   LAYER 1 — RAW DATA INPUT           │
                            │   exchanges • feeds • biometric • L2 │
                            └────────────────┬─────────────────────┘
                                             │
                            ┌────────────────▼─────────────────────┐
                            │   LAYER 2 — PRE-PROCESSING / SENSORS │
                            │   observer singletons • L2 algos     │
                            └────────────────┬─────────────────────┘
                                             │
                            ┌────────────────▼─────────────────────┐
                            │   LAYER 3 — PATTERN DETECTION        │
                            │   probability • truth • patterns     │
                            └────────────────┬─────────────────────┘
                                             │
                            ┌────────────────▼─────────────────────┐
                            │   LAYER 4 — SENTIMENT / SENSORY      │
                            │   seer oracles • intuition • lyra    │
                            └────────────────┬─────────────────────┘
                                             │
                            ┌────────────────▼─────────────────────┐
                            │   LAYER 5 — FIELD / COSMIC           │
                            │   earth resonance • cosmic • solar   │
                            └────────────────┬─────────────────────┘
                                             │
                            ┌────────────────▼─────────────────────┐
                            │   LAYER 6 — QUEEN DECISION           │
                            │   neural confidence • narrator • hive│
                            └────────────────┬─────────────────────┘
                                             │
                            ┌────────────────▼─────────────────────┐
                            │   LAYER 7 — RISK / VALIDATION        │
                            │   sim-fallback gate • health • veto  │
                            └────────────────┬─────────────────────┘
                                             │
                            ┌────────────────▼─────────────────────┐
                            │   LAYER 8 — EXECUTION                │
                            │   master_launcher • labyrinth • orca │
                            └────────────────┬─────────────────────┘
                                             │
                            ┌────────────────▼─────────────────────┐
                            │   OUTPUT — DASHBOARDS / BROADCASTS   │
                            │   /health • flight status • twitch   │
                            └──────────────────────────────────────┘
```

The flow is one-way per cycle. A break at any layer either (a) skips the
cycle in production posture, or (b) propagates `None` / `no_real_data`
sentinels downstream so the next layer knows to skip its slice rather
than absorb a fake value.

---

## Layer-by-Layer Status

### Layer 1 · Raw Data Input

| Component | Status | File:line | Stage | Notes |
|---|---|---|---|---|
| Price feeds (5-source chain: unified_cache → coingecko_cache → Kraken → Binance → CoinGecko REST) | ✅ FIXED | `aureon/observer/real_price_fallback.py` | AM | Returns `({}, [])` when every source fails — caller skips cycle. Configurable via `AUREON_PRICE_FALLBACK_CHAIN`. |
| Schumann resonance — Bridge → Kp-derived → SKIP | ✅ FIXED | `aureon/harmonic/aureon_schumann_resonance_bridge.py` + `aureon/harmonic/earth_resonance_engine.py:240-298` | AK / AO | Real Barcelona/USGS reading first; on failure, derive from real NOAA Kp; only when both fail does the gate raise. |
| Solar weather (NOAA Kp / flares / wind) | ✅ FIXED | `aureon/data_feeds/aureon_space_weather_bridge.py` | AF | Real NOAA fetch; gated synthetic fallback. |
| Sentiment news (Yahoo RSS, Fear/Greed) | ✅ FIXED | `aureon/intelligence/aureon_seer.py:1738-2090` | AP | Returns `Optional[float]`; `None` on source failure with WARNING log. |
| Biometric (HRV / EEG streams) | 🔍 GATED | `aureon/queen/queen_live_signal_tracker.py:50` + `queen_street_homing.py:49` | AH | No real device wired; raises in production with remediation hint. |
| Order books (exchange L2 data) | ✅ FIXED | `aureon/intelligence/aureon_real_intelligence_engine.py:280-418` | AO | Real CV / cadence / depth-ratio algorithms; safe sentinels (0.0 / -1) on empty book. |
| Wallet balances (Kraken + unified) | ✅ FIXED | `aureon/trading/aureon_kraken_ecosystem.py:1256` + `aureon_unified_ecosystem.py:14805` | AL | Per-asset parse warnings + summary count; no silent `except: continue`. |
| OHLC historical fetch | ✅ FIXED | `aureon/intelligence/nexus_predictor.py:680-740` | AL | Per-row + per-batch error counters; raises if >10% rows or >25% batches corrupt. |

### Layer 2 · Pre-processing / Sensors

| Component | Status | File:line | Stage | Notes |
|---|---|---|---|---|
| HarmonicObserver (singleton) | ✅ FIXED | `aureon/observer/harmonic_observer.py` + `aureon/observer/__init__.py:38` | AG | Daemon constructs the singleton; `coherence_score()` reads real field. |
| WavePredictor (singleton) | ✅ FIXED | `aureon/observer/wave_predictor.py:306` | AG | Daemon-wired; `predict()` returns real confidence. |
| MomentumTracker (singleton) | ✅ FIXED | `aureon/observer/momentum.py:287` | AG | Daemon-wired. |
| RealBotProfiler L2 algorithms (consistency / latency / layering) | ✅ FIXED | `aureon/intelligence/aureon_real_intelligence_engine.py:280-418` | AO | Real CV from order qty distribution; cadence-based latency; depth-ratio layering. |
| `_simulate_firm_activity` (queen_quantum_frog) | 🔍 GATED | `aureon/queen/queen_quantum_frog.py:3036` | AH | Returns `[]` in production; orca's separate copy still synthesises (caller-bounded). |
| `aura_validator.fnum` / `clamp01` | ✅ FIXED | `aureon/utils/aura_validator.py:36-72` | AL | Raises `ValueError` on malformed input; `None` still allowed → `0.0`. |

### Layer 3 · Pattern Detection / Intelligence

| Component | Status | File:line | Stage | Notes |
|---|---|---|---|---|
| ProbabilityUltimateIntelligence | ⚠️ PARTIAL | `aureon/strategies/probability_ultimate_intelligence.py` | — | Class is real; integration into Queen neural still uses 0.5 placeholder for `probability_score` field. |
| TruthPredictionEngine — `accel` | ✅ FIXED | `aureon/intelligence/aureon_truth_prediction_engine.py:316-347` | AO / AP | Real per-symbol momentum history (16-entry deque); `dt = max(1e-3, abs(t_now - t_prev))` clock-skew guard. |
| TruthPredictionEngine — `risk` / `proximity` / `queen_flags` | ❌ NOT FIXED | `aureon/intelligence/aureon_truth_prediction_engine.py:283-295` | — | Still hardcoded `risk="none"`, `proximity="far"`, `queen_flags=[]`; logged once per (symbol, scenario). Needs risk-flag pipeline + target-distance tracker. |
| HistoricalPatternHunter | 🔍 GATED | `aureon/analytics/historical_pattern_hunter.py` | AI | Standalone backtest harness; banner clarifies; not on production graph. |
| PhaseTransitionDetector | ✅ FIXED | `aureon/intelligence/aureon_phase_transition_detector.py:206-227` | AJ | Logs `[insufficient-data]` on coherence-fallback paths. |
| NexusPredictor OHLC parser | ✅ FIXED | `aureon/intelligence/nexus_predictor.py:680-740` | AL | Refuses to train on >10% corrupt rows or >25% failed batches. |
| AdvancedIntelligence neutrals | ✅ FIXED | `aureon/intelligence/aureon_advanced_intelligence.py:247-411` | AJ | All 5 silent 0.5 returns now log `[insufficient-data]` with shortfall reason. |
| `_predict_*` heuristics (firm_intelligence_catalog) | ✅ FIXED | `aureon/bots_intelligence/aureon_firm_intelligence_catalog.py:537-598` | AL | Heuristic branches use real FirmMovement data; fallback paths log `[insufficient-data]`. |

### Layer 4 · Sentiment / Sensory

| Component | Status | File:line | Stage | Notes |
|---|---|---|---|---|
| OracleOfSentiment — 5 oracles + aggregator | ✅ FIXED | `aureon/intelligence/aureon_seer.py:1670-1734` | AP | Each oracle returns `Optional[float]`; aggregator filters `None` and reweights remaining components proportionally. `sentiment_no_sources_active=True` flag when all 5 fail. |
| IntuitionSense / AncestralSense | ⚠️ PARTIAL | `aureon/intelligence/aureon_sensory_framework.py:1085-1199` | AP | Defaults to 0.5 with one-time WARNING when consciousness_measurement unwired. Operator sees the channel is degraded; needs consciousness module wiring. |
| TemporalBiometricLink | ✅ FIXED | `aureon/intelligence/aureon_temporal_biometric_link.py:316-349` | AJ | Logs `[insufficient-data]` when no biometric reading available; correct sentinel behaviour for unwired hardware. |
| Lyra resonance | ✅ FIXED | `aureon/intelligence/aureon_seer.py:1856-1881` | AP | Returns `None` when no resonance reading; aggregator reweights without it. |

### Layer 5 · Field / Cosmic

| Component | Status | File:line | Stage | Notes |
|---|---|---|---|---|
| EarthResonanceEngine (Bridge → Kp → SKIP) | ✅ FIXED | `aureon/harmonic/earth_resonance_engine.py:158-330` | AK / AK-followup / AO | `_schumann_state_initialized` flag defeats dataclass-default masquerade; Kp-derived modes when bridge down; raises only when both fail. |
| HarmonicRealityField | ✅ FIXED | `aureon/harmonic/aureon_harmonic_reality.py:695-705` | AK | Logs `[insufficient-data]` when `ontological_history` empty. |
| CosmicStateEngine | ✅ FIXED | `aureon/strategies/hnc_imperial_predictability.py:279-305` | AH | Real flares / Kp from `space_weather_bridge`; gated synthetic fallback. |
| QueenSolarSystemAwareness | ✅ FIXED | `aureon/queen/queen_solar_system_awareness.py:307-385` | AK | NOAA Kp fetch with WARNING when fallback to 2.0 fires; docstring documents Kp→Schumann estimation. |

### Layer 6 · Queen Decision Layer

| Component | Status | File:line | Stage | Notes |
|---|---|---|---|---|
| Queen `_build_real_neural_input` (4 of 7 fields wired) | ⚠️ PARTIAL | `aureon/queen/queen_hive_command.py:487-560` | AO | `wisdom_score` ← `HarmonicObserver.coherence_score()`; `quantum_signal` ← `WavePredictor.predict().confidence`; `gaia_resonance` ← `EarthResonanceEngine.field_coherence` (only when initialised); `mycelium_signal` ← per-symbol bee consensus. **Still placeholders**: `probability_score`, `emotional_coherence`, `happiness_pursuit`. |
| Queen `_get_neural_confidence` | ✅ FIXED | `aureon/queen/queen_hive_command.py:452-505` | AL / AO | Returns `Optional[float]`; composite_score collapses to non-neural term when `None`. |
| QueenHiveMind — `gather_all_intelligence` | ✅ FIXED | `aureon/utils/aureon_queen_hive_mind.py:2395-2445` | AL / AM | Walks real-price chain; returns empty intelligence when every source fails (no synthetic prices). |
| QueenSeer (sentiment aggregator) | ✅ FIXED | `aureon/intelligence/aureon_seer.py:1670-1734` | AP | See Layer 4. |
| QueenCognitiveNarrator | ✅ FIXED | `aureon/queen/queen_cognitive_narrator.py:78-109` | AH | Real `coherence` / `lambda_stability` reads from observer + wave_predictor; omits the line when no real values rather than fold random.uniform. |
| Bee swarm import warnings | ✅ FIXED | `aureon/queen/queen_hive_command.py:75-102` | AL | Per-bee load failures logged at WARNING (was DEBUG). |

### Layer 7 · Risk / Validation

| Component | Status | File:line | Stage | Notes |
|---|---|---|---|---|
| `simulation_fallback_allowed()` env-gate | ✅ FIXED | `aureon/observer/live_data_policy.py:42` | AE | Single primitive used by every gate. |
| `compute_real_health()` (HNC daemon + price_cache + Kraken ticker freshness) | ✅ FIXED | `aureon/queen/queen_quantum_frog.py:48-95` | AL | 503 + `failed_checks` JSON when any source stale/down — orchestrators actually restart. |
| Phase-4 Veto | ✅ FIXED | (observer Stage AB) | AB | Wired into the live decision loop. |
| Earth gate `_schumann_state_initialized` | ✅ FIXED | `aureon/harmonic/earth_resonance_engine.py:158-405` | AK followup | Defaults to closed until first successful Schumann read. |

### Layer 8 · Execution

| Component | Status | File:line | Stage | Notes |
|---|---|---|---|---|
| `master_launcher.run_autonomous_trading` cycle | ✅ FIXED | `aureon/autonomous/aureon_master_launcher.py:498-560` | AL / AM | Walks real-price chain; skips cycle and logs `[live-data] real prices unavailable` when every source fails. |
| `aureon_unified_ecosystem` (wallet parse + fallback tickers) | ✅ FIXED | `aureon/trading/aureon_unified_ecosystem.py:14795-18510` | AL | Per-asset warnings + summary; `_get_hardcoded_fallback_tickers` raises in production unless cached snapshot exists. |
| `micro_profit_labyrinth` | ⚠️ PARTIAL | `aureon/trading/micro_profit_labyrinth.py` | AN | Now uses real `GlassnodeClient` for whale flows; **deferred**: position-record rollback when `execute_validated_opportunity` returns no order_id. |
| `orca_complete_kill_cycle._get_live_crypto_prices` | ✅ FIXED | `aureon/bots/orca_complete_kill_cycle.py:8131-8180` | AN | Real-price chain instead of 14-pair hardcoded dict. |
| `aureon_historical_live` | 🔍 GATED | `aureon/trading/aureon_historical_live.py:618-700` | AJ | Stub module — `get_kraken_markets` and `execute_signal` raise in production. Real exchange wiring is a separate project. |
| `gaia_planetary_reclaimer.get_total_portfolio` | ✅ FIXED | `aureon/bots/gaia_planetary_reclaimer.py:1968-2010` | AN | Real Binance ticker + chain fallback per asset; skips asset rather than fabricate. |
| `glassnode_client._get_btc_price_at_timestamp` | ✅ FIXED | `aureon/exchanges/glassnode_client.py:323-355` | AN | `get_real_price('BTC/USD')`; returns 0.0 sentinel on chain failure. |

### Outputs / Broadcasts

| Component | Status | File:line | Stage | Notes |
|---|---|---|---|---|
| `/health` endpoint (queen_quantum_frog) | ✅ FIXED | `aureon/queen/queen_quantum_frog.py:48-150` | AL | Returns 503 when underlying APIs stale/unreachable; container orchestrators actually restart on real outages. |
| Flight-status banner (command_center) | ✅ FIXED | `aureon/command_centers/aureon_command_center.py:798-836` | AL | Imports `compute_real_health`; "ALL SYSTEMS GO" requires both per-system checks AND real connectivity. |
| `_update_warroom` / `_update_surveillance` / `_generate_test_data` (master_hub) | 🔍 GATED | `aureon/trading/aureon_unified_master_hub.py:3090-3596` | AI | Synthetic dashboard demos return early in production. |
| `_generate_mock_signals` / `_queen_commentary` (command_center_enhanced) | 🔍 GATED | `aureon/command_centers/aureon_command_center_enhanced.py:825-883` | AI | Demo signals + canned Queen messages return early in production. |
| `generate_test_thoughts` (mind_thought_action_hub) | 🔍 GATED | `aureon/autonomous/aureon_mind_thought_action_hub.py:767-790` | AI | Returns early in production. |
| `aureon_realtime_surveillance.start` | 🔍 GATED | `aureon/monitors/aureon_realtime_surveillance.py:594-614` | AI | Synthetic feed raises in production with remediation hint. |

---


## Production Guarantees

*See subsequent sections.*

---

## Still to Wire

*See subsequent sections.*

---

## Smoke Verification

*See subsequent sections.*

---

## Stage Map

*See subsequent sections.*
