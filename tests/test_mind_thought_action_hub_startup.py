import asyncio
import json
import os
from types import SimpleNamespace

os.environ.setdefault("AUREON_SUPPRESS_IMPORT_SIDE_EFFECTS", "1")

from aureon.autonomous.aureon_mind_thought_action_hub import MindThoughtActionHub


class _FakeVoiceAdapter:
    def __init__(self, text: str, model: str = "fake-voice", raw=None):
        self.text = text
        self.model = model
        self.raw = raw

    def prompt(self, *args, **kwargs):
        return SimpleNamespace(text=self.text, model=self.model, usage={"total_tokens": 7}, raw=self.raw)


def test_hub_constructor_does_not_run_heavy_initialization(monkeypatch):
    def fail_if_called(self):
        raise AssertionError("_init_systems should run after HTTP startup")

    monkeypatch.setattr(MindThoughtActionHub, "_init_systems", fail_if_called)

    hub = MindThoughtActionHub()

    assert hub.initialized is False
    assert hub.initializing is False
    assert any(
        route.resource.canonical == "/api/thoughts"
        for route in hub.app.router.routes()
    )


def test_thoughts_endpoint_is_live_while_initializing(monkeypatch):
    monkeypatch.setattr(MindThoughtActionHub, "_init_systems", lambda self: None)

    hub = MindThoughtActionHub()
    response = asyncio.run(hub.handle_thoughts(None))
    payload = json.loads(response.text)

    assert payload["status"] == "initializing"
    assert payload["initialized"] is False
    assert payload["thoughts"] == []


def test_flight_test_defers_reboot_outside_downtime_with_open_positions(monkeypatch):
    monkeypatch.setattr(MindThoughtActionHub, "_init_systems", lambda self: None)
    monkeypatch.setenv("AUREON_MIND_DOWNTIME_DAYS", "Sun")
    monkeypatch.setenv("AUREON_MIND_DOWNTIME_START_LOCAL", "03:00")
    monkeypatch.setenv("AUREON_MIND_DOWNTIME_END_LOCAL", "03:15")

    hub = MindThoughtActionHub()
    hub.initialized = True
    monkeypatch.setattr(
        hub,
        "_downtime_window_state",
        lambda: {
            "in_window": False,
            "days": "Sun",
            "start_local": "03:00",
            "end_local": "03:15",
            "now_local": "2026-05-12T08:00:00+01:00",
            "next_start_local": "2026-05-17T03:00:00+01:00",
            "next_end_local": "2026-05-17T03:15:00+01:00",
        },
    )
    monkeypatch.setattr(
        hub,
        "_read_market_runtime_summary",
        lambda: {
            "available": True,
            "trading_ready": True,
            "data_ready": True,
            "stale": False,
            "open_positions": 5,
            "pending_orders": 0,
        },
    )
    monkeypatch.setattr(
        hub,
        "_read_reboot_intent",
        lambda: {"pending": True, "surface": "mind", "reason": "validated_change"},
    )

    payload = hub._run_internal_flight_test()

    assert payload["reboot_advice"]["can_reboot_now"] is False
    assert payload["reboot_advice"]["decision"] == "hold_live_state"
    assert "outside_downtime_window" in payload["reboot_advice"]["blockers"]
    assert "open_positions_active" in payload["reboot_advice"]["blockers"]


def test_flight_test_approves_reboot_inside_clear_downtime(monkeypatch):
    monkeypatch.setattr(MindThoughtActionHub, "_init_systems", lambda self: None)

    hub = MindThoughtActionHub()
    hub.initialized = True
    monkeypatch.setattr(
        hub,
        "_downtime_window_state",
        lambda: {
            "in_window": True,
            "days": "Sun",
            "start_local": "03:00",
            "end_local": "03:15",
            "now_local": "2026-05-17T03:05:00+01:00",
            "next_start_local": "2026-05-17T03:00:00+01:00",
            "next_end_local": "2026-05-17T03:15:00+01:00",
        },
    )
    monkeypatch.setattr(
        hub,
        "_read_market_runtime_summary",
        lambda: {
            "available": True,
            "trading_ready": True,
            "data_ready": True,
            "stale": False,
            "open_positions": 0,
            "pending_orders": 0,
        },
    )
    monkeypatch.setattr(hub, "_read_reboot_intent", lambda: {"pending": True})

    payload = hub._run_internal_flight_test()

    assert payload["reboot_advice"]["can_reboot_now"] is True
    assert payload["reboot_advice"]["decision"] == "approve_reboot"
    assert payload["reboot_advice"]["blockers"] == []


