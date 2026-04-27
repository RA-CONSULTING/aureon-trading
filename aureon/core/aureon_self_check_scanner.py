"""
aureon_self_check_scanner.py — The organism's antivirus.

Periodically scans the repo for problems and *gives itself jobs* by
publishing authoring.request events onto the ThoughtBus. The existing
authoring loop (aureon.core.aureon_cognitive_authoring_loop) is already
subscribed to authoring.request, so every job the scanner emits flows
straight to the architect → integrator → confirm → refine pipeline.

Problem classes the scanner detects:

  1. DORMANT         — modules that exist on disk but are not reached
                       from the ICS entry point. Fix job: wire them in.
  2. SYNTAX          — files whose AST parse fails. Fix job: repair.
  3. REGRESSION      — scoring log shows mean_score < threshold for a
                       target_path. Fix job: refine that file.
  4. REFINEMENT_WAIT — refinement_queue has entries the architect has
                       not picked up yet. Fix job: rebroadcast them.

For each problem the scanner emits a payload on `authoring.request` of
the form the authoring loop already knows how to dispatch:

  {"kind": "edit_file", "path": "...", "old_text": "...",
   "new_text": "...", "rationale": "...", "self_check_origin": "..."}

For problems that need the LLM to draft content (SYNTAX repair,
REGRESSION refinement), the scanner emits a lighter
`authoring.research` event carrying just the target + the issue, so the
architect can research → propose → stage. Those events are additive to
the existing bus surface and do not interfere with anything else.

The scanner runs as a background thread at `scan_interval_s` cadence
(default 60s). It is rate-limited: no more than `max_jobs_per_scan`
events published per scan to avoid flooding the architect.
"""

from __future__ import annotations

import ast
import json
import logging
import threading
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

logger = logging.getLogger("aureon.core.self_check_scanner")

_REPO_ROOT = Path(__file__).resolve().parents[2]
_STATE_ROOT = _REPO_ROOT / "state"
_SCAN_LOG = _STATE_ROOT / "self_check_log.jsonl"
_SCORING_LOG = _STATE_ROOT / "scoring_log.jsonl"
_REFINEMENT_QUEUE = _STATE_ROOT / "refinement_queue.jsonl"


# ─────────────────────────────────────────────────────────────────────────────
# Problem classes
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Problem:
    kind: str                   # "dormant" | "syntax" | "regression" | "refinement_wait"
    target: str                 # dotted module name OR relative file path
    severity: float             # 0.0 = cosmetic, 1.0 = blocks everything
    detail: str = ""
    evidence: Dict[str, Any] = field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────────────────
# The scanner
# ─────────────────────────────────────────────────────────────────────────────

