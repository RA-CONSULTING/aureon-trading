#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
  FLAMEBORN + AUREON STRESS TEST SUITE
═══════════════════════════════════════════════════════════════════════════════

Pure Python — zero external dependencies.
Uses threading + urllib from stdlib for maximum portability.

Test Types (inspired by k6/Locust best practices):
  • SMOKE      : 1 user, 5s — verify system functions
  • LOAD       : 10 users, 30s — typical traffic simulation
  • STRESS     : 50 users, 60s — peak traffic, find breaking point
  • SPIKE      : ramp to 100 users in 5s, hold 10s — sudden surge
  • SOAK       : 10 users, 300s — memory leak / degradation detection
  • ENDPOINT   : hit every API with 5 concurrent users

Usage:
    python scripts/flameborn_stress_test.py --type stress --host http://127.0.0.1:4173
    python scripts/flameborn_stress_test.py --type all --host http://127.0.0.1:4173 --json

SLO Thresholds:
  • p95 latency < 2000ms
  • error rate < 5%
  • 99% availability

"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import threading
import time
import urllib.request
import urllib.error
import urllib.parse
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

DEFAULT_HOST = "http://127.0.0.1:4173"
AUREON_HOST = "http://127.0.0.1:5566"

ENDPOINTS = [
    # Flameborn native
    {"method": "GET", "path": "/api/health", "weight": 10},
    {"method": "GET", "path": "/api/aureon/status", "weight": 8},
    {"method": "GET", "path": "/api/aureon/systems", "weight": 5},
    {"method": "GET", "path": "/api/aureon/supervisor", "weight": 3},
    {"method": "GET", "path": "/api/aureon/full-capability-stress", "weight": 2},
    {"method": "GET", "path": "/api/aureon/capabilities", "weight": 4},
    {"method": "GET", "path": "/api/trading/status", "weight": 6},
    {"method": "GET", "path": "/api/audit/trail", "weight": 3},
    {"method": "GET", "path": "/api/coder/skills", "weight": 2},
    {"method": "GET", "path": "/api/llm/models", "weight": 2},
    {"method": "GET", "path": "/api/integrations/status", "weight": 2},
    # POST endpoints (lightweight)
    {"method": "POST", "path": "/api/world-data/ingest", "body": {"query": "BTC", "sources": ["wikipedia"]}, "weight": 3},
    {"method": "POST", "path": "/api/aureon/message", "body": {"content": "stress test"}, "weight": 5},
    {"method": "POST", "path": "/api/aureon/tick", "body": {}, "weight": 4},
]

SLO_THRESHOLDS = {
    "p95_ms": 2000,
    "error_rate": 0.05,
    "availability": 0.99,
}


# ═══════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class RequestResult:
    endpoint: str
    method: str
    status: int
    latency_ms: float
    error: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class EndpointStats:
    requests: int = 0
    successes: int = 0
    failures: int = 0
    latencies: List[float] = field(default_factory=list)
    errors: Dict[str, int] = field(default_factory=lambda: defaultdict(int))

    @property
    def avg_latency(self) -> float:
        return statistics.mean(self.latencies) if self.latencies else 0.0

    @property
    def min_latency(self) -> float:
        return min(self.latencies) if self.latencies else 0.0

    @property
    def max_latency(self) -> float:
        return max(self.latencies) if self.latencies else 0.0

    @property
    def p50_latency(self) -> float:
        return statistics.median(self.latencies) if self.latencies else 0.0

    @property
    def p95_latency(self) -> float:
        if not self.latencies:
            return 0.0
        s = sorted(self.latencies)
        idx = int(len(s) * 0.95)
        return s[min(idx, len(s) - 1)]

    @property
    def p99_latency(self) -> float:
        if not self.latencies:
            return 0.0
        s = sorted(self.latencies)
        idx = int(len(s) * 0.99)
        return s[min(idx, len(s) - 1)]

    @property
    def error_rate(self) -> float:
        return self.failures / self.requests if self.requests > 0 else 0.0


