# Aureon sensor suite — the whole picture, one φ engine

Every sensor below scans a derived tone set through the **same unchanged** phenolic
fingerprint engine (`phenolic_fingerprint.py`: Test A coherence-clustering + Test B
golden-interval/φ alignment + positive/negative controls). Each lane only supplies
data; the φ logic is never modified, and every verdict is reported exactly as the
pre-registered test returns it.

## Shared backbone (`aureon/bio/human_harmonic_proxy.py`)

- **`fold_to_band`** — octave-folds any raw Hz into the `TARGET_BAND_HZ = [1000, 2000)`
  modulation band.
- **`score_signal`** — the one governed pipeline: consent + provenance gate →
  Operator hard-boundary → Queen conscience veto (fail-safe blocks if unreachable) →
  engine positive/negative controls → Test A / Test B → separability at `ALPHA`.
- **`SCIENTIFIC_BOUNDARY`** — rides on every `ProxyResult`: statistical structure in a
  derived signal only; no claim about a person's aura/field/health/trait; no efficacy.

## The lanes

| Lane | Module | Modality | Domain boundary | Real data source | Benchmark |
|------|--------|----------|-----------------|------------------|-----------|
| Human proxy (core) | `human_harmonic_proxy.py` | `synthetic` | SCIENTIFIC_BOUNDARY | synthetic self-test (no real subject) | b9† |
| Image colour | `image_signal_adapter.py` | `image` | SCIENTIFIC_BOUNDARY | any consented image (global colour stats only) | **b18** |
| Image overlay | `image_harmonic_overlay.py` | (image) | SCIENTIFIC_BOUNDARY | consented image → geometry PNG | **b18** |
| UPE (biophoton) | `upe_signal_adapter.py` | `upe` | SCIENTIFIC_BOUNDARY | UPE spectrum / photon-count series | b10 |
| Convergence map | `convergence_map.py` | `image` | GHOST_HUNTER_BOUNDARY | image → RA-free spatial grid | b10 |
| Sky spectra | `sky_signal_adapter.py` | `sky` | SCIENTIFIC_BOUNDARY | Balmer / Fraunhofer / airglow / 21 cm | b11, b14 |
| NASA stellar/orbital | `sky_signal_adapter.py` + `scripts/validation` | `sky` | SCIENTIFIC_BOUNDARY | NASA Exoplanet Archive (`data/sky/…csv`) | b12 |
| Market | `market_signal_adapter.py` | `market` | MARKET_BOUNDARY | `probability_predictions.jsonl`, `queen_trades.jsonl` | b13 |
| QGITA φ calibration | `qgita_calibration.py` | `qgita` | SCIENTIFIC_BOUNDARY | QGITA golden lattice + Auris freqs | b15 |
| Sky map (RA/Dec) | `sky_map.py` | `sky` | SKY_MAP_BOUNDARY | NASA hosts + `de440_ephemeris.csv` | b16 |
| Cosmic sensors | `cosmic_scan.py` | `sky` | COSMIC_BOUNDARY | Schumann + planetary + `sim_kp.csv` | b17 |
| Coherence | `coherence_scan.py` | `sky` | SCIENTIFIC_BOUNDARY | `de440_gate3_coherence.csv` | **b19** |
| Sacred lattice (stargate/Maeshowe/Metatron) | `sacred_lattice_scan.py` | `sky` | SACRED_LATTICE_BOUNDARY | repo's own site coords + φ-geometry + Solfeggio/Schumann | **b22** |
| Harmonic core (Λ(t)/Ogham/Ghost Dance) | `harmonic_core_scan.py` | `sky` | HARMONIC_CORE_BOUNDARY | repo's own HNC Master-Formula modes + Celtic Ogham + ancestral Solfeggio | **b23** |
| **φ Celestial Observatory** | `celestial_observatory.py` | (orchestrator) | OBSERVATORY_BOUNDARY | every sky/cosmic lane above | **b20** |

Reference/data modules (no governance surface): `upe_reference.py`,
`sky_reference.py`, `market_reference.py`, `cosmic_reference.py`, `sacred_lattice_reference.py`, `harmonic_core_reference.py`.

The **φ Celestial Observatory** (`celestial_observatory.py`) is the capstone: it
operates every sky-facing lane at once through the one unchanged engine, renders one
consolidated picture, and **emits it to cognition** (`bio.observatory.run` on the
ThoughtBus, benchmark **b21**) so the Queen/metacognition monitor can sense the
whole-sky reading — see [CELESTIAL_OBSERVATORY.md](CELESTIAL_OBSERVATORY.md).

The **sacred lattice** (`sacred_lattice_scan.py`) is how the repo maps the sky *differently*: not with object catalogs but through Earth's own harmonic lattice — ancient-site coordinates, φ-scaled sacred geometry, and the Solfeggio/Schumann canon — scanned through the same engine and grided into an Earth-referenced map. See [SACRED_LATTICE.md](SACRED_LATTICE.md).

The **harmonic core** (`harmonic_core_scan.py`) goes one level deeper still — to the frequency substrate the framework itself is built on: the HNC **Master Formula Λ(t)** modes, the **Celtic Ogham** φ-scaled tree-tones, and the **Ghost Dance** ancestral Solfeggio ladder, each scanned through the same engine. See [HARMONIC_CORE.md](HARMONIC_CORE.md).

† b9 is the phenolic→cognition bridge; b10–b23 are the bio lanes. Tier-A total: **23**.

## Shared invariants (asserted per lane)

Every governed lane's tests assert: **valid + deterministic** scan; a **negative
control / null** that does not over-fire and a **positive** that is detected;
**consent gate blocks** (and a blank provenance blocks); the **boundary** is present
on the result; and a **no person-reading surface** guard (`dir()`-grep for
face/landmark/detect/emotion/biometric/recognize). Convenience helpers that default
`consent=True` for public data still block a blank provenance.

## Per-lane reports

`HUMAN_HARMONIC_PROXY.md` · `UPE_DATA_AVAILABILITY.md` · `SKY_FINGERPRINT.md` ·
`FAINT_SKY_UPE.md` · `NASA_SKY_DATA.md` · `MARKET_FINGERPRINT.md` ·
`QGITA_CALIBRATION.md` · `SKY_MAP.md` · `COSMIC_SENSORS.md` · `COHERENCE_LANE.md` · `SACRED_LATTICE.md` · `HARMONIC_CORE.md`.

## Run the whole suite

```bash
AUREON_LLM_OFFLINE=1 AUREON_SUPPRESS_IMPORT_SIDE_EFFECTS=1 pytest tests/bio/ -q
python tests/benchmarks/benchmark_aureon_scope.py     # Tier-A 23/23
```
