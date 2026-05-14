"""Trading intelligence freshness checklist.

This module turns the live trading runtime snapshot into a checklist showing
which intelligence and counter-intelligence systems are present, active,
fresh-live, and wired into the HNC/Auris decision path.
"""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Sequence


SCHEMA_VERSION = "aureon-trading-intelligence-checklist-v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_STATUS_PATH = Path("state/unified_runtime_status.json")
DEFAULT_OUTPUT_JSON = REPO_ROOT / "docs/audits/aureon_trading_intelligence_checklist.json"
DEFAULT_OUTPUT_MD = REPO_ROOT / "docs/audits/aureon_trading_intelligence_checklist.md"
DEFAULT_PUBLIC_JSON = REPO_ROOT / "frontend/public/aureon_trading_intelligence_checklist.json"

LIVE_MARKET = "live_market_intelligence"
HNC_AURIS = "hnc_auris_cognition"
COUNTER_INTELLIGENCE = "counter_intelligence_validation"
PROFIT_TIMING = "profit_timing"
RESEARCH_CONTEXT = "research_context_mesh"

HNC_AURIS_NAMES = {"HNCMasterProtocol", "HNCProbabilityMatrix", "Seer", "Lyra", "KingCapitalLogic", "AurisNodes"}
COUNTER_NAMES = {
    "PhantomSignalFilter",
    "ShadowTradeValidator",
    "SelfValidatingPredictor",
    "TruthPredictionEngine",
    "RuntimeWatchdog",
    "APIGovernor",
    "ExchangeRouteClearance",
}
PROFIT_NAMES = {
    "MicroMomentumGoal",
    "PennyProfitEngine",
    "DynamicTakeProfit",
    "TemporalTradeCognition",
    "TorchBearerSystem",
    "RisingStarLogic",
    "ProfitVelocityRanker",
}
RESEARCH_NAMES = {
    "NewsSignal",
    "QueenOnlineResearcher",
    "ResearchCorpusIndex",
    "QueenRepositoryScanner",
    "MinerBrain",
}
LIVE_NAMES = {"LiveExchangeFeeds", "UnifiedSignalEngine", "ModelSignalFeed", "OrcaIntelligence"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path, default: Any) -> Any:
    try:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
        if math.isfinite(number):
            return number
    except Exception:
        pass
    return default


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(_as_float(value, default))
    except Exception:
        return default


def _runtime_stale(runtime: dict[str, Any]) -> bool:
    watchdog = runtime.get("runtime_watchdog") if isinstance(runtime.get("runtime_watchdog"), dict) else {}
    return bool(runtime.get("stale") or watchdog.get("tick_stale"))


def _stale_reason(runtime: dict[str, Any]) -> str:
    watchdog = runtime.get("runtime_watchdog") if isinstance(runtime.get("runtime_watchdog"), dict) else {}
    return str(runtime.get("stale_reason") or watchdog.get("tick_stale_reason") or "runtime_stale")


def _runtime_fresh(runtime: dict[str, Any]) -> bool:
    return bool(runtime.get("data_ready") and not _runtime_stale(runtime))


def _mesh(runtime: dict[str, Any]) -> dict[str, Any]:
    plan = runtime.get("exchange_action_plan") if isinstance(runtime.get("exchange_action_plan"), dict) else {}
    order_flow = runtime.get("order_flow_feed") if isinstance(runtime.get("order_flow_feed"), dict) else {}
    for candidate in (
        runtime.get("intelligence_mesh"),
        plan.get("intelligence_mesh"),
        order_flow.get("intelligence_mesh"),
    ):
        if isinstance(candidate, dict):
            return candidate
    return {}


def _category_for(name: str, facet: str, wire: str) -> str:
    if name in HNC_AURIS_NAMES or wire == "hnc_proof" or facet in {"hnc_harmonic", "harmonic_affect", "oracle_forecast", "capital_logic"}:
        return HNC_AURIS
    if name in COUNTER_NAMES or facet in {"noise_filter", "self_validation", "prediction_truth"}:
        return COUNTER_INTELLIGENCE
    if name in PROFIT_NAMES or facet in {"fast_profit_eta", "exit_logic", "temporal_trade_logic", "fast_strike_strategy", "whole_market_search"}:
        return PROFIT_TIMING
    if name in RESEARCH_NAMES or wire in {"research_context", "sentiment_context"}:
        return RESEARCH_CONTEXT
    if name in LIVE_NAMES or wire in {"direct_live_signal", "model_stack", "thought_bus"} or facet in {"live_market_data", "signal_fusion", "whale_intelligence"}:
        return LIVE_MARKET
    return COUNTER_INTELLIGENCE if wire == "mesh_context" else LIVE_MARKET


