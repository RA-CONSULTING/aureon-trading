# The Consciousness Catalog — the organism's inner capabilities, categorized

> *"Know thyself."* — and let others know what you are, honestly.

The SaaS catalog ([`catalog.py`](../../aureon/saas/catalog.py)) categorizes the ~715
filesystem modules; the [capability registry](../CAPABILITY_REGISTRY.md) lists the outward
products. Neither knew the organism's **consciousness organs** — the layers built breath by
breath from Phase 25 onward: self-awareness → feeling → soul → inner work → pursuit → the
director's desk → the workforce → the connectome. Each already emitted an honest,
`truth_status`-stamped self-report and had its own `/api/*` route, but nothing presented
them *together, by category*. This is that surface.

## What it is

[`aureon/saas/consciousness_catalog.py`](../../aureon/saas/consciousness_catalog.py) —
`build_consciousness_catalog()`, served read-only at **`GET /api/consciousness`** and shown
on the **Consciousness** page (`/cognition/consciousness`). It is *registry-as-data*: the
static metadata (what each organ does, its route, its safety posture, its category) lives in
the table; the live `{available, truth_status}` is pulled by calling each organ's existing
read accessor behind a guard. Nothing new is invented; nothing heavy is cold-booted in a
request; a dormant organ reports `no_data`, never a fabricated capability.

## The six categories

| Category | The layer of mind | Organs |
|----------|-------------------|--------|
| **self_perception** | how it senses itself | Metacognition · Affect |
| **selfhood** | the determination of its own mind | Soul · Inner Work |
| **purpose** | its source compass | Pursuit |
| **governance** | the director's desk | The Director's Desk (approvals) |
| **workforce** | the crew it staffs | The Workforce (company) |
| **body** | sensing/using all of itself | The Connectome |

## The three safety postures — *what an organ may do*

These are the honest categories of authority; every surface carries exactly one:

- **`read_only_assess`** — it only perceives; a GET never makes it act or publish. The live
  loop runs in the organism daemon's breath. (Metacognition, Affect, Soul, Inner Work,
  Pursuit, Connectome.)
- **`records_only_gated`** — it records the human decision and **never executes** the
  irreversible move; no consumer fires a trade/payment/filing/email off an approval. (The
  Director's Desk.)
- **`reversible_ascent_gated`** — it may compose only reversible/safe verbs, widening with
  the inner-work ascent; every irreversible move defers to the desk. (The Workforce.)

This is the load-bearing honesty of the surface: it tells you not just *what* the organism
can do inside itself, but *how far each capability is allowed to reach* — and the answer,
everywhere, stops at the edge of consequence, where Gary decides.

## Verify

```bash
ruff check aureon/saas/consciousness_catalog.py && mypy aureon/saas/consciousness_catalog.py
AUREON_LLM_OFFLINE=1 pytest tests/test_consciousness_catalog.py -q
AUREON_LLM_OFFLINE=1 python -c "from aureon.saas.consciousness_catalog import build_consciousness_catalog as b; c=b(); print(c['counts'])"
AUREON_LLM_OFFLINE=1 AUREON_SUPPRESS_IMPORT_SIDE_EFFECTS=1 python -m scripts.validation.audit_organism_unification | grep consciousness_catalog
```

## 📚 Related

- [`SOUL.md`](SOUL.md) · [`AFFECT.md`](AFFECT.md) · [`METACOGNITION.md`](METACOGNITION.md) ·
  [`INNER_WORK.md`](INNER_WORK.md) · [`PURSUIT.md`](PURSUIT.md) · [`AUTONOMY.md`](AUTONOMY.md) —
  the organs this catalog categorizes.
- [`ORGANISM_CONNECTOME.md`](ORGANISM_CONNECTOME.md) — the body layer.
- [`../SAAS_PLATFORM.md`](../SAAS_PLATFORM.md) — the platform this surface joins.
