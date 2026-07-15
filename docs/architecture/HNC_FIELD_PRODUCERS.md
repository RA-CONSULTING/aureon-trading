# The field's producers, seen — who feeds the whole-body field

> *"The organism is only as connected as the voices it can actually hear."* — the HNC
> field blends whatever sub-fields are **present**; this map shows exactly **who is
> feeding it right now** versus who is intended-but-dark, and names the dark ones truthfully.

## The whole-body field, in one breath

Every breath, producers publish a `symbolic.life.subfield` (via
`publish_subfield(source, state, bus)`), and `blend_field()` (`aureon/core/hnc_field.py`)
fuses **whatever is present** into the organism's whole-body consensus. That is honest by
design — a dormant producer simply isn't in the blend. But nothing said *which* of the
intended producers are live and which are silent. `field_producers()`
(`aureon/saas/cognitive.py`) closes that gap: a **documented intended set**, each entry
marked `live` iff its exact `source` string is currently a key in `read_subfields()`.
Real signal, nothing fabricated. Surfaced additively on `field_surface()` →
`GET /api/cognition/field` and `GET /api/cognition` as `producers: {producers[], live_count, intended_count}`.

## The map

### Live-in-daemon — booted by `organism_daemon` and publishing each breath

| Source | Fed by | Note |
|---|---|---|
| `metacognition_monitor` | `breathe()` `reflect()` | the organism reads its own signals and loops self-coherence back each breath |
| `affect_monitor` | `breathe()` `reflect()` | victory/defeat/fear/resolve, felt from real signals and folded in each breath |
| `inner_work` | `breathe()` `reflect()` | the seven-chakra ascent state, folded in each breath |
| `pursuit` | `breathe()` `reflect()` | the pursuit-of-happiness compass, folded in each breath |
| `consciousness_module` | `heartbeat()` step | the metacognitive Λ field, published when the engine is live |
| `dr_auris_throne` | throne loop | the cosmic/harmonic throne, autostarted in `boot()` |
| `mycelium_mesh` | `publish_mesh_subfield()` | the mesh's network coherence — **live once the connectome sweep first weaves** the mesh singleton in-process (Phase 45) |

### ICS-hosted — dark unless `integrated_cognitive_system` boots

These six publish **only inside** `integrated_cognitive_system` (ICS). The minimal
`organism_daemon` does not boot ICS, so they read **dark** — and the map says so plainly.

| Source | Note |
|---|---|
| `queen_cortex` | Queen Λ engine; host not booted in the minimal daemon |
| `queen_source_law` | Queen Λ engine; host not booted, and **event-driven** (publishes per decision) |
| `queen_metacognition` | Queen Λ engine; host not booted in the minimal daemon |
| `queen_sentient_loop` | Queen Λ engine; host not booted in the minimal daemon |
| `queen_mycelium_mind` | the thought-propagation **spore** engine; host not booted in the minimal daemon |
| `hnc_human_loop` | human-in-the-loop Λ producer; host not booted, and **event-driven** (publishes per message) |

## The honest boot gap (not papered over)

Booting ICS is a **deployment decision**, not something this map fabricates. The dark
producers are named truthfully (host not booted / event-driven) rather than bridged with a
decorative shim — the map **never overclaims a dark producer as connected**. When ICS (or a
larger queen-unified configuration) boots, those sources start publishing and the same map
turns them `live` automatically, because `live` is derived purely from the real
`read_subfields()` signal.

## Guardrails

Read-only + additive + honest. `field_producers()` derives `live` purely from
`read_subfields()` — never fabricated; the intended set is a documented constant; a dormant
producer is labelled dark, never a guessed value. No route, no daemon, no behaviour change.

## 📚 Related

- [`ORGANISM_UNIFICATION.md`](ORGANISM_UNIFICATION.md) — the shared field and its edges.
- [`MYCELIUM.md`](MYCELIUM.md) — the mesh producer (`mycelium_mesh`) and its live-once-woven bridge.
- [`COGNITIVE_SAAS.md`](COGNITIVE_SAAS.md) — the read surfaces and provenance model.
