"""
AureonVaultUI — Flask Server for Communicating with the Vault
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

A small Flask HTTP server that exposes the self-feedback vault and its
voice layer as a REST API plus a single-file web UI. Lets the user:

  • Watch the vault's state in real time (love, gratitude, Casimir, Λ(t),
    dominant chakra, rally status, vote consensus)
  • Read the stream of utterances as voices speak to each other
  • Send messages to the vault and get responses from a chosen voice
  • Force a specific voice to speak
  • Trigger one tick of the feedback loop on demand
  • Start/stop the background loop

Endpoints:
  GET  /                       — the chat UI (index.html)
  GET  /api/status             — full vault + loop status dict
  GET  /api/voices             — list of voice names
  GET  /api/utterances?n=50    — recent utterances (most recent last)
  POST /api/message            — {"text": "...", "voice": "queen"?}
                                  vault ingests + voice responds
  POST /api/speak              — {"voice": "miner"?} force a voice to speak
  POST /api/converse           — trigger one voice_engine.converse()
  POST /api/tick               — trigger one full loop.tick()
  POST /api/loop/start         — start the loop daemon
  POST /api/loop/stop          — stop the loop daemon

Usage:
    from aureon.vault.ui import create_app, run_server
    run_server(host="127.0.0.1", port=5566)

Or programmatically:
    from aureon.vault import AureonSelfFeedbackLoop
    from aureon.vault.ui import create_app
    loop = AureonSelfFeedbackLoop()
    app = create_app(loop=loop)
    app.run(port=5566)
"""

from __future__ import annotations

import logging
import os
import time
from typing import Optional

try:
    from flask import Flask, jsonify, request, send_from_directory
    _FLASK_AVAILABLE = True
except Exception:  # pragma: no cover
    Flask = None  # type: ignore[assignment,misc]
    jsonify = None  # type: ignore[assignment]
    request = None  # type: ignore[assignment]
    send_from_directory = None  # type: ignore[assignment]
    _FLASK_AVAILABLE = False

from aureon.vault.self_feedback_loop import AureonSelfFeedbackLoop

logger = logging.getLogger("aureon.vault.ui")

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


# ─────────────────────────────────────────────────────────────────────────────
# Error helper
# ─────────────────────────────────────────────────────────────────────────────


def _check_flask() -> None:
    if not _FLASK_AVAILABLE:
        raise RuntimeError(
            "Flask is not installed. Run `pip install flask` to enable the vault UI."
        )


# ─────────────────────────────────────────────────────────────────────────────
# App factory
# ─────────────────────────────────────────────────────────────────────────────


