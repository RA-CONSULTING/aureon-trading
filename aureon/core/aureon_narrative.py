"""
aureon_narrative.py — Who did it, why, and what moved because of it.

Every loop in the self-authoring stack writes its own audit lane. This
module is the single reader that composes those lanes into a readable
narrative: "At T, agent X proposed edit Y to file Z because scanner
detected problem P; reviewer scored it S; the file delta was D; it moved
the wheel by R."

Sources it reads (all under state/, all gitignored runtime state):

    integrations_applied.jsonl   — every confirmed edit with full diff,
                                    metrics_before/after, improvement,
                                    comparison_id + variant
    integrations_rejected.jsonl  — discarded + lost-comparison siblings
    scoring_log.jsonl            — observer + backtest scores per edit
    self_check_log.jsonl         — every scan summary (problems + jobs)
    repair_swarm_log.jsonl       — every swarm dispatch (which agent)
    refinement_queue.jsonl       — refinement requests awaiting pickup
    improvement_log.jsonl        — per-edit improvement verdict
    consciousness_digests.jsonl  — rolling score aggregates

For every applied edit it answers:

    WHO        — which agent / source proposed it
                 (scanner origin, swarm agent name, manual propose,
                  refinement follow-up)
    WHY        — the causal chain:
                   1. what problem triggered the job
                   2. what evidence / scoring motivated it
                   3. what goal it serves
    WHAT       — the target file + diff summary (lines/imports/calls)
    VERDICT    — improvement verdict + observer score + comparison winner
    WHEEL      — reachability delta or metric that moved as a result

Public API:

    n = get_narrator()
    n.narrate(limit=10)          — narrative for the last N applied edits
    n.why(pending_id)            — single-edit causal chain
    n.who(pending_id)            — source chain only
    n.wheel_delta(window=20)     — aggregate "what moved" across recent edits
    n.print_recent(limit=5)      — human-readable stdout report
"""

from __future__ import annotations

import json
import logging
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

logger = logging.getLogger("aureon.core.narrative")

_REPO_ROOT = Path(__file__).resolve().parents[2]
_STATE_ROOT = _REPO_ROOT / "state"

_APPLIED_LOG = _STATE_ROOT / "integrations_applied.jsonl"
_REJECTED_LOG = _STATE_ROOT / "integrations_rejected.jsonl"
_SCORING_LOG = _STATE_ROOT / "scoring_log.jsonl"
_SCAN_LOG = _STATE_ROOT / "self_check_log.jsonl"
_SWARM_LOG = _STATE_ROOT / "repair_swarm_log.jsonl"
_REFINEMENT_QUEUE = _STATE_ROOT / "refinement_queue.jsonl"
_IMPROVEMENT_LOG = _STATE_ROOT / "improvement_log.jsonl"


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _tail(path: Path, limit: int = 500) -> List[Dict[str, Any]]:
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


def _fmt_ts(ts: Optional[float]) -> str:
    if not ts:
        return ""
    try:
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(float(ts)))
    except Exception:
        return str(ts)


