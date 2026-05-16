from __future__ import annotations

import json
from pathlib import Path

from aureon.autonomous.aureon_coding_agent_skill_base import build_and_write_profile
from aureon.core.goal_execution_engine import GoalExecutionEngine
from aureon.inhouse_ai.tool_registry import ToolRegistry


def _fake_repo(root: Path) -> None:
    (root / "aureon" / "demo").mkdir(parents=True)
    (root / "scripts").mkdir()
    (root / "tests").mkdir()
    (root / "frontend" / "src").mkdir(parents=True)
    (root / "aureon" / "demo" / "worker.py").write_text("def run_worker():\n    return 'ok'\n", encoding="utf-8")
    (root / "tests" / "test_worker.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    (root / "frontend" / "src" / "App.tsx").write_text(
        'import { AureonWorkOrderExecutionConsole } from "@/components/generated/AureonWorkOrderExecutionConsole";\n'
        "export default function App() {\n"
        "  return (\n"
        "    <main>\n"
        "        <AureonWorkOrderExecutionConsole />\n"
        "    </main>\n"
        "  );\n"
        "}\n",
        encoding="utf-8",
    )


def test_tool_registry_exposes_coder_learning_tools(tmp_path: Path, monkeypatch) -> None:
    _fake_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    registry = ToolRegistry(include_builtins=True)

    assert {"web_search", "web_fetch", "repo_search", "skill_base_status"}.issubset(set(registry.names()))
    result = json.loads(registry.execute("repo_search", {"pattern": "run_worker", "directory": "aureon"}))
    assert result["hit_count"] == 1


def test_coding_agent_skill_base_writes_profile_and_mount(tmp_path: Path) -> None:
    _fake_repo(tmp_path)

    result = build_and_write_profile("Teach Aureon coder agents and skills", root=tmp_path, online=False)
    app_text = (tmp_path / "frontend" / "src" / "App.tsx").read_text(encoding="utf-8")

    assert result["schema_version"] == "aureon-coding-agent-skill-base-v2"
    assert result["summary"]["coder_agent_count"] >= 5
    assert result["summary"]["coding_logic_rule_count"] >= 6
    assert result["summary"]["web_tools_ready"] is True
    assert result["write_info"]["writer"] == "QueenCodeArchitect"
    logic_map = result["coding_logic_map"]
    assert logic_map["status"] == "who_what_where_when_how_ready"
    assert {"who:", "what:", "where:", "when:", "how:"}.issubset(
        {item.split()[0] for item in logic_map["decision_loop"]}
    )
    assert "frontend/src/App.tsx" in logic_map["file_area_index"]
    assert (tmp_path / "frontend" / "public" / "aureon_coding_agent_skill_base.json").exists()
    assert (tmp_path / "frontend" / "src" / "components" / "generated" / "AureonCodingAgentSkillBaseConsole.tsx").exists()
    assert "AureonCodingAgentSkillBaseConsole" in app_text
    assert "Who What Where When How" in (
        tmp_path / "frontend" / "src" / "components" / "generated" / "AureonCodingAgentSkillBaseConsole.tsx"
    ).read_text(encoding="utf-8")
    assert "logicMap.status" in (
        tmp_path / "frontend" / "src" / "components" / "generated" / "AureonCodingAgentSkillBaseConsole.tsx"
    ).read_text(encoding="utf-8")


def test_goal_engine_routes_coder_skill_goal(tmp_path: Path, monkeypatch) -> None:
    _fake_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    engine = GoalExecutionEngine()
    plan = engine.submit_goal("Aureon must teach its coder agents the coding skill base and learning workflow.")

    assert plan.status == "completed"
    assert plan.steps[0].intent == "coding_agent_skill_base"
    assert plan.steps[0].validation_result["valid"] is True
    evidence = json.loads((tmp_path / "state" / "aureon_coding_agent_skill_base_last_run.json").read_text(encoding="utf-8"))
    assert evidence["write_info"]["writer"] == "QueenCodeArchitect"
    assert evidence["coding_logic_map"]["status"] == "who_what_where_when_how_ready"


def test_goal_engine_routes_coding_desktop_handoff_goal(tmp_path: Path, monkeypatch) -> None:
    _fake_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    engine = GoalExecutionEngine()
    plan = engine.submit_goal(
        "Aureon must connect the remote desktop run handoff to the coding organism "
        "so the user prompt becomes a finished product audit."
    )

    assert plan.status == "completed"
    assert plan.steps[0].intent == "coding_agent_skill_base"
    assert plan.steps[0].validation_result["valid"] is True


def test_goal_engine_routes_code_builder_terminal_goal(tmp_path: Path, monkeypatch) -> None:
    _fake_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    engine = GoalExecutionEngine()
    plan = engine.submit_goal(
        "Connect Aureon coding systems, inspect the repo, propose the smallest safe patch, "
        "and run focused tests so the code builder terminal works."
    )

    assert plan.status == "completed"
    assert plan.steps[0].intent == "coding_agent_skill_base"
    assert plan.steps[0].validation_result["valid"] is True


def test_goal_engine_routes_visual_asset_prompt_without_agentcore(tmp_path: Path, monkeypatch) -> None:
    _fake_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    engine = GoalExecutionEngine()
    plan = engine.submit_goal("drwaw me a image of a cat and open the file and show me it")

    assert plan.status == "completed"
    assert [step.intent for step in plan.steps] == ["visual_asset_request"]
    assert plan.steps[0].validation_result["valid"] is True
    payload = plan.steps[0].result["result"]
    assert payload["status"] == "visual_asset_ready"
    assert payload["public_url"].startswith("/aureon_visual_artifacts/")
    assert Path(payload["asset_path"]).exists()
    assert "cat" in payload["subject"]
