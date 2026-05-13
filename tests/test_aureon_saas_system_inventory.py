import json

from aureon.autonomous.aureon_autonomous_capability_switchboard import (
    build_autonomous_capability_switchboard,
    write_switchboard,
)
from aureon.autonomous.aureon_frontend_evolution_queue import build_frontend_evolution_queue, write_queue
from aureon.autonomous.aureon_frontend_unification_plan import build_frontend_unification_plan, write_plan
from aureon.autonomous.aureon_saas_system_inventory import build_saas_system_inventory, write_inventory


def _make_fake_saas_repo(root):
    (root / "aureon").mkdir()
    (root / "scripts").mkdir()
    (root / "frontend" / "src" / "components").mkdir(parents=True)
    (root / "frontend" / "src" / "lib").mkdir(parents=True)
    (root / "frontend" / "src" / "services").mkdir(parents=True)
    (root / "supabase" / "functions" / "execute-trade").mkdir(parents=True)
    (root / "supabase" / "functions" / "orphan-function").mkdir(parents=True)
    (root / "aureon" / "vault" / "ui" / "static").mkdir(parents=True)
    (root / "templates").mkdir()
    (root / "public").mkdir()
    (root / "Kings_Accounting_Suite" / "output" / "statutory").mkdir(parents=True)

    (root / "frontend" / "index.html").write_text("<div id=\"root\"></div>", encoding="utf-8")
    (root / "frontend" / "src" / "main.tsx").write_text(
        "import App from './App';\n",
        encoding="utf-8",
    )
    (root / "frontend" / "src" / "App.tsx").write_text(
        "import { TradingPanel } from '@/components/TradingPanel';\nexport default function App(){return <TradingPanel/>}\n",
        encoding="utf-8",
    )
    (root / "frontend" / "src" / "components" / "TradingPanel.tsx").write_text(
        "import { supabase } from '@/integrations/supabase/client';\n"
        "export function TradingPanel(){ supabase.functions.invoke('execute-trade'); return null }\n",
        encoding="utf-8",
    )
    (root / "frontend" / "src" / "lib" / "harmonic-nexus-auth.ts").write_text(
        "export class HarmonicNexusAuth { autoLogin(){ return true } }\n",
        encoding="utf-8",
    )
    (root / "frontend" / "src" / "services" / "researchService.ts").write_text(
        "export async function load(){ return fetch('/api/research/status') }\n",
        encoding="utf-8",
    )
    (root / "supabase" / "functions" / "execute-trade" / "index.ts").write_text(
        "Deno.serve(() => new Response('{}'));\n",
        encoding="utf-8",
    )
    (root / "supabase" / "functions" / "orphan-function" / "index.ts").write_text(
        "Deno.serve(() => new Response('{}'));\n",
        encoding="utf-8",
    )
    (root / "aureon" / "vault" / "ui" / "static" / "index.html").write_text(
        "<script>fetch('/api/status')</script>",
        encoding="utf-8",
    )
    (root / "templates" / "queen_dashboard.html").write_text("<script>fetch('/api/state')</script>", encoding="utf-8")
    (root / "public" / "dashboard.html").write_text("<html>dashboard</html>", encoding="utf-8")
    (root / "Kings_Accounting_Suite" / "output" / "statutory" / "accounts_readable_for_ixbrl.html").write_text(
        "<html>accounts</html>",
        encoding="utf-8",
    )


def test_saas_inventory_counts_surfaces_and_detects_gaps(tmp_path):
    _make_fake_saas_repo(tmp_path)

    inventory = build_saas_system_inventory(tmp_path)
    data = inventory.to_dict()

    assert data["summary"]["surface_count"] >= 10
    assert data["summary"]["supabase_function_count"] == 2
    assert data["summary"]["security_blocker_count"] == 1
    assert data["summary"]["uncalled_supabase_function_count"] == 1
    assert any(surface["path"].endswith("TradingPanel.tsx") and surface["wiring_status"] == "wired" for surface in data["surfaces"])
    assert any(surface["wiring_status"] == "security_blocker" for surface in data["surfaces"])
    assert "orphan-function" in data["gaps"]["uncalled_supabase_functions"]


def test_saas_inventory_writes_audit_public_and_vault_artifacts(tmp_path):
    _make_fake_saas_repo(tmp_path)
    inventory = build_saas_system_inventory(tmp_path)

    md_path, json_path, public_path, vault_path = write_inventory(inventory)

    assert md_path.exists()
    assert public_path.exists()
    assert vault_path.exists()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["schema_version"] == "aureon-saas-system-inventory-v1"