class SelfCheckScanner:
    """
    The organism's periodic self-diagnostic. Finds problems, publishes fix
    jobs onto the authoring bus, logs every scan.
    """

    def __init__(
        self,
        scan_interval_s: float = 60.0,
        max_jobs_per_scan: int = 5,
        regression_threshold: float = 0.5,
        min_regression_samples: int = 2,
    ) -> None:
        self.scan_interval_s = max(5.0, float(scan_interval_s))
        self.max_jobs_per_scan = int(max_jobs_per_scan)
        self.regression_threshold = float(regression_threshold)
        self.min_regression_samples = int(min_regression_samples)

        self.bus: Any = None
        self.introspection: Any = None
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Suppress re-publishing the same fix job too often.
        self._recently_published: Dict[str, float] = {}
        self._republish_cooldown_s = 15 * 60  # 15 min
        self.scan_count = 0

    # ------------------------------------------------------------------
    # Wiring
    # ------------------------------------------------------------------
    def _wire(self) -> None:
        if self.bus is None:
            try:
                from aureon.core.aureon_thought_bus import get_thought_bus
                self.bus = get_thought_bus()
            except Exception as e:
                logger.debug("bus unavailable: %s", e)
        if self.introspection is None:
            try:
                from aureon.core.aureon_self_introspection import get_self_introspection
                self.introspection = get_self_introspection()
            except Exception as e:
                logger.debug("introspection unavailable: %s", e)

    # ------------------------------------------------------------------
    # Detection
    # ------------------------------------------------------------------
    def detect(self) -> List[Problem]:
        problems: List[Problem] = []
        problems.extend(self._detect_dormant())
        problems.extend(self._detect_syntax())
        problems.extend(self._detect_regression())
        problems.extend(self._detect_refinement_waiting())
        # Sort: highest severity first, then lexicographic for stability.
        problems.sort(key=lambda p: (-p.severity, p.kind, p.target))
        return problems

    def _detect_dormant(self) -> List[Problem]:
        if self.introspection is None:
            return []
        try:
            r = self.introspection.reachability()
        except Exception as e:
            logger.debug("reachability failed: %s", e)
            return []

        # Prioritise packages the user cares about most. These are the
        # heaviest dormant clusters per the last scan:
        priority_packages = (
            "aureon.atn",            # unlocks real backtesting
            "aureon.queen",          # ethical + cognitive core
            "aureon.analytics",      # insight
            "aureon.strategies",     # trading brain
            "aureon.bots_intelligence",
            "aureon.command_centers",
            "aureon.code_architect",
            "aureon.alignment",
            "aureon.cognition",
            "aureon.data_feeds",
        )

        out: List[Problem] = []
        dormant = set(r.get("dormant") or [])
        for pkg_prefix in priority_packages:
            picks = sorted(m for m in dormant if m.startswith(pkg_prefix + ".") or m == pkg_prefix)
            for m in picks[:3]:  # no more than 3 per package per scan
                out.append(Problem(
                    kind="dormant",
                    target=m,
                    severity=0.7 if pkg_prefix in ("aureon.atn", "aureon.queen") else 0.5,
                    detail=f"dormant: not reached from ICS",
                    evidence={"package": pkg_prefix, "reach_ratio": r.get("reach_ratio")},
                ))
        return out

    def _detect_syntax(self) -> List[Problem]:
        out: List[Problem] = []
        aureon_root = _REPO_ROOT / "aureon"
        # Only scan top-level files + one level down this pass to stay
        # fast; deeper files are picked up on subsequent scans via rotation.
        for path in aureon_root.rglob("*.py"):
            try:
                # skip obvious non-source locations
                if "__pycache__" in path.parts:
                    continue
                text = path.read_text(encoding="utf-8", errors="replace")
                ast.parse(text, filename=str(path))
            except SyntaxError as e:
                rel = str(path.relative_to(_REPO_ROOT)).replace("\\", "/")
                out.append(Problem(
                    kind="syntax",
                    target=rel,
                    severity=1.0,
                    detail=f"SyntaxError line {e.lineno}: {e.msg}",
                    evidence={"lineno": e.lineno, "msg": e.msg},
                ))
            except Exception:
                continue
        return out

    def _detect_regression(self) -> List[Problem]:
        if not _SCORING_LOG.exists():
            return []
        by_target: Dict[str, List[float]] = defaultdict(list)
        try:
            for raw in _SCORING_LOG.read_text(encoding="utf-8").splitlines()[-400:]:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    rec = json.loads(raw)
                except Exception:
                    continue
                t = rec.get("target_path")
                s = rec.get("score")
                if t and isinstance(s, (int, float)):
                    by_target[str(t)].append(float(s))
        except Exception:
            return []

        out: List[Problem] = []
        for target, scores in by_target.items():
            if len(scores) < self.min_regression_samples:
                continue
            mean = sum(scores) / len(scores)
            if mean < self.regression_threshold:
                out.append(Problem(
                    kind="regression",
                    target=target,
                    severity=min(1.0, 0.5 + (self.regression_threshold - mean)),
                    detail=f"mean_score={mean:.3f} over {len(scores)} samples",
                    evidence={"mean_score": mean, "samples": len(scores)},
                ))
        return out

    def _detect_refinement_waiting(self) -> List[Problem]:
        if not _REFINEMENT_QUEUE.exists():
            return []
        out: List[Problem] = []
        try:
            for raw in _REFINEMENT_QUEUE.read_text(encoding="utf-8").splitlines()[-100:]:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    rec = json.loads(raw)
                except Exception:
                    continue
                target = rec.get("target_path") or "?"
                rid = rec.get("refinement_id") or ""
                out.append(Problem(
                    kind="refinement_wait",
                    target=str(target),
                    severity=0.6,
                    detail=f"refinement {rid} awaiting architect pickup",
                    evidence={"refinement_id": rid},
                ))
        except Exception:
            return []
        # De-dup: one waiting problem per target path is enough.
        seen = set()
        dedup: List[Problem] = []
        for p in out:
            if p.target in seen:
                continue
            seen.add(p.target)
            dedup.append(p)
        return dedup

    # ------------------------------------------------------------------
    # Publication — give the organism a job
    # ------------------------------------------------------------------
    def _publish_job(self, problem: Problem) -> Optional[Dict[str, Any]]:
        """
        Turn a detected problem into an authoring.request event on the bus.
        Returns the payload published, or None if the problem cannot be
        converted to a concrete job (e.g. dormant without a known wire-in
        anchor — that becomes an authoring.research event instead).
        """
        if self.bus is None:
            return None

        now = time.time()
        dedup_key = f"{problem.kind}::{problem.target}"
        last = self._recently_published.get(dedup_key, 0.0)
        if now - last < self._republish_cooldown_s:
            return None
        self._recently_published[dedup_key] = now

        if problem.kind == "dormant":
            # Ask the architect to research a wire-in edit for the dormant
            # module. The architect will inspect the module's entry API and
            # propose an edit_file at the appropriate ICS boot phase.
            payload = {
                "kind": "research",                # non-standard kind → architect's attention
                "intent": "wire_in_dormant",
                "target_module": problem.target,
                "rationale": (
                    f"Module {problem.target} is on disk but not reached from "
                    f"aureon.core.integrated_cognitive_system. Propose an "
                    f"edit_file that imports and launches/instantiates it at "
                    f"the appropriate ICS boot phase."
                ),
                "self_check_origin": "dormant",
                "severity": problem.severity,
            }
            topic = "authoring.research"
        elif problem.kind == "syntax":
            payload = {
                "kind": "research",
                "intent": "repair_syntax",
                "target_path": problem.target,
                "rationale": (
                    f"File {problem.target} has a SyntaxError: "
                    f"{problem.detail}. Propose an edit_file that fixes the "
                    f"parse-blocking statement without changing surrounding "
                    f"semantics."
                ),
                "self_check_origin": "syntax",
                "severity": problem.severity,
                "evidence": problem.evidence,
            }
            topic = "authoring.research"
        elif problem.kind == "regression":
            payload = {
                "kind": "research",
                "intent": "refine_regression",
                "target_path": problem.target,
                "rationale": (
                    f"{problem.target} has mean observer score "
                    f"{problem.evidence.get('mean_score'):.3f} over "
                    f"{problem.evidence.get('samples')} samples — below "
                    f"threshold {self.regression_threshold}. Review the "
                    f"diffs in state/integrations_applied.jsonl for this "
                    f"target and propose a refinement edit that addresses "
                    f"the reviewer comments."
                ),
                "self_check_origin": "regression",
                "severity": problem.severity,
                "evidence": problem.evidence,
            }
            topic = "authoring.research"
        elif problem.kind == "refinement_wait":
            payload = {
                "kind": "research",
                "intent": "follow_up_refinement",
                "target_path": problem.target,
                "refinement_id": problem.evidence.get("refinement_id"),
                "rationale": (
                    f"Refinement {problem.evidence.get('refinement_id')} for "
                    f"{problem.target} is waiting. Draft the replacement "
                    f"edit now."
                ),
                "self_check_origin": "refinement_wait",
                "severity": problem.severity,
            }
            topic = "authoring.research"
        else:
            return None

        try:
            self.bus.publish(topic, payload, source="self_check_scanner")
        except Exception as e:
            logger.debug("publish failed: %s", e)
            return None
        return payload

    # ------------------------------------------------------------------
    # Scan cycle
    # ------------------------------------------------------------------
    def scan_once(self) -> Dict[str, Any]:
        """
        One full scan → detect → publish → log. Returns a summary dict.
        """
        self.scan_count += 1
        started = time.time()
        self._wire()
        problems = self.detect()

        by_kind = Counter(p.kind for p in problems)
        jobs_published: List[Dict[str, Any]] = []
        publish_budget = self.max_jobs_per_scan
        for p in problems:
            if publish_budget <= 0:
                break
            job = self._publish_job(p)
            if job is not None:
                jobs_published.append(job)
                publish_budget -= 1

        summary = {
            "scan_n": self.scan_count,
            "started_at": started,
            "duration_s": time.time() - started,
            "problems_total": len(problems),
            "problems_by_kind": dict(by_kind),
            "jobs_published": len(jobs_published),
            "publish_budget_remaining": publish_budget,
            "top_problems": [
                {"kind": p.kind, "target": p.target, "severity": p.severity, "detail": p.detail}
                for p in problems[:5]
            ],
        }

        try:
            _SCAN_LOG.parent.mkdir(parents=True, exist_ok=True)
            with _SCAN_LOG.open("a", encoding="utf-8") as f:
                f.write(json.dumps(summary, default=str) + "\n")
        except Exception:
            pass

        if self.bus is not None:
            try:
                self.bus.publish(
                    "self_check.summary",
                    summary,
                    source="self_check_scanner",
                )
            except Exception:
                pass

        return summary

    # ------------------------------------------------------------------
    # Background loop
    # ------------------------------------------------------------------
    def start(self) -> None:
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._stop.clear()
            self._thread = threading.Thread(
                target=self._run,
                name="aureon-self-check",
                daemon=True,
            )
            self._thread.start()
            logger.info("self-check scanner: started (interval=%.0fs)", self.scan_interval_s)

    def stop(self, timeout: float = 3.0) -> None:
        with self._lock:
            self._stop.set()
            t = self._thread
        if t is not None:
            t.join(timeout=timeout)

    def is_alive(self) -> bool:
        t = self._thread
        return bool(t is not None and t.is_alive())

    def _run(self) -> None:
        # One eager scan so the first signal lands fast.
        try:
            self.scan_once()
        except Exception as e:
            logger.debug("initial scan error: %s", e)
        while not self._stop.is_set():
            self._stop.wait(self.scan_interval_s)
            if self._stop.is_set():
                break
            try:
                self.scan_once()
            except Exception as e:
                logger.debug("scan error: %s", e)


