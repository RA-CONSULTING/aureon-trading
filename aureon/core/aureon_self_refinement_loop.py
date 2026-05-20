"""
aureon_self_refinement_loop.py — The observer feedback lane.

Goal: the organism writes its own code, validates it, and self-corrects.
The human / this observer scores the result. Low-scoring edits go back
to the architect as refinement requests with the failure signal attached.
Over time, the consciousness layer gets an aggregated view of the scoring
history and learns which classes of proposed edit tend to fail.

Public surface:

    loop = get_refinement_loop()

    loop.score(applied_id_or_pending_id, score=0.3, reviewer="observer",
               comment="rolled back trading tick cadence")
        -> stores score, emits edit.scored, and if below threshold
           generates a refinement_request in state/refinement_queue.jsonl

    loop.backtest(applied_id_or_pending_id, mode="fast")
        -> tries aureon.atn (or any other backtest harness) to measure
           whether the post-edit state regresses real metrics.
           Returns a score + raw detail.

    loop.consciousness_digest(window=50)
        -> rolling aggregate of score history, grouped by target_path +
           variant + dominant edit type. This is what the consciousness
           module consumes to learn at scale.

Storage (all under state/, gitignored):
    state/scoring_log.jsonl        — every score submission
    state/refinement_queue.jsonl   — refinement requests ready for the
                                     architect to pick up
    state/consciousness_digests.jsonl  — periodic aggregates

Score semantics:
    1.0 = perfect improvement
    0.5 = neutral / acceptable
    0.0 = clear regression
    score < threshold (default 0.5) -> refinement triggered
"""

from __future__ import annotations

import json
import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

logger = logging.getLogger("aureon.core.self_refinement")

_REPO_ROOT = Path(__file__).resolve().parents[2]
_STATE_ROOT = _REPO_ROOT / "state"
_SCORING_LOG = _STATE_ROOT / "scoring_log.jsonl"
_REFINEMENT_QUEUE = _STATE_ROOT / "refinement_queue.jsonl"
_DIGEST_LOG = _STATE_ROOT / "consciousness_digests.jsonl"
_APPLIED_LOG = _STATE_ROOT / "integrations_applied.jsonl"
_IMPROVEMENT_LOG = _STATE_ROOT / "improvement_log.jsonl"


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _now() -> float:
    return time.time()


def _append_jsonl(path: Path, record: Dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=str) + "\n")
    except Exception as e:
        logger.warning("append %s failed: %s", path, e)


def _read_jsonl_tail(path: Path, limit: int = 200) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return []
    out: List[Dict[str, Any]] = []
    for raw in lines[-limit:]:
        raw = raw.strip()
        if not raw:
            continue
        try:
            out.append(json.loads(raw))
        except Exception:
            continue
    return out


def _find_applied_record(id_: str) -> Optional[Dict[str, Any]]:
    """Locate an applied-edit record by pending_id (the stable handle)."""
    for rec in reversed(_read_jsonl_tail(_APPLIED_LOG, limit=500)):
        if rec.get("pending_id") == id_:
            return rec
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Refinement loop
# ─────────────────────────────────────────────────────────────────────────────

