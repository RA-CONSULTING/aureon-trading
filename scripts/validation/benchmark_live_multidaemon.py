#!/usr/bin/env python3
"""
Live multi-daemon benchmark — boot the real processes, watch the organism sense
itself across the process boundary, and prove the self-loop closes.

Every prior cross-process cycle was validated in-process (one interpreter, one
bus). This benchmark boots the THREE supervisord daemons as separate OS
processes — ``hnc_live_daemon``, ``organism_daemon``, ``operator_server`` — lets
them breathe for a bounded window, then verifies from the OUTSIDE that:

  • the organism daemon breathes a whole-body consensus (``organism_consensus`` trace);
  • the metacognition monitor runs live in that daemon and loops back on itself
    (a ``metacognition_monitor`` sub-field appears in the shared trace) — the
    HNC-style β·Λ(t−τ) self-term, proven across processes;
  • the operator serves live self-state (``GET /api/pulse`` / ``/api/metacognition``);
  • the HNC daemon computes and persists a real field (``hnc_live_trace.jsonl``);
  • the SaaS surface is compliant (delegates to the compliance audit).

Critical checks are the offline-robust plumbing + self-loop; network-dependent
source readings are informational (offline the Layer-1 fetchers degrade honestly,
so a missing live field is reported, never faked). Always cleans up its children.

``--wait`` is a MAX deadline: the benchmark polls the traces and exits as soon as
the self-loop closes, so a healthy run finishes fast and a slow daemon boot is
tolerated (not a fixed sleep — that was flaky).

Usage:
    AUREON_LLM_OFFLINE=1 python -m scripts.validation.benchmark_live_multidaemon [--wait 45] [--json]
"""

from __future__ import annotations

import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HNC_TRACE = _REPO_ROOT / "state" / "hnc_live_trace.jsonl"


def _check(name: str, ok: bool, detail: str, critical: bool = True, metrics: dict | None = None) -> dict:
    return {"check": name, "ok": bool(ok), "detail": detail, "critical": critical, "metrics": metrics or {}}


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _http_json(url: str, timeout: float = 3.0) -> dict | None:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:  # noqa: S310 — localhost only
            return json.loads(resp.read().decode("utf-8"))
    except Exception:  # noqa: BLE001
        return None


def _boot(module: str, env: dict, log: Path) -> subprocess.Popen:
    fh = log.open("wb")
    return subprocess.Popen(
        [sys.executable, "-m", module], env=env,
        stdout=fh, stderr=subprocess.STDOUT, cwd=str(_REPO_ROOT),
    )


