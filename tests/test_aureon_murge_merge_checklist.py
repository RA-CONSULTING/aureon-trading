from __future__ import annotations

from pathlib import Path

from aureon.autonomous.aureon_murge_merge_checklist import build_report


def test_aureon_murge_merge_checklist_maps_tracks_and_collisions(tmp_path: Path) -> None:
    staging = tmp_path / "aureon_murge_required_test"
    (staging / "runtime").mkdir(parents=True)
    (staging / "docs").mkdir(parents=True)
    (staging / "scripts").mkdir(parents=True)
    (staging / "README.md").write_text("# incoming\n", encoding="utf-8")
    (staging / "runtime" / "server.mjs").write_text("console.log('runtime');\n", encoding="utf-8")
    (staging / "scripts" / "start.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    (staging / "docs" / "SECURITY.md").write_text("# incoming security\n", encoding="utf-8")

    report = build_report(staging)

    assert report["status"] == "murge_merge_collision_review_required"
    assert report["summary"]["file_count"] == 4
    assert any(row["track_id"] == "local_companion_runtime" for row in report["merge_tracks"])
    assert any(row["track_id"] == "operator_scripts" for row in report["merge_tracks"])
    assert any(row["path"] == "README.md" for row in report["collision_rows"])
    assert any(task["id"] == "murge-008" and task["status"] == "blocked" for task in report["merge_checklist"])


def test_aureon_murge_merge_checklist_staging_missing_is_visible(tmp_path: Path) -> None:
    report = build_report(tmp_path / "missing")

    assert report["status"] == "murge_staging_missing"
    assert report["summary"]["file_count"] == 0
    assert report["merge_tracks"] == []
