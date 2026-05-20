#!/usr/bin/env python3
"""
AUREON + FLAMEBORN - FULL INTEGRATION AUDIT & STRESS TEST
============================================================

Tests every endpoint, proxy route, WebSocket, and capability surface
between Flameborn (frontend) and Aureon (skeleton backend).

Usage:
    python scripts/audit_aureon_flameborn_full.py
    python scripts/audit_aureon_flameborn_full.py --aureon-port 5566 --flameborn-port 4173 --runtime-port 7331
    python scripts/audit_aureon_flameborn_full.py --json > audit_report.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

# Windows-safe stdout
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


@dataclass
class TestResult:
    name: str
    passed: bool
    url: str
    method: str = "GET"
    status_code: Optional[int] = None
    latency_ms: float = 0.0
    error: Optional[str] = None
    payload_preview: Optional[str] = None


@dataclass
class AuditReport:
    generated_at: str
    aureon_port: int
    flameborn_port: int
    runtime_port: int
    results: List[TestResult] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "aureon_port": self.aureon_port,
            "flameborn_port": self.flameborn_port,
            "runtime_port": self.runtime_port,
            "results": [asdict(r) for r in self.results],
            "summary": self.summary,
        }


def _fetch(method: str, url: str, body: Optional[bytes] = None, headers: Optional[Dict[str, str]] = None, timeout: int = 10) -> tuple:
    req = urllib.request.Request(url, method=method, data=body, headers=headers or {}, unverifiable=True)
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read().decode("utf-8", errors="replace")
            latency = (time.perf_counter() - start) * 1000
            return resp.status, data, latency, None
    except urllib.error.HTTPError as e:
        latency = (time.perf_counter() - start) * 1000
        data = e.read().decode("utf-8", errors="replace") if e.fp else ""
        return e.code, data, latency, None
    except Exception as e:
        latency = (time.perf_counter() - start) * 1000
        return 0, "", latency, str(e)


def run_tests(args: argparse.Namespace) -> AuditReport:
    report = AuditReport(
        generated_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        aureon_port=args.aureon_port,
        flameborn_port=args.flameborn_port,
        runtime_port=args.runtime_port,
    )

    aureon = f"http://127.0.0.1:{args.aureon_port}"
    flameborn = f"http://127.0.0.1:{args.flameborn_port}"
    runtime = f"http://127.0.0.1:{args.runtime_port}"
    proxy = f"{flameborn}/api/aureon/vault"

    tests: List[tuple] = []

    # =========================================================================
    # FLAMEBORN NATIVE ENDPOINTS
    # =========================================================================
    tests += [
        ("Flameborn health", "GET", f"{flameborn}/api/aureon/status", None),
        ("Flameborn systems", "GET", f"{flameborn}/api/aureon/systems", None),
        ("Flameborn supervisor", "GET", f"{flameborn}/api/aureon/supervisor", None),
        ("Flameborn stress", "GET", f"{flameborn}/api/aureon/full-capability-stress", None),
        ("Flameborn metacognition", "GET", f"{flameborn}/api/metacognition", None),
        ("Flameborn terminal status", "GET", f"{flameborn}/api/terminal/status", None),
        ("Flameborn sandbox status", "GET", f"{flameborn}/api/sandbox/status", None),
        ("Flameborn classroom state", "GET", f"{flameborn}/api/classroom/state", None),
    ]

    # =========================================================================
    # AUREON DIRECT (skeleton backend)
    # =========================================================================
    tests += [
        ("Aureon vault status", "GET", f"{aureon}/api/status", None),
        ("Aureon vault health", "GET", f"{aureon}/api/health", None),
        ("Aureon voices", "GET", f"{aureon}/api/voices", None),
        ("Aureon utterances", "GET", f"{aureon}/api/utterances?n=10", None),
        ("Aureon queen status", "GET", f"{aureon}/api/queen/status", None),
        ("Aureon queen memory", "GET", f"{aureon}/api/queen/memory", None),
        ("Aureon queen tools", "GET", f"{aureon}/api/queen/tools", None),
        ("Aureon queen skills", "GET", f"{aureon}/api/queen/skills", None),
        ("Aureon queen actions", "GET", f"{aureon}/api/queen/actions", None),
        ("Aureon bridge info", "GET", f"{aureon}/api/bridge/info", None),
        ("Aureon bridge state", "GET", f"{aureon}/api/bridge/state", None),
    ]

    # =========================================================================
    # AUREON THROUGH FLAMEBORN PROXY
    # =========================================================================
    tests += [
        ("Proxy: vault status", "GET", f"{proxy}/api/status", None),
        ("Proxy: vault health", "GET", f"{proxy}/api/health", None),
        ("Proxy: voices", "GET", f"{proxy}/api/voices", None),
        ("Proxy: utterances", "GET", f"{proxy}/api/utterances?n=10", None),
        ("Proxy: queen status", "GET", f"{proxy}/api/queen/status", None),
        ("Proxy: queen memory", "GET", f"{proxy}/api/queen/memory", None),
        ("Proxy: queen tools", "GET", f"{proxy}/api/queen/tools", None),
        ("Proxy: bridge info", "GET", f"{proxy}/api/bridge/info", None),
        ("Proxy: bridge state", "GET", f"{proxy}/api/bridge/state", None),
    ]

    # POST tests (safe, non-destructive)
    post_body = json.dumps({"text": "audit ping", "voice": "queen", "fast": True}).encode("utf-8")
    tests += [
        ("Aureon message POST", "POST", f"{aureon}/api/message", post_body),
        ("Proxy: message POST", "POST", f"{proxy}/api/message", post_body),
    ]

    tick_body = json.dumps({}).encode("utf-8")
    tests += [
        ("Aureon tick POST", "POST", f"{aureon}/api/tick", tick_body),
        ("Proxy: tick POST", "POST", f"{proxy}/api/tick", tick_body),
    ]

    # =========================================================================
    # FLAMEBORN CAPABILITY SURFACES
    # =========================================================================
    tests += [
        ("Flameborn capabilities", "GET", f"{flameborn}/api/aureon/capabilities", None),
        ("Flameborn coder skills", "GET", f"{flameborn}/api/coder/skills", None),
        ("Flameborn LLM models", "GET", f"{flameborn}/api/llm/models", None),
        ("Flameborn integrations", "GET", f"{flameborn}/api/integrations/status", None),
        ("Flameborn unified health", "GET", f"{flameborn}/api/health", None),
        ("Flameborn trading status", "GET", f"{flameborn}/api/trading/status", None),
        ("Flameborn audit trail", "GET", f"{flameborn}/api/audit/trail", None),
    ]

    # =========================================================================
    # OPTIONAL RUNTIME
    # =========================================================================
    if args.test_runtime:
        tests += [
            ("Runtime health", "GET", f"{runtime}/health", None),
            ("Runtime info", "GET", f"{runtime}/api/runtime/info", None),
        ]

    # Execute all tests
    for name, method, url, body in tests:
        status, data, latency, error = _fetch(method, url, body, {"Content-Type": "application/json"} if body else None)
        passed = status >= 200 and status < 500 and error is None
        preview = (data[:120] + "...") if len(data) > 120 else data
        report.results.append(TestResult(
            name=name,
            passed=passed,
            url=url,
            method=method,
            status_code=status if status else None,
            latency_ms=round(latency, 2),
            error=error,
            payload_preview=preview if preview else None,
        ))

    # =========================================================================
    # Summary
    # =========================================================================
    passed = sum(1 for r in report.results if r.passed)
    failed = sum(1 for r in report.results if not r.passed)
    avg_latency = round(sum(r.latency_ms for r in report.results) / max(len(report.results), 1), 2)
    max_latency = round(max((r.latency_ms for r in report.results), default=0), 2)

    report.summary = {
        "total": len(report.results),
        "passed": passed,
        "failed": failed,
        "pass_rate_percent": round(passed / max(len(report.results), 1) * 100, 1),
        "avg_latency_ms": avg_latency,
        "max_latency_ms": max_latency,
        "aureon_reachable": any(r.passed for r in report.results if r.name.startswith("Aureon")),
        "proxy_working": any(r.passed for r in report.results if r.name.startswith("Proxy:")),
        "flameborn_native_ok": all(r.passed for r in report.results if "Flameborn" in r.name),
    }

    return report


def main() -> int:
    ap = argparse.ArgumentParser(description="Full Aureon + Flameborn integration audit")
    ap.add_argument("--aureon-port", type=int, default=5566)
    ap.add_argument("--flameborn-port", type=int, default=4173)
    ap.add_argument("--runtime-port", type=int, default=7331)
    ap.add_argument("--test-runtime", action="store_true", help="Also test flameborn runtime")
    ap.add_argument("--json", action="store_true", help="Emit JSON only")
    args = ap.parse_args()

    print("===============================================================================")
    print("  AUREON + FLAMEBORN - FULL INTEGRATION AUDIT")
    print("===============================================================================")
    print(f"  Aureon port:   {args.aureon_port}")
    print(f"  Flameborn port: {args.flameborn_port}")
    print(f"  Runtime port:  {args.runtime_port}")
    print("")

    report = run_tests(args)

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
        return 0 if report.summary["failed"] == 0 else 1

    for r in report.results:
        status = "PASS" if r.passed else "FAIL"
        tone = "[PASS]" if r.passed else "[FAIL]"
        print(f"  {tone} {status:4}  {r.method:4} {r.status_code or 'ERR':>4}  {r.latency_ms:>6.2f}ms  {r.name}")
        if r.error:
            print(f"         error: {r.error}")

    print("")
    print("===============================================================================")
    print(f"  Results: {report.summary['passed']}/{report.summary['total']} passed  ({report.summary['pass_rate_percent']}%)")
    print(f"  Failed:  {report.summary['failed']}")
    print(f"  Avg latency: {report.summary['avg_latency_ms']}ms  |  Max: {report.summary['max_latency_ms']}ms")
    print(f"  Aureon reachable: {report.summary['aureon_reachable']}  |  Proxy working: {report.summary['proxy_working']}")
    print("===============================================================================")

    return 0 if report.summary["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
