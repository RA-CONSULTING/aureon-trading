from aureon.generated.research_cinema.harmonic_nexus_score_model import HarmonicNexusScoreInputs, harmonic_nexus_score, score_breakdown, build_default_inputs


def test_harmonic_nexus_score_bounds_inputs():
    score = harmonic_nexus_score(HarmonicNexusScoreInputs(2.0, -1.0, 0.5, 0.5, 0.5))
    assert 0.0 <= score <= 100.0


def test_harmonic_nexus_score_full_strength_is_100():
    score = harmonic_nexus_score(HarmonicNexusScoreInputs(1.0, 1.0, 1.0, 1.0, 1.0))
    assert score == 100.0


def test_harmonic_nexus_breakdown_matches_score():
    inputs = HarmonicNexusScoreInputs(1.0, 0.5, 0.25, 0.5, 1.0)
    breakdown = score_breakdown(inputs)
    assert breakdown["score"] == harmonic_nexus_score(inputs)
    assert set(breakdown) == {
        "source_strength",
        "coherence_agreement",
        "repeatability",
        "friction_feasibility",
        "contradiction_handling",
        "score",
    }


def test_default_inputs_are_conservative():
    score = harmonic_nexus_score(build_default_inputs())
    assert 0.0 <= score < 100.0
