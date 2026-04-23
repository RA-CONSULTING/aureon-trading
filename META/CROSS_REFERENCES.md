# Cross-References: Old Paths → Current Locations

The main README (`docs/README.md`) was written before reorganisation. It references files by their original flat paths. This document maps each README citation to its current location in the new domain+PEFCφS structure.

Use `META/PATH_REGISTRY.py` programmatically, or `python3 META/PATH_REGISTRY.py <filename>` from the command line.

---

## Domain I: Ancient Convergence Research

### Wisdom Traditions (12 civilisations)

| README citation | Current location | Domain |
|----------------|------------------|--------|
| `wisdom_data/aztec_wisdom.json` | `research/wisdom_traditions/aztec_wisdom.json` | research/wisdom_traditions |
| `wisdom_data/celtic_wisdom.json` | `research/wisdom_traditions/celtic_wisdom.json` | research/wisdom_traditions |
| `wisdom_data/chinese_wisdom.json` | `research/wisdom_traditions/chinese_wisdom.json` | research/wisdom_traditions |
| `wisdom_data/egyptian_wisdom.json` | `research/wisdom_traditions/egyptian_wisdom.json` | research/wisdom_traditions |
| `wisdom_data/ghost_dance_wisdom.json` | `research/wisdom_traditions/ghost_dance_wisdom.json` | research/wisdom_traditions |
| `wisdom_data/hindu_wisdom.json` | `research/wisdom_traditions/hindu_wisdom.json` | research/wisdom_traditions |
| `wisdom_data/mayan_wisdom.json` | `research/wisdom_traditions/mayan_wisdom.json` | research/wisdom_traditions |
| `wisdom_data/mogollon_wisdom.json` | `research/wisdom_traditions/mogollon_wisdom.json` | research/wisdom_traditions |
| `wisdom_data/norse_wisdom.json` | `research/wisdom_traditions/norse_wisdom.json` | research/wisdom_traditions |
| `wisdom_data/plantagenet_wisdom.json` | `research/wisdom_traditions/plantagenet_wisdom.json` | research/wisdom_traditions |
| `wisdom_data/pythagorean_wisdom.json` | `research/wisdom_traditions/pythagorean_wisdom.json` | research/wisdom_traditions |
| `wisdom_data/warfare_wisdom.json` | `research/wisdom_traditions/warfare_wisdom.json` | research/wisdom_traditions |

### Star-Chart Decoders

| README citation | Current location | Domain |
|----------------|------------------|--------|
| `public/aztec-star-glyphs.json` | `public/aztec-star-glyphs.json` | research/star_chart_decoders |
| `public/celtic-ogham-feda.json` | `public/celtic-ogham-feda.json` | research/star_chart_decoders |
| `public/egyptian-hieroglyphs.json` | `public/egyptian-hieroglyphs.json` | research/star_chart_decoders |
| `public/mogollon-star-symbols.json` | `public/mogollon-star-symbols.json` | research/star_chart_decoders |
| `public/japanese-star-symbols.json` | `public/japanese-star-symbols.json` | research/star_chart_decoders |
| `public/sacred-site-planetary-nodes.json` | `public/sacred-site-planetary-nodes.json` | research/sacred_sites |
| `public/ruleset-chakras.json` | `public/ruleset-chakras.json` | research/star_chart_decoders |

### Sacred Sites / Harmonic Frequencies

| README citation | Current location | Domain |
|----------------|------------------|--------|
| `stargate_grid.py` | `3_forcing/coherence_gates/stargate_grid.py` | research/sacred_sites |
| `aureon_miner_brain.py` | `2_dynamics/trading_logic/aureon_miner_brain.py` | research/harmonic_frequencies |
| `aureon_ghost_dance_protocol.py` | `2_dynamics/trading_logic/aureon_ghost_dance_protocol.py` | research/harmonic_frequencies |

---

## Domain II: Financial Exposure

