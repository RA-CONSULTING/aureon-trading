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

*See subsequent sections for full layer tables.*

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