def create_app(
    loop: Optional[AureonSelfFeedbackLoop] = None,
    base_interval_s: float = 1.0,
    enable_voice: bool = True,
) -> "Flask":
    """
    Create a Flask app bound to a SelfFeedbackLoop.

    If no loop is provided, a fresh one is constructed.
    """
    _check_flask()

    if loop is None:
        loop = AureonSelfFeedbackLoop(
            base_interval_s=base_interval_s,
            enable_voice=enable_voice,
        )

    app = Flask(
        "aureon_vault_ui",
        static_folder=STATIC_DIR,
        static_url_path="/static",
    )

    # Expose the loop on the app config so tests can reach it
    app.config["AUREON_LOOP"] = loop

    # ─────────────────────────────────────────────────────────────────────
    # UI page
    # ─────────────────────────────────────────────────────────────────────

    @app.route("/")
    def index():
        index_path = os.path.join(STATIC_DIR, "index.html")
        if not os.path.exists(index_path):
            return (
                "<h1>Aureon Vault UI</h1>"
                "<p>index.html not found at " + index_path + "</p>"
            ), 200
        return send_from_directory(STATIC_DIR, "index.html")

    # ─────────────────────────────────────────────────────────────────────
    # Status + introspection
    # ─────────────────────────────────────────────────────────────────────

    @app.route("/api/status")
    def api_status():
        try:
            status = loop.get_status()
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500
        return jsonify({"ok": True, "status": status})

    @app.route("/api/voices")
    def api_voices():
        if loop.voice_engine is None:
            return jsonify({"ok": False, "error": "voice engine disabled"}), 400
        return jsonify({
            "ok": True,
            "voices": list(loop.voice_engine.voices.keys()),
        })

    @app.route("/api/utterances")
    def api_utterances():
        if loop.voice_engine is None:
            return jsonify({"ok": True, "utterances": []})
        n = request.args.get("n", default=50, type=int)
        history = loop.voice_engine.history[-n:]
        return jsonify({
            "ok": True,
            "count": len(history),
            "utterances": [u.to_dict() for u in history],
        })

    # ─────────────────────────────────────────────────────────────────────
    # Interaction
    # ─────────────────────────────────────────────────────────────────────

    @app.route("/api/message", methods=["POST"])
    def api_message():
        """Human sends a message to the vault; a voice responds."""
        if loop.voice_engine is None:
            return jsonify({"ok": False, "error": "voice engine disabled"}), 400

        data = request.get_json(silent=True) or {}
        text = str(data.get("text", "")).strip()
        voice_name = data.get("voice")

        if not text:
            return jsonify({"ok": False, "error": "missing text"}), 400

        try:
            utterance = loop.voice_engine.respond_to_human(
                message=text, voice_name=voice_name,
            )
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

        if utterance is None:
            return jsonify({"ok": False, "error": "voice did not respond"}), 200

        return jsonify({"ok": True, "utterance": utterance.to_dict()})

    @app.route("/api/speak", methods=["POST"])
    def api_speak():
        """Force a specific voice to speak right now."""
        if loop.voice_engine is None:
            return jsonify({"ok": False, "error": "voice engine disabled"}), 400

        data = request.get_json(silent=True) or {}
        voice_name = data.get("voice")

        try:
            if voice_name:
                utterance = loop.voice_engine.speak_as(voice_name)
            else:
                utterance = loop.voice_engine.converse()
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

        if utterance is None:
            return jsonify({
                "ok": False,
                "error": "gate suppressed or voice not found",
            }), 200

        return jsonify({"ok": True, "utterance": utterance.to_dict()})

    @app.route("/api/converse", methods=["POST"])
    def api_converse():
        """Trigger one voice_engine.converse() call (respects the gate)."""
        if loop.voice_engine is None:
            return jsonify({"ok": False, "error": "voice engine disabled"}), 400
        try:
            utterance = loop.voice_engine.converse()
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

        if utterance is None:
            gate_status = loop.voice_engine.gate.get_status()
            return jsonify({
                "ok": True,
                "spoke": False,
                "gate": gate_status,
            })

        return jsonify({
            "ok": True,
            "spoke": True,
            "utterance": utterance.to_dict(),
        })

    @app.route("/api/tick", methods=["POST"])
    def api_tick():
        """Trigger one full loop.tick() (including voice, Casimir, Auris, ping)."""
        try:
            result = loop.tick()
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500
        return jsonify({"ok": True, "tick": result.to_dict()})

    # ─────────────────────────────────────────────────────────────────────
    # Loop control
    # ─────────────────────────────────────────────────────────────────────

    @app.route("/api/loop/start", methods=["POST"])
    def api_loop_start():
        try:
            loop.start()
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500
        return jsonify({"ok": True, "running": True})

    @app.route("/api/loop/stop", methods=["POST"])
    def api_loop_stop():
        try:
            loop.stop()
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500
        return jsonify({"ok": True, "running": False})

    # ─────────────────────────────────────────────────────────────────────
    # Health
    # ─────────────────────────────────────────────────────────────────────

    @app.route("/api/health")
    def api_health():
        return jsonify({
            "ok": True,
            "service": "aureon_vault_ui",
            "loop_id": loop.loop_id,
            "cycles": loop._cycle,
            "voice_enabled": loop.voice_engine is not None,
            "timestamp": time.time(),
        })

    return app


# ─────────────────────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────────────────────


def run_server(
    host: str = "127.0.0.1",
    port: int = 5566,
    loop: Optional[AureonSelfFeedbackLoop] = None,
    start_loop: bool = False,
    debug: bool = False,
) -> None:
    """Blocking server run. Use `start_loop=True` to also spawn the loop."""
    app = create_app(loop=loop)
    if start_loop:
        cfg_loop = app.config["AUREON_LOOP"]
        cfg_loop.start()
    logger.info("Aureon Vault UI listening on http://%s:%d/", host, port)
    app.run(host=host, port=port, debug=debug, use_reloader=False, threaded=True)
