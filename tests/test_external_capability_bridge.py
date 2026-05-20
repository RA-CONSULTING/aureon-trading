from __future__ import annotations

import json
from pathlib import Path

from aureon.autonomous.aureon_external_capability_bridge import (
    build_and_write_external_capability_bridge,
    build_external_capability_bridge,
)


def test_external_capability_bridge_declares_three_contracts(tmp_path: Path) -> None:
    report = build_external_capability_bridge(root=tmp_path, goal="bridge external skills")

    assert report["schema_version"] == "aureon-external-capability-bridge-v1"
    assert report["summary"]["bridge_count"] == 3
    ids = {row["id"] for row in report["what"]["bridges"]}
    assert ids == {"documents_and_pdfs", "image_generation", "automations"}
    assert all(row["contract"]["verification"] for row in report["what"]["bridges"])
    assert all("boundary" in row["public_boundary"].lower() or row["public_boundary"] for row in report["what"]["bridges"])


def test_external_capability_bridge_writes_public_artifacts(tmp_path: Path) -> None:
    (tmp_path / "docs/audits").mkdir(parents=True)
    (tmp_path / "frontend/public").mkdir(parents=True)

    report = build_and_write_external_capability_bridge(root=tmp_path, goal="write bridge")

    assert report["write_info"]["all_ok"] is True
    assert (tmp_path / "docs/audits/aureon_external_capability_bridge.json").exists()
    assert (tmp_path / "docs/audits/aureon_external_capability_bridge.md").exists()
    assert (tmp_path / "frontend/public/aureon_external_capability_bridge.json").exists()
    public = json.loads((tmp_path / "frontend/public/aureon_external_capability_bridge.json").read_text(encoding="utf-8"))
    assert public["summary"]["ready_count"] == 3
