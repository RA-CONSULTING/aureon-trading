from aureon.autonomous.aureon_safe_code_control import CodeProposal, SafeCodeControl


def test_code_proposals_queue_for_review_by_default(tmp_path, monkeypatch):
    monkeypatch.delenv("AUREON_CODE_AUTO_APPROVE", raising=False)
    ctl = SafeCodeControl(state_path=tmp_path / "code_state.json")

    result = ctl.propose(CodeProposal(kind="code_task", title="Add dashboard card"))

    assert result["status"] == "pending_review"
    assert ctl.status()["pending_count"] == 1
    assert ctl.status()["recent_reviews"] == []


def test_code_proposals_can_be_explicitly_auto_approved(tmp_path, monkeypatch):
    monkeypatch.setenv("AUREON_CODE_AUTO_APPROVE", "1")
    ctl = SafeCodeControl(state_path=tmp_path / "code_state.json")

    result = ctl.propose(CodeProposal(kind="code_task", title="Trusted local workflow"))

    assert result["status"] == "approved"
    assert result["reviewer"] == "env:AUREON_CODE_AUTO_APPROVE"
    assert ctl.status()["pending_count"] == 0
    assert ctl.status()["recent_reviews"][0]["title"] == "Trusted local workflow"


def test_code_proposals_approve_and_reject_from_queue(tmp_path, monkeypatch):
    monkeypatch.delenv("AUREON_CODE_AUTO_APPROVE", raising=False)
    ctl = SafeCodeControl(state_path=tmp_path / "code_state.json")

    ctl.propose(CodeProposal(kind="code_task", title="Review me"))
    approved = ctl.approve_next(reviewer="operator")

    assert approved["ok"] is True
    assert approved["proposal"]["status"] == "approved"
    assert approved["proposal"]["reviewer"] == "operator"
    assert ctl.status()["pending_count"] == 0

    ctl.propose(CodeProposal(kind="code_task", title="Reject me"))
    rejected = ctl.reject_next(reviewer="operator", reason="not_needed")

    assert rejected["ok"] is True
    assert rejected["proposal"]["status"] == "rejected"
    assert rejected["proposal"]["reject_reason"] == "not_needed"
    assert ctl.status()["pending_count"] == 0
