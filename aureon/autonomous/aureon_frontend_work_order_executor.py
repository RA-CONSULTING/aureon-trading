"""Execute Aureon's frontend evolution work orders as safe adapter records.

This does not import or run legacy dashboards. It converts every work order in
the current queue into a visible execution state:
- ready orders become generated read-only adapter records
- blocked orders become blocker card records
- generated outputs become link card records
- archive candidates become archive decision records
- credential/admin boundaries become safe status adapter records

All artifacts are written through QueenCodeArchitect when available.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Sequence

from aureon.autonomous.aureon_frontend_evolution_queue import build_frontend_evolution_queue
from aureon.autonomous.aureon_saas_system_inventory import repo_root_from

try:
    from aureon.queen.queen_code_architect import QueenCodeArchitect
except Exception:  # pragma: no cover
    QueenCodeArchitect = None  # type: ignore[assignment]


SCHEMA_VERSION = "aureon-frontend-work-order-execution-v1"
DEFAULT_OUTPUT_JSON = Path("docs/audits/aureon_frontend_work_order_execution.json")
DEFAULT_OUTPUT_MD = Path("docs/audits/aureon_frontend_work_order_execution.md")
DEFAULT_PUBLIC_JSON = Path("frontend/public/aureon_frontend_work_order_execution.json")
DEFAULT_STATE_PATH = Path("state/aureon_frontend_work_order_execution_last_run.json")
DEFAULT_COMPONENT = Path("frontend/src/components/generated/AureonWorkOrderExecutionConsole.tsx")
DEFAULT_APP_PATH = Path("frontend/src/App.tsx")


@dataclass
class ExecutedWorkOrder:
    id: str
    title: str
    source_path: str
    target_screen: str
    source_status: str
    execution_status: str
    artifact_type: str
    generated_artifact: str
    safety_boundary: str
    evidence: dict[str, Any] = field(default_factory=dict)
    next_action: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class WorkOrderExecutionReport:
    schema_version: str
    generated_at: str
    repo_root: str
    status: str
    goal: str
    summary: dict[str, Any]
    executions: list[ExecutedWorkOrder]
    generated_files: list[str]
    authoring_path: list[str]
    safety: dict[str, Any]
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "repo_root": self.repo_root,
            "status": self.status,
            "goal": self.goal,
            "summary": dict(self.summary),
            "executions": [item.to_dict() for item in self.executions],
            "generated_files": list(self.generated_files),
            "authoring_path": list(self.authoring_path),
            "safety": dict(self.safety),
            "notes": list(self.notes),
        }


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        return payload if isinstance(payload, dict) else {}
    except Exception as exc:
        return {"error": f"{type(exc).__name__}: {exc}", "path": str(path)}


def _execution_for_order(order: dict[str, Any]) -> ExecutedWorkOrder:
    status = str(order.get("status") or "")
    target = str(order.get("target_screen") or "overview")
    source_path = str(order.get("source_path") or "")
    order_id = str(order.get("id") or source_path)
    safety = str(order.get("safety_boundary") or "Read-only adapter; no external mutation.")
    artifact = f"frontend/public/aureon_frontend_work_order_execution.json#{order_id}"

    if status == "blocked_security_review":
        execution_status = "blocker_card_created"
        artifact_type = "read_only_blocker_card"
        next_action = "Security or live-action owner must clear this boundary before any interactive adapter is generated."
    elif status == "ready_for_frontend_adapter":
        execution_status = "read_only_adapter_record_created"
        artifact_type = "read_only_status_adapter"
        next_action = "Mounted through the generated execution console; promote to a bespoke component only if the source becomes canonical."
    elif status == "needs_safe_status_adapter":
        execution_status = "safe_status_adapter_record_created"
        artifact_type = "credential_safe_status_adapter"
        next_action = "Expose metadata only; keep secret values and privileged actions hidden."
    elif status == "link_generated_output":
        execution_status = "generated_output_link_record_created"
        artifact_type = "evidence_link_card"
        next_action = "Open as evidence output, not as a live system."
    elif status == "archive_candidate":
        execution_status = "archive_decision_recorded"
        artifact_type = "archive_decision"
        next_action = "Keep out of operator navigation unless it gains runtime evidence."
    else:
        execution_status = "watch_record_created"
        artifact_type = "watch_only_record"
        next_action = "Keep visible as inventory until a stronger adapter contract exists."

    return ExecutedWorkOrder(
        id=order_id,
        title=str(order.get("title") or source_path),
        source_path=source_path,
        target_screen=target,
        source_status=status,
        execution_status=execution_status,
        artifact_type=artifact_type,
        generated_artifact=artifact,
        safety_boundary=safety,
        evidence={
            "priority": order.get("priority"),
            "source_kind": order.get("source_kind"),
            "source_domain": order.get("source_domain"),
            "data_contract": order.get("data_contract") or {},
            "frontend_action": order.get("frontend_action"),
            "acceptance_tests": order.get("acceptance_tests") or [],
        },
        next_action=next_action,
    )


def render_component() -> str:
    return r'''import { useEffect, useMemo, useState } from "react";
import { Activity, Archive, CheckCircle2, Lock, ShieldAlert } from "lucide-react";
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

function compact(value: unknown): string {
  const number = Number(value || 0);
  return Number.isFinite(number) ? number.toLocaleString() : String(value || "0");
}

function tone(status: string): string {
  if (status.includes("blocker")) return "border-yellow-500/40 bg-yellow-500/10 text-yellow-100";
  if (status.includes("archive")) return "border-slate-500/40 bg-slate-500/10 text-slate-100";
  if (status.includes("adapter") || status.includes("link")) return "border-green-500/40 bg-green-500/10 text-green-100";
  return "border-border bg-muted/20 text-muted-foreground";
}

function iconFor(status: string) {
  if (status.includes("blocker")) return ShieldAlert;
  if (status.includes("archive")) return Archive;
  if (status.includes("adapter") || status.includes("link")) return CheckCircle2;
  return Activity;
}

export function AureonWorkOrderExecutionConsole() {
  const [report, setReport] = useState<JsonMap>({});

  useEffect(() => {
    let cancelled = false;
    fetchJson("/aureon_frontend_work_order_execution.json").then((payload) => {
      if (!cancelled) setReport(payload);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const executions = Array.isArray(report.executions) ? report.executions : [];
  const summary = report.summary || {};
  const top = useMemo(() => executions.slice(0, 80), [executions]);

  return (
    <Card className="mb-5 bg-card/80">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <Activity className="h-4 w-4 text-primary" />
          Aureon Work Order Execution
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap gap-2">
          <Badge variant="outline" className="border-green-500/40 bg-green-500/10 text-green-100">{report.status || "pending"}</Badge>
          <Badge variant="outline" className="border-border bg-muted/20 text-muted-foreground">updated {report.generated_at ? new Date(report.generated_at).toLocaleTimeString() : "pending"}</Badge>
        </div>
        <div className="grid gap-2 md:grid-cols-5">
          <Stat label="orders executed" value={summary.executed_count} />
          <Stat label="adapters" value={summary.adapter_record_count} />
          <Stat label="blocker cards" value={summary.blocker_card_count} />
          <Stat label="archive decisions" value={summary.archive_decision_count} />
          <Stat label="screens" value={summary.target_screen_count} />
        </div>
        <ScrollArea className="h-[420px] pr-3">
          <div className="space-y-2">
            {top.length ? top.map((item: JsonMap) => {
              const Icon = iconFor(String(item.execution_status || ""));
              return (
                <div key={item.id} className="rounded-md border border-border/40 bg-muted/10 p-3">
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 text-sm font-medium">
                        <Icon className="h-4 w-4 text-primary" />
                        {item.title}
                      </div>
                      <div className="mt-1 truncate font-mono text-[11px] text-muted-foreground">{item.source_path}</div>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      <Badge variant="outline" className={tone(String(item.execution_status || ""))}>{item.execution_status}</Badge>
                      <Badge variant="outline" className="border-border bg-muted/20 text-muted-foreground">{item.target_screen}</Badge>
                    </div>
                  </div>
                  <div className="mt-2 text-xs text-muted-foreground">{item.next_action}</div>
                  <div className="mt-2 text-[11px] text-yellow-100">{item.safety_boundary}</div>
                </div>
              );
            }) : (
              <div className="rounded-md border border-border/40 bg-muted/10 p-4 text-sm text-muted-foreground">No work-order execution manifest loaded.</div>
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

function Stat({ label, value }: { label: string; value: unknown }) {
  return (
    <div className="rounded-md border border-border/40 bg-muted/10 p-3">
      <div className="text-[11px] uppercase text-muted-foreground">{label}</div>
      <div className="mt-1 text-lg font-semibold">{compact(value)}</div>
    </div>
  );
}
'''


def mount_component_in_app(app_text: str) -> tuple[str, bool]:
    """Mount the generated work-order execution console in App.tsx."""

    changed = False
    import_line = 'import { AureonWorkOrderExecutionConsole } from "@/components/generated/AureonWorkOrderExecutionConsole";'
    if import_line not in app_text:
        anchor = 'import { AureonGeneratedOperationalConsole } from "@/components/generated/AureonGeneratedOperationalConsole";'
        if anchor in app_text:
            app_text = app_text.replace(anchor, f"{anchor}\n{import_line}", 1)
            changed = True

    mount_line = "        <AureonWorkOrderExecutionConsole />"
    if mount_line not in app_text:
        anchor = "        <AureonGeneratedOperationalConsole />"
        if anchor in app_text:
            app_text = app_text.replace(anchor, f"{anchor}\n{mount_line}", 1)
            changed = True
    return app_text, changed


def build_report(goal: str, root: Optional[Path] = None) -> WorkOrderExecutionReport:
    repo_root = repo_root_from(root)
    queue_path = repo_root / "docs" / "audits" / "aureon_frontend_evolution_queue.json"
    queue = load_json(queue_path)
    if not queue:
        queue = build_frontend_evolution_queue(repo_root).to_dict()
    work_orders = list(queue.get("work_orders") or [])
    executions = [_execution_for_order(order) for order in work_orders]

    by_execution: dict[str, int] = {}
    by_target: dict[str, int] = {}
    for execution in executions:
        by_execution[execution.execution_status] = by_execution.get(execution.execution_status, 0) + 1
        by_target[execution.target_screen] = by_target.get(execution.target_screen, 0) + 1

    summary = {
        "executed_count": len(executions),
        "source_queue_count": (queue.get("summary") or {}).get("queue_count", len(executions)),
        "adapter_record_count": sum(
            count for status, count in by_execution.items()
            if status in {"read_only_adapter_record_created", "safe_status_adapter_record_created"}
        ),
        "blocker_card_count": by_execution.get("blocker_card_created", 0),
        "generated_output_link_count": by_execution.get("generated_output_link_record_created", 0),
        "archive_decision_count": by_execution.get("archive_decision_recorded", 0),
        "target_screen_count": len(by_target),
        "by_execution_status": dict(sorted(by_execution.items())),
        "by_target_screen": dict(sorted(by_target.items())),
    }
    status = "frontend_work_orders_executed_with_blockers_visible" if summary["blocker_card_count"] else "frontend_work_orders_executed"
    return WorkOrderExecutionReport(
        schema_version=SCHEMA_VERSION,
        generated_at=utc_now(),
        repo_root=str(repo_root),
        status=status,
        goal=goal,
        summary=summary,
        executions=executions,
        generated_files=[
            DEFAULT_OUTPUT_JSON.as_posix(),
            DEFAULT_OUTPUT_MD.as_posix(),
            DEFAULT_PUBLIC_JSON.as_posix(),
            DEFAULT_STATE_PATH.as_posix(),
            DEFAULT_COMPONENT.as_posix(),
            DEFAULT_APP_PATH.as_posix(),
        ],
        authoring_path=[
            "GoalExecutionEngine.submit_goal",
            "GoalExecutionEngine._execute_frontend_work_orders",
            "aureon.autonomous.aureon_frontend_work_order_executor.execute_frontend_work_orders",
            "QueenCodeArchitect.write_file",
        ],
        safety={
            "legacy_systems_executed": False,
            "read_only_adapters": True,
            "secret_values_written": False,
            "live_trading_mutation": False,
            "official_filing_or_payment": False,
        },
        notes=[
            "Every current queue item is represented in an execution manifest.",
            "Blocked security/live-action items are completed as blocker cards, not bypassed.",
            "Ready items are completed through a generated read-only adapter layer.",
        ],
    )


def render_markdown(report: WorkOrderExecutionReport) -> str:
    lines = [
        "# Aureon Frontend Work Order Execution",
        "",
        f"- Generated: `{report.generated_at}`",
        f"- Status: `{report.status}`",
        f"- Goal: {report.goal}",
        "",
        "## Summary",
    ]
    for key, value in report.summary.items():
        if isinstance(value, dict):
            lines.extend([f"- `{key}`:", "  ```json", json.dumps(value, indent=2, sort_keys=True), "  ```"])
        else:
            lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Top Executions"])
    for item in report.executions[:100]:
        lines.append(f"- `{item.execution_status}` `{item.target_screen}` `{item.source_path}`")
    if len(report.executions) > 100:
        lines.append(f"- ... {len(report.executions) - 100} more executions in JSON")
    lines.extend(["", "## Safety"])
    for key, value in report.safety.items():
        lines.append(f"- `{key}`: `{value}`")
    return "\n".join(lines) + "\n"


def write_report(report: WorkOrderExecutionReport, root: Path) -> dict[str, Any]:
    payload = json.dumps(report.to_dict(), indent=2, sort_keys=True, default=str)
    markdown = render_markdown(report)
    component = render_component()
    files = {
        DEFAULT_OUTPUT_JSON.as_posix(): payload,
        DEFAULT_OUTPUT_MD.as_posix(): markdown,
        DEFAULT_PUBLIC_JSON.as_posix(): payload,
        DEFAULT_STATE_PATH.as_posix(): payload,
        DEFAULT_COMPONENT.as_posix(): component,
    }
    app_path = root / DEFAULT_APP_PATH
    if app_path.exists():
        next_app_text, _changed = mount_component_in_app(app_path.read_text(encoding="utf-8", errors="replace"))
        files[DEFAULT_APP_PATH.as_posix()] = next_app_text
    if QueenCodeArchitect is not None:
        queen = QueenCodeArchitect(repo_path=str(root))
        for rel, content in files.items():
            ok = queen.write_file(rel, content, backup=True)
            if not ok:
                raise RuntimeError(f"QueenCodeArchitect refused to write {rel}")
        return {"writer": "QueenCodeArchitect", "created_files": list(getattr(queen, "created_files", []))}
    for rel, content in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return {"writer": "direct_python_fallback", "created_files": list(files)}


def execute_frontend_work_orders(goal: str, *, root: Optional[Path] = None) -> dict[str, Any]:
    repo_root = repo_root_from(root)
    report = build_report(goal, repo_root)
    write_info = write_report(report, repo_root)
    result = report.to_dict()
    result["write_info"] = write_info
    state_payload = json.dumps(result, indent=2, sort_keys=True, default=str)
    if QueenCodeArchitect is not None:
        queen = QueenCodeArchitect(repo_path=str(repo_root))
        ok = queen.write_file(DEFAULT_STATE_PATH.as_posix(), state_payload, backup=True)
        if not ok:
            raise RuntimeError(f"QueenCodeArchitect refused to write {DEFAULT_STATE_PATH.as_posix()}")
    else:
        state_path = repo_root / DEFAULT_STATE_PATH
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(state_payload, encoding="utf-8")
    return result


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Execute Aureon frontend work orders as safe adapter records.")
    parser.add_argument("--repo-root", default="")
    parser.add_argument("--goal", default="Execute Aureon frontend work orders")
    args = parser.parse_args(argv)
    root = Path(args.repo_root).resolve() if args.repo_root else repo_root_from()
    result = execute_frontend_work_orders(args.goal, root=root)
    print(json.dumps({"status": result["status"], "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