def test_goal_pursuit_keeps_live_trading_inside_safety_envelope(monkeypatch):
    monkeypatch.setattr(MindThoughtActionHub, "_init_systems", lambda self: None)

    hub = MindThoughtActionHub()
    hub.initialized = True
    monkeypatch.setattr(
        hub,
        "_read_market_runtime_summary",
        lambda: {
            "available": True,
            "trading_ready": True,
            "data_ready": True,
            "stale": False,
            "open_positions": 5,
            "pending_orders": 0,
            "exchanges_ready": True,
        },
    )
    monkeypatch.setattr(
        hub,
        "_read_organism_runtime_status",
        lambda: {
            "available": True,
            "blind_spot_count": 1,
            "highest_blind_spots": [
                {
                    "severity": "high",
                    "next_action": "Run python -m aureon.autonomous.aureon_saas_system_inventory.",
                }
            ],
            "next_actions": [],
        },
    )

    payload = hub._run_goal_pursuit_assessment()

    assert payload["decision"] == "pursue_goal_with_full_live_capability"
    assert "live_trading_runtime_ready" in payload["active_modes"]
    assert "open_position_monitoring" in payload["active_modes"]
    assert "obey_runtime_risk_and_exchange_gates" in payload["constraints"]
    assert any(
        "Protect and supervise 5 open position" in action
        for action in payload["next_best_actions"]
    )


def test_flight_test_includes_goal_pursuit(monkeypatch):
    monkeypatch.setattr(MindThoughtActionHub, "_init_systems", lambda self: None)

    hub = MindThoughtActionHub()
    hub.initialized = True
    monkeypatch.setattr(
        hub,
        "_downtime_window_state",
        lambda: {
            "in_window": False,
            "days": "Sun",
            "start_local": "03:00",
            "end_local": "03:15",
            "now_local": "2026-05-12T08:00:00+01:00",
            "next_start_local": "2026-05-17T03:00:00+01:00",
            "next_end_local": "2026-05-17T03:15:00+01:00",
        },
    )
    monkeypatch.setattr(
        hub,
        "_read_market_runtime_summary",
        lambda: {
            "available": True,
            "trading_ready": True,
            "data_ready": True,
            "stale": False,
            "open_positions": 0,
            "pending_orders": 0,
            "exchanges_ready": True,
        },
    )
    monkeypatch.setattr(hub, "_read_reboot_intent", lambda: {"pending": False})
    monkeypatch.setattr(
        hub,
        "_read_organism_runtime_status",
        lambda: {"available": True, "blind_spot_count": 0, "next_actions": []},
    )

    payload = hub._run_internal_flight_test()

    assert payload["goal_pursuit"]["decision"] == "pursue_goal_with_full_live_capability"
    assert payload["reboot_advice"]["should_reboot"] is False


def test_phi_bridge_status_exposes_live_chat_lane(monkeypatch):
    monkeypatch.setattr(MindThoughtActionHub, "_init_systems", lambda self: None)
    monkeypatch.setattr(
        MindThoughtActionHub,
        "_ollama_cognitive_status_payload",
        lambda self, force=False: {
            "schema_version": "aureon-ollama-cognitive-bridge-v1",
            "ok": True,
            "status": "ollama_cognitive_bridge_ready",
        },
    )
    monkeypatch.setattr(
        MindThoughtActionHub,
        "_get_phi_voice_adapter",
        lambda self: _FakeVoiceAdapter("ready", model="aureon-ollama-hybrid:llama3:latest"),
    )

    hub = MindThoughtActionHub()
    payload = hub._phi_bridge_status_payload()

    assert payload["service"] == "aureon_phi_bridge_chat"
    assert payload["chat"]["endpoint"] == "POST /api/phi-bridge/chat"
    assert payload["refresh_interval_ms"] >= 618
    assert "no credential reveal" in payload["authority_boundaries"]
    assert payload["ollama_cognitive_bridge"]["schema_version"] == "aureon-ollama-cognitive-bridge-v1"


def test_phi_voice_adapter_reload_resets_cached_backend(monkeypatch):
    monkeypatch.setattr(MindThoughtActionHub, "_init_systems", lambda self: None)
    monkeypatch.setattr(
        MindThoughtActionHub,
        "_get_phi_voice_adapter",
        lambda self: _FakeVoiceAdapter("ready", model="aureon-ollama-hybrid:llama3:latest"),
    )

    hub = MindThoughtActionHub()
    payload = hub._reload_phi_voice_adapter()

    assert payload["ok"] is True
    assert payload["adapter_model"] == "aureon-ollama-hybrid:llama3:latest"