def _stage_for(name: str, category: str, wire: str) -> str:
    if name == "AurisNodes":
        return "auris_state"
    if category == HNC_AURIS:
        return "hnc_proof"
    if name == "ShadowTradeValidator" or category == COUNTER_INTELLIGENCE:
        return "shadow_validation" if name in {"ShadowTradeValidator", "PhantomSignalFilter", "SelfValidatingPredictor", "TruthPredictionEngine"} else "exchange_action_plan"
    if category == PROFIT_TIMING:
        return "profit_velocity"
    if wire == "direct_live_signal" or category == LIVE_MARKET:
        return "market_feed"
    return "exchange_action_plan"


def _evidence_timestamp(runtime: dict[str, Any], stage: str, fallback: str) -> str:
    plan = runtime.get("exchange_action_plan") if isinstance(runtime.get("exchange_action_plan"), dict) else {}
    shadow = runtime.get("shadow_trading") if isinstance(runtime.get("shadow_trading"), dict) else {}
    hnc = runtime.get("hnc_cognitive_proof") if isinstance(runtime.get("hnc_cognitive_proof"), dict) else {}
    watchdog = runtime.get("runtime_watchdog") if isinstance(runtime.get("runtime_watchdog"), dict) else {}
    if stage in {"hnc_proof", "auris_state"}:
        return str(hnc.get("generated_at") or fallback)
    if stage == "shadow_validation":
        return str(shadow.get("generated_at") or plan.get("generated_at") or fallback)
    if stage in {"exchange_action_plan", "profit_velocity"}:
        return str(plan.get("generated_at") or fallback)
    return str(watchdog.get("heartbeat_at") or runtime.get("dashboard_generated_at") or fallback)


def _row(
    *,
    name: str,
    facet: str,
    wire: str,
    path: str,
    present: bool,
    active: bool,
    fed: bool,
    runtime: dict[str, Any],
    evidence_source: str,
    stage: str,
    extra_blockers: Optional[list[str]] = None,
) -> dict[str, Any]:
    runtime_fresh = _runtime_fresh(runtime)
    blockers = list(extra_blockers or [])
    if not present:
        blockers.append("repo_path_missing")
    if present and not active:
        blockers.append("not_active_this_cycle")
    if not fed:
        blockers.append("not_wired_to_decision_logic")
    if not runtime_fresh:
        blockers.append(_stale_reason(runtime) if _runtime_stale(runtime) else "runtime_data_not_ready")
    fresh = bool(present and active and runtime_fresh)
    usable = bool(fresh and fed and not blockers)
    category = _category_for(name, facet, wire)
    return {
        "system": name,
        "category": category,
        "facet": facet,
        "wire_path": wire,
        "path": path,
        "evidence_source": evidence_source,
        "last_timestamp": _evidence_timestamp(runtime, stage, utc_now()),
        "present": bool(present),
        "active_this_cycle": bool(active),
        "fresh": fresh,
        "usable_for_decision": usable,
        "fed_to_decision_logic": bool(fed),
        "blocker": ", ".join(dict.fromkeys(blockers)),
        "downstream_stage": stage,
    }


