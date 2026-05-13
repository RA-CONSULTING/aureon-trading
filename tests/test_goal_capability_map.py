from aureon.autonomous.aureon_goal_capability_map import (
    build_goal_capability_map,
    recommend_goal_routes,
)


def test_goal_capability_map_declares_whole_organism_goal_loop(tmp_path):
    goal_map = build_goal_capability_map(repo_root=tmp_path)
    data = goal_map.to_dict()

    assert data["directive_version"] == "goal-capability-v1"
    assert "inventory_capabilities" in data["goal_loop"]
    assert "use_relevant_systems" in data["goal_loop"]
    assert "memory" in data["route_surfaces"]
    assert "tools" in data["route_surfaces"]
    assert "contracts" in data["route_surfaces"]
    assert "accounting" in data["route_surfaces"]
    assert "research" in data["route_surfaces"]
    assert "self_catalog" in data["route_surfaces"]
    assert "capability_growth" in data["route_surfaces"]
    assert "self_enhancement" in data["route_surfaces"]
    assert "saas_security" in data["route_surfaces"]
    assert "saas_product_inventory" in data["route_surfaces"]
    assert "create_goal_contract" in data["goal_loop"]
    assert "queue_work_orders" in data["goal_loop"]
    assert data["contract_capabilities"]["contract_schema_version"] == "aureon-organism-contract-v1"
    assert "work_order" in data["contract_capabilities"]["contract_types"]
    assert "accounting_capabilities" in data
    assert data["tool_registry"]["count"] >= 5
    assert data["real_orders_allowed"] is False


def test_goal_route_recommendations_include_trading_and_code_surfaces():
    routes = recommend_goal_routes(
        "fix the Kraken margin code so temporal trade cognition can size positions"
    )
    names = {route["route"] for route in routes}

    assert "safe_trading_cognition" in names
    assert "safe_code_repair" in names
    assert any(route.get("requires_human") for route in routes if route["route"] == "safe_trading_cognition")


def test_goal_route_recommendations_include_internal_contract_stack():
    routes = recommend_goal_routes("create contract stack for tasks jobs work order queues and skills")
    names = {route["route"] for route in routes}

    assert "internal_contract_stack" in names
    contract_route = [route for route in routes if route["route"] == "internal_contract_stack"][0]
    assert "OrganismContractStack" in contract_route["systems"]
    assert "WorkOrderContract" in contract_route["systems"]


def test_goal_route_recommendations_include_accounting_manual_filing_boundary():
    routes = recommend_goal_routes("fix the company accounts, HMRC tax, CT600, and Companies House filing")
    accounting = [route for route in routes if route["route"] == "safe_accounting_context"]

    assert accounting
    assert accounting[0]["manual_filing_required"] is True
    assert accounting[0]["requires_human"] is True
    assert "AccountingSystemRegistry" in accounting[0]["systems"]


def test_goal_route_recommendations_include_research_corpus():
    routes = recommend_goal_routes("research the evidence corpus and write a source-linked note")
    research = [route for route in routes if route["route"] == "safe_research_corpus"]

    assert research
    assert research[0]["risk"] == "low"
    assert "ResearchCorpusIndex" in research[0]["systems"]
    assert "ObsidianBridge" in research[0]["systems"]


def test_goal_route_recommendations_include_self_enhancement_lifecycle():
    routes = recommend_goal_routes("audit itself, learn improvements, apply enhancements, and restart safely")
    names = {route["route"] for route in routes}

    assert "safe_self_enhancement_lifecycle" in names
    route = [item for item in routes if item["route"] == "safe_self_enhancement_lifecycle"][0]
    assert route["restart_handoff_required"] is True
    assert route["requires_human"] is True
    assert "SelfEnhancementEngine" in route["systems"]
    assert "CodeArchitect" in route["systems"]


def test_goal_route_recommendations_include_repo_self_catalog():
    routes = recommend_goal_routes("categorize and label every file so Aureon knows what it does")
    names = {route["route"] for route in routes}

    assert "repo_self_catalog" in names
    route = [item for item in routes if item["route"] == "repo_self_catalog"][0]
    assert route["risk"] == "low"
    assert "AureonRepoSelfCatalog" in route["systems"]


def test_goal_route_recommendations_include_capability_growth_loop():
    routes = recommend_goal_routes("test benchmark audit fix all capabilities and repeat improvements")
    names = {route["route"] for route in routes}

    assert "capability_growth_loop" in names
    route = [item for item in routes if item["route"] == "capability_growth_loop"][0]
    assert route["requires_validation"] is True
    assert "AureonCapabilityGrowthLoop" in route["systems"]
    assert "SkillLibrary" in route["systems"]


def test_goal_route_recommendations_include_hnc_saas_security_architect():
    routes = recommend_goal_routes("use HNC to create a secure zero trust SaaS for itself")
    names = {route["route"] for route in routes}

    assert "hnc_saas_security_architect" in names
    assert "saas_product_inventory" in names
    route = [item for item in routes if item["route"] == "hnc_saas_security_architect"][0]
    assert route["requires_validation"] is True
    assert route["unhackable_internal_goal_active"] is True
    assert route["public_unhackable_claim_allowed"] is False
    assert route["authorized_self_attack_required"] is True
    assert "HNCSaaSSecurityArchitect" in route["systems"]


def test_goal_route_recommendations_include_saas_product_inventory():
    routes = recommend_goal_routes("build a unified frontend dashboard and SaaS operator cockpit")
    names = {route["route"] for route in routes}

    assert "saas_product_inventory" in names
    route = [item for item in routes if item["route"] == "saas_product_inventory"][0]
    assert route["requires_validation"] is True
    assert "AureonSaaSSystemInventory" in route["systems"]
    assert "AureonFrontendUnificationPlan" in route["systems"]