def test_ollama_cognitive_status_payload_is_exposed(monkeypatch):
    monkeypatch.setattr(MindThoughtActionHub, "_init_systems", lambda self: None)

    fake_payload = {
        "schema_version": "aureon-ollama-cognitive-bridge-v1",
        "ok": True,
        "status": "ollama_cognitive_bridge_ready",
        "summary": {"ollama_reachable": True, "cognitive_ready": True},
    }

    import aureon.autonomous.aureon_ollama_cognitive_bridge as bridge_module

    monkeypatch.setattr(bridge_module, "build_and_write_ollama_cognitive_bridge", lambda: fake_payload)

    hub = MindThoughtActionHub()
    payload = hub._ollama_cognitive_status_payload(force=True)

    assert payload["status"] == "ollama_cognitive_bridge_ready"
    assert payload["summary"]["ollama_reachable"] is True


def test_phi_bridge_chat_uses_voice_adapter_and_redacts_context(monkeypatch):
    monkeypatch.setattr(MindThoughtActionHub, "_init_systems", lambda self: None)
    monkeypatch.setattr(
        MindThoughtActionHub,
        "_ollama_cognitive_status_payload",
        lambda self, force=False: {"schema_version": "aureon-ollama-cognitive-bridge-v1", "ok": True},
    )

    hub = MindThoughtActionHub()
    monkeypatch.setattr(hub, "_get_phi_voice_adapter", lambda: _FakeVoiceAdapter("I can see the live coding cockpit."))

    payload = hub._run_phi_chat(
        "what can you see?",
        context={
            "coding": {"status": "coding_organism_ready", "route_clean": True},
            "api_key": "secret-value",
        },
    )

    assert payload["ok"] is True
    assert payload["reply_source"] == "local_llm"
    assert payload["reply"] == "I can see the live coding cockpit."
    assert payload["context_summary"]["api_key"] == "[redacted]"
    assert payload["history"][-1]["role"] == "assistant"


def test_phi_bridge_chat_marks_ollama_context_weaver(monkeypatch):
    monkeypatch.setattr(MindThoughtActionHub, "_init_systems", lambda self: None)
    monkeypatch.setattr(
        MindThoughtActionHub,
        "_ollama_cognitive_status_payload",
        lambda self, force=False: {"schema_version": "aureon-ollama-cognitive-bridge-v1", "ok": True},
    )

    raw = {
        "weaver": True,
        "policy": "small_ollama_shards_then_aureon_recomposition",
        "shards": [{"name": "intent_scope", "ok": True, "latency_ms": 5}],
    }
    hub = MindThoughtActionHub()
    monkeypatch.setattr(
        hub,
        "_get_phi_voice_adapter",
        lambda: _FakeVoiceAdapter(
            "I split this into small Ollama packets and recomposed it through Aureon.",
            model="aureon-ollama-weaver:llama3:latest",
            raw=raw,
        ),
    )

    payload = hub._run_phi_chat("use Ollama in smaller pieces", context={})

    assert payload["reply_source"] == "ollama_cognitive_weaver"
    assert payload["weaver_trace"]["weaver"] is True
    assert payload["history"][-1]["weaver"]["shards"][0]["name"] == "intent_scope"


def test_phi_bridge_chat_falls_back_when_llm_backend_is_missing(monkeypatch):
    monkeypatch.setattr(MindThoughtActionHub, "_init_systems", lambda self: None)
    monkeypatch.setattr(
        MindThoughtActionHub,
        "_ollama_cognitive_status_payload",
        lambda self, force=False: {"schema_version": "aureon-ollama-cognitive-bridge-v1", "ok": False},
    )

    hub = MindThoughtActionHub()
    monkeypatch.setattr(
        hub,
        "_get_phi_voice_adapter",
        lambda: _FakeVoiceAdapter("No LLM backend is reachable.", model="no-backend"),
    )

    payload = hub._run_phi_chat(
        "are you alive?",
        context={"coding": {"status": "ready", "scope_status": "scope_locked", "route_clean": False}},
    )

    assert payload["ok"] is True
    assert payload["reply_source"] == "guided_fallback"
    assert "Phi Bridge" in payload["reply"]
    assert "route needs attention" in payload["reply"]


def test_phi_bridge_chat_discards_late_reply_after_timeout(monkeypatch):
    monkeypatch.setattr(MindThoughtActionHub, "_init_systems", lambda self: None)
    monkeypatch.setattr(
        MindThoughtActionHub,
        "_ollama_cognitive_status_payload",
        lambda self, force=False: {"schema_version": "aureon-ollama-cognitive-bridge-v1", "ok": True},
    )

    hub = MindThoughtActionHub()
    monkeypatch.setattr(hub, "_get_phi_voice_adapter", lambda: _FakeVoiceAdapter("late local model reply"))
    hub._phi_chat_timeout_ids.add("late-1")

    payload = hub._run_phi_chat("slow reply", context={}, chat_id="late-1")

    assert payload["status"] == "phi_bridge_chat_late_reply_discarded"
    assert payload["reply_source"] == "discarded_late_reply"
    assert payload["history"] == []
    assert "late-1" not in hub._phi_chat_timeout_ids
