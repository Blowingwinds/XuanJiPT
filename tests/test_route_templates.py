from ptt_orchestrator.core.loaders import load_yaml
from ptt_orchestrator.core.route_selector import extract_candidate_techniques


REQUIRED_ROUTE_FIELDS = {
    "route_id",
    "name",
    "display_name",
    "description",
    "enabled",
    "risk_level",
    "route_type",
    "knowledge_refs",
    "recommended_for",
    "selection_hints",
    "expected_outputs",
    "default_selected_techniques",
    "tactics",
    "execution_dependencies",
    "safety_constraints",
}


def _routes() -> list[dict]:
    return load_yaml("data/route_templates.yaml")["routes"]


def test_route_templates_have_required_fields() -> None:
    for route in _routes():
        missing = REQUIRED_ROUTE_FIELDS - set(route)
        assert not missing, f"{route.get('route_id')}: missing {sorted(missing)}"


def test_default_selected_techniques_are_candidates() -> None:
    for route in _routes():
        candidates = set(extract_candidate_techniques(route))
        defaults = set(route["default_selected_techniques"])

        assert defaults <= candidates, f"{route['route_id']}: defaults outside candidates"


def test_execution_dependencies_reference_candidate_techniques() -> None:
    for route in _routes():
        candidates = set(extract_candidate_techniques(route))
        for dependency in route["execution_dependencies"]:
            assert dependency["from"] in candidates, route["route_id"]
            assert dependency["to"] in candidates, route["route_id"]


def test_enabled_routes_are_auto_executable_without_human_approval() -> None:
    for route in _routes():
        constraints = route["safety_constraints"]
        if route["enabled"]:
            assert constraints["requires_human_approval"] is False
            assert constraints["auto_execute_allowed"] is True


def test_high_risk_routes_are_not_auto_executable() -> None:
    for route in _routes():
        constraints = route["safety_constraints"]
        if route["risk_level"] == "high":
            assert constraints["requires_human_approval"] is True
            assert constraints["auto_execute_allowed"] is False
