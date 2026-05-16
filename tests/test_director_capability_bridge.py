from __future__ import annotations

import json
from pathlib import Path

from aureon.autonomous.aureon_director_capability_bridge import (
    CODEX_CLASS_CAPABILITIES,
    build_and_write_director_capability_bridge,
    build_director_capability_bridge,
)
from aureon.core.goal_execution_engine import GoalExecutionEngine


def _seed_repo(root: Path) -> None:
    for path in [
        "aureon/autonomous",
        "aureon/core",
        "aureon/code_architect",
        "aureon/inhouse_ai",
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
    (root / "frontend" / "src" / "App.tsx").write_text(
        'import { AureonCodingOrganismConsole } from "@/components/generated/AureonCodingOrganismConsole";\n'
        "export default function App() {\n"
        "  return (\n"
        "    <main>\n"
        "        <AureonCodingOrganismConsole />\n"
        "    </main>\n"
        "  );\n"
        "}\n",
        encoding="utf-8",
    )


def test_director_capability_bridge_builds_codex_parity_map(tmp_path: Path) -> None:
    _seed_repo(tmp_path)

    report = build_director_capability_bridge("Map Codex-class capability gaps", root=tmp_path)

    assert report["schema_version"] == "aureon-director-capability-bridge-v1"
    assert report["summary"]["capability_count"] == len(CODEX_CLASS_CAPABILITIES)
    ids = {row["id"] for row in report["codex_class_capabilities"]}
    assert {"prompt_goal_routing", "browser_visual_smoke", "git_release_flow"}.issubset(ids)
    assert report["aureon_bridge_work_orders"]
    assert all(order["exact_aureon_prompt"].startswith("Aureon must") for order in report["aureon_bridge_work_orders"])


def test_director_capability_bridge_writes_artifacts_and_console(tmp_path: Path) -> None:
    _seed_repo(tmp_path)

    report = build_and_write_director_capability_bridge("Director bridge the gaps", root=tmp_path)

    assert report["write_info"]["writer"] == "QueenCodeArchitect"
    assert (tmp_path / "docs" / "audits" / "aureon_director_capability_bridge.json").exists()
    assert (tmp_path / "frontend" / "public" / "aureon_director_capability_bridge.json").exists()
    assert (tmp_path / "frontend" / "src" / "components" / "generated" / "AureonDirectorCapabilityBridgeConsole.tsx").exists()
    app_text = (tmp_path / "frontend" / "src" / "App.tsx").read_text(encoding="utf-8")
    assert "AureonDirectorCapabilityBridgeConsole" in app_text
    public = json.loads((tmp_path / "frontend" / "public" / "aureon_director_capability_bridge.json").read_text(encoding="utf-8"))
    assert public["summary"]["bridge_work_order_count"] == len(public["aureon_bridge_work_orders"])


def test_goal_engine_routes_director_capability_bridge(tmp_path: Path, monkeypatch) -> None:
    _seed_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    engine = GoalExecutionEngine()
    plan = engine.submit_goal(
        "Aureon director mode must create a list of what Codex can do, marry it to Aureon capabilities, "
        "bridge the gaps, and write the code work orders."
    )

    assert plan.status == "completed"
    assert plan.steps[0].intent == "director_capability_bridge"
    assert plan.steps[0].validation_result["valid"] is True
    evidence = json.loads((tmp_path / "state" / "aureon_director_capability_bridge_last_run.json").read_text(encoding="utf-8"))
    assert evidence["authoring_path"][-1] == "QueenCodeArchitect.write_file"
