# 🎛️ AUREON OPERATOR SWITCHBOARD
## "Many voices in. One grounded answer out."

> *"That which is below is like that which is above."* — the Emerald Tablet
>
> The operator is that principle wired into silicon: the many models above
> (ChatGPT, Grok, Gemini) are made to speak *through* the one repository below,
> so what falls out the far side carries the coherence of the source, not the
> drift of the crowd.

---

## 🌌 What it is

The **Aureon Operator** is a *switchboard*. A question comes in on one line;
the operator patches it out across every AI model it can reach, but it never
lets a model answer from its own vendor memory alone. First it **grounds** the
prompt in the Aureon repository. Then it collects the replies, **collapses**
them to a single answer by agreement, runs that answer past the Queen's
**conscience** (the 4th-pass veto), and only then speaks.

This is the "response synthesis engine" from the *Aureon Setup — Complete
Overview* diagram, made concrete. The guarantee on that diagram — **no logic
drift · no hallucination · fully grounded via the Aureon repository** — is not
a slogan here. It is a chain of falsifiable steps you can read in the code and
watch on the bus:

```
[ prompt ] → ground → fan_out → consensus → veto → [ grounded answer ]
                 │        │          │         │
             repo     N AI       agreement   Queen's
            sources   lines       collapse   conscience
```

The design principle from the WhatsApp field notes holds: **no big heavy load
on the PC**. The operator is thin glue — the models are the black-box data
centre, the repo is the ground truth, and the operator is the exchange between
them. It runs offline-first: with zero API keys it answers from grounded repo
context on a stub line; add keys and the same code fans out across live models.

---

## 🔄 The flow, box by box

```
        ┌─────────────────────┐
        │  USER PROMPT         │   "How does Aureon integrate data across systems?"
        └──────────┬──────────┘
                   │
                   ▼
        ┌─────────────────────────────────────────────┐
        │  AI MODEL LAYER (the switchboard lines)       │
        │  [ChatGPT] [Grok] [Gemini] … + local/stub     │   aureon/operator/providers.py
        │  every line speaks the LLMAdapter interface   │
        └──────────┬──────────────────────────────────┘
                   │  each line answers the SAME grounded prompt
                   ▼
        ┌─────────────────────────────────────────────┐
        │  AUREON OPERATOR (IONOS / small cloud)        │   aureon/operator/aureon_operator.py
        │   1. ground   ─ repo sources + response       │
        │                 contract  (dynamic prompt     │
        │                 filter + research corpus)     │
        │   2. fan_out  ─ patch prompt to every line    │
        │   3. consensus─ collapse N answers → 1        │
        │   4. veto     ─ Queen's conscience 4th-pass   │
        └──────────┬──────────────────────────────────┘
                   │  every step publishes a Thought (shared trace_id)
                   ▼
        ┌─────────────────────────────────────────────┐
        │  RESPONSE FLOW (guaranteed consistency)       │
        │  grounded → agreed → vetted → spoken          │
        │  streamed over SSE to browser / phone /       │   aureon/operator/operator_server.py
        │  (future) voice + Ray-Ban glasses             │   aureon/operator/voice_bridge.py
        └─────────────────────────────────────────────┘
```

---

## 🧩 Component → code

Every box maps to a real module. Almost the entire spine already existed in the
repo — the operator is composition, not new machinery.

| Box | Reused component | Path | Status |
|---|---|---|---|
| Switchboard line (any model) | `LLMAdapter` ABC · `AureonLocalAdapter` · `AureonStubAdapter` | `aureon/inhouse_ai/llm_adapter.py` | 🟢 reused |
| ChatGPT / Grok / Gemini lines | `AureonOpenAIAdapter` · `AureonGrokAdapter` · `AureonGeminiAdapter` | `aureon/operator/providers.py` | 🟢 new (thin) |
| Line-up assembly | `build_provider_set()` (key-gated, offline-first) | `aureon/operator/providers.py` | 🟢 new |
| Phase orchestration | patterned on `CognitionPipeline` (trace_id + per-phase publish) | `aureon/cognition/pipeline.py` | 🟢 pattern reused |
| **ground** | `build_dynamic_prompt_filter` · `select_source_packets` | `aureon/autonomous/aureon_dynamic_prompt_filter.py` | 🟢 reused |
| corpus retrieval | `ResearchCorpusIndex` · `KnowledgeDataset` | `aureon/queen/research_corpus_index.py` | 🟢 available |
| **consensus** | medoid collapse + Jaccard agreement (Samuel Γ-vote idiom) | `aureon/operator/aureon_operator.py` | 🟢 new |
| **veto** | `QueenConscience.ask_why` (4th-pass) | `aureon/queen/queen_conscience.py` | 🟢 reused |
| transport / trace | `ThoughtBus` · `Thought` · `get_thought_bus` | `aureon/core/aureon_thought_bus.py` | 🟢 reused |
| config / secrets | `SECRET_KEYS` · `AI_PROVIDER_REQUIRED_ENV` | `aureon/core/aureon_env.py` | 🟢 extended |
| stream + phone page | Flask SSE + self-contained HTML | `aureon/operator/operator_server.py` | 🟢 new |
| voice / glasses | `VoiceGlassesBridge` → `aureon_unified_voice_agent` | `aureon/operator/voice_bridge.py` | 🟡 stub |

---

## 🛡️ The grounding guarantee (why "no hallucination" is falsifiable)

Four gates stand between a model's raw output and what the operator will say.
Each is inspectable; each can be made to fail on purpose.

