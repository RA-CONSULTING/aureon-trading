from __future__ import annotations

import json
from pathlib import Path

from aureon.vault.voice.whole_knowledge_voice import (
    build_expression_profile,
    compose_voice_artifact,
    translate_runtime_state,
)


def test_expression_profile_classifies_repo_facets(tmp_path: Path):
    human = tmp_path / "bhoy_voice.md"
    human.write_text(
        "A Bhoy voice speaks of family, street rain, tea, courage, and ordinary human care.",
        encoding="utf-8",
    )
    harmonic = tmp_path / "hnc_math.py"
    harmonic.write_text(
        "def signal():\n"
        "    return 'HNC harmonic resonance with phi ratio, gamma coherence, frequency Hz, and Auris nodes'\n",
        encoding="utf-8",
    )
    trading = tmp_path / "trader.md"
    trading.write_text(
        "Kraken Binance Alpaca Capital trade orders, positions, market action, HMRC tax filing.",
        encoding="utf-8",
    )

    profile = build_expression_profile(
        root=tmp_path,
        source_paths=[human, harmonic, trading],
        evidence_dir=tmp_path,
    )

    assert profile.source_count == 3
    assert profile.facet_counts["human_voice"] >= 1
    assert profile.facet_counts["hnc_harmonic"] >= 1
    assert profile.facet_counts["math_equation"] >= 1
    assert profile.facet_counts["trading_action"] >= 1
    assert profile.facet_counts["accounting_legal"] >= 1
    assert (tmp_path / "aureon_expression_profile.json").exists()


def test_runtime_state_translation_uses_senses_and_redacts():
    translated = translate_runtime_state(
        {
            "runtime_state": {
                "mood": "FOCUSED",
                "coherence": 0.84,
                "resonance_frequency_hz": 528,
                "hot_topic": "market pulse",
                "n_tools": 49,
                "runtime_stale": True,
            },
            "API_SECRET": "do-not-emit",
        }
    )

    assert "market pulse" in translated.senses["see"]
    assert "528.00 Hz" in translated.senses["hear"]
    assert "runtime_stale" in translated.blockers
    assert translated.redaction_applied
    assert "do-not-emit" not in json.dumps(translated.to_dict())


def test_compose_voice_artifact_writes_evidence_without_raw_telemetry(tmp_path: Path):
    source = tmp_path / "knowledge.md"
    source.write_text(
        "Human voice, HNC harmonic resonance, sensory affect, touch, smell, trading action, code tooling.",
        encoding="utf-8",
    )
    profile = build_expression_profile(
        root=tmp_path,
        source_paths=[source],
        evidence_dir=tmp_path,
        publish=False,
    )

    artifact = compose_voice_artifact(
        "explain what Aureon senses before it speaks",
        mode="conversation",
        evidence={
            "runtime_state": {
                "coherence_gamma": 0.912345,
                "dominant_band": "theta",
                "hot_topic": "voice core",
                "action": "ANSWER",
            }
        },
        profile=profile,
        root=tmp_path,
        evidence_dir=tmp_path,
    )

    assert artifact.ok
    assert artifact.word_count > 40
    assert "voice core" in artifact.text
    assert "coherence_gamma" not in artifact.text
    assert "dominant_band" not in artifact.text
    assert artifact.novelty_checks["paragraphs_out"] >= 3
    assert Path(artifact.evidence_path).exists()