def test_frontend_unification_plan_builds_canonical_screens(tmp_path):
    _make_fake_saas_repo(tmp_path)
    inventory = build_saas_system_inventory(tmp_path).to_dict()

    plan = build_frontend_unification_plan(tmp_path, inventory=inventory)
    data = plan.to_dict()

    assert data["summary"]["screen_count"] == 7
    assert data["summary"]["security_blocker_count"] == 1
    assert "fix_security_blockers" in [action["id"] for action in data["migration_actions"]]
    assert "live_trading_requires_existing_runtime_gates" in data["safety_contract"]
    assert {screen["id"] for screen in data["canonical_screens"]} >= {"overview", "trading", "accounting", "saas_security", "admin"}

    md_path, json_path, public_path, vault_path = write_plan(plan)
    assert md_path.exists()
    assert public_path.exists()
    assert vault_path.exists()
    assert json.loads(json_path.read_text(encoding="utf-8"))["status"].startswith("unification_plan_ready")


def test_frontend_evolution_queue_turns_old_surfaces_into_work_orders(tmp_path):
    _make_fake_saas_repo(tmp_path)
    inventory = build_saas_system_inventory(tmp_path).to_dict()

    queue = build_frontend_evolution_queue(tmp_path, inventory=inventory)
    data = queue.to_dict()

    assert data["schema_version"] == "aureon-frontend-evolution-queue-v1"
    assert data["summary"]["queue_count"] > 0
    assert any(order["source_path"].endswith("queen_dashboard.html") for order in data["work_orders"])
    assert any(order["target_screen"] in {"overview", "trading", "research", "self_improvement"} for order in data["work_orders"])
    assert all(order["safety_boundary"] for order in data["work_orders"])
    assert data["safety_contract"]["proposal_only"] is True

    md_path, json_path, public_path, vault_path = write_queue(queue)
    assert md_path.exists()
    assert public_path.exists()
    assert vault_path.exists()
    assert json.loads(json_path.read_text(encoding="utf-8"))["summary"]["queue_count"] == data["summary"]["queue_count"]


def test_autonomous_capability_switchboard_routes_ui_app_visual_and_conversation_modes(tmp_path):
    _make_fake_saas_repo(tmp_path)
    inventory = build_saas_system_inventory(tmp_path).to_dict()
    queue = build_frontend_evolution_queue(tmp_path, inventory=inventory).to_dict()
    plan = build_frontend_unification_plan(tmp_path, inventory=inventory).to_dict()
    runtime = {
        "generated_at": "2026-05-11T00:00:00+00:00",
        "status": "organism_observing_with_attention",
        "summary": {"runtime_feed_status": "offline"},
        "domains": [
            {"id": "capability_growth_loop", "status": "fresh"},
            {"id": "self_enhancement_lifecycle", "status": "fresh"},
            {"id": "repo_self_catalog", "status": "fresh"},
            {"id": "accounting_registry", "status": "attention"},
        ],
    }

    switchboard = build_autonomous_capability_switchboard(
        tmp_path,
        goal="Let Aureon choose app generation, frontend design, image generation, search, and conversation surfaces.",
        inventory=inventory,
        evolution_queue=queue,
        runtime_status=runtime,
        frontend_plan=plan,
        hnc_saas_state={"status": "ready"},
    )
    data = switchboard.to_dict()
    mode_ids = {mode["id"] for mode in data["capability_modes"]}

    assert data["schema_version"] == "aureon-autonomous-capability-switchboard-v1"
    assert {
        "conversation_goal_router",
        "frontend_design_orchestrator",
        "app_generation",
        "image_generation_request",
        "research_search_and_vault",
    }.issubset(mode_ids)
    assert data["summary"]["capability_count"] >= 9
    assert data["summary"]["presentation_intent_count"] > 0
    assert data["safety_contract"]["llm_can_select_capability"] is True
    assert data["safety_contract"]["llm_can_request_labelled_generated_visuals"] is True
    assert data["safety_contract"]["llm_can_place_direct_live_orders"] is False
    assert data["safety_contract"]["llm_can_file_hmrc_or_companies_house"] is False
    assert "source_evidence_required" in data["hnc_control_contract"]["anti_hallucination_gates"]
    assert any(intent["display_mode"] in {"generated_app_surface", "dashboard_panel"} for intent in data["presentation_intents"])

    md_path, json_path, public_path, vault_path = write_switchboard(switchboard)
    assert md_path.exists()
    assert json_path.exists()
    assert public_path.exists()
    assert vault_path.exists()
    assert json.loads(public_path.read_text(encoding="utf-8"))["summary"]["capability_count"] == data["summary"]["capability_count"]