# ─────────────────────────────────────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────────────────────────────────────

_instance: Optional[SelfCheckScanner] = None
_instance_lock = threading.Lock()


def get_self_check_scanner() -> SelfCheckScanner:
    global _instance
    with _instance_lock:
        if _instance is None:
            _instance = SelfCheckScanner()
        return _instance


def launch_self_check_scanner(scan_interval_s: float = 60.0) -> SelfCheckScanner:
    scanner = get_self_check_scanner()
    scanner.scan_interval_s = max(5.0, float(scan_interval_s))
    scanner.start()
    return scanner


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Aureon self-check scanner.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_once = sub.add_parser("scan", help="Run one scan and print the summary")

    p_watch = sub.add_parser("watch", help="Run the scanner in the foreground")
    p_watch.add_argument("--interval", type=float, default=60.0)
    p_watch.add_argument("--runtime-seconds", type=float, default=0.0,
                         help="Stop after N seconds; 0 = run until interrupted.")

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(name)s :: %(message)s")

    if args.cmd == "scan":
        scanner = get_self_check_scanner()
        summary = scanner.scan_once()
        print(json.dumps(summary, indent=2, default=str))
    elif args.cmd == "watch":
        scanner = launch_self_check_scanner(scan_interval_s=args.interval)
        t0 = time.time()
        try:
            while scanner.is_alive():
                time.sleep(1.0)
                if args.runtime_seconds and (time.time() - t0) >= args.runtime_seconds:
                    break
        except KeyboardInterrupt:
            pass
        finally:
            scanner.stop()
