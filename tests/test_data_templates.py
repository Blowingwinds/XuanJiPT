from ptt_orchestrator.core.loaders import load_yaml
from ptt_orchestrator.core.route_selector import extract_candidate_techniques


def test_data_template_metadata_exists() -> None:
    route_templates = load_yaml("data/route_templates.yaml")
    mapping = load_yaml("data/technique_operator_mapping.yaml")
    operators = load_yaml("data/operator_templates.yaml")
    tools = load_yaml("data/tool_registry.yaml")

    assert route_templates["metadata"]["library_id"] == "default_route_template_library"
    assert mapping["metadata"]["mapping_id"] == "default_technique_operator_mapping"
    assert operators["metadata"]["library_id"] == "default_operator_template_library"
    assert tools["metadata"]["registry_id"] == "default_tool_registry"


def test_all_route_techniques_have_mapping_and_profile() -> None:
    routes = load_yaml("data/route_templates.yaml")["routes"]
    mapping = load_yaml("data/technique_operator_mapping.yaml")
    mapped_techniques = set(mapping["techniques"])
    profiled_techniques = set(mapping["technique_profiles"])

    route_techniques = set()
    for route in routes:
        route_techniques.update(extract_candidate_techniques(route))

    assert route_techniques <= mapped_techniques
    assert route_techniques <= profiled_techniques


def test_all_candidate_operators_exist() -> None:
    mapping = load_yaml("data/technique_operator_mapping.yaml")
    operator_ids = {operator["operator_id"] for operator in load_yaml("data/operator_templates.yaml")["operators"]}

    for technique_id, item in mapping["techniques"].items():
        assert set(item["candidate_operators"]) <= operator_ids, technique_id


def test_all_operator_allowed_tools_exist() -> None:
    operators = load_yaml("data/operator_templates.yaml")["operators"]
    tool_ids = {tool["tool_id"] for tool in load_yaml("data/tool_registry.yaml")["tools"]}

    for operator in operators:
        assert set(operator["allowed_tools"]) <= tool_ids, operator["operator_id"]


def test_all_tool_supported_operators_exist() -> None:
    tools = load_yaml("data/tool_registry.yaml")["tools"]
    operator_ids = {operator["operator_id"] for operator in load_yaml("data/operator_templates.yaml")["operators"]}

    for tool in tools:
        assert set(tool["supported_operators"]) <= operator_ids, tool["tool_id"]


def test_high_risk_technique_profiles_require_approval() -> None:
    profiles = load_yaml("data/technique_operator_mapping.yaml")["technique_profiles"]

    for technique_id, profile in profiles.items():
        if profile["risk_level"] == "high":
            assert profile["requires_human_approval"] is True, technique_id


def test_tool_registry_has_selection_profiles() -> None:
    tools = load_yaml("data/tool_registry.yaml")["tools"]

    for tool in tools:
        profile = tool["selection_profile"]
        assert "cost_score" in profile
        assert "safety_score" in profile
        assert "output_quality" in profile
