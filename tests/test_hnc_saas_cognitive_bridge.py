import json

from aureon.autonomous.hnc_authorized_attack_lab import build_authorized_attack_lab_report, write_report as write_attack_lab
from aureon.autonomous.hnc_saas_cognitive_bridge import (
    SaaSCognitiveBridge,
    build_saas_cognitive_state,
    render_markdown,
    write_report,
)
from aureon.autonomous.hnc_saas_security_architect import build_hnc_saas_security_blueprint, write_report as write_blueprint


class FakeBus:
    def __init__(self):
        self.events = []

    def publish(self, topic, payload=None, source=""):
        self.events.append({"topic": topic, "payload": payload or {}, "source": source})


class FakeWorkOrder:
    def __init__(self, title, payload):
        self.title = title
        self.payload = payload

    def to_dict(self):
        return {"title": self.title, "payload": self.payload, "contract_type": "work_order", "status": "queued"}


class FakeContractStack:
    def __init__(self):
        self.work_orders = []

    def enqueue_work_order(self, title, action_type, **kwargs):
        work_order = FakeWorkOrder(title, kwargs.get("payload") or {})
        self.work_orders.append(work_order)
        return work_order

    def publish_status(self):
        return {"queue_count": len(self.work_orders), "contract_count": len(self.work_orders)}


def _make_fake_repo(root):
    (root / "aureon" / "core").mkdir(parents=True)
    (root / "aureon" / "autonomous").mkdir(parents=True)
    (root / "scripts").mkdir()
    (root / "docs" / "audits").mkdir(parents=True)
    (root / "docs" / "runbooks").mkdir(parents=True)
    (root / "frontend" / "src" / "lib").mkdir(parents=True)
    (root / "aureon" / "core" / "hnc_gateway.py").write_text("class HNCGateway: pass\n", encoding="utf-8")
    (root / "docs" / "SECURITY.md").write_text("Report vulnerability. Never commit secret material.\n", encoding="utf-8")
    (root / "docs" / "runbooks" / "SECURITY_TRADING.md").write_text("Trading risk and live order gates.\n", encoding="utf-8")
    (root / "frontend" / "src" / "lib" / "harmonic-nexus-auth.ts").write_text(
        "export class HarmonicNexusAuth { autoLogin() { return true } }\n",
        encoding="utf-8",
    )
    (root / "aureon" / "core" / "organism_contracts.py").write_text(
        "UNSAFE_ACTION_TYPES = {'place_live_order'}\n",
        encoding="utf-8",
    )
    write_blueprint(build_hnc_saas_security_blueprint(root), root / "docs/audits/hnc_saas_security_blueprint.md", root / "docs/audits/hnc_saas_security_blueprint.json", root / "vault_blueprint.md")
    write_attack_lab(
        build_authorized_attack_lab_report(root, targets=["http://localhost"], execute_simulations=True, queue_fixes=False),
        root / "docs/audits/hnc_authorized_attack_lab.md",
        root / "docs/audits/hnc_authorized_attack_lab.json",
        root / "vault_attack.md",
    )


def test_saas_cognitive_bridge_builds_questions_decisions_and_routes(tmp_path):
    _make_fake_repo(tmp_path)
    bus = FakeBus()
    contracts = FakeContractStack()

    bridge = SaaSCognitiveBridge(tmp_path, thought_bus=bus, contract_stack=contracts)
    state = bridge.load_context()
    data = state.to_dict()

    assert data["status"] == "thinking_with_actionable_findings"
    assert data["summary"]["cognitive_topics_wired"] is True
    assert data["summary"]["actionable_finding_count"] == 1
    assert any(question["id"] == "q_findings" for question in data["questions"])
    assert any(decision["kind"] == "fix_finding" for decision in data["decisions"])
    assert contracts.work_orders


def test_saas_cognitive_bridge_publishes_thoughtbus_topics(tmp_path):
    _make_fake_repo(tmp_path)
    bus = FakeBus()
    bridge = SaaSCognitiveBridge(tmp_path, thought_bus=bus, contract_stack=FakeContractStack())

    bridge.load_context()
    bridge.publish_ready()
    bridge.publish_state()
    topics = {event["topic"] for event in bus.events}

    assert "saas.cognition.ready" in topics
    assert "saas.cognition.state" in topics
    assert "saas.cognition.question" in topics
    assert "saas.security.finding" in topics


def test_saas_cognitive_bridge_outputs_report(tmp_path):
    _make_fake_repo(tmp_path)
    state = build_saas_cognitive_state(tmp_path)

    markdown = render_markdown(state)
    assert "HNC SaaS Cognitive Bridge" in markdown
    assert "think on its feet" in markdown

    md_path, json_path, vault_path = write_report(
        state,
        tmp_path / "bridge.md",
        tmp_path / "bridge.json",
        tmp_path / "vault.md",
    )
    assert md_path.exists()
    assert vault_path.exists()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["summary"]["external_attacks_allowed"] is False
