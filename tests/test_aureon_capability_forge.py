from __future__ import annotations

import json
from pathlib import Path

from aureon.autonomous.aureon_artifact_quality_gate import build_artifact_quality_report
from aureon.autonomous.aureon_capability_forge import build_and_write_capability_forge, classify_task_family
from aureon.core.goal_execution_engine import GoalExecutionEngine


def _fake_expression_context(*args, **kwargs):
    return {
        "schema_features": ["aureon_code_expression_context_v1"],
        "ok": True,
        "voice_summary": "Aureon local capability forge recorded safe code evidence.",
        "runtime_summary": "capability forge state translated",
        "redaction_applied": False,
    }


def test_capability_forge_classifies_core_task_families() -> None:
    assert classify_task_family("make a 10 second video of a dog")["primary_family"] == "video"
    assert classify_task_family("draw a logo and graphic design")["task_family"] == "image_graphic_design"
    assert classify_task_family("write code for a Python module and run tests")["task_family"] == "coding"
    assert classify_task_family("build a React UI dashboard panel")["primary_family"] == "ui"
    assert classify_task_family("write a PDF document report")["task_family"] == "document"
    assert classify_task_family("open the browser and run a Playwright smoke test")["primary_family"] == "browser_qa"


def test_capability_forge_local_only_reference_patterns_and_no_external_calls(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "aureon.autonomous.aureon_safe_code_control.build_code_expression_context",
        _fake_expression_context,
    )

    report = build_and_write_capability_forge(
        "Aureon must research how AI systems do coding jobs, build a local coding forge, "
        "publish proof, and keep cloud providers reference-only.",
        root=tmp_path,
    )

    assert report["provider_policy"] == "local_only_v1"
    assert report["external_api_calls"] == []
    assert report["summary"]["external_api_call_count"] == 0
    assert report["summary"]["safe_code_route_recorded"] is True
    assert report["approval_state"]["state"] == "pending_user_review_after_apply"
    assert all(item["external_api_call_allowed"] is False for item in report["reference_patterns"])
    assert (tmp_path / "frontend" / "public" / "aureon_capability_forge.json").exists()


def test_capability_forge_video_job_produces_quality_gated_public_artifacts(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "aureon.autonomous.aureon_safe_code_control.build_code_expression_context",
        _fake_expression_context,
    )
    monkeypatch.chdir(tmp_path)
    (tmp_path / "aureon").mkdir()

    report = build_and_write_capability_forge(
        "Make a 1 second video of a dog running across the screen, show it in the UI, "
        "and do not hand it over unless the browser-playable preview passes.",
        root=tmp_path,
    )

    quality = report["artifact_quality_report"]
    manifest = report["artifact_manifest"]
    assert report["task_family"] == "video"
    assert report["handover_ready"] is True
    assert quality["handover_ready"] is True
    assert quality["score"] >= 0.8
    assert manifest["public_url"].endswith((".webm", ".gif"))
    assert manifest["preview_url"].endswith("_preview.html")
    assert Path(manifest["asset_path"]).exists()
    assert Path(manifest["preview_path"]).exists()
    assert (tmp_path / "frontend" / "public" / "aureon_artifact_quality_report.json").exists()


def test_artifact_quality_gate_blocks_unplayable_video_without_preview(tmp_path: Path) -> None:
    bad_video = tmp_path / "frontend" / "public" / "aureon_visual_artifacts" / "bad.mp4"
    bad_video.parent.mkdir(parents=True, exist_ok=True)
    bad_video.write_bytes(b"not a playable video")

    report = build_artifact_quality_report(
        {
            "kind": "video",
            "asset_path": str(bad_video),
            "source_asset_path": str(bad_video),
            "public_url": "/aureon_visual_artifacts/bad.mp4",
            "preview_url": "",
            "preview_path": "",
            "duration_seconds": 10,
        },
        prompt="make a 10 second video",
        task_family="video",
        root=tmp_path,
    )

    assert report["handover_ready"] is False
    assert report["status"] == "artifact_quality_blocked"
    snag_ids = {item["id"] for item in report["snags"]}
    assert "artifact_playable_or_renderable_format" in snag_ids
    assert "artifact_preview_page_present" in snag_ids


