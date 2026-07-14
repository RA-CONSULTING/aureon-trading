# Cognitive Systems SaaS — the substrate as verified read APIs

The organism's cognitive and meta-cognitive systems — the HNC field, the
thought-bus links, the mycelium mesh, the connectome body-map, and the miner
brain — are now a first-class SaaS surface. Anyone with a token can read the
living substrate over HTTP, and **every response is stamped with honest data
provenance** so a consumer knows whether they are reading live truth, a cached
real value, a derived value, or nothing at all.

This is the productization layer on top of [organism unification](ORGANISM_UNIFICATION.md):
unification made the substrate *connected*; this makes it *readable, metered, and
verified*.

## The surfaces

| Route | Surface | Backing accessor | Typical truth_status |
|-------|---------|------------------|----------------------|
| `GET /api/cognition` | the whole substrate + provenance + roll-up | `build_cognitive_payload()` | — |
| `GET /api/cognition/field` | HNC field: canonical + sub-fields + blend + consensus age | `hnc_field.read_canonical_field` / `read_subfields` / `blend_field` | `live` · `cached_real` |
| `GET /api/cognition/bus` | thought-bus links: topic families, subscribers, recent flow | `thought_bus.list_subscribed_topics` / `subscriber_count` / `recall` | `live` |
| `GET /api/cognition/mycelium` | mesh: coherence, hives, agents, connected systems, growth | `mycelium.get_mesh_status` / `get_growth_stats` | `live` · `no_data` (dormant) |
| `GET /api/cognition/connectome` | body-map coverage + node roll-up | `connectome.status` / `nodes` | `live` |
| `GET /api/cognition/brain` | prediction accuracy + knowledge memory | persisted-file shim (see below) | `real_derived` · `no_data` |

All routes are mounted by `register_saas_routes` in `aureon/saas/gateway.py`,
served on the operator port behind the same bearer / rate-limit gate as the rest
of `/api/*`, plus the optional Supabase-JWT tenancy bridge. Because they live
under `/api/`, each request is **auto-metered** as an `api_request` usage event by
the billing `after_request` hook — no per-route wiring.

## Data provenance — verified, never fabricated

Every surface carries a `truth_status` drawn from the repo's real-data contract
vocabulary (`aureon/observer/real_data_contract.py`):

- **`live`** — read directly from the running bus / connectome this instant.
- **`real_derived`** — computed from real persisted inputs, with the derivation named.
- **`cached_real`** — a last-good real value (e.g. the HNC field read from the
  cross-process trace file when this process's bus hasn't seen a pulse).
- **`no_data`** — the signal isn't flowing here; the surface says so with a
  `blocker` and returns **no fabricated number**.

The umbrella payload adds a `provenance` header (`simulation_fallback_allowed`,
the contract's `truth_statuses`, and the count of registered real-data sources)
and a `truth_summary` roll-up via `summarize_truth_status` — so a consumer sees
`operational_ready` vs `blocked` at a glance. The frontend **Cognitive Systems**
page (`/cognition/systems`) renders each surface with its provenance badge.

## Two safety invariants

1. **Never cold-boot a heavy organ from a GET.** `get_miner_brain()`,
   `get_mycelium()`, and `Connectome.sense()` all have heavy / side-effectful
   init. So:
   - the **brain** surface reads the persisted state files
     (`brain_predictions_history.json`, `miner_brain_knowledge.json` at the repo
     root; overridable via `AUREON_BRAIN_PREDICTIONS_PATH` /
     `AUREON_BRAIN_KNOWLEDGE_PATH`) — it never constructs the brain;
   - the **mycelium** surface reports only when the `_mycelium_instance` singleton
     already exists — otherwise `no_data` ("dormant"), never a spawn.

   This mirrors `build_organism_payload`'s Queen-children guard.

2. **Never fabricate.** A dormant or unreachable organ is reported honestly as
   `no_data`; the layer reuses the truth-envelope vocabulary rather than inventing
   a status scheme.

## Where it lives

- `aureon/saas/cognitive.py` — the surface builders + `build_cognitive_payload()`
- `aureon/saas/gateway.py` — the six `/api/cognition*` routes
- `aureon/saas/domains.py` — `COGNITIVE_SURFACES` + `cognitive_surface_report()`
  (the catalog view: which backing accessors are import-reachable)
- `frontend/src/shell/pages/CognitivePage.tsx` — the console page
- `tests/test_cognitive_saas.py` — hermetic tests (incl. the no-cold-boot invariant)
- `scripts/validation/audit_organism_unification.py` — the `cognitive_saas` edge

## Verify

```bash
ruff check aureon/saas/ && mypy aureon/saas/
AUREON_LLM_OFFLINE=1 pytest tests/test_cognitive_saas.py -q
AUREON_LLM_OFFLINE=1 python -m scripts.validation.audit_organism_unification | grep cognitive_saas
```

## 📚 Related
- [`ORGANISM_UNIFICATION.md`](ORGANISM_UNIFICATION.md) — how the substrate became connected
- [`../SAAS_PLATFORM.md`](../SAAS_PLATFORM.md) — the platform this surface plugs into
- `aureon/observer/real_data_contract.py` — the truth-envelope vocabulary reused here
