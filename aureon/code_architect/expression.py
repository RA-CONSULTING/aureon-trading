"""Code-writing expression context for Aureon's self-authoring systems.

This module reuses the whole-knowledge voice core for code work. It keeps
generated skills and reviewable patch proposals grounded in repo evidence,
runtime state translation, and readable intent without changing execution
semantics.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, Optional


CODE_EXPRESSION_SCHEMA = "aureon_code_expression_context_v1"


def build_code_expression_context(
    goal: str,
    *,
    evidence: Optional[Dict[str, Any]] = None,
    profile: Any = None,
    root: Optional[str | Path] = None,
    evidence_dir: Optional[str | Path] = None,
    publish: bool = True,
) -> Dict[str, Any]:
    """Return a human-readable evidence context for a code proposal.

    The returned dict is intentionally safe to embed in SkillProposal,
    Skill, and SafeCodeControl JSON. It stores compact public summaries,
    not raw source text or secrets.
    """

    context: Dict[str, Any] = {
        "schema_features": [CODE_EXPRESSION_SCHEMA],
        "ok": False,
        "goal": str(goal or "code proposal"),
        "created_at": time.time(),
        "voice_summary": "",
        "runtime_summary": "",
        "top_facets": [],
        "source_count": 0,
        "novelty_checks": {},
        "redaction_applied": False,
        "evidence_path": "",
        "warnings": [],
    }

    try:
        from aureon.vault.voice.whole_knowledge_voice import compose_voice_artifact

        artifact = compose_voice_artifact(
            goal or "code proposal",
            audience="developer",
            mode="conversation",
            evidence=evidence or {},
            profile=profile,
            root=root,
            evidence_dir=evidence_dir,
            publish=publish,
        )
        runtime_translation = artifact.runtime_translation or {}
        profile_summary = artifact.profile_summary or {}
        context.update(
            {
                "ok": bool(artifact.ok),
                "voice_summary": _compact_text(artifact.text, limit=700),
                "runtime_summary": _compact_text(str(runtime_translation.get("summary") or ""), limit=360),
                "senses": runtime_translation.get("senses", {}),
                "blockers": runtime_translation.get("blockers", []),
                "top_facets": profile_summary.get("top_facets", []),
                "source_count": int(profile_summary.get("source_count") or 0),
                "novelty_checks": artifact.novelty_checks,
                "redaction_applied": bool(runtime_translation.get("redaction_applied")),
                "evidence_path": artifact.evidence_path,
                "warnings": list(artifact.warnings or []),
            }
        )
    except Exception as exc:
        context["warnings"].append(f"code_expression_unavailable:{exc}")

    if publish:
        try:
            out_dir = Path(evidence_dir) if evidence_dir else Path(root or ".") / "state"
            out_dir.mkdir(parents=True, exist_ok=True)
            out = out_dir / "aureon_code_expression_last_run.json"
            context["evidence_path"] = str(out)
            out.write_text(json.dumps(context, indent=2, sort_keys=True), encoding="utf-8")
        except Exception as exc:
            context["warnings"].append(f"code_expression_publish_failed:{exc}")

    return context


def _compact_text(text: str, *, limit: int) -> str:
    clean = " ".join(str(text or "").split())
    if len(clean) <= limit:
        return clean
    return clean[: max(0, limit - 3)].rstrip() + "..."
