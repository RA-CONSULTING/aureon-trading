import asyncio
import json
import os

os.environ.setdefault("AUREON_SUPPRESS_IMPORT_SIDE_EFFECTS", "1")

from aureon.autonomous.aureon_mind_thought_action_hub import MindThoughtActionHub


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