# ─────────────────────────────────────────────────────────────────────────────
# Story dataclass
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class EditStory:
    pending_id: str
    target_path: str
    applied_at: float
    who: str = "?"                 # short source chain
    why: str = "?"                 # causal chain in one sentence
    what: str = ""                 # diff summary
    verdict: str = ""              # improvement verdict
    score: Optional[float] = None
    comparison_id: str = ""
    variant: str = ""
    file_delta: Dict[str, Any] = field(default_factory=dict)
    rationale: str = ""
    related_refinement_id: str = ""
    related_swarm_dispatch: Optional[Dict[str, Any]] = None
    related_scan: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pending_id": self.pending_id,
            "target_path": self.target_path,
            "applied_at": self.applied_at,
            "applied_at_human": _fmt_ts(self.applied_at),
            "who": self.who,
            "why": self.why,
            "what": self.what,
            "verdict": self.verdict,
            "score": self.score,
            "comparison_id": self.comparison_id,
            "variant": self.variant,
            "file_delta": self.file_delta,
            "rationale": self.rationale,
            "related_refinement_id": self.related_refinement_id,
            "related_swarm_dispatch": self.related_swarm_dispatch,
            "related_scan": self.related_scan,
        }

    def human(self) -> str:
        """One-paragraph readable story."""
        lines: List[str] = []
        lines.append(
            f"[{_fmt_ts(self.applied_at)}] {self.target_path}  "
            f"verdict={self.verdict or 'unknown'}  "
            f"score={self.score if self.score is not None else '-'}"
        )
        lines.append(f"  WHO: {self.who}")
        lines.append(f"  WHY: {self.why}")
        if self.what:
            lines.append(f"  WHAT: {self.what}")
        if self.variant or self.comparison_id:
            lines.append(
                f"  COMPARISON: {self.comparison_id or '-'}  "
                f"variant={self.variant or '-'}"
            )
        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Narrator
# ─────────────────────────────────────────────────────────────────────────────