def run_benchmark(wait_s: float = 45.0) -> list[dict]:
    checks: list[dict] = []
    start = time.time()
    tmp = tempfile.mkdtemp(prefix="aureon_bench_")
    port = _free_port()
    hnc_before = _HNC_TRACE.stat().st_size if _HNC_TRACE.exists() else 0

    env = {
        **os.environ,
        "AUREON_LLM_OFFLINE": "1",
        "AUREON_SUPPRESS_IMPORT_SIDE_EFFECTS": "1",
        "AUREON_BUS_TRACE_DIR": tmp,
        "AUREON_METACOG_LAMBDA_PATH": str(Path(tmp) / "metacog_lambda.json"),
        "AUREON_ORGANISM_BREATH_S": "3",
        "AUREON_HNC_DAEMON_DURATION": str(int(wait_s)),
        "AUREON_OPERATOR_PORT": str(port),
        "AUREON_OPERATOR_HOST": "127.0.0.1",
        "AUREON_TRACE_PUMP": "1",
    }
    procs: dict[str, subprocess.Popen] = {}
    try:
        for name, mod in (("hnc", "aureon.core.hnc_live_daemon"),
                          ("organism", "aureon.core.organism_daemon"),
                          ("operator", "aureon.operator.operator_server")):
            procs[name] = _boot(mod, env, Path(tmp) / f"{name}.log")

        checks.append(_check(
            "daemon_boot",
            all(p.poll() is None for p in procs.values()),
            f"launched {sorted(procs)} on port {port}",
            metrics={"pids": {k: p.pid for k, p in procs.items()}}))

        # ── cross-process reads (from the shared temp trace dir) ──────────────
        from aureon.core.bus_trace import read_trace_latest
        from aureon.core.hnc_field import read_subfields

        # Point our own readers at the children's trace dir.
        os.environ["AUREON_BUS_TRACE_DIR"] = tmp

        # Wait for the CONDITION, not a guessed duration: the organism daemon's
        # import is heavy (~10-15s), so a fixed sleep is flaky. Poll until the
        # consensus breathes AND the metacognition self-loop closes, or a generous
        # deadline. This makes the nightly a true signal, not a timing race.
        deadline = time.time() + wait_s
        consensus: dict | None = None
        subs: dict = {}
        waited = 0.0
        while time.time() < deadline:
            time.sleep(2.0)
            waited += 2.0
            consensus = read_trace_latest("organism_consensus")
            subs = read_subfields()  # reads the symbolic_subfield trace in tmp
            if consensus and "metacognition_monitor" in subs:
                break

        c_age = (time.time() - float(consensus.get("ts", 0))) if consensus else None
        checks.append(_check(
            "consensus_breathing",
            bool(consensus) and c_age is not None,
            f"consensus age={round(c_age, 1) if c_age else None}s after {round(waited)}s "
            "(organism daemon breathed)",
            metrics={"age_s": c_age, "waited_s": waited}))

        selfloop = "metacognition_monitor" in subs
        checks.append(_check(
            "metacognition_selfloop",
            selfloop,
            f"metacognition_monitor sub-field present={selfloop} "
            f"(the daemon read its own signals and looped back); sources={sorted(subs)}",
            metrics={"subfield_sources": sorted(subs)}))

        # ── live self-state over HTTP ────────────────────────────────────────
        pulse = None
        for _ in range(8):  # operator boot can lag
            pulse = _http_json(f"http://127.0.0.1:{port}/api/pulse")
            if pulse:
                break
            time.sleep(1.0)
        checks.append(_check(
            "operator_pulse",
            bool(pulse) and pulse.get("ok") is not False,
            f"/api/pulse served={bool(pulse)}",
            metrics={"service": (pulse or {}).get("service")}))

        meta = _http_json(f"http://127.0.0.1:{port}/api/metacognition")
        checks.append(_check(
            "api_metacognition",
            bool(meta) and "provenance" in (meta or {}),
            f"/api/metacognition self_coherence={(meta or {}).get('self_coherence')} "
            f"truth={(meta or {}).get('truth_status')}",
            critical=False,
            metrics={"self_coherence": (meta or {}).get("self_coherence"),
                     "psi": (meta or {}).get("psi")}))

        # cross-process field read-back through the operator's organism payload
        field_flowing = bool(((pulse or {}).get("organism", {}) or {}).get(
            "unification", {}).get("field_flowing"))
        checks.append(_check(
            "cross_process_field",
            field_flowing,
            f"/api/pulse organism.unification.field_flowing={field_flowing} "
            "(informational — HNC Layer-1 sources degrade offline)",
            critical=False))

        # ── the HNC daemon computed + persisted a real field ─────────────────
        hnc_after = _HNC_TRACE.stat().st_size if _HNC_TRACE.exists() else 0
        hnc_last = None
        if _HNC_TRACE.exists():
            try:
                lines = [ln for ln in _HNC_TRACE.read_text(encoding="utf-8").splitlines() if ln.strip()]
                hnc_last = json.loads(lines[-1]) if lines else None
            except Exception:  # noqa: BLE001
                hnc_last = None
        hnc_recent = bool(hnc_last and float(hnc_last.get("ts", 0)) >= start)
        checks.append(_check(
            "hnc_field_flowing",
            hnc_after > hnc_before and hnc_recent,
            f"trace grew {hnc_before}→{hnc_after} bytes; last sls="
            f"{(hnc_last or {}).get('symbolic_life_score')}",
            critical=False,
            metrics={"sls": (hnc_last or {}).get("symbolic_life_score")}))

        # ── flight test: standing-wave health of a live mini-organism ────────
        checks.append(_flight_check())

        # ── SaaS compliance (delegated) ──────────────────────────────────────
        try:
            from scripts.validation.audit_saas_compliance import run_audit as _saas_audit

            saas = _saas_audit()
            failed_req = [r for r in saas if not r["ok"] and r["required"]]
            checks.append(_check(
                "saas_compliance", not failed_req,
                f"{sum(1 for r in saas if r['ok'])}/{len(saas)} checks; "
                f"{len(failed_req)} required failures",
                metrics={"checks": len(saas)}))
        except Exception as exc:  # noqa: BLE001
            checks.append(_check("saas_compliance", False, f"audit error: {exc}"))

    finally:
        for p in procs.values():
            try:
                p.send_signal(signal.SIGTERM)
            except Exception:  # noqa: BLE001
                pass
        for p in procs.values():
            try:
                p.wait(timeout=5)
            except Exception:  # noqa: BLE001
                try:
                    p.kill()
                except Exception:  # noqa: BLE001
                    pass
        shutil.rmtree(tmp, ignore_errors=True)
    return checks