| Gate | What it enforces | How you falsify it |
|---|---|---|
| **Grounding** | The system prompt is compiled from repo source packets + a response contract, not from vendor memory. | Ask a repo-specific question; the answer must cite the packets in `grounding.sources`. Empty sources on a substantive prompt = gate failed. |
| **Fan-out** | Multiple independent lines answer the *same* grounded prompt. | Count `answers[]`. One line answering ≠ consensus. |
| **Consensus** | Agreement across lines is measured (mean pairwise token overlap); the medoid — the answer most like the others — wins, outliers are recorded as runner-ups. | Feed one outlier among agreeing lines; the outlier must not win, and `agreement` must drop. |
| **Veto** | The Queen's conscience passes over the answer and can `VETO` it before it is spoken. | Any `VETO` verdict must set `blocked = true` and replace the spoken text. |

The whole cascade is stamped with one `trace_id` and published phase-by-phase on
the `ThoughtBus` (`operator.phase.*` → `operator.complete`), so nothing is taken
on faith — the record is the proof.

<!-- editorial -->
> The consensus step is deliberately simple in this first cut: token-overlap
> agreement and a medoid pick, inspired by the Samuel Γ-vote (`Γ > 0.945`) idiom
> in `aureon/wisdom/aureon_samuel_agent.py`. It is a coherence *proxy*, not the
> full harmonic collapse — and it is honest about that. A richer Λ-coupled
> collapse can drop in behind the same interface without changing the flow.
<!-- /editorial -->

---

## 📡 Streaming & the glasses path

> *"Operator will be like streaming YouTube. You talk and it's a live stream.
> Two-way conversation. Think brain chip — but without circuits in the brain.
> All run from Ray-Ban glasses."*

The prototype ships the first rung of that ladder and marks the rest:

```
 voice in ─▶ [STT]* ─▶ AureonOperator ─▶ SSE stream ─▶ phone / browser
                            │                              (live tokens +
                            └─▶ ThoughtBus (trace)          phase chips)
 speech out ◀─ [TTS]* ◀─────┘
     * capture/playback edges are # TODO(glasses) seams in voice_bridge.py
```

- **Now:** `operator_server.py` serves a self-contained, mobile-responsive chat
  page at `/` and streams the answer token-by-token over Server-Sent Events at
  `/api/operator/stream`. Open the URL on a phone and you have the live two-way
  conversation — the proof of concept.
- **Next:** `voice_bridge.py`'s `VoiceGlassesBridge` routes a transcribed
  utterance through the operator and back to the existing unified voice agent
  (`aureon/autonomous/aureon_unified_voice_agent.py`) for TTS. The Ray-Ban mic
  capture and earpiece playback are clean `# TODO(glasses)` seams.

---

## 🚀 Deployment

The overview diagram names **IONOS**. IONOS is *net-new* to this repo — nothing
here targets it yet — so treat it as an alternative to the existing
**DigitalOcean** stack and mirror those conventions:

| Concern | DigitalOcean (current) | IONOS (proposed, mirror it) |
|---|---|---|
| Region | London (`lon`) | choose the closest low-latency region |
| Process model | `supervisord`, priority-ordered | same — add the operator as a service |
| Ports | 8080 (Power Station) · 8800 (Command Center) | operator on **8080** by default (`AUREON_OPERATOR_PORT`) |
| State | root-level JSONs (see `docs/STATE_FILES.md`) | unchanged — CWD-relative, do not move |

```bash
# run the switchboard + phone proof-of-concept
python -m aureon.operator.operator_server            # binds 0.0.0.0:8080
AUREON_OPERATOR_PORT=8899 python -m aureon.operator.operator_server

# one prompt, full cascade, no keys needed
python scripts/run_operator_demo.py "How does Aureon integrate data across systems?"
```

> **Reaching it from a phone.** This repo usually runs in a remote container, so
> `localhost` won't resolve on the phone. Open the *deployed* IONOS/DigitalOcean
> URL, or a tunnel to the container, over HTTPS.

Provider keys are optional and read from the environment (see `.env.example`):
`OPENAI_API_KEY`, `XAI_API_KEY`, `GEMINI_API_KEY`. With none set, the operator
runs fully offline. The repo's audit/offline guards (`AUREON_LLM_OFFLINE`,
`AUREON_AUDIT_MODE`, `AUREON_DISABLE_LLM_HTTP`) are honoured — set any of them and
no outbound HTTP is attempted.

---

## 🧪 Verify

```bash
pytest tests/test_aureon_operator.py -v          # 9 offline tests, no keys/network
python scripts/run_operator_demo.py "…"          # end-to-end cascade + trace
AUREON_LLM_OFFLINE=1 python scripts/run_operator_demo.py "…"   # offline guard
```

---

## 📚 Related Documentation

- [`docs/cognition`](../../aureon/cognition/pipeline.py) — `CognitionPipeline`, the seven-pane prism this operator's phase shape is patterned on
- [`docs/architecture/SYSTEM_ARCHITECTURE_MAP.md`](SYSTEM_ARCHITECTURE_MAP.md) — where the operator sits in the wider system
- [`docs/architecture/THEORY_TO_CODE.md`](THEORY_TO_CODE.md) — HNC equation → Python mapping, incl. the voice agent
- [`docs/integrations/NEXUS_LIVE_FEED_INTEGRATION.md`](../integrations/NEXUS_LIVE_FEED_INTEGRATION.md) — the live-feed pattern the streaming layer will follow
- [`docs/STATE_FILES.md`](../STATE_FILES.md) — root-level state JSONs (do not move)
- `aureon/inhouse_ai/llm_adapter.py` · `aureon/queen/queen_conscience.py` · `aureon/autonomous/aureon_dynamic_prompt_filter.py`

---

***🎛️ The switchboard is open. Many voices in — one grounded answer out.***
