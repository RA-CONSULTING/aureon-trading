# 🕶️ Aureon Watch — the voice-first wearable command surface

> *"Operator will be like streaming YouTube. You talk and it's a live stream. Two-way
> conversation. Think brain chip — but without circuits in the brain. All run from Ray-Ban
> glasses. No big heavy load on the PC, the data centre a black box."*
> — the creator's field notes, [`AUREON_OPERATOR_SWITCHBOARD.md`](../architecture/AUREON_OPERATOR_SWITCHBOARD.md)

**Aureon Watch** is that vision on the wrist: a self-contained, voice-first Progressive Web App
that lets you *do everything you need from anywhere* — ask, watch the system's pulse, browse what
the platform can do — from a Pixel Watch (Wear OS, round ~400 px) or any small screen.

It is a **thin client**. The watch captures your voice in the browser, streams the question to the
Aureon Operator, streams the answer back token-by-token, and speaks it aloud. No heavy compute on
the device; the data centre stays a black box.

```
mic → browser speech-to-text → /api/cognition/stream (SSE) → tokens → browser text-to-speech
```

---

## How to open it

The watch app is served **two ways**, both same-origin (so there is no CORS and streaming just
works):

1. **From the operator front door** — `GET /watch` on the operator server
   (`aureon/operator/operator_server.py`). This is the simplest path and needs nothing but the
   operator running. Because the repo usually runs in a remote container, open the **deployed
   HTTPS URL or a tunnel** on the watch (Cloudflare / ngrok / tailscale), exactly like the phone
   PoC — see [`OPERATOR_DEPLOY.md`](../deployment/OPERATOR_DEPLOY.md). `localhost` won't reach the
   watch.
2. **From the platform frontend** — the same app is shipped as static files in
   `frontend/public/watch/`, so the production nginx serves it at `/watch/` alongside the React
   console (same origin as the `/api` proxy).

> **HTTPS is required** for the microphone, install-to-home-screen, and the service worker. Over
> plain `http://` the app still loads and works by tap/text, but voice and offline install are
> disabled by the browser.

**Install as an app:** open `/watch/` on the watch, then *Add to home screen* / *Install*. It
launches full-screen (`display: standalone`), black-themed for OLED, with the shell cached offline.

---

## What's on it

Six scroll-snap screens (swipe up/down or use the crown). A dot rail on the right shows where you
are.

| Screen | What it does | Source |
|---|---|---|
| **Ask** | Tap the orb and speak (or type). The question fans across the line-up / cognition, grounds in the repo, and streams back — spoken aloud. Live chips show ground → fan-out → consensus → veto (or grounding → tool → veto), and the Queen's conscience verdict. | `/api/operator/stream`, `/api/cognition/stream` (SSE) |
| **Pulse** | Glanceable vitals: healthy/degraded, the active model line-up, domains reachable, organism state — auto-refreshing. | `/api/pulse` |
| **Organism** | The connectome's honest coverage of the body, recent pulses, and mycelium membership. | `/api/pulse` → `/api/organism` payload |
| **Systems** | The full catalog — every category and system Aureon exposes. Tap a category to see its systems. | `/api/catalog` |
| **Trading** | A **read-only** state read, run through the gated cognition tools. | `/api/cognition/reason` (read-only prompt) |
| **Quick** | Big one-tap prompts for the common asks. | — |

### Voice & hands-free
- **Speak:** tap the orb → speak → the answer streams and is read aloud (Web Speech API:
  `SpeechRecognition` + `speechSynthesis`).
- **Hands-free:** toggle it on and the mic re-arms after each answer; say **"Aureon, …"** as the
  wake word so ambient talk doesn't fire it.
- **Toggles:** `cognition` (agentic mode), `speak` (TTS on/off), `hands-free`.
- If a browser lacks the speech APIs, the app falls back cleanly to tap + a text box — nothing
  breaks.

---

## Safety posture — read-only on the wrist

The watch is a **window and a voice, not a trigger**. The hard authority boundaries are unchanged:

- **Nothing trades, pays, files, or mutates from the watch.** The Trading screen is read-only; the
  charge-fee path stays off; no autonomous action surface is added.
- Every answer still passes the Operator's grounding + consensus + **Queen conscience veto** before
  it is spoken.
- Same-origin, open-by-default like the phone PoC. **Caveat:** if you harden the operator with
  `AUREON_OPERATOR_API_KEY`, the browser `EventSource` API cannot send an `Authorization` header,
  so bearer-protected SSE would need a query-param token scheme (not built yet). Deploy the watch
  behind a network boundary / tunnel auth for now.

---

## Files

```
aureon/operator/wearable/         ← source of truth
├── index.html        app shell (6 scroll-snap screens)
├── watch.css         round-safe, OLED-black, 48px+ targets
├── watch.js          screens · voice (STT/TTS) · SSE · pollers · PWA
├── manifest.webmanifest
├── sw.js             precache shell; /api always live; offline shell fallback
└── icon.svg · icon-192.png · icon-512.png · icon-maskable.png
frontend/public/watch/            ← verbatim copy (nginx serves at /watch/)
```

Operator routes: `GET /watch`, `GET /watch/<asset>` (sets `Service-Worker-Allowed: /` on `sw.js`),
and the composed read-only `GET /api/pulse`. Tests: `tests/test_operator_wearable.py`.

See also: [`AUREON_OPERATOR_SWITCHBOARD.md`](../architecture/AUREON_OPERATOR_SWITCHBOARD.md) (the
glasses path & the switchboard it rides on) and [`OPERATOR_DEPLOY.md`](../deployment/OPERATOR_DEPLOY.md)
(reaching it from your pocket).
