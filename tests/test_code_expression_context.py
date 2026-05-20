from __future__ import annotations

import json
from pathlib import Path

from aureon.code_architect import Skill, SkillWriter, build_code_expression_context
from aureon.vault.voice.whole_knowledge_voice import build_expression_profile


def _profile(tmp_path: Path):
    source = tmp_path / "code_voice.md"
    source.write_text(
        "Human voice, code tooling, HNC harmonic signal, sensory affect, and practical patch review.",
        encoding="utf-8",
    )
    return build_expression_profile(
        root=tmp_path,
        source_paths=[source],
        evidence_dir=tmp_path,
        publish=False,
    )


def test_code_expression_context_reuses_whole_knowledge_voice(tmp_path: Path):
    profile = _profile(tmp_path)

    context = build_code_expression_context(
        "write a safer dashboard adapter",
        evidence={
            "runtime_state": {
                "hot_topic": "dashboard.patch",
                "action": "WRITE_CODE",
            },
            "API_SECRET": "do-not-emit",
        },
        profile=profile,
        evidence_dir=tmp_path,
        publish=True,
    )

    dumped = json.dumps(context)
    assert context["ok"] is True
    assert "aureon_code_expression_context_v1" in context["schema_features"]
    assert context["voice_summary"]
    assert context["runtime_summary"]
    assert context["redaction_applied"] is True
    assert "do-not-emit" not in dumped
    assert (tmp_path / "aureon_code_expression_last_run.json").exists()


def test_skill_writer_attaches_expression_context_to_proposals(tmp_path: Path):
    profile = _profile(tmp_path)
    writer = SkillWriter(
        expression_profile=profile,
        expression_evidence_dir=str(tmp_path),
        expression_publish=False,
    )

    proposal = writer.propose_atomic("screenshot", name="capture_screen")
    skill = Skill.from_proposal(proposal)

    assert proposal.expression_context["ok"] is True
    assert "aureon_code_expression_context_v1" in proposal.expression_context["schema_features"]
    assert proposal.expression_context["voice_summary"]
    assert "Expression context:" in proposal.reasoning
    assert skill.expression_context == proposal.expression_context
    assert writer.get_stats()["expression_enriched"] == 1
