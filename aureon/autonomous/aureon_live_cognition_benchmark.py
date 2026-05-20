"""Read-only live benchmark for Aureon's trading cognition path.

The benchmark measures local runtime/cognition/HNC signal latency and health.
It never places orders, cancels orders, changes exchange state, or bypasses
runtime gates. Its purpose is to prove how quickly the system can observe,
score, guard, and publish trading cognition under the current live supervisor.
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional, Sequence

from aureon.autonomous.aureon_cognitive_trade_evidence import build_cognitive_trade_state
from aureon.autonomous.aureon_harmonic_affect_state import build_harmonic_affect_state
from aureon.autonomous.aureon_organism_runtime_observer import build_organism_runtime_status
from aureon.queen.hnc_human_loop import (
    HNCHumanLoop,
    build_phi_ladder,
    build_phi_prime_train,
    compute_vibration_accumulator,
)
from aureon.trading.composite_signal import score as composite_score
from aureon.trading.unified_signal_engine import UnifiedSignalEngine


SCHEMA_VERSION = "aureon-live-cognition-benchmark-v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_JSON = REPO_ROOT / "docs/audits/aureon_live_cognition_benchmark.json"
DEFAULT_OUTPUT_MD = REPO_ROOT / "docs/audits/aureon_live_cognition_benchmark.md"
DEFAULT_PUBLIC_JSON = REPO_ROOT / "frontend/public/aureon_live_cognition_benchmark.json"


@dataclass
class SyntheticOpportunity:
    symbol: str
    exchange: str
    price: float
    change_pct: float
    momentum_score: float
    volume_24h: float = 100000.0


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path, default: Any) -> Any:
    try:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _as_number(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
        if number == number and number not in {float("inf"), float("-inf")}:
            return number
    except Exception:
        pass
    return default


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * pct))))
    return ordered[index]


def latency_stats(samples_ms: list[float]) -> dict[str, Any]:
    if not samples_ms:
        return {
            "samples": 0,
            "ok": False,
            "mean_ms": None,
            "p50_ms": None,
            "p95_ms": None,
            "min_ms": None,
            "max_ms": None,
            "throughput_per_sec": 0.0,
        }
    total_sec = sum(samples_ms) / 1000.0
    return {
        "samples": len(samples_ms),
        "ok": True,
        "mean_ms": round(statistics.mean(samples_ms), 3),
        "p50_ms": round(_percentile(samples_ms, 0.50), 3),
        "p95_ms": round(_percentile(samples_ms, 0.95), 3),
        "min_ms": round(min(samples_ms), 3),
        "max_ms": round(max(samples_ms), 3),
        "throughput_per_sec": round(len(samples_ms) / total_sec, 3) if total_sec > 0 else 0.0,
    }


def fetch_json(url: str, timeout_seconds: float = 2.0) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        data = response.read()
    payload = json.loads(data.decode("utf-8", errors="replace"))
    return payload if isinstance(payload, dict) else {"payload": payload}


def time_call(fn: Callable[[], Any]) -> tuple[float, Any, Optional[str]]:
    start = time.perf_counter()
    try:
        value = fn()
        return (time.perf_counter() - start) * 1000.0, value, None
    except Exception as exc:
        return (time.perf_counter() - start) * 1000.0, None, str(exc)


def benchmark_callable(
    label: str,
    fn: Callable[[], Any],
    *,
    samples: int,
    pause_seconds: float = 0.0,
) -> dict[str, Any]:
    durations: list[float] = []
    errors: list[str] = []
    last_value: Any = None
    for _ in range(max(1, samples)):
        duration_ms, value, error = time_call(fn)
        durations.append(duration_ms)
        if error:
            errors.append(error)
        else:
            last_value = value
        if pause_seconds > 0:
            time.sleep(pause_seconds)
    stats = latency_stats(durations)
    stats.update(
        {
            "label": label,
            "error_count": len(errors),
            "errors": errors[:3],
            "success_count": max(0, len(durations) - len(errors)),
            "last_value_type": type(last_value).__name__ if last_value is not None else "none",
        }
    )
    stats["ok"] = stats["ok"] and not errors
    return stats


def benchmark_endpoint(label: str, url: str, *, samples: int) -> dict[str, Any]:
    result = benchmark_callable(label, lambda: fetch_json(url), samples=samples, pause_seconds=0.05)
    result["url"] = url
    try:
        payload = fetch_json(url)
    except Exception as exc:
        payload = {"error": str(exc)}
    result["payload_summary"] = summarize_payload(payload)
    return result


def summarize_payload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {"type": type(payload).__name__}
    runtime_watchdog = payload.get("runtime_watchdog") if isinstance(payload.get("runtime_watchdog"), dict) else {}
    combined = payload.get("combined") if isinstance(payload.get("combined"), dict) else {}
    checks = payload.get("checks") if isinstance(payload.get("checks"), dict) else {}
    advice = payload.get("reboot_advice") if isinstance(payload.get("reboot_advice"), dict) else {}
    return {
        "ok": payload.get("ok"),
        "status": payload.get("status"),
        "runtime_ok": checks.get("runtime_ok"),
        "tick_fresh": checks.get("tick_fresh"),
        "downtime_window": checks.get("downtime_window"),
        "heartbeat_fresh_but_tick_stale": checks.get("heartbeat_fresh_but_tick_stale"),
        "trading_ready": payload.get("trading_ready"),
        "data_ready": payload.get("data_ready"),
        "stale": payload.get("stale"),
        "stale_reason": payload.get("stale_reason") or runtime_watchdog.get("tick_stale_reason"),
        "open_positions": combined.get("open_positions") or checks.get("open_positions"),
        "can_reboot_now": advice.get("can_reboot_now"),
        "reboot_decision": advice.get("decision"),
    }


def manifest_urls(root: Path) -> dict[str, str]:
    manifest = _read_json(root / "frontend/public/aureon_wake_up_manifest.json", {})
    if not isinstance(manifest, dict) or not manifest.get("runtime_feed_url"):
        manifest = _read_json(root / "state/aureon_wake_up_manifest.json", {})
    feed_url = str((manifest if isinstance(manifest, dict) else {}).get("runtime_feed_url") or "http://127.0.0.1:8791/api/terminal-state")
    return {
        "runtime_feed_url": feed_url,
        "runtime_flight_test_url": str((manifest if isinstance(manifest, dict) else {}).get("runtime_flight_test_url") or feed_url.replace("/api/terminal-state", "/api/flight-test")),
        "runtime_reboot_advice_url": str((manifest if isinstance(manifest, dict) else {}).get("runtime_reboot_advice_url") or feed_url.replace("/api/terminal-state", "/api/reboot-advice")),
        "mind_thoughts_url": "http://127.0.0.1:13002/api/thoughts",
    }


def synthetic_opportunities() -> list[SyntheticOpportunity]:
    return [
        SyntheticOpportunity("BTC/USD", "kraken", 64000.0, 0.24, 0.68),
        SyntheticOpportunity("ETH/USD", "kraken", 3100.0, 0.19, 0.62),
        SyntheticOpportunity("SOL/USD", "binance", 152.0, -0.12, 0.44),
        SyntheticOpportunity("EURUSD", "capital", 1.081, 0.05, 0.55),
        SyntheticOpportunity("US500", "capital", 5260.0, -0.08, 0.46),
        SyntheticOpportunity("AAPL", "alpaca", 189.0, 0.14, 0.58),
    ]


def benchmark_signal_algorithms(samples: int) -> dict[str, Any]:
    engine = UnifiedSignalEngine()
    opportunities = synthetic_opportunities()
    hnc_loop = HNCHumanLoop()
    phrase = "live market signal coherence hnc harmonic risk gate profit verification"
    return {
        "composite_score": benchmark_callable(
            "composite score",
            lambda: composite_score("EURUSD", 0.12, 1.0800, 1.0802, 1.0830, 1.0785, 1.0801, 180000.0),
            samples=samples,
        ),
        "unified_signal_engine": benchmark_callable(
            "unified signal engine",
            lambda: engine.process(
                opportunities,
                regime="MILD_RISK_ON",
                category_moves={"crypto": 0.17, "forex": 0.03, "index": -0.05, "stock": 0.11},
                harp_boosts={"BTC": 0.62, "ETH": 0.51, "EURUSD": 0.28},
                news_sentiment={"crypto": 0.18, "forex": -0.04, "stock": 0.08},
                macro_score=0.4,
                fear_greed=59,
                geo_risk_level="NORMAL",
            ),
            samples=samples,
        ),
        "hnc_phi_prime_train": benchmark_callable(
            "HNC phi prime train",
            lambda: build_phi_prime_train(13),
            samples=samples,
        ),
        "hnc_phi_ladder": benchmark_callable(
            "HNC phi ladder",
            lambda: build_phi_ladder(7.83),
            samples=samples,
        ),
        "hnc_vibration_accumulator": benchmark_callable(
            "HNC vibration accumulator",
            lambda: compute_vibration_accumulator(phrase),
            samples=samples,
        ),
        "hnc_human_loop": benchmark_callable(
            "HNC human loop",
            lambda: hnc_loop.process("benchmark live trading cognition signal readiness"),
            samples=max(1, min(samples, 10)),
        ),
    }


def api_governor_summary(runtime: dict[str, Any]) -> dict[str, Any]:
    governor = runtime.get("api_governor") if isinstance(runtime.get("api_governor"), dict) else {}
    exchanges = governor.get("exchanges") if isinstance(governor.get("exchanges"), dict) else {}
    rows: dict[str, Any] = {}
    for name, state in exchanges.items():
        if not isinstance(state, dict):
            continue
        rows[name] = {
            "max_calls_per_min": state.get("max_calls_per_min"),
            "recent_calls_60s": state.get("recent_calls_60s"),
            "utilization": state.get("utilization"),
            "processed": state.get("processed"),
            "skipped": state.get("skipped"),
            "cache_hits": state.get("cache_hits"),
            "errors": state.get("errors"),
            "last_error": state.get("last_error"),
        }
    return rows


def build_benchmark(root: Optional[Path] = None, *, endpoint_samples: int = 8, local_samples: int = 100) -> dict[str, Any]:
    root = (root or REPO_ROOT).resolve()
    urls = manifest_urls(root)
    runtime_state = _read_json(root / "state/unified_runtime_status.json", {})
    if not isinstance(runtime_state, dict):
        runtime_state = {}

    endpoint_timings = {
        "runtime_feed": benchmark_endpoint("runtime feed", urls["runtime_feed_url"], samples=endpoint_samples),
        "flight_test": benchmark_endpoint("flight test", urls["runtime_flight_test_url"], samples=max(3, endpoint_samples // 2)),
        "mind_hub_thoughts": benchmark_endpoint("mind hub thoughts", urls["mind_thoughts_url"], samples=max(3, endpoint_samples // 2)),
    }
    try:
        endpoint_timings["reboot_advice"] = benchmark_endpoint("reboot advice", urls["runtime_reboot_advice_url"], samples=max(3, endpoint_samples // 2))
    except Exception as exc:
        endpoint_timings["reboot_advice"] = {"label": "reboot advice", "ok": False, "errors": [str(exc)], "url": urls["runtime_reboot_advice_url"]}

    local_timings = {
        "organism_status_build": benchmark_callable(
            "organism status build",
            lambda: build_organism_runtime_status(root, local_terminal_url=urls["runtime_feed_url"]).to_dict(),
            samples=2,
        ),
        "cognitive_trade_evidence_build": benchmark_callable(
            "cognitive trade evidence build",
            lambda: build_cognitive_trade_state(root),
            samples=5,
        ),
        "harmonic_affect_state_build": benchmark_callable(
            "harmonic affect state build",
            lambda: build_harmonic_affect_state(root),
            samples=5,
        ),
    }
    signal_timings = benchmark_signal_algorithms(local_samples)

    terminal_payload = endpoint_timings["runtime_feed"].get("payload_summary", {})
    flight_payload = endpoint_timings["flight_test"].get("payload_summary", {})
    cognitive_state = build_cognitive_trade_state(root)
    affect_state = build_harmonic_affect_state(root)
    organism_state = build_organism_runtime_status(root, local_terminal_url=urls["runtime_feed_url"]).to_dict()

    runtime_watchdog = runtime_state.get("runtime_watchdog") if isinstance(runtime_state.get("runtime_watchdog"), dict) else {}
    exchanges = runtime_state.get("exchanges") if isinstance(runtime_state.get("exchanges"), dict) else {}
    action_plan = runtime_state.get("exchange_action_plan") if isinstance(runtime_state.get("exchange_action_plan"), dict) else {}
    venues = action_plan.get("venues") if isinstance(action_plan.get("venues"), dict) else {}
    latest_intents = action_plan.get("latest_published") if isinstance(action_plan.get("latest_published"), dict) else {}
    latest_execution = action_plan.get("latest_execution") if isinstance(action_plan.get("latest_execution"), dict) else {}
    exchange_ready_count = sum(1 for value in exchanges.values() if value is True)
    exchange_count = len(exchanges)
    flight_tick_stale = flight_payload.get("tick_fresh") is False or flight_payload.get("heartbeat_fresh_but_tick_stale") is True
    stale = bool(runtime_state.get("stale") or runtime_watchdog.get("tick_stale") or terminal_payload.get("stale") or flight_tick_stale)
    open_positions = _as_number(
        (runtime_state.get("combined") if isinstance(runtime_state.get("combined"), dict) else {}).get("open_positions"),
        0.0,
    )
    blockers: list[str] = []
    if stale:
        blockers.append("runtime_stale")
    stale_reason = str(runtime_state.get("stale_reason") or runtime_watchdog.get("tick_stale_reason") or "").strip()
    if not stale_reason and flight_tick_stale:
        stale_reason = "flight_test_tick_not_fresh"
    if stale_reason:
        blockers.append(stale_reason)
    if open_positions > 0:
        blockers.append("open_positions")
    if flight_payload.get("downtime_window") is False:
        blockers.append("downtime_window_false")
    if flight_payload.get("can_reboot_now") is False:
        blockers.append("reboot_held_by_flight_test")

    hnc_summary = affect_state.get("summary", {}) if isinstance(affect_state.get("summary"), dict) else {}
    cognitive_summary = cognitive_state.get("summary", {}) if isinstance(cognitive_state.get("summary"), dict) else {}
    organism_summary = organism_state.get("summary", {}) if isinstance(organism_state.get("summary"), dict) else {}
    hnc_working = (
        bool(signal_timings["hnc_phi_prime_train"].get("ok"))
        and bool(signal_timings["hnc_phi_ladder"].get("ok"))
        and bool(signal_timings["hnc_vibration_accumulator"].get("ok"))
        and _as_number(hnc_summary.get("hnc_anchor_count")) > 0
        and _as_number(hnc_summary.get("hnc_coherence_score")) >= 0.0
    )
    signal_path_working = (
        bool(runtime_state.get("trading_ready") or terminal_payload.get("trading_ready"))
        and bool(runtime_state.get("data_ready") or terminal_payload.get("data_ready"))
        and exchange_ready_count == exchange_count
        and bool(local_timings["cognitive_trade_evidence_build"].get("ok"))
        and bool(local_timings["harmonic_affect_state_build"].get("ok"))
        and hnc_working
    )

    fastest_decision_ms = min(
        _as_number(signal_timings["composite_score"].get("p50_ms"), 999999.0),
        _as_number(signal_timings["unified_signal_engine"].get("p50_ms"), 999999.0),
    )
    end_to_end_local_ms = (
        _as_number(endpoint_timings["runtime_feed"].get("p50_ms"))
        + _as_number(signal_timings["unified_signal_engine"].get("p50_ms"))
        + _as_number(signal_timings["hnc_vibration_accumulator"].get("p50_ms"))
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_now(),
        "status": "live_cognition_benchmark_complete",
        "safety": {
            "mode": "read_only_no_orders_no_exchange_mutations",
            "orders_submitted": 0,
            "exchange_mutations": 0,
            "note": "Measures local live status, cognition, HNC, and signal functions only.",
        },
        "summary": {
            "signal_path_working": signal_path_working,
            "hnc_working": hnc_working,
            "runtime_connected": bool(endpoint_timings["runtime_feed"].get("success_count")),
            "trading_ready": bool(runtime_state.get("trading_ready") or terminal_payload.get("trading_ready")),
            "data_ready": bool(runtime_state.get("data_ready") or terminal_payload.get("data_ready")),
            "exchange_ready_count": exchange_ready_count,
            "exchange_count": exchange_count,
            "execution_venue_ready_count": int(action_plan.get("ready_venue_count", 0) or 0),
            "execution_venue_count": int(action_plan.get("venue_count", 0) or len(venues)),
            "order_intent_mode": action_plan.get("mode"),
            "order_intent_count": int(latest_intents.get("intent_count", 0) or action_plan.get("order_intents_published", 0) or 0),
            "executor_enabled": bool(action_plan.get("executor_enabled")),
            "executor_submitted_count": int(latest_execution.get("submitted_count", 0) or 0),
            "executor_blocked_count": int(latest_execution.get("blocked_count", 0) or 0),
            "runtime_stale": stale,
            "stale_reason": stale_reason or terminal_payload.get("stale_reason"),
            "open_positions": int(open_positions),
            "flight_can_reboot_now": flight_payload.get("can_reboot_now"),
            "reboot_decision": flight_payload.get("reboot_decision"),
            "action_now": "guarded_hold" if blockers else "runtime_gated_action_ready",
            "blockers": sorted(set(blockers)),
            "fastest_local_signal_p50_ms": round(fastest_decision_ms, 3),
            "estimated_local_observe_score_guard_p50_ms": round(end_to_end_local_ms, 3),
            "runtime_feed_p50_ms": endpoint_timings["runtime_feed"].get("p50_ms"),
            "flight_test_p50_ms": endpoint_timings["flight_test"].get("p50_ms"),
            "mind_hub_p50_ms": endpoint_timings["mind_hub_thoughts"].get("p50_ms"),
            "hnc_coherence_score": hnc_summary.get("hnc_coherence_score"),
            "affect_phase": hnc_summary.get("affect_phase"),
            "cognitive_trade_action_mode": cognitive_summary.get("action_mode"),
            "organism_action_mode": organism_summary.get("action_mode"),
        },
        "urls": urls,
        "api_governor": api_governor_summary(runtime_state),
        "exchange_action_plan": action_plan,
        "endpoint_timings": endpoint_timings,
        "local_timings": local_timings,
        "signal_timings": signal_timings,
        "hnc_state": hnc_summary,
        "cognitive_trade_state": cognitive_summary,
        "organism_state": organism_summary,
        "runtime_watchdog": runtime_watchdog,
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary", {})
    lines = [
        "# Aureon Live Cognition Benchmark",
        "",
        f"Generated: {report.get('generated_at')}",
        "",
        "## Verdict",
        "",
        f"- Signal path working: {summary.get('signal_path_working')}",
        f"- HNC working: {summary.get('hnc_working')}",
        f"- Action now: {summary.get('action_now')}",
        f"- Blockers: {', '.join(summary.get('blockers') or []) or 'none'}",
        "",
        "## Speed",
        "",
        f"- Fastest local signal p50: {summary.get('fastest_local_signal_p50_ms')} ms",
        f"- Estimated observe-score-guard p50: {summary.get('estimated_local_observe_score_guard_p50_ms')} ms",
        f"- Runtime feed p50: {summary.get('runtime_feed_p50_ms')} ms",
        f"- Flight test p50: {summary.get('flight_test_p50_ms')} ms",
        f"- Mind hub p50: {summary.get('mind_hub_p50_ms')} ms",
        "",
        "## Runtime",
        "",
        f"- Trading ready: {summary.get('trading_ready')}",
        f"- Data ready: {summary.get('data_ready')}",
        f"- Exchanges ready: {summary.get('exchange_ready_count')}/{summary.get('exchange_count')}",
        f"- Execution venues ready: {summary.get('execution_venue_ready_count')}/{summary.get('execution_venue_count')}",
        f"- Order intent mode: {summary.get('order_intent_mode')}",
        f"- Latest order intents: {summary.get('order_intent_count')}",
        f"- Executor enabled: {summary.get('executor_enabled')}",
        f"- Executor submitted/blocked: {summary.get('executor_submitted_count')}/{summary.get('executor_blocked_count')}",
        f"- Runtime stale: {summary.get('runtime_stale')} ({summary.get('stale_reason')})",
        f"- Open positions: {summary.get('open_positions')}",
        f"- Flight reboot decision: {summary.get('reboot_decision')} / can reboot now: {summary.get('flight_can_reboot_now')}",
        "",
        "## HNC And Cognitive State",
        "",
        f"- HNC coherence score: {summary.get('hnc_coherence_score')}",
        f"- Affect phase: {summary.get('affect_phase')}",
        f"- Cognitive trade action mode: {summary.get('cognitive_trade_action_mode')}",
        f"- Organism action mode: {summary.get('organism_action_mode')}",
        "",
        "## Safety",
        "",
        f"- Orders submitted by benchmark: {report.get('safety', {}).get('orders_submitted')}",
        f"- Exchange mutations by benchmark: {report.get('safety', {}).get('exchange_mutations')}",
    ]
    return "\n".join(lines) + "\n"


def write_report(
    report: dict[str, Any],
    output_json: Path = DEFAULT_OUTPUT_JSON,
    output_md: Path = DEFAULT_OUTPUT_MD,
    public_json: Path = DEFAULT_PUBLIC_JSON,
) -> tuple[Path, Path, Path]:
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    public_json.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(report, indent=2, sort_keys=True, default=str)
    output_json.write_text(data, encoding="utf-8")
    public_json.write_text(data, encoding="utf-8")
    output_md.write_text(render_markdown(report), encoding="utf-8")
    return output_json, output_md, public_json


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark Aureon's live read-only trading cognition path.")
    parser.add_argument("--repo-root", default="", help="Repo root; defaults to this Aureon repo.")
    parser.add_argument("--endpoint-samples", type=int, default=8, help="Local endpoint samples; keep low to avoid noise.")
    parser.add_argument("--local-samples", type=int, default=100, help="In-process signal/HNC samples.")
    parser.add_argument("--json", default=str(DEFAULT_OUTPUT_JSON), help="Audit JSON output path.")
    parser.add_argument("--markdown", default=str(DEFAULT_OUTPUT_MD), help="Markdown output path.")
    parser.add_argument("--public-json", default=str(DEFAULT_PUBLIC_JSON), help="Frontend public JSON output path.")
    parser.add_argument("--no-write", action="store_true", help="Print summary without writing artifacts.")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    root = Path(args.repo_root).resolve() if args.repo_root else REPO_ROOT
    report = build_benchmark(root, endpoint_samples=max(1, args.endpoint_samples), local_samples=max(1, args.local_samples))
    paths: tuple[Path, Path, Path] | None = None
    if not args.no_write:
        paths = write_report(report, Path(args.json), Path(args.markdown), Path(args.public_json))
    print(
        json.dumps(
            {
                "summary": report["summary"],
                "json": str(paths[0]) if paths else None,
                "markdown": str(paths[1]) if paths else None,
                "public_json": str(paths[2]) if paths else None,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