@dataclass
class TestReport:
    test_type: str
    host: str
    duration_sec: float
    users: int
    total_requests: int = 0
    total_successes: int = 0
    total_failures: int = 0
    endpoint_stats: Dict[str, EndpointStats] = field(default_factory=lambda: defaultdict(EndpointStats))
    start_time: float = field(default_factory=time.time)
    end_time: float = 0.0
    slo_passed: bool = True
    slo_violations: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "test_type": self.test_type,
            "host": self.host,
            "duration_sec": self.duration_sec,
            "users": self.users,
            "total_requests": self.total_requests,
            "total_successes": self.total_successes,
            "total_failures": self.total_failures,
            "rps": round(self.total_requests / max(self.duration_sec, 0.001), 2),
            "availability": round(self.total_successes / max(self.total_requests, 1), 4),
            "slo_passed": self.slo_passed,
            "slo_violations": self.slo_violations,
            "endpoints": {
                k: {
                    "requests": v.requests,
                    "successes": v.successes,
                    "failures": v.failures,
                    "avg_ms": round(v.avg_latency, 2),
                    "min_ms": round(v.min_latency, 2),
                    "max_ms": round(v.max_latency, 2),
                    "p50_ms": round(v.p50_latency, 2),
                    "p95_ms": round(v.p95_latency, 2),
                    "p99_ms": round(v.p99_latency, 2),
                    "error_rate": round(v.error_rate, 4),
                }
                for k, v in self.endpoint_stats.items()
            },
        }


# ═══════════════════════════════════════════════════════════════════════════════
# HTTP CLIENT
# ═══════════════════════════════════════════════════════════════════════════════