def _flight_check() -> dict:
    """Run BusFlightCheck over a live mini-organism (a few metacognition reflects)
    to score the standing-wave health — the in-process flight test."""
    try:
        from aureon.core.aureon_thought_bus import get_thought_bus
        from aureon.core.metacognition_monitor import MetacognitionMonitor
        from aureon.vault.voice.bus_flight_check import BusFlightCheck

        bus = get_thought_bus()
        fc = BusFlightCheck(bus)
        fc.start()
        mon = MetacognitionMonitor()
        for _ in range(3):
            mon.reflect()
        report = fc.standing_wave_report()
        health = report.get("health")
        return _check("flight_check", health is not None,
                      f"standing-wave health={health}", critical=False,
                      metrics={"health": health})
    except Exception as exc:  # noqa: BLE001
        return _check("flight_check", False, f"flight check error: {exc}", critical=False)


def build_report(checks: list[dict], wait_s: float) -> dict:
    crit = [c for c in checks if c["critical"]]
    crit_pass = sum(1 for c in crit if c["ok"])
    return {
        "name": "aureon-live-multidaemon-benchmark",
        "schema_version": 1,
        "wait_s": wait_s,
        "summary": {
            "status": "pass" if crit_pass == len(crit) else "fail",
            "critical_passed": crit_pass,
            "critical_total": len(crit),
            "informational_passed": sum(1 for c in checks if not c["critical"] and c["ok"]),
            "informational_total": sum(1 for c in checks if not c["critical"]),
            "check_count": len(checks),
        },
        "checks": checks,
    }


def _write_artifacts(report: dict) -> list[str]:
    out_dir = _REPO_ROOT / "docs" / "research" / "benchmarks"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "live_multidaemon_benchmark.json"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    lines = [
        "# Live Multi-Daemon Benchmark",
        "",
        f"**Status:** {report['summary']['status']} · "
        f"{report['summary']['critical_passed']}/{report['summary']['critical_total']} critical · "
        f"{report['summary']['informational_passed']}/{report['summary']['informational_total']} informational",
        "",
        "Boots the three supervisord daemons as separate processes and verifies the organism "
        "senses itself across the process boundary — including the metacognition self-loop.",
        "",
        "| Check | Tier | Result | Detail |",
        "|-------|------|--------|--------|",
    ]
    for c in report["checks"]:
        tier = "critical" if c["critical"] else "info"
        mark = "✅" if c["ok"] else ("❌" if c["critical"] else "⚠️")
        lines.append(f"| {c['check']} | {tier} | {mark} | {c['detail']} |")
    md_path = out_dir / "live_multidaemon_benchmark.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return [str(json_path), str(md_path)]


def main() -> int:
    wait_s = 45.0
    if "--wait" in sys.argv:
        try:
            wait_s = float(sys.argv[sys.argv.index("--wait") + 1])
        except (ValueError, IndexError):
            pass
    checks = run_benchmark(wait_s)
    report = build_report(checks, wait_s)
    paths = _write_artifacts(report)
    if "--json" in sys.argv:
        print(json.dumps(report, indent=2))
    else:
        print("=" * 70)
        print("AUREON LIVE MULTI-DAEMON BENCHMARK")
        print("=" * 70)
        for c in checks:
            mark = "PASS" if c["ok"] else ("FAIL" if c["critical"] else "warn")
            tier = "  " if c["critical"] else " ~"
            print(f" {tier} [{mark}] {c['check']:26} {c['detail']}")
        s = report["summary"]
        print("-" * 70)
        print(f"  {s['status'].upper()} · {s['critical_passed']}/{s['critical_total']} critical · "
              f"{s['informational_passed']}/{s['informational_total']} informational")
        print(f"  artifacts: {', '.join(p.split('/')[-1] for p in paths)}")
        print("=" * 70)
    return 0 if report["summary"]["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