def _capability_rows(runtime: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    mesh = _mesh(runtime)
    capabilities = mesh.get("capabilities") if isinstance(mesh.get("capabilities"), list) else []
    for capability in capabilities:
        if not isinstance(capability, dict):
            continue
        name = str(capability.get("name") or "UnknownSystem")
        facet = str(capability.get("facet") or "uncategorized")
        wire = str(capability.get("wire") or "mesh_context")
        category = _category_for(name, facet, wire)
        stage = _stage_for(name, category, wire)
        active = bool(capability.get("active_this_cycle"))
        fed = bool(active and category in {LIVE_MARKET, HNC_AURIS, COUNTER_INTELLIGENCE, PROFIT_TIMING, RESEARCH_CONTEXT})
        rows.append(
            _row(
                name=name,
                facet=facet,
                wire=wire,
                path=str(capability.get("path") or ""),
                present=bool(capability.get("present")),
                active=active,
                fed=fed,
                runtime=runtime,
                evidence_source=f"state/unified_runtime_status.json#exchange_action_plan.intelligence_mesh.capabilities.{name}",
                stage=stage,
            )
        )
    return rows


def _candidate_has_model_signal(candidate: Any) -> bool:
    return isinstance(candidate, dict) and isinstance(candidate.get("model_signal"), dict) and bool(candidate.get("model_signal"))


def _synthetic_rows(runtime: dict[str, Any]) -> list[dict[str, Any]]:
    plan = runtime.get("exchange_action_plan") if isinstance(runtime.get("exchange_action_plan"), dict) else {}
    shadow = runtime.get("shadow_trading") if isinstance(runtime.get("shadow_trading"), dict) else {}
    hnc = runtime.get("hnc_cognitive_proof") if isinstance(runtime.get("hnc_cognitive_proof"), dict) else {}
    watchdog = runtime.get("runtime_watchdog") if isinstance(runtime.get("runtime_watchdog"), dict) else {}
    governor = runtime.get("api_governor") if isinstance(runtime.get("api_governor"), dict) else {}
    venues = plan.get("venues") if isinstance(plan.get("venues"), dict) else {}
    candidates: list[Any] = []
    for venue in venues.values():
        if isinstance(venue, dict):
            top = venue.get("top_candidates")
            if isinstance(top, list):
                candidates.extend(top)
    ready_venues = _as_int(plan.get("ready_venue_count"))
    venue_count = _as_int(plan.get("venue_count"), len(venues))
    runtime_clearances = plan.get("runtime_clearances") if isinstance(plan.get("runtime_clearances"), list) else []
    model_active = bool(plan.get("model_coverage") or any(_candidate_has_model_signal(item) for item in candidates))
    profit_active = bool(
        "profit_velocity" in str(plan.get("selection_process", {}).get("mode") if isinstance(plan.get("selection_process"), dict) else "")
        or any(isinstance(item, dict) and item.get("profit_velocity_score") is not None for item in candidates)
    )
    auris = hnc.get("auris_nodes") if isinstance(hnc.get("auris_nodes"), dict) else {}
    shadow_active = bool(shadow.get("enabled", True) and (shadow.get("shadow_opened_count") is not None or shadow.get("active_shadow_count") is not None))
    rows = [
        _row(
            name="ModelSignalFeed",
            facet="signal_fusion",
            wire="direct_live_signal",
            path="state/unified_runtime_status.json",
            present=bool(plan),
            active=model_active,
            fed=model_active,
            runtime=runtime,
            evidence_source="state/unified_runtime_status.json#exchange_action_plan.model_coverage/top_candidates",
            stage="market_feed",
        ),
        _row(
            name="AurisNodes",
            facet="sensory_market_texture",
            wire="hnc_proof",
            path="aureon/utils/aureon_queen_hive_mind.py",
            present=bool(auris),
            active=bool(auris.get("evaluated") or auris.get("node_count")),
            fed=bool(auris),
            runtime=runtime,
            evidence_source="state/unified_runtime_status.json#hnc_cognitive_proof.auris_nodes",
            stage="auris_state",
        ),
        _row(
            name="RuntimeWatchdog",
            facet="freshness_truth",
            wire="runtime_watchdog",
            path="state/unified_runtime_status.json",
            present=bool(watchdog),
            active=bool(watchdog.get("heartbeat_alive") or watchdog.get("tick_stale") is not None),
            fed=True,
            runtime=runtime,
            evidence_source="state/unified_runtime_status.json#runtime_watchdog",
            stage="exchange_action_plan",
        ),
        _row(
            name="APIGovernor",
            facet="api_rate_counter_intelligence",
            wire="exchange_action_plan",
            path="state/unified_runtime_status.json",
            present=bool(governor),
            active=bool(governor),
            fed=bool(governor),
            runtime=runtime,
            evidence_source="state/unified_runtime_status.json#api_governor",
            stage="exchange_action_plan",
        ),
        _row(
            name="ExchangeRouteClearance",
            facet="route_validation",
            wire="exchange_action_plan",
            path="state/unified_runtime_status.json",
            present=bool(plan),
            active=bool(venue_count),
            fed=bool(plan),
            runtime=runtime,
            evidence_source="state/unified_runtime_status.json#exchange_action_plan.venues",
            stage="exchange_action_plan",
            extra_blockers=[str(item) for item in runtime_clearances if str(item)] + ([] if ready_venues > 0 else ["no_ready_venues"]),
        ),
        _row(
            name="ProfitVelocityRanker",
            facet="fast_profit_eta",
            wire="profit_context",
            path="aureon/exchanges/unified_market_trader.py",
            present=bool(plan),
            active=profit_active,
            fed=profit_active,
            runtime=runtime,
            evidence_source="state/unified_runtime_status.json#exchange_action_plan.selection_process/top_candidates",
            stage="profit_velocity",
        ),
        _row(
            name="ShadowTradeSelfMeasurement",
            facet="self_validation",
            wire="direct_live_signal",
            path="state/unified_shadow_trade_report.json",
            present=bool(shadow),
            active=shadow_active,
            fed=shadow_active,
            runtime=runtime,
            evidence_source="state/unified_runtime_status.json#shadow_trading",
            stage="shadow_validation",
        ),
    ]
    return rows


def _dedupe_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_name: dict[str, dict[str, Any]] = {}
    for row in rows:
        name = str(row.get("system") or "")
        if not name:
            continue
        existing = by_name.get(name)
        if existing is None or (row.get("active_this_cycle") and not existing.get("active_this_cycle")):
            by_name[name] = row
    return list(by_name.values())


def _summary(rows: list[dict[str, Any]], runtime: dict[str, Any]) -> dict[str, Any]:
    runtime_fresh = _runtime_fresh(runtime)
    categories = {category: [row for row in rows if row.get("category") == category] for category in (LIVE_MARKET, HNC_AURIS, COUNTER_INTELLIGENCE, PROFIT_TIMING, RESEARCH_CONTEXT)}
    fresh_usable = [row for row in rows if row.get("usable_for_decision")]
    stale_or_blocked = [row for row in rows if not row.get("usable_for_decision")]
    decision_fed = [row for row in rows if row.get("fed_to_decision_logic")]
    blockers = [row for row in stale_or_blocked if row.get("blocker")]
    status = "fresh_decision_ready" if runtime_fresh and not blockers else "connected_guarded" if runtime.get("data_ready") else "runtime_data_not_ready"
    return {
        "status": status,
        "runtime_fresh": runtime_fresh,
        "runtime_stale": _runtime_stale(runtime),
        "stale_reason": _stale_reason(runtime) if _runtime_stale(runtime) else "",
        "trading_ready": bool(runtime.get("trading_ready")),
        "data_ready": bool(runtime.get("data_ready")),
        "system_count": len(rows),
        "present_count": sum(1 for row in rows if row.get("present")),
        "active_count": sum(1 for row in rows if row.get("active_this_cycle")),
        "fresh_usable_count": len(fresh_usable),
        "stale_or_blocked_count": len(stale_or_blocked),
        "decision_fed_count": len(decision_fed),
        "direct_live_systems_passing": sum(1 for row in categories[LIVE_MARKET] if row.get("usable_for_decision")),
        "hnc_auris_passing": sum(1 for row in categories[HNC_AURIS] if row.get("usable_for_decision")),
        "counter_intelligence_passing": sum(1 for row in categories[COUNTER_INTELLIGENCE] if row.get("usable_for_decision")),
        "profit_timing_passing": sum(1 for row in categories[PROFIT_TIMING] if row.get("usable_for_decision")),
        "research_context_passing": sum(1 for row in categories[RESEARCH_CONTEXT] if row.get("usable_for_decision")),
        "category_counts": {
            category: {
                "total": len(items),
                "usable": sum(1 for row in items if row.get("usable_for_decision")),
                "fed": sum(1 for row in items if row.get("fed_to_decision_logic")),
            }
            for category, items in categories.items()
        },
        "top_blockers": [
            {
                "system": row.get("system"),
                "category": row.get("category"),
                "blocker": row.get("blocker"),
                "evidence_source": row.get("evidence_source"),
            }
            for row in blockers[:8]
        ],
    }


def build_trading_intelligence_checklist(root: Optional[Path] = None) -> dict[str, Any]:
    root = (root or REPO_ROOT).resolve()
    runtime_rel = RUNTIME_STATUS_PATH
    runtime = _read_json(root / runtime_rel, {})
    if not isinstance(runtime, dict):
        runtime = {}
    rows = _dedupe_rows(_capability_rows(runtime) + _synthetic_rows(runtime))
    summary = _summary(rows, runtime)
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_now(),
        "status": summary["status"],
        "repo_root": str(root),
        "runtime_source": str(runtime_rel).replace("\\", "/"),
        "summary": summary,
        "contract": {
            "freshness_source": "state/unified_runtime_status.json runtime stale/tick truth checks",
            "fed_to_decision_logic": "system evidence is wired into exchange_action_plan, HNC/Auris proof, shadow validation, or profit velocity ranking",
            "usable_for_decision": "present, active, fed, and runtime fresh-live",
            "no_execution_change": "checklist is proof/visibility only and does not loosen live exchange mutation rules",
        },
        "rows": rows,
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    rows = report.get("rows") if isinstance(report.get("rows"), list) else []
    lines = [
        "# Aureon Trading Intelligence Checklist",
        "",
        f"- Generated: {report.get('generated_at', '')}",
        f"- Status: {report.get('status', '')}",
        f"- Runtime fresh: {summary.get('runtime_fresh')}",
        f"- Fresh usable: {summary.get('fresh_usable_count', 0)}/{summary.get('system_count', 0)}",
        f"- Decision fed: {summary.get('decision_fed_count', 0)}",
        f"- Stale reason: {summary.get('stale_reason') or 'none'}",
        "",
        "| System | Category | Stage | Fresh | Usable | Fed | Blocker |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {system} | {category} | {stage} | {fresh} | {usable} | {fed} | {blocker} |".format(
                system=str(row.get("system", "")),
                category=str(row.get("category", "")),
                stage=str(row.get("downstream_stage", "")),
                fresh=str(row.get("fresh", False)),
                usable=str(row.get("usable_for_decision", False)),
                fed=str(row.get("fed_to_decision_logic", False)),
                blocker=str(row.get("blocker", "")).replace("|", "/"),
            )
        )
    lines.append("")
    lines.append("This checklist is evidence-only. It does not place orders, change exchange credentials, or bypass runtime truth checks.")
    return "\n".join(lines) + "\n"


def write_trading_intelligence_checklist(
    report: dict[str, Any],
    output_json: Path = DEFAULT_OUTPUT_JSON,
    output_md: Path = DEFAULT_OUTPUT_MD,
    public_json: Path = DEFAULT_PUBLIC_JSON,
) -> tuple[Path, Path, Path]:
    _write_json(output_json, report)
    _write_json(public_json, report)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(render_markdown(report), encoding="utf-8")
    return output_json, output_md, public_json


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Aureon's trading intelligence freshness checklist.")
    parser.add_argument("--repo-root", default="", help="Repo root; defaults to current Aureon repo.")
    parser.add_argument("--json", default=str(DEFAULT_OUTPUT_JSON), help="Audit JSON path.")
    parser.add_argument("--md", default=str(DEFAULT_OUTPUT_MD), help="Audit Markdown path.")
    parser.add_argument("--public-json", default=str(DEFAULT_PUBLIC_JSON), help="Frontend public JSON path.")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    root = Path(args.repo_root).resolve() if args.repo_root else REPO_ROOT
    report = build_trading_intelligence_checklist(root)
    output_json, output_md, public_json = write_trading_intelligence_checklist(
        report,
        Path(args.json),
        Path(args.md),
        Path(args.public_json),
    )
    print(
        json.dumps(
            {
                "json": str(output_json),
                "md": str(output_md),
                "public_json": str(public_json),
                "summary": report["summary"],
            },
            indent=2,
            sort_keys=True,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
