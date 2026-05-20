"""Director-mode capability bridge for Aureon.

This report compares a Codex-class operator/coding agent workflow with the
current Aureon organism. It produces a concrete parity map plus exact Aureon
build orders for anything missing or only partially wired.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Sequence

try:
    from aureon.queen.queen_code_architect import QueenCodeArchitect
except Exception:  # pragma: no cover
    QueenCodeArchitect = None  # type: ignore[assignment]


SCHEMA_VERSION = "aureon-director-capability-bridge-v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STATE_PATH = Path("state/aureon_director_capability_bridge_last_run.json")
DEFAULT_OUTPUT_JSON = Path("docs/audits/aureon_director_capability_bridge.json")
DEFAULT_OUTPUT_MD = Path("docs/audits/aureon_director_capability_bridge.md")
DEFAULT_PUBLIC_JSON = Path("frontend/public/aureon_director_capability_bridge.json")
DEFAULT_COMPONENT = Path("frontend/src/components/generated/AureonDirectorCapabilityBridgeConsole.tsx")
DEFAULT_APP_PATH = Path("frontend/src/App.tsx")


CODEX_CLASS_CAPABILITIES: list[dict[str, Any]] = [
    {
        "id": "prompt_goal_routing",
        "title": "Prompt intake and goal routing",
        "codex_can": "Take a natural-language operator prompt, infer the task, and choose a route.",
        "aureon_surfaces": [
            "aureon/autonomous/aureon_mind_thought_action_hub.py",
            "aureon/core/goal_execution_engine.py",
            "aureon/autonomous/aureon_coding_organism_bridge.py",
        ],
        "bridge_prompt": "Aureon must strengthen prompt intake so every operator request produces a typed goal, route, owner, and evidence packet before execution.",
    },
    {
        "id": "planning_and_decomposition",
        "title": "Planning and decomposition",
        "codex_can": "Break broad work into ordered steps with acceptance criteria.",
        "aureon_surfaces": [
            "aureon/core/goal_execution_engine.py",
            "aureon/core/organism_contracts.py",
            "aureon/autonomous/aureon_goal_capability_map.py",
        ],
        "bridge_prompt": "Aureon must expand its planner so every complex prompt becomes a plan with dependencies, blockers, tests, and exact next actions.",
    },
    {
        "id": "repo_cartography",
        "title": "Repo cartography and file reading",
        "codex_can": "Search, inspect, and understand a large repo before changing it.",
        "aureon_surfaces": [
            "aureon/autonomous/aureon_repo_explorer_service.py",
            "aureon/autonomous/aureon_repo_self_catalog.py",
            "aureon/autonomous/aureon_coding_agent_skill_base.py",
        ],
        "bridge_prompt": "Aureon must make repo cartography available to every coding route with path ownership, dependency hints, and test discovery.",
    },
    {
        "id": "safe_code_authoring",
        "title": "Safe code authoring",
        "codex_can": "Patch files, keep diffs scoped, and avoid reverting unrelated work.",
        "aureon_surfaces": [
            "aureon/autonomous/aureon_safe_code_control.py",
            "aureon/autonomous/aureon_queen_code_bridge.py",
            "aureon/code_architect/architect.py",
        ],
        "bridge_prompt": "Aureon must turn safe code proposals into a patch-authoring lane with diff summaries, ownership checks, and retest requirements.",
    },
    {
        "id": "test_and_build_verification",
        "title": "Test and build verification",
        "codex_can": "Run focused tests, frontend builds, and smoke checks after changes.",
        "aureon_surfaces": [
            "aureon/autonomous/aureon_coding_organism_bridge.py",
            "aureon/autonomous/aureon_repo_self_repair.py",
            "tests/test_aureon_coding_organism_bridge.py",
        ],
        "bridge_prompt": "Aureon must attach focused test, build, and smoke commands to every code work order and publish pass/fail evidence.",
    },
    {
        "id": "browser_visual_smoke",
        "title": "Browser and visual smoke checks",
        "codex_can": "Open a local UI, inspect rendered content, and catch runtime browser errors.",
        "aureon_surfaces": [
            "aureon/autonomous/vm_control/tools.py",
            "aureon/autonomous/aureon_safe_desktop_control.py",
            "frontend/src/components/generated/AureonCodingOrganismConsole.tsx",
        ],
        "expected_future_surface": "aureon/autonomous/aureon_browser_smoke_bridge.py",
        "bridge_prompt": "Aureon must build a browser smoke bridge that opens local console URLs, checks visible text, captures console errors, and writes evidence without external mutation.",
    },
    {
        "id": "desktop_remote_handoff",
        "title": "Desktop and remote run handoff",
        "codex_can": "Use desktop/VM actions to inspect, click, type, run, and verify a finished product.",
        "aureon_surfaces": [
            "aureon/autonomous/aureon_safe_desktop_control.py",
            "aureon/autonomous/vm_control/tools.py",
            "aureon/autonomous/aureon_coding_organism_bridge.py",
        ],
        "bridge_prompt": "Aureon must keep desktop run handoff attached to finished-product audit with dry-run default and explicit arm/disarm state.",
    },
    {
        "id": "documents_and_pdfs",
        "title": "Documents and PDFs",
        "codex_can": "Create and edit document artifacts, render/verify documents, and produce human-readable reports.",
        "aureon_surfaces": [
            "aureon/autonomous/aureon_external_capability_bridge.py",
            "aureon/core/goal_execution_engine.py",
            "docs/audits",
        ],
        "bridge_prompt": "Aureon must route document and PDF requests through a typed artifact contract with source paths, output paths, verification, and manual filing/payment boundaries.",
    },
    {
        "id": "image_generation",
        "title": "Image generation",
        "codex_can": "Generate bitmap visuals or edit images when requested.",
        "aureon_surfaces": [
            "aureon/autonomous/aureon_external_capability_bridge.py",
            "frontend/public",
            "docs/audits",
        ],
        "bridge_prompt": "Aureon must route image generation through a prompt contract and asset registry, treating visuals as presentation assets rather than hidden evidence.",
    },
    {
        "id": "automations",
        "title": "Automations",
        "codex_can": "Create reminders, monitors, and recurring follow-ups where supported.",
        "aureon_surfaces": [
            "aureon/autonomous/aureon_external_capability_bridge.py",
            "aureon/autonomous/aureon_local_task_queue.py",
            "docs/audits",
        ],
        "bridge_prompt": "Aureon must record automation handoff contracts with self-contained prompts, schedule text, destination, status, and operator/app scheduler activation boundaries.",
    },
    {
        "id": "web_learning",
        "title": "Web and official-doc learning",
        "codex_can": "Search and read official sources when local knowledge is not enough.",
        "aureon_surfaces": [
            "aureon/inhouse_ai/tool_registry.py",
            "aureon/autonomous/aureon_coding_agent_skill_base.py",
            "aureon/core/goal_execution_engine.py",
        ],
        "bridge_prompt": "Aureon must route coding agents through official docs and source-linked web learning before writing unfamiliar code.",
    },
    {
        "id": "evidence_publication",
        "title": "Evidence publication",
        "codex_can": "Explain what changed, where, why, and how it was verified.",
        "aureon_surfaces": [
            "docs/audits",
            "frontend/public",
            "aureon/autonomous/aureon_coding_organism_bridge.py",
        ],
        "bridge_prompt": "Aureon must publish every finished task into state, docs/audits, frontend/public, and a console panel with no hidden claims.",
    },
    {
        "id": "frontend_console_integration",
        "title": "Frontend console integration",
        "codex_can": "Add a visible UI panel for new runtime evidence.",
        "aureon_surfaces": [
            "frontend/src/App.tsx",
            "frontend/src/components/generated/AureonCodingOrganismConsole.tsx",
            "aureon/autonomous/aureon_frontend_work_order_executor.py",
        ],
        "bridge_prompt": "Aureon must generate and mount console panels for every new evidence artifact it creates.",
    },
    {
        "id": "parallel_agent_work",
        "title": "Parallel agent work and ownership",
        "codex_can": "Split work across agents with disjoint ownership and integrate results.",
        "aureon_surfaces": [
            "aureon/inhouse_ai/orchestrator.py",
            "aureon/core/goal_execution_engine.py",
            "aureon/autonomous/aureon_coding_agent_skill_base.py",
        ],
        "expected_future_surface": "aureon/autonomous/aureon_coder_swarm_director.py",
        "bridge_prompt": "Aureon must build a coder swarm director that assigns disjoint file ownership, runs workers, prevents conflicting edits, and merges evidence.",
    },
    {
        "id": "git_release_flow",
        "title": "Git release and publish flow",
        "codex_can": "Review dirty files, avoid secrets, commit scoped changes, and push to the main branch when asked.",
        "aureon_surfaces": [
            ".git",
            "README.md",
        ],
        "expected_future_surface": "aureon/autonomous/aureon_git_release_bridge.py",
        "bridge_prompt": "Aureon must build a git release bridge that classifies dirty files, excludes runtime/private state, scans for secrets, proposes a commit, and only pushes when explicitly requested.",
    },
    {
        "id": "operator_clarification",
        "title": "Clarification and assumption handling",
        "codex_can": "Ask concise questions only when needed and otherwise proceed with safe assumptions.",
        "aureon_surfaces": [
            "aureon/autonomous/aureon_mind_thought_action_hub.py",
            "aureon/vault/voice/whole_knowledge_voice.py",
            "aureon/core/organism_contracts.py",
        ],
        "expected_future_surface": "aureon/autonomous/aureon_clarification_contracts.py",
        "bridge_prompt": "Aureon must build a clarification contract layer that records assumptions, asks only blocking questions, and resumes execution after the operator answers.",
    },
    {
        "id": "long_running_supervision",
        "title": "Long-running supervision",
        "codex_can": "Keep processes alive, watch logs, and report status without losing the task.",
        "aureon_surfaces": [
            "AUREON_PRODUCTION_LIVE.cmd",
            "AUREON_WAKE_UP_FULL_AUTONOMOUS.ps1",
            "AUREON_DATA_OCEAN.cmd",
        ],
        "bridge_prompt": "Aureon must keep supervisor state, task state, and runtime health tied together so long-running work can resume cleanly.",
    },
    {
        "id": "docs_and_runbooks",
        "title": "Docs and runbooks",
        "codex_can": "Update README, runbooks, and capability docs with current paths and commands.",
        "aureon_surfaces": [
            "README.md",
            "RUNNING.md",
            "QUICK_START.md",
            "CAPABILITIES.md",
        ],
        "bridge_prompt": "Aureon must update public docs automatically after validated system changes, while keeping private state and secrets out.",
    },
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_root() -> Path:
    cwd = Path.cwd().resolve()
    if (cwd / "frontend").exists() or (cwd / "aureon").exists() or (cwd / "README.md").exists():
        return cwd
    return REPO_ROOT


def _rooted(root: Path, path: str | Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else root / candidate


def _exists(root: Path, path: str) -> bool:
    return _rooted(root, path).exists()


def _write_text_with_queen(root: Path, rel_path: Path, content: str) -> dict[str, Any]:
    rel = str(rel_path).replace("\\", "/")
    if QueenCodeArchitect is not None:
        queen = QueenCodeArchitect(repo_path=str(root))
        ok = queen.write_file(rel, content, backup=True)
        return {"path": rel, "ok": bool(ok), "writer": "QueenCodeArchitect"}
    target = _rooted(root, rel_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return {"path": rel, "ok": True, "writer": "direct_fallback"}


def _write_json_with_queen(root: Path, rel_path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    return _write_text_with_queen(root, rel_path, json.dumps(payload, indent=2, sort_keys=True, default=str))


def _capability_row(root: Path, capability: dict[str, Any]) -> dict[str, Any]:
    surfaces = []
    for surface in capability.get("aureon_surfaces", []):
        surfaces.append(
            {
                "path": surface,
                "present": _exists(root, surface),
                "role": "current_surface",
            }
        )
    future = capability.get("expected_future_surface")
    if future:
        surfaces.append({"path": future, "present": _exists(root, future), "role": "expected_future_surface"})

    required_count = len([item for item in surfaces if item["role"] == "current_surface"])
    present_required = len([item for item in surfaces if item["role"] == "current_surface" and item["present"]])
    future_ready = bool(future) and _exists(root, future)
    if required_count and present_required == required_count and (not future or future_ready):
        status = "ready"
    elif present_required:
        status = "partial"
    else:
        status = "gap"

    blockers = []
    for item in surfaces:
        if not item["present"]:
            blockers.append(f"missing:{item['path']}")
    return {
        "id": capability["id"],
        "title": capability["title"],
        "codex_can": capability["codex_can"],
        "status": status,
        "coverage_ratio": round(present_required / max(required_count, 1), 3),
        "surfaces": surfaces,
        "blockers": blockers,
        "bridge_prompt": capability["bridge_prompt"],
    }


def _work_order(row: dict[str, Any], index: int) -> dict[str, Any]:
    priority = 100 if row["status"] == "gap" else 80
    return {
        "id": f"director_bridge_{index:03d}_{row['id']}",
        "title": f"Bridge {row['title']}",
        "priority": priority,
        "status": "queued_for_aureon_coding_organism",
        "capability_id": row["id"],
        "reason": "; ".join(row.get("blockers") or ["partial coverage"]),
        "exact_aureon_prompt": row["bridge_prompt"],
        "route": "aureon.autonomous.aureon_coding_organism_bridge.submit_coding_prompt",
        "acceptance_criteria": [
            "Aureon writes or updates the missing bridge code through QueenCodeArchitect or SafeCodeControl evidence.",
            "Focused pytest/build checks pass.",
            "state, docs/audits, frontend/public, and console evidence are updated.",
            "No credential values, private runtime state, payments, filings, or live exchange mutation are introduced.",
        ],
    }


def _probe_runtime_tools() -> dict[str, Any]:
    tools: dict[str, Any] = {"vm_tools": {"available": False, "tool_count": 0}, "tool_registry": {}}
    try:
        from aureon.autonomous.vm_control.tools import VM_TOOL_NAMES

        tools["vm_tools"] = {"available": True, "tool_count": len(VM_TOOL_NAMES), "tools": list(VM_TOOL_NAMES)}
    except Exception as exc:
        tools["vm_tools"] = {"available": False, "tool_count": 0, "error": str(exc)}
    try:
        from aureon.inhouse_ai.tool_registry import ToolRegistry

        registry = ToolRegistry(include_builtins=True)
        names = sorted(registry.names())
        tools["tool_registry"] = {
            "available": True,
            "tool_count": len(names),
            "required_present": {
                "web_search": "web_search" in names,
                "web_fetch": "web_fetch" in names,
                "repo_search": "repo_search" in names,
                "execute_shell": "execute_shell" in names,
            },
            "tools": names,
        }
    except Exception as exc:
        tools["tool_registry"] = {"available": False, "tool_count": 0, "error": str(exc)}
    return tools


def build_director_capability_bridge(goal: str, *, root: Optional[Path] = None) -> dict[str, Any]:
    root = Path(root or _default_root()).resolve()
    rows = [_capability_row(root, capability) for capability in CODEX_CLASS_CAPABILITIES]
    work_orders = [
        _work_order(row, index)
        for index, row in enumerate(rows, 1)
        if row["status"] in {"gap", "partial"}
    ]
    status_counts = {status: len([row for row in rows if row["status"] == status]) for status in ("ready", "partial", "gap")}
    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_now(),
        "status": "director_capability_bridge_ready" if not status_counts["gap"] else "director_capability_bridge_ready_with_gaps",
        "goal": goal,
        "summary": {
            "capability_count": len(rows),
            "ready_count": status_counts["ready"],
            "partial_count": status_counts["partial"],
            "gap_count": status_counts["gap"],
            "bridge_work_order_count": len(work_orders),
            "coverage_percent": round((status_counts["ready"] / max(len(rows), 1)) * 100, 2),
        },
        "director_mode": {
            "role": "Codex directs the capability target; Aureon writes the bridge work through its own coding organism.",
            "rule": "Anything not ready becomes an exact Aureon build prompt with tests and evidence requirements.",
            "no_private_state": True,
        },
        "codex_class_capabilities": rows,
        "aureon_bridge_work_orders": work_orders,
        "runtime_tool_probe": _probe_runtime_tools(),
        "authoring_path": [
            "GoalExecutionEngine.submit_goal",
            "GoalExecutionEngine._execute_director_capability_bridge",
            "aureon.autonomous.aureon_director_capability_bridge.build_and_write_director_capability_bridge",
            "QueenCodeArchitect.write_file",
        ],
    }
    return report


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Aureon Director Capability Bridge",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Status: `{report.get('status')}`",
        f"- Goal: {report.get('goal')}",
        "",
        "## Summary",
        "",
    ]
    for key, value in (report.get("summary") or {}).items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Capability Parity", ""])
    for row in report.get("codex_class_capabilities") or []:
        lines.append(f"- `{row['status']}` `{row['id']}`: {row['title']}")
    lines.extend(["", "## Aureon Bridge Work Orders", ""])
    for order in report.get("aureon_bridge_work_orders") or []:
        lines.append(f"- P{order['priority']} `{order['id']}`: {order['exact_aureon_prompt']}")
    return "\n".join(lines) + "\n"


def component_source() -> str:
    return r'''import { useEffect, useState } from "react";
import { BrainCircuit, GitBranch, Hammer, ShieldCheck } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";

type JsonMap = Record<string, any>;

async function fetchJson(url: string): Promise<JsonMap> {
  try {
    const response = await fetch(url, { cache: "no-store" });
    if (!response.ok) return {};
    return await response.json();
  } catch {
    return {};
  }
}

function fmt(value: unknown): string {
  const number = Number(value || 0);
  return Number.isFinite(number) ? number.toLocaleString() : String(value || "0");
}

export function AureonDirectorCapabilityBridgeConsole() {
  const [report, setReport] = useState<JsonMap>({});

  useEffect(() => {
    const refresh = async () => setReport(await fetchJson("/aureon_director_capability_bridge.json"));
    refresh();
    const timer = window.setInterval(refresh, 20000);
    return () => window.clearInterval(timer);
  }, []);

  const summary = report.summary || {};
  const rows = Array.isArray(report.codex_class_capabilities) ? report.codex_class_capabilities : [];
  const orders = Array.isArray(report.aureon_bridge_work_orders) ? report.aureon_bridge_work_orders : [];

  return (
    <Card className="mb-5 bg-card/80">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <BrainCircuit className="h-4 w-4 text-primary" />
          Aureon Director Capability Bridge
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap gap-2">
          <Badge variant={summary.gap_count ? "warning" : "success"}>{report.status || "waiting"}</Badge>
          <Badge variant="outline">coverage {fmt(summary.coverage_percent)}%</Badge>
          <Badge variant="outline">work orders {fmt(summary.bridge_work_order_count)}</Badge>
          <Badge variant="outline">updated {report.generated_at ? new Date(report.generated_at).toLocaleTimeString() : "pending"}</Badge>
        </div>

        <div className="grid gap-2 md:grid-cols-4">
          <Metric icon={ShieldCheck} label="ready" value={summary.ready_count || 0} />
          <Metric icon={Hammer} label="partial" value={summary.partial_count || 0} />
          <Metric icon={GitBranch} label="gaps" value={summary.gap_count || 0} />
          <Metric icon={BrainCircuit} label="capabilities" value={summary.capability_count || 0} />
        </div>

        <div className="grid gap-3 lg:grid-cols-[1fr_1fr]">
          <ScrollArea className="h-[340px] pr-3">
            <div className="space-y-2">
              {rows.map((row: JsonMap) => (
                <div key={row.id} className="rounded-md border border-border/40 bg-muted/10 p-3">
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div>
                      <div className="text-sm font-medium">{row.title}</div>
                      <div className="mt-1 text-xs text-muted-foreground">{row.codex_can}</div>
                    </div>
                    <Badge variant={row.status === "ready" ? "success" : row.status === "gap" ? "warning" : "outline"}>
                      {row.status}
                    </Badge>
                  </div>
                  <div className="mt-2 truncate font-mono text-[10px] text-muted-foreground">
                    {(row.blockers || []).join(" | ") || "all required surfaces present"}
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>

          <ScrollArea className="h-[340px] pr-3">
            <div className="space-y-2">
              {orders.map((order: JsonMap) => (
                <div key={order.id} className="rounded-md border border-yellow-500/30 bg-yellow-500/10 p-3">
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div className="text-sm font-medium">{order.title}</div>
                    <Badge variant="outline">P{order.priority}</Badge>
                  </div>
                  <div className="mt-2 text-xs text-yellow-50">{order.exact_aureon_prompt}</div>
                  <div className="mt-2 truncate font-mono text-[10px] text-muted-foreground">{order.route}</div>
                </div>
              ))}
              {!orders.length ? (
                <div className="rounded-md border border-green-500/30 bg-green-500/10 p-4 text-sm text-green-100">
                  No bridge gaps detected.
                </div>
              ) : null}
            </div>
          </ScrollArea>
        </div>
      </CardContent>
    </Card>
  );
}

function Metric({ icon: Icon, label, value }: { icon: any; label: string; value: unknown }) {
  return (
    <div className="rounded-md border border-border/40 bg-muted/10 p-3">
      <div className="flex items-center gap-2 text-[11px] uppercase text-muted-foreground">
        <Icon className="h-3.5 w-3.5" />
        {label}
      </div>
      <div className="mt-1 text-lg font-semibold">{fmt(value)}</div>
    </div>
  );
}
'''


def _mount_component(app_text: str) -> str:
    import_line = 'import { AureonDirectorCapabilityBridgeConsole } from "@/components/generated/AureonDirectorCapabilityBridgeConsole";'
    mount_line = "        <AureonDirectorCapabilityBridgeConsole />"
    if import_line not in app_text:
        anchor = 'import { AureonCodingOrganismConsole } from "@/components/generated/AureonCodingOrganismConsole";'
        app_text = app_text.replace(anchor, f"{anchor}\n{import_line}", 1) if anchor in app_text else f"{import_line}\n{app_text}"
    if mount_line not in app_text:
        anchor = "        <AureonCodingOrganismConsole />"
        app_text = app_text.replace(anchor, f"{anchor}\n{mount_line}", 1) if anchor in app_text else app_text
    return app_text


def build_and_write_director_capability_bridge(goal: str, *, root: Optional[Path] = None) -> dict[str, Any]:
    root = Path(root or _default_root()).resolve()
    report = build_director_capability_bridge(goal, root=root)
    write_info = {
        "writer": "QueenCodeArchitect" if QueenCodeArchitect is not None else "direct_fallback",
        "files": [
            _write_json_with_queen(root, DEFAULT_OUTPUT_JSON, report),
            _write_text_with_queen(root, DEFAULT_OUTPUT_MD, render_markdown(report)),
            _write_json_with_queen(root, DEFAULT_PUBLIC_JSON, report),
            _write_json_with_queen(root, DEFAULT_STATE_PATH, report),
            _write_text_with_queen(root, DEFAULT_COMPONENT, component_source()),
        ],
    }
    app_path = _rooted(root, DEFAULT_APP_PATH)
    if app_path.exists():
        write_info["files"].append(_write_text_with_queen(root, DEFAULT_APP_PATH, _mount_component(app_path.read_text(encoding="utf-8"))))
    report["write_info"] = write_info
    for rel_path in (DEFAULT_OUTPUT_JSON, DEFAULT_PUBLIC_JSON, DEFAULT_STATE_PATH):
        _write_json_with_queen(root, rel_path, report)
    return report


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build Aureon's director capability bridge.")
    parser.add_argument("--goal", default="Map Codex-class capability parity and bridge Aureon gaps.")
    parser.add_argument("--json", action="store_true", help="Print compact JSON instead of writing only.")
    args = parser.parse_args(argv)
    report = build_and_write_director_capability_bridge(args.goal)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
