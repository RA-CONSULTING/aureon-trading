from __future__ import annotations

from aureon.autonomous.aureon_murge_unity_bridge import build_unity_bridge


def test_aureon_murge_unity_bridge_reports_staged_tracks() -> None:
    report = build_unity_bridge()

    assert report["schema_version"] == "aureon-murge-unity-bridge-v1"
    assert report["summary"]["track_count"] >= 6
    assert report["summary"]["staged_track_count"] >= 5
    assert any(row["track_id"] == "local_companion_runtime" for row in report["unity_track_rows"])
    assert any(row["track_id"] == "web_app_provider_shell" for row in report["organism_adapter_rows"])
    assert report["online_requirement_baseline"]
    assert "hidden_activation" in report["summary"]


def test_aureon_murge_unity_bridge_keeps_collisions_visible() -> None:
    report = build_unity_bridge()

    assert report["summary"]["collision_count"] >= 1
    assert "collision_review_required" in report["blockers"]
    assert report["status"] == "aureon_unity_staged_collision_review"
