import logging

from aureon.inhouse_ai.llm_adapter import (
    AureonBrainAdapter,
    AureonHybridAdapter,
    AureonLocalAdapter,
)


def test_audit_mode_disables_local_llm_http(monkeypatch):
    monkeypatch.setenv("AUREON_AUDIT_MODE", "1")
    monkeypatch.delenv("AUREON_LLM_ALLOW_HTTP_IN_AUDIT", raising=False)

    adapter = AureonLocalAdapter()
    response = adapter.prompt([{"role": "user", "content": "ping"}])

    assert response.stop_reason == "error"
    assert "LLM HTTP disabled" in response.text
    assert adapter.health_check() is False


def test_hybrid_adapter_uses_brain_in_audit_mode(monkeypatch):
    monkeypatch.setenv("AUREON_AUDIT_MODE", "1")
    monkeypatch.delenv("AUREON_LLM_ALLOW_HTTP_IN_AUDIT", raising=False)

    adapter = AureonHybridAdapter()
    response = adapter.prompt([{"role": "user", "content": "analyse BTCUSDT exposure"}])

    assert response.model == "aureon-brain-v1"
    assert "AureonBrain" in response.text


def test_brain_adapter_matches_current_decide_signature(monkeypatch, caplog):
    monkeypatch.setenv("AUREON_AUDIT_MODE", "1")
    adapter = AureonBrainAdapter()

    with caplog.at_level(logging.WARNING, logger="aureon.inhouse_ai.llm"):
        response = adapter.prompt([{"role": "user", "content": "analyse BTCUSDT exposure"}])

    assert response.model == "aureon-brain-v1"
    assert '"source": "AureonBrain"' in response.text
    assert not any("AureonBrain reasoning failed" in r.message for r in caplog.records)