def test_goal_engine_routes_capability_forge_request(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "aureon.autonomous.aureon_safe_code_control.build_code_expression_context",
        _fake_expression_context,
    )
    monkeypatch.chdir(tmp_path)
    (tmp_path / "aureon").mkdir()

    plan = GoalExecutionEngine().submit_goal(
        "Aureon must build the local capability forge quality gate so it does not send half baked cake to the client."
    )

    assert plan.status == "completed"
    assert [step.intent for step in plan.steps] == ["capability_forge"]
    assert plan.steps[0].validation_result["valid"] is True
    payload = plan.steps[0].result["result"]
    assert payload["schema_version"] == "aureon-local-capability-forge-v1"
    assert payload["provider_policy"] == "local_only_v1"
    assert payload["approval_state"]["state"] == "pending_user_review_after_apply"


def test_capability_forge_public_json_has_required_report_fields(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "aureon.autonomous.aureon_safe_code_control.build_code_expression_context",
        _fake_expression_context,
    )
    report = build_and_write_capability_forge("Build a UI panel and browser smoke proof for the cockpit.", root=tmp_path)
    public = json.loads((tmp_path / "frontend" / "public" / "aureon_capability_forge.json").read_text(encoding="utf-8"))

    for key in (
        "task_family",
        "director_brief",
        "recruited_crew",
        "local_tools_used",
        "reference_patterns",
        "artifact_manifest",
        "artifact_quality_report",
        "regeneration_attempts",
        "applied_change_evidence",
        "approval_state",
        "handover_ready",
    ):
        assert key in public
        assert key in report


def test_capability_forge_interactive_game_builds_local_playable_artifact(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "aureon.autonomous.aureon_safe_code_control.build_code_expression_context",
        _fake_expression_context,
    )

    report = build_and_write_capability_forge(
        "Make me a game where a man walks up to a glowing door and tell the end user how to play from the keyboard.",
        root=tmp_path,
    )

    manifest = report["artifact_manifest"]
    quality = report["artifact_quality_report"]
    assert report["handover_ready"] is True
    assert report["summary"]["adaptive_skill_created"] is True
    assert report["adaptive_skill_evidence"]["name"] == "local_html_game_forge"
    assert manifest["kind"] == "html_game"
    assert manifest["public_url"].endswith(".html")
    assert manifest["preview_url"] == manifest["public_url"]
    assert Path(manifest["asset_path"]).exists()
    html = Path(manifest["asset_path"]).read_text(encoding="utf-8")
    assert "Move: Arrow keys or WASD" in html
    assert "Jump: Space" in html
    assert quality["handover_ready"] is True
    assert quality["score"] >= 0.8


def test_capability_forge_unknown_tool_request_builds_adaptive_skill_capsule(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "aureon.autonomous.aureon_safe_code_control.build_code_expression_context",
        _fake_expression_context,
    )

    report = build_and_write_capability_forge(
        "Build a local barcode label generator tool for the warehouse team, with run instructions and proof.",
        root=tmp_path,
    )

    manifest = report["artifact_manifest"]
    quality = report["artifact_quality_report"]
    assert report["handover_ready"] is True
    assert report["summary"]["adaptive_skill_created"] is True
    assert report["adaptive_skill_evidence"]["name"] == "universal_adaptive_skill_forge"
    assert manifest["kind"] == "adaptive_skill_capsule"
    assert manifest["public_url"].endswith("/index.html")
    assert Path(manifest["asset_path"]).exists()
    assert Path(manifest["tool_path"]).exists()
    assert Path(manifest["runbook_path"]).exists()
    assert quality["handover_ready"] is True
    assert any(check["id"] == "adaptive_skill_run_contract_exists" for check in quality["checks"])
