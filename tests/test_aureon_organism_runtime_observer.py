import json
from datetime import datetime, timezone
from pathlib import Path

import aureon.autonomous.aureon_organism_runtime_observer as observer
from aureon.autonomous.aureon_organism_runtime_observer import (
    build_organism_runtime_status,
    write_status,
)


def _write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _make_fake_repo(root: Path):
    (root / "aureon").mkdir()
    (root / "scripts").mkdir()
    now = datetime.now(timezone.utc).isoformat()

    _write_json(
        root / "docs" / "audits" / "aureon_saas_system_inventory.json",
        {
            "generated_at": now,
            "status": "inventory_ready",
            "summary": {
                "surface_count": 12,
                "frontend_surface_count": 4,
                "supabase_function_count": 2,
                "security_blocker_count": 0,
                "orphaned_frontend_count": 0,
                "missing_supabase_function_call_count": 0,
            },
        },
    )
    _write_json(
        root / "frontend" / "public" / "aureon_saas_system_inventory.json",
        {"generated_at": now, "summary": {"surface_count": 12}},
    )
    _write_json(
        root / "docs" / "audits" / "aureon_frontend_unification_plan.json",
        {
            "generated_at": now,
            "status": "unification_plan_ready",
            "summary": {
                "screen_count": 7,
                "source_surface_count": 12,
                "security_blocker_count": 0,
                "missing_screen_capability_count": 0,
            },
        },
    )
    _write_json(
        root / "frontend" / "public" / "aureon_frontend_unification_plan.json",
        {"generated_at": now, "summary": {"screen_count": 7}},
    )
    _write_json(
        root / "docs" / "audits" / "aureon_system_readiness_audit.json",
        {
            "generated_at": now,
            "status": "working",
            "summary": {"proof_count": 10, "blocked_count": 0, "attention_count": 0},
        },
    )
    (root / "adaptive_learning_history.json").write_text("[]", encoding="utf-8")
    (root / "brain_predictions_history.json").write_text("[]", encoding="utf-8")
    (root / "miner_brain_knowledge.json").write_text("{}", encoding="utf-8")
    (root / "public").mkdir(exist_ok=True)
    (root / "public" / "consciousness_state.json").write_text("{}", encoding="utf-8")


def test_organism_observer_builds_safe_status_and_blind_spots(tmp_path):
    _make_fake_repo(tmp_path)

    status = build_organism_runtime_status(
        tmp_path,
        local_terminal_url="http://127.0.0.1:1/aureon-offline-test",
    )
    data = status.to_dict()

    assert data["schema_version"] == "aureon-organism-runtime-status-v1"
    assert data["mode"] == "safe_observation"
    assert data["safety"]["live_orders_allowed"] is False
    assert data["summary"]["domain_count"] >= 10
    assert data["summary"]["runtime_feed_status"] == "offline"
    assert any(item["id"] == "runtime_feed.offline" for item in data["blind_spots"])
    assert any(domain["id"] == "saas_inventory" and domain["freshness"] == "fresh" for domain in data["domains"])


def test_organism_observer_writes_public_and_vault_artifacts(tmp_path):
    _make_fake_repo(tmp_path)
    status = build_organism_runtime_status(
        tmp_path,
        local_terminal_url="http://127.0.0.1:1/aureon-offline-test",
    )

    md_path, json_path, public_path, vault_path = write_status(status)

    assert md_path.exists()
    assert json_path.exists()
    assert public_path.exists()
    assert vault_path.exists()
    payload = json.loads(public_path.read_text(encoding="utf-8"))
    assert payload["status"].startswith("organism_observing")
    assert payload["real_time_feeds"]["local_terminal"]["status"] == "offline"


def test_organism_observer_reports_live_stale_runtime_as_guarded(monkeypatch, tmp_path):
    _make_fake_repo(tmp_path)
    _write_json(
        tmp_path / "state" / "aureon_wake_up_manifest.json",
        {
            "mode": "LIVE_TRADING_OPERATOR_CONFIRMED + PRODUCTION_SUPERVISOR",
            "runtime_feed_url": "http://127.0.0.1:8791/api/terminal-state",
            "runtime_flight_test_url": "http://127.0.0.1:8791/api/flight-test",
            "safety": {
                "live_trading": "1",
                "disable_real_orders": "0",
                "disable_exchange_mutations": "0",
                "allow_sim_fallback": "0",
            },
        },
    )

    def fake_runtime_feed(url: str, timeout_seconds: float = 1.5):
        return {
            "status": "online",
            "url": url,
            "ok": False,
            "trading_ready": True,
            "data_ready": True,
            "stale": True,
            "booting": False,
            "open_positions": 4,
            "runtime_watchdog": {
                "tick_stale": True,
                "tick_stale_reason": "tick_in_progress_stalled",
                "open_positions": True,
            },
        }

    def fake_flight_test(url: str, timeout_seconds: float = 1.5):
        return {
            "status": "online",
            "url": "http://127.0.0.1:8791/api/flight-test",
            "ok": False,
            "checks": {"downtime_window": False, "open_positions": True},
            "reboot_advice": {
                "should_reboot": True,
                "can_reboot_now": False,
                "decision": "hold_monitor_positions",
            },
        }

    monkeypatch.setattr(observer, "probe_local_runtime_feed", fake_runtime_feed)
    monkeypatch.setattr(observer, "probe_runtime_flight_test", fake_flight_test)

    status = build_organism_runtime_status(tmp_path)
    data = status.to_dict()
    blocked_by = data["safety"]["action_capability"]["trading"]["blocked_by"]

    assert data["mode"] == "guarded_observe_plan"
    assert data["summary"]["trading_action_allowed"] is False
    assert "runtime_stale" in blocked_by
    assert "tick_in_progress_stalled" in blocked_by
    assert "open_positions" in blocked_by
    assert "downtime_window_false" in blocked_by