class Narrator:
    """
    Single-reader composer. Holds no long-term state; every call
    re-reads the logs so the narrative is always current.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Core composition
    # ------------------------------------------------------------------
    def narrate(self, limit: int = 10) -> List[EditStory]:
        with self._lock:
            applied = _tail(_APPLIED_LOG, limit=max(100, limit * 5))
            applied = applied[-limit:]
            scores = _tail(_SCORING_LOG, limit=400)
            scans = _tail(_SCAN_LOG, limit=100)
            swarm = _tail(_SWARM_LOG, limit=100)

        score_by_pid: Dict[str, List[Dict[str, Any]]] = {}
        for s in scores:
            pid = str(s.get("applied_id") or "")
            if pid:
                score_by_pid.setdefault(pid, []).append(s)

        stories: List[EditStory] = []
        for rec in applied:
            stories.append(self._build_story(rec, score_by_pid, scans, swarm))
        return stories

    def _build_story(
        self,
        applied: Dict[str, Any],
        scores_by_pid: Dict[str, List[Dict[str, Any]]],
        scans: List[Dict[str, Any]],
        swarm: List[Dict[str, Any]],
    ) -> EditStory:
        pid = str(applied.get("pending_id") or "")
        target = str(applied.get("target_path") or "?")
        applied_at = float(applied.get("applied_at") or 0.0)
        rationale = str(applied.get("rationale") or "")
        improvement = applied.get("improvement") or {}
        file_delta = improvement.get("file") or {}
        verdict = str(improvement.get("verdict") or "unknown")
        comparison_id = str(applied.get("comparison_id") or "")
        variant = str(applied.get("variant") or "")

        # --- WHO ---------------------------------------------------------
        who = self._derive_who(rationale, applied, swarm, pid)

        # --- WHY ---------------------------------------------------------
        why = self._derive_why(rationale, applied, scans, applied_at)

        # --- WHAT --------------------------------------------------------
        what_bits: List[str] = []
        if file_delta:
            what_bits.append(
                f"+{file_delta.get('lines_added', 0)} lines, "
                f"+{file_delta.get('imports_added', 0)} imports, "
                f"+{file_delta.get('calls_added', 0)} calls, "
                f"+{file_delta.get('functions_added', 0)} functions, "
                f"+{file_delta.get('classes_added', 0)} classes"
            )
        if variant or comparison_id:
            what_bits.append(f"variant={variant or '-'} cmp={comparison_id or '-'}")
        what = "; ".join(what_bits)

        # --- VERDICT / SCORE --------------------------------------------
        mean_score: Optional[float] = None
        pid_scores = scores_by_pid.get(pid) or []
        if pid_scores:
            try:
                mean_score = sum(float(s.get("score") or 0.0) for s in pid_scores) / len(pid_scores)
            except Exception:
                mean_score = None

        # --- Related refinement ------------------------------------------
        related_refinement_id = ""
        if "[refinement" in rationale.lower() or "refinement of" in rationale.lower():
            # Rationale typically contains the refinement_id or prior pending_id.
            for tok in rationale.split():
                if tok.startswith("ref_") or tok.startswith("pe_"):
                    related_refinement_id = tok.strip(":,()")
                    break

        # --- Related swarm dispatch --------------------------------------
        related_swarm = None
        for d in swarm[-20:][::-1]:
            # Look for any result in this dispatch that landed this pending_id.
            for r in d.get("results", []) or []:
                if str(r.get("pending_id") or "") == pid:
                    related_swarm = {
                        "dispatch_n": d.get("dispatch_n"),
                        "agent_name": r.get("agent_name"),
                        "job_intent": r.get("job_intent"),
                        "job_target": r.get("job_target"),
                    }
                    break
            if related_swarm is not None:
                break

        # --- Related scan ------------------------------------------------
        related_scan = None
        # Heuristic: the scan window closest-before applied_at that
        # mentioned this target in top_problems.
        for s in reversed(scans):
            started = float(s.get("started_at") or 0.0)
            if started > applied_at:
                continue
            for p in s.get("top_problems", []) or []:
                if str(p.get("target") or "") == target or target.startswith(str(p.get("target") or "xxx")):
                    related_scan = {
                        "scan_n": s.get("scan_n"),
                        "problem_kind": p.get("kind"),
                        "problem_target": p.get("target"),
                        "severity": p.get("severity"),
                        "detail": p.get("detail"),
                    }
                    break
            if related_scan is not None:
                break

        return EditStory(
            pending_id=pid,
            target_path=target,
            applied_at=applied_at,
            who=who,
            why=why,
            what=what,
            verdict=verdict,
            score=mean_score,
            comparison_id=comparison_id,
            variant=variant,
            file_delta=file_delta,
            rationale=rationale,
            related_refinement_id=related_refinement_id,
            related_swarm_dispatch=related_swarm,
            related_scan=related_scan,
        )

    # ------------------------------------------------------------------
    # Derivation heuristics
    # ------------------------------------------------------------------
    @staticmethod
    def _derive_who(
        rationale: str,
        applied: Dict[str, Any],
        swarm: List[Dict[str, Any]],
        pid: str,
    ) -> str:
        # Swarm is the most specific signal.
        for d in swarm[-20:][::-1]:
            for r in d.get("results", []) or []:
                if str(r.get("pending_id") or "") == pid:
                    return f"RepairSwarm/{r.get('agent_name', '?')}"
        # Rationale tokens
        low = rationale.lower()
        if "via repairswarm" in low:
            # Parse agent name out of the tag.
            idx = low.find("via repairswarm/")
            if idx >= 0:
                tail = rationale[idx + len("via RepairSwarm/"):]
                return f"RepairSwarm/{tail.split(')')[0].split(' ')[0]}"
            return "RepairSwarm"
        if "comparison" in low and "variant=aureon" in low:
            return "aureon variant (A/B comparison)"
        if "comparison" in low and "variant=human" in low:
            return "human variant (A/B comparison)"
        if "refinement of" in low:
            return "refinement follow-up"
        if applied.get("variant"):
            return f"{applied['variant']} variant (A/B)"
        return "direct propose (observer)"

    @staticmethod
    def _derive_why(
        rationale: str,
        applied: Dict[str, Any],
        scans: List[Dict[str, Any]],
        applied_at: float,
    ) -> str:
        # The rationale usually carries the why; we expand it with the
        # scan context that preceded the apply.
        low = rationale.lower()
        if "dormant" in low or "not reached from ics" in low:
            return (
                "wire-in of a dormant module so ICS can reach it — "
                "reach_ratio progress. " + rationale[:160]
            )
        if "syntax" in low and "error" in low:
            return "repair a SyntaxError surfaced by the self-check scanner. " + rationale[:160]
        if "refinement of" in low:
            return "refinement of a prior edit that scored below threshold. " + rationale[:160]
        if "comparison" in low:
            return "A/B comparison — whichever variant scored better applied. " + rationale[:160]
        if "trinity" in low or "wire in" in low or "wire-in" in low:
            return "wire-in edit that adds imports + launch calls. " + rationale[:160]
        return rationale[:200] or "(no rationale recorded)"

    # ------------------------------------------------------------------
    # Small convenience queries
    # ------------------------------------------------------------------
    def why(self, pending_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            applied = _tail(_APPLIED_LOG, limit=500)
            scores = _tail(_SCORING_LOG, limit=400)
            scans = _tail(_SCAN_LOG, limit=100)
            swarm = _tail(_SWARM_LOG, limit=100)
        for rec in applied:
            if str(rec.get("pending_id") or "") == pending_id:
                scores_by_pid = {pending_id: [s for s in scores if str(s.get("applied_id") or "") == pending_id]}
                return self._build_story(rec, scores_by_pid, scans, swarm).to_dict()
        return None

    def who(self, pending_id: str) -> str:
        d = self.why(pending_id)
        return d["who"] if d else "?"

    def wheel_delta(self, window: int = 20) -> Dict[str, Any]:
        """Aggregate "what moved" across the last `window` applied edits."""
        stories = self.narrate(limit=window)
        totals = {
            "edits": len(stories),
            "lines_added": 0,
            "imports_added": 0,
            "calls_added": 0,
            "functions_added": 0,
            "classes_added": 0,
            "verdict_counts": {},
            "who_counts": {},
            "mean_score": 0.0,
        }
        scored = 0
        sum_score = 0.0
        for s in stories:
            fd = s.file_delta or {}
            totals["lines_added"] += int(fd.get("lines_added", 0) or 0)
            totals["imports_added"] += int(fd.get("imports_added", 0) or 0)
            totals["calls_added"] += int(fd.get("calls_added", 0) or 0)
            totals["functions_added"] += int(fd.get("functions_added", 0) or 0)
            totals["classes_added"] += int(fd.get("classes_added", 0) or 0)
            totals["verdict_counts"][s.verdict] = totals["verdict_counts"].get(s.verdict, 0) + 1
            totals["who_counts"][s.who] = totals["who_counts"].get(s.who, 0) + 1
            if s.score is not None:
                scored += 1
                sum_score += float(s.score)
        if scored > 0:
            totals["mean_score"] = sum_score / scored
        return totals

    def print_recent(self, limit: int = 5) -> str:
        stories = self.narrate(limit=limit)
        if not stories:
            return "(no applied edits yet)"
        return "\n\n".join(s.human() for s in stories)


# ─────────────────────────────────────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────────────────────────────────────

_instance: Optional[Narrator] = None
_instance_lock = threading.Lock()


def get_narrator() -> Narrator:
    global _instance
    with _instance_lock:
        if _instance is None:
            _instance = Narrator()
        return _instance


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Aureon narrative — who, why, what moved.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_recent = sub.add_parser("recent", help="Human-readable story of last N applied edits")
    p_recent.add_argument("--limit", type=int, default=10)

    p_why = sub.add_parser("why", help="Full story for one pending_id")
    p_why.add_argument("pending_id")

    p_wheel = sub.add_parser("wheel", help="Aggregate delta across last N edits")
    p_wheel.add_argument("--window", type=int, default=20)

    args = parser.parse_args()
    n = get_narrator()

    if args.cmd == "recent":
        print(n.print_recent(limit=args.limit))
    elif args.cmd == "why":
        d = n.why(args.pending_id)
        print(json.dumps(d, indent=2, default=str) if d else "not found")
    elif args.cmd == "wheel":
        print(json.dumps(n.wheel_delta(window=args.window), indent=2, default=str))
