from __future__ import annotations

import json
from pathlib import Path

from aureon.autonomous.aureon_codex_capability_ingestion import (
    build_and_write_codex_capability_ingestion,
    build_codex_capability_ingestion,
)
from aureon.core.goal_execution_engine import GoalExecutionEngine


def _seed_repo(root: Path) -> None:
    for path in [
        "aureon/autonomous",
        "aureon/core",
        "aureon/inhouse_ai",
        "aureon/code_architect",
        "aureon/autonomous/vm_control",
        "docs/audits",
        "frontend/public",
        "frontend/src/components/generated",
        "tests",
    ]:
        (root / path).mkdir(parents=True, exist_ok=True)
    for file_path in [
        "aureon/autonomous/aureon_mind_thought_action_hub.py",
        "aureon/core/goal_execution_engine.py",
        "aureon/autonomous/aureon_coding_organism_bridge.py",
        "aureon/autonomous/aureon_director_capability_bridge.py",
        "aureon/autonomous/aureon_repo_explorer_service.py",
        "aureon/autonomous/aureon_safe_code_control.py",
        "aureon/autonomous/aureon_coding_agent_skill_base.py",
        "aureon/autonomous/aureon_safe_desktop_control.py",
        "aureon/autonomous/vm_control/tools.py",
        "aureon/inhouse_ai/tool_registry.py",
        "aureon/code_architect/architect.py",
        "README.md",
        "RUNNING.md",
        "QUICK_START.md",
        "CAPABILITIES.md",
    ]:
        (root / file_path).parent.mkdir(parents=True, exist_ok=True)
        (root / file_path).write_text("# seeded\n", encoding="utf-8")
    (root / "frontend/src/App.tsx").write_text(
        'import { AureonCodingOrganismConsole } from "@/components/generated/AureonCodingOrganismConsole";\n'
        "export default function App(){return <AureonCodingOrganismConsole />}\n",
        encoding="utf-8",
    )
    (root / "EVERYTHING_CODEX_CAN_DO.md").write_text(
        "# Everything Codex Can Do\n\n"
        "| Codex capability | What Codex can do | Aureon bridge requirement |\n"
        "| --- | --- | --- |\n"
        "| Prompt intake | Accept natural language and route work. | Aureon must create typed goals. |\n"
        "| Browser inspection | Open local URLs and inspect rendered content. | Aureon must add browser smoke evidence. |\n"
        "| Git operations | Commit and push when asked. | Aureon must build a release bridge. |\n",
        encoding="utf-8",
    )


def test_codex_capability_ingestion_reads_markdown_and_maps_work_orders(tmp_path: Path) -> None:
    _seed_repo(tmp_path)

    report = build_codex_capability_ingestion(root=tmp_path, goal="ingest codex capability file")

    assert report["schema_version"] == "aureon-codex-capability-ingestion-v1"
    assert report["summary"]["capability_rows_read"] == 3
    assert report["completion_report"]["did_read_source_document"] is True
    assert report["completion_report"]["did_generate_bridge_work_orders"] is True
    assert report["act"]["validation"]["director_bridge_ran"] is True


def test_codex_capability_ingestion_writes_public_progress_report(tmp_path: Path) -> None:
    _seed_repo(tmp_path)

    report = build_and_write_codex_capability_ingestion(root=tmp_path, goal="write evidence")

    assert report["write_info"]["all_ok"] is True
    assert (tmp_path / "docs/audits/aureon_codex_capability_ingestion_report.json").exists()
    assert (tmp_path / "docs/audits/aureon_codex_capability_ingestion_report.md").exists()
    assert (tmp_path / "frontend/public/aureon_codex_capability_ingestion_report.json").exists()
    public = json.loads((tmp_path / "frontend/public/aureon_codex_capability_ingestion_report.json").read_text(encoding="utf-8"))
    assert public["completion_report"]["self_validation_result"] == "passing"


def test_goal_engine_routes_everything_codex_can_do_ingestion(tmp_path: Path, monkeypatch) -> None:
    _seed_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    engine = GoalExecutionEngine()
    plan = engine.submit_goal(
        "Aureon must ingest EVERYTHING_CODEX_CAN_DO.md, marry up what Codex can do with Aureon, "
        "write bridge work orders, test itself, and publish a completion report."
    )

    assert plan.status == "completed"
    assert plan.steps[0].intent == "codex_capability_ingestion"
    assert plan.steps[0].validation_result["valid"] is True
    evidence = json.loads((tmp_path / "state/aureon_codex_capability_ingestion_last_run.json").read_text(encoding="utf-8"))
    assert evidence["completion_report"]["did_marriage_map"] is True