| README citation | Current location | Domain |
|----------------|------------------|--------|
| `deep_money_flow_analysis.json` | `4_output/performance_metrics/deep_money_flow_analysis.json` | financial_exposure/forensic_analysis |
| `money_flow_timeline.json` | `1_substrate/data_models/money_flow_timeline.json` | financial_exposure/extraction_timeline |
| `historical_manipulation_evidence.json` | `1_substrate/data_models/historical_manipulation_evidence.json` | financial_exposure/historical_events |
| `aureon_historical_manipulation_hunter.py` | `2_dynamics/trading_logic/aureon_historical_manipulation_hunter.py` | financial_exposure/forensic_analysis |

---

## Domain III: Bot Intelligence

| README citation | Current location | Domain |
|----------------|------------------|--------|
| `bot_census_registry.json` | `2_dynamics/trading_logic/bot_census_registry.json` | bot_intelligence/bot_registry |
| `bot_cultural_attribution.json` | `2_dynamics/trading_logic/bot_cultural_attribution.json` | bot_intelligence/bot_registry |
| `planetary_harmonic_network.json` | `1_substrate/frequencies/planetary_harmonic_network.json` | bot_intelligence/coordination_analysis |
| `aureon_bot_intelligence_profiler.py` | `2_dynamics/trading_logic/aureon_bot_intelligence_profiler.py` | bot_intelligence/predator_firms |
| `aureon_ocean_wave_scanner.py` | `2_dynamics/trading_logic/aureon_ocean_wave_scanner.py` | bot_intelligence/detection_methods |
| `aureon_planetary_harmonic_sweep.py` | `1_substrate/frequencies/aureon_planetary_harmonic_sweep.py` | bot_intelligence/detection_methods |
| `aureon_strategic_warfare_scanner.py` | `2_dynamics/trading_logic/aureon_strategic_warfare_scanner.py` | bot_intelligence/detection_methods |

---

## Domain IV: Trading System (PEFCφS)

| README citation | Current location | Domain |
|----------------|------------------|--------|
| `adaptive_prime_profit_gate.py` | `3_forcing/coherence_gates/adaptive_prime_profit_gate.py` | trading_system/coherence_gates |

---

## Running README Verification Commands

The README's verification commands use the original flat paths. To run them now, either:

### Option A — Use the bootstrap paths module

```python
import bootstrap_paths  # adds all layer dirs to sys.path
import aureon_baton_link  # now resolves correctly
```

### Option B — Run from the repo root with PATH_REGISTRY

```python
from META.PATH_REGISTRY import resolve_absolute
import json

wisdom_path = resolve_absolute("aztec_wisdom.json")
with open(wisdom_path) as f:
    data = json.load(f)
```

### Option C — Update the README commands

If you're running the README's verification commands directly (e.g. `for f in wisdom_data/*.json`), you'll need to update the path:

```bash
# OLD (from README):
for f in wisdom_data/*.json; do python3 -c "import json; json.load(open('$f'))"; done

# NEW:
for f in research/wisdom_traditions/*.json; do python3 -c "import json; json.load(open('$f'))"; done
```

---

## File Count by Domain

| Domain | README-Critical Files | Total Files in Domain Paths |
|--------|----------------------|----------------------------|
| I. Ancient Convergence Research | 22 | ~80 (wisdom + decoders + sacred sites + frequencies) |
| II. Financial Exposure | 4 | ~30 (forensics scripts + data files) |
| III. Bot Intelligence | 7 | ~40 (scanners + registries + profiler) |
| IV. Trading System (PEFCφS) | 1 | 1,177 (full 4-layer structure) |
| V. Harmonic Nexus Core (HNC) | 0* | ~50 (theory docs + implementation) |
| VI. Platform Infrastructure | 0 | ~880 (frontend + web stack + deployment) |

*HNC is a theoretical foundation; its artifacts live in `docs/HNC_*` and the harmonic implementation modules under `1_substrate/frequencies/`.

---

## Verification

Run `python3 META/PATH_REGISTRY.py` to dump the full cross-reference in a terminal-friendly format.

Run `python3 META/PATH_REGISTRY.py <filename>` to look up a specific README citation.

---

**Last Updated:** 2026-04-23