class SelfRefinementLoop:
    """
    Observer feedback lane. Consumes scores, emits refinement requests,
    and produces rolling consciousness digests.
    """

    def __init__(self, refinement_threshold: float = 0.5) -> None:
        self.refinement_threshold = float(refinement_threshold)
        self.bus: Any = None
        self._lock = threading.Lock()
        self._wire_bus()

    def _wire_bus(self) -> None:
        if self.bus is not None:
            return
        try:
            from aureon.core.aureon_thought_bus import get_thought_bus
            self.bus = get_thought_bus()
        except Exception:
            self.bus = None

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------
    def score(
        self,
        applied_id: str,
        score: float,
        reviewer: str = "observer",
        comment: str = "",
    ) -> Dict[str, Any]:
        """
        Record a score for an applied edit (by pending_id). Score in [0, 1].
        If score < refinement_threshold, a refinement request is queued.
        """
        if not applied_id:
            return {"ok": False, "error": "applied_id required"}
        try:
            score = float(score)
        except Exception:
            return {"ok": False, "error": "score must be numeric"}
        score = max(0.0, min(1.0, score))

        applied = _find_applied_record(applied_id)
        if applied is None:
            return {
                "ok": False,
                "error": f"no applied record for {applied_id} — score only "
                         "accepts pending_ids that were confirmed.",
            }

        record = {
            "at": _now(),
            "applied_id": applied_id,
            "target_path": applied.get("target_path"),
            "reviewer": reviewer or "observer",
            "score": score,
            "comment": comment or "",
            "comparison_id": applied.get("comparison_id"),
            "variant": applied.get("variant"),
            "improvement_verdict": (applied.get("improvement") or {}).get("verdict"),
        }

        with self._lock:
            _append_jsonl(_SCORING_LOG, record)

        if self.bus is not None:
            try:
                self.bus.publish("edit.scored", record, source="refinement_loop")
            except Exception:
                pass

        refinement = None
        if score < self.refinement_threshold:
            refinement = self._queue_refinement(applied, record)

        return {
            "ok": True,
            "score": score,
            "refinement_triggered": refinement is not None,
            "refinement": refinement,
        }

    # ------------------------------------------------------------------
    # Refinement generation
    # ------------------------------------------------------------------
    def _queue_refinement(
        self,
        applied: Dict[str, Any],
        scoring: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Build an authoring.request payload the architect can consume to
        propose a replacement edit. Includes the original target, the
        rejected diff, the improvement verdict, and the reviewer's comment
        as failure context.
        """
        refinement_id = f"ref_{int(_now() * 1000)}_{uuid.uuid4().hex[:8]}"
        failure_context = {
            "prior_pending_id": applied.get("pending_id"),
            "prior_target_path": applied.get("target_path"),
            "prior_diff": applied.get("diff"),
            "prior_improvement": applied.get("improvement"),
            "reviewer_score": scoring.get("score"),
            "reviewer_comment": scoring.get("comment"),
        }
        request = {
            "refinement_id": refinement_id,
            "created_at": _now(),
            "kind": "edit_file",
            "intent": "refinement",
            "target_path": applied.get("target_path"),
            "rationale": (
                f"refinement of {applied.get('pending_id')}: "
                f"prior score {scoring.get('score')} < threshold "
                f"{self.refinement_threshold}. reviewer: "
                f"{scoring.get('comment') or 'no comment'}"
            ),
            "failure_context": failure_context,
        }
        _append_jsonl(_REFINEMENT_QUEUE, request)

        if self.bus is not None:
            try:
                self.bus.publish(
                    "edit.refinement_needed",
                    {
                        "refinement_id": refinement_id,
                        "target_path": applied.get("target_path"),
                        "score": scoring.get("score"),
                        "reviewer": scoring.get("reviewer"),
                    },
                    source="refinement_loop",
                )
            except Exception:
                pass
        return request

    # ------------------------------------------------------------------
    # Backtest
    # ------------------------------------------------------------------
    def backtest(
        self,
        applied_id: str,
        mode: str = "fast",
    ) -> Dict[str, Any]:
        """
        Run whatever backtest harness is available against the current
        tree state to measure whether the applied edit regressed anything.

        Tries (in order):
          1. aureon.atn.runner (if importable) — full ATN backtest
          2. A lightweight introspection-only "static regression" check:
             every previously-loaded module must still import cleanly.

        Returns a dict with `score` in [0, 1]. The score is stored on the
        same scoring log so it contributes to the consciousness digest.
        """
        started = _now()
        detail: Dict[str, Any] = {
            "mode": mode,
            "started_at": started,
            "attempts": [],
        }

        # Attempt 1: full ATN backtest.
        score: Optional[float] = None
        try:
            from aureon.atn import runner as atn_runner  # type: ignore
            if hasattr(atn_runner, "run_fast") and mode == "fast":
                result = atn_runner.run_fast()
                score = float(result.get("score", 0.5))
                detail["attempts"].append({"harness": "atn.runner", "result": result})
            elif hasattr(atn_runner, "run"):
                result = atn_runner.run(mode=mode)
                score = float(result.get("score", 0.5))
                detail["attempts"].append({"harness": "atn.runner", "result": result})
        except Exception as e:
            detail["attempts"].append({"harness": "atn.runner", "error": str(e)})

        # Attempt 2: lightweight static regression — every aureon.* module
        # that was loaded before the edit must still parse now.
        if score is None:
            regression = self._static_regression_check()
            detail["attempts"].append({"harness": "static_regression", "result": regression})
            total = max(1, regression.get("checked", 0))
            failed = regression.get("failed", 0)
            score = 1.0 - (failed / total)

        detail["duration_s"] = _now() - started
        detail["score"] = score

        # Append as a score record so the consciousness digest picks it up.
        record = {
            "at": _now(),
            "applied_id": applied_id,
            "target_path": (_find_applied_record(applied_id) or {}).get("target_path"),
            "reviewer": f"backtest:{mode}",
            "score": score,
            "comment": f"backtest mode={mode}",
            "detail": detail,
        }
        with self._lock:
            _append_jsonl(_SCORING_LOG, record)

        if self.bus is not None:
            try:
                self.bus.publish("edit.backtest", record, source="refinement_loop")
            except Exception:
                pass

        # Trigger a refinement if the backtest score itself is below threshold.
        if score < self.refinement_threshold:
            applied = _find_applied_record(applied_id) or {}
            self._queue_refinement(applied, record)

        return {"ok": True, "score": score, "detail": detail}

    def _static_regression_check(self) -> Dict[str, Any]:
        """
        For every aureon.* module currently in sys.modules, try to reload
        its source via ast.parse. If parsing fails, that's a regression.
        Cheap enough to run on every edit.
        """
        import ast
        import sys
        from pathlib import Path as _P
        checked = 0
        failed = 0
        failures: List[str] = []
        for name, mod in list(sys.modules.items()):
            if not name.startswith("aureon."):
                continue
            file = getattr(mod, "__file__", None)
            if not file:
                continue
            try:
                text = _P(file).read_text(encoding="utf-8", errors="replace")
                ast.parse(text, filename=file)
                checked += 1
            except Exception as e:
                checked += 1
                failed += 1
                failures.append(f"{name}: {e}")
                if len(failures) > 20:
                    break
        return {
            "checked": checked,
            "failed": failed,
            "failures": failures[:20],
        }

    # ------------------------------------------------------------------
    # Consciousness digest — feedback on feedback
    # ------------------------------------------------------------------
    def consciousness_digest(self, window: int = 50) -> Dict[str, Any]:
        """
        Aggregate the last `window` score records into a digest the
        consciousness module can consume. Groups by target_path and
        variant so patterns emerge (e.g. "aureon variant wins 0.8, human
        variant wins 0.6 on queen/* files").
        """
        records = _read_jsonl_tail(_SCORING_LOG, limit=window)
        if not records:
            return {"ok": True, "window": window, "records": 0, "groups": {}}

        groups: Dict[str, Dict[str, Any]] = {}
        total_score = 0.0
        total_n = 0
        below_threshold = 0

        for r in records:
            score = float(r.get("score") or 0.0)
            total_score += score
            total_n += 1
            if score < self.refinement_threshold:
                below_threshold += 1

            key_target = str(r.get("target_path") or "unknown")
            key_variant = str(r.get("variant") or "none")
            key = f"{key_target}::{key_variant}"

            g = groups.setdefault(key, {
                "target_path": key_target,
                "variant": key_variant,
                "count": 0,
                "sum_score": 0.0,
            })
            g["count"] += 1
            g["sum_score"] += score

        for g in groups.values():
            g["mean_score"] = g["sum_score"] / max(1, g["count"])
            del g["sum_score"]

        digest = {
            "taken_at": _now(),
            "window": window,
            "records": total_n,
            "mean_score": total_score / max(1, total_n),
            "below_threshold": below_threshold,
            "below_threshold_rate": below_threshold / max(1, total_n),
            "refinement_threshold": self.refinement_threshold,
            "groups": groups,
        }

        # Persist so the consciousness module can read historic digests.
        _append_jsonl(_DIGEST_LOG, digest)

        if self.bus is not None:
            try:
                self.bus.publish("consciousness.digest", digest, source="refinement_loop")
            except Exception:
                pass
        return digest

    # ------------------------------------------------------------------
    # Queue inspection
    # ------------------------------------------------------------------
    def pending_refinements(self, limit: int = 20) -> List[Dict[str, Any]]:
        return _read_jsonl_tail(_REFINEMENT_QUEUE, limit=limit)

    def score_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        return _read_jsonl_tail(_SCORING_LOG, limit=limit)


# ─────────────────────────────────────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────────────────────────────────────

_instance: Optional[SelfRefinementLoop] = None
_instance_lock = threading.Lock()


def get_refinement_loop() -> SelfRefinementLoop:
    global _instance
    with _instance_lock:
        if _instance is None:
            _instance = SelfRefinementLoop()
        return _instance


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Aureon self-refinement loop CLI.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_score = sub.add_parser("score", help="Record an observer score for an applied edit")
    p_score.add_argument("applied_id")
    p_score.add_argument("score", type=float, help="0.0 (regression) .. 1.0 (perfect)")
    p_score.add_argument("--reviewer", default="observer")
    p_score.add_argument("--comment", default="")

    p_bt = sub.add_parser("backtest", help="Run a backtest on an applied edit")
    p_bt.add_argument("applied_id")
    p_bt.add_argument("--mode", default="fast")

    p_hist = sub.add_parser("history", help="Show recent score history")
    p_hist.add_argument("--limit", type=int, default=20)

    p_queue = sub.add_parser("queue", help="Show refinement queue")
    p_queue.add_argument("--limit", type=int, default=20)

    p_dig = sub.add_parser("digest", help="Produce consciousness digest")
    p_dig.add_argument("--window", type=int, default=50)

    args = parser.parse_args()
    loop = get_refinement_loop()

    if args.cmd == "score":
        print(json.dumps(
            loop.score(args.applied_id, args.score, args.reviewer, args.comment),
            indent=2, default=str,
        ))
    elif args.cmd == "backtest":
        print(json.dumps(loop.backtest(args.applied_id, args.mode), indent=2, default=str))
    elif args.cmd == "history":
        print(json.dumps(loop.score_history(args.limit), indent=2, default=str))
    elif args.cmd == "queue":
        print(json.dumps(loop.pending_refinements(args.limit), indent=2, default=str))
    elif args.cmd == "digest":
        print(json.dumps(loop.consciousness_digest(args.window), indent=2, default=str))