def make_request(host: str, endpoint: dict, timeout: float = 15.0) -> RequestResult:
    """Make a single HTTP request and return timing + status."""
    path = endpoint["path"]
    method = endpoint["method"]
    url = host.rstrip("/") + path
    body = endpoint.get("body")

    start = time.perf_counter()
    try:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        data = json.dumps(body).encode("utf-8") if body else None
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            _ = resp.read()
            status = resp.status
            latency = (time.perf_counter() - start) * 1000
            return RequestResult(endpoint=path, method=method, status=status, latency_ms=latency)
    except urllib.error.HTTPError as e:
        latency = (time.perf_counter() - start) * 1000
        return RequestResult(
            endpoint=path, method=method, status=e.code, latency_ms=latency,
            error=f"HTTPError: {e.code}"
        )
    except urllib.error.URLError as e:
        latency = (time.perf_counter() - start) * 1000
        return RequestResult(
            endpoint=path, method=method, status=0, latency_ms=latency,
            error=f"URLError: {e.reason}"
        )
    except Exception as e:
        latency = (time.perf_counter() - start) * 1000
        return RequestResult(
            endpoint=path, method=method, status=0, latency_ms=latency,
            error=f"Exception: {type(e).__name__}: {e}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# LOAD GENERATORS
# ═══════════════════════════════════════════════════════════════════════════════

class LoadGenerator:
    """Base load generator."""

    def __init__(self, host: str, report: TestReport):
        self.host = host
        self.report = report
        self.running = False
        self._lock = threading.Lock()

    def _pick_endpoint(self) -> dict:
        """Weighted random endpoint selection."""
        weights = [e["weight"] for e in ENDPOINTS]
        total = sum(weights)
        r = (time.time() * 1000) % total
        cumulative = 0
        for ep in ENDPOINTS:
            cumulative += ep["weight"]
            if r <= cumulative:
                return ep
        return ENDPOINTS[-1]

    def _record(self, result: RequestResult):
        with self._lock:
            self.report.total_requests += 1
            key = f"{result.method} {result.endpoint}"
            stats = self.report.endpoint_stats[key]
            stats.requests += 1
            stats.latencies.append(result.latency_ms)
            if result.error:
                stats.failures += 1
                stats.errors[result.error] += 1
                self.report.total_failures += 1
            else:
                stats.successes += 1
                self.report.total_successes += 1

    def _worker(self, stop_event: threading.Event):
        while not stop_event.is_set():
            ep = self._pick_endpoint()
            result = make_request(self.host, ep)
            self._record(result)
            time.sleep(0.05)  # Small delay between requests per worker

    def run(self, users: int, duration_sec: float):
        self.running = True
        stop_event = threading.Event()
        threads = []

        for _ in range(users):
            t = threading.Thread(target=self._worker, args=(stop_event,))
            t.daemon = True
            t.start()
            threads.append(t)

        time.sleep(duration_sec)
        stop_event.set()

        for t in threads:
            t.join(timeout=5.0)

        self.report.end_time = time.time()
        self.running = False


class SpikeGenerator(LoadGenerator):
    """Rapid ramp-up then hold."""

    def run(self, target_users: int, ramp_sec: float, hold_sec: float):
        self.running = True
        stop_event = threading.Event()
        threads = []
        start = time.time()

        # Rapid ramp
        while time.time() - start < ramp_sec and len(threads) < target_users:
            t = threading.Thread(target=self._worker, args=(stop_event,))
            t.daemon = True
            t.start()
            threads.append(t)
            time.sleep(ramp_sec / target_users)

        # Hold
        time.sleep(hold_sec)
        stop_event.set()

        for t in threads:
            t.join(timeout=5.0)

        self.report.end_time = time.time()
        self.running = False


class EndpointCrawler(LoadGenerator):
    """Hit every endpoint sequentially with concurrency."""

    def run(self, concurrency: int):
        self.running = True
        stop_event = threading.Event()
        threads = []

        def crawler():
            for ep in ENDPOINTS:
                if stop_event.is_set():
                    break
                for _ in range(concurrency):
                    result = make_request(self.host, ep)
                    self._record(result)

        for _ in range(concurrency):
            t = threading.Thread(target=crawler)
            t.daemon = True
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        self.report.end_time = time.time()
        self.running = False


# ═══════════════════════════════════════════════════════════════════════════════
# SLO VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════

def validate_slo(report: TestReport) -> TestReport:
    """Check report against SLO thresholds."""
    report.slo_violations = []

    # Overall availability
    availability = report.total_successes / max(report.total_requests, 1)
    if availability < SLO_THRESHOLDS["availability"]:
        report.slo_violations.append(
            f"Availability {availability:.2%} < {SLO_THRESHOLDS['availability']:.0%}"
        )

    # Per-endpoint p95
    for key, stats in report.endpoint_stats.items():
        if stats.p95_latency > SLO_THRESHOLDS["p95_ms"]:
            report.slo_violations.append(
                f"{key} p95 {stats.p95_latency:.0f}ms > {SLO_THRESHOLDS['p95_ms']}ms"
            )
        if stats.error_rate > SLO_THRESHOLDS["error_rate"]:
            report.slo_violations.append(
                f"{key} error rate {stats.error_rate:.2%} > {SLO_THRESHOLDS['error_rate']:.0%}"
            )

    report.slo_passed = len(report.slo_violations) == 0
    return report


# ═══════════════════════════════════════════════════════════════════════════════
# OUTPUT FORMATTERS
# ═══════════════════════════════════════════════════════════════════════════════

def print_banner():
    print("=" * 80)
    print("  FLAMEBORN + AUREON STRESS TEST SUITE")
    print("=" * 80)


def print_report(report: TestReport):
    print(f"\n{'─' * 80}")
    print(f"  TEST RESULTS: {report.test_type.upper()}")
    print(f"{'─' * 80}")
    print(f"  Host:        {report.host}")
    print(f"  Users:       {report.users}")
    print(f"  Duration:    {report.duration_sec:.1f}s")
    print(f"  Requests:    {report.total_requests}")
    print(f"  Successes:   {report.total_successes}")
    print(f"  Failures:    {report.total_failures}")
    print(f"  RPS:         {report.total_requests / max(report.duration_sec, 0.001):.2f}")
    print(f"  Availability: {report.total_successes / max(report.total_requests, 1):.2%}")
    print(f"  SLO Status:  {'✅ PASSED' if report.slo_passed else '❌ FAILED'}")

    if report.slo_violations:
        print(f"\n  SLO Violations:")
        for v in report.slo_violations:
            print(f"    [!] {v}")

    print(f"\n  Endpoint Breakdown:")
    for key, stats in sorted(report.endpoint_stats.items(), key=lambda x: -x[1].requests):
        status = "✅" if stats.error_rate < SLO_THRESHOLDS["error_rate"] and stats.p95_latency < SLO_THRESHOLDS["p95_ms"] else "❌"
        print(f"    {status} {key}")
        print(f"       Requests: {stats.requests} | Avg: {stats.avg_latency:.0f}ms | p95: {stats.p95_latency:.0f}ms | Err: {stats.error_rate:.1%}")

    print(f"{'─' * 80}\n")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def run_smoke(host: str, quiet: bool = False) -> TestReport:
    if not quiet:
        print("\n[SMOKE] SMOKE TEST -- 1 user, 5 seconds")
    report = TestReport(test_type="smoke", host=host, duration_sec=5, users=1)
    gen = LoadGenerator(host, report)
    gen.run(users=1, duration_sec=5)
    return validate_slo(report)


def run_load(host: str, quiet: bool = False) -> TestReport:
    if not quiet:
        print("\n[LOAD] LOAD TEST -- 10 users, 30 seconds")
    report = TestReport(test_type="load", host=host, duration_sec=30, users=10)
    gen = LoadGenerator(host, report)
    gen.run(users=10, duration_sec=30)
    return validate_slo(report)


def run_stress(host: str, quiet: bool = False) -> TestReport:
    if not quiet:
        print("\n[STRESS] STRESS TEST -- 50 users, 60 seconds")
    report = TestReport(test_type="stress", host=host, duration_sec=60, users=50)
    gen = LoadGenerator(host, report)
    gen.run(users=50, duration_sec=60)
    return validate_slo(report)


def run_spike(host: str, quiet: bool = False) -> TestReport:
    if not quiet:
        print("\n[SPIKE] SPIKE TEST -- ramp to 100 users in 5s, hold 10s")
    report = TestReport(test_type="spike", host=host, duration_sec=15, users=100)
    gen = SpikeGenerator(host, report)
    gen.run(target_users=100, ramp_sec=5, hold_sec=10)
    return validate_slo(report)


def run_soak(host: str, quiet: bool = False) -> TestReport:
    if not quiet:
        print("\n[SOAK] SOAK TEST -- 10 users, 300 seconds (5 minutes)")
    report = TestReport(test_type="soak", host=host, duration_sec=300, users=10)
    gen = LoadGenerator(host, report)
    gen.run(users=10, duration_sec=300)
    return validate_slo(report)


def run_endpoint_crawl(host: str, quiet: bool = False) -> TestReport:
    if not quiet:
        print("\n[CRAWL] ENDPOINT CRAWL -- all endpoints, 5 concurrent per endpoint")
    report = TestReport(test_type="endpoint_crawl", host=host, duration_sec=0, users=5)
    gen = EndpointCrawler(host, report)
    gen.run(concurrency=5)
    return validate_slo(report)


def main():
    parser = argparse.ArgumentParser(description="Flameborn + Aureon Stress Test Suite")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Flameborn host URL")
    parser.add_argument("--type", default="smoke", choices=["smoke", "load", "stress", "spike", "soak", "endpoint", "all"])
    parser.add_argument("--json", action="store_true", help="Output raw JSON report")
    parser.add_argument("--aureon", action="store_true", help="Also test Aureon direct (:5566)")
    args = parser.parse_args()

    if not args.json:
        print_banner()
        print(f"Target: {args.host}")
        print(f"Test Type: {args.type}")
        print()

    reports = []
    quiet = args.json

    if args.type in ("smoke", "all"):
        reports.append(run_smoke(args.host, quiet))
    if args.type in ("load", "all"):
        reports.append(run_load(args.host, quiet))
    if args.type in ("stress", "all"):
        reports.append(run_stress(args.host, quiet))
    if args.type in ("spike", "all"):
        reports.append(run_spike(args.host, quiet))
    if args.type in ("soak", "all"):
        reports.append(run_soak(args.host, quiet))
    if args.type in ("endpoint", "all"):
        reports.append(run_endpoint_crawl(args.host, quiet))

    if args.aureon:
        if not quiet:
            print(f"\n[AUREON] AUREON DIRECT TEST -- {AUREON_HOST}")
        aureon_report = run_smoke(AUREON_HOST, quiet)
        aureon_report.test_type = "aureon_direct_smoke"
        reports.append(aureon_report)

    all_passed = all(r.slo_passed for r in reports)

    if args.json:
        print(json.dumps({"reports": [r.to_dict() for r in reports], "all_passed": all_passed}, indent=2))
    else:
        for r in reports:
            print_report(r)
        print("=" * 80)
        if all_passed:
            print("  [PASS] ALL TESTS PASSED -- SYSTEM IS RESILIENT")
        else:
            print("  [FAIL] SOME TESTS FAILED -- REVIEW SLO VIOLATIONS ABOVE")
        print("=" * 80)

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
