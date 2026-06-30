from ptt_orchestrator.core.loaders import load_yaml
from ptt_orchestrator.core.route_selector import (
    extract_candidate_techniques,
    get_route_by_id,
    select_route,
)


def _routes() -> list[dict]:
    return load_yaml("data/route_templates.yaml")["routes"]


def test_select_route_by_intent() -> None:
    result = select_route({"intent": "web_security_assessment"}, _routes())

    assert result.route["route_id"] == "route_web_service_risk_assessment"
    assert result.reason == "intent_matched:web_security_assessment"
    assert "web_tech_stack_identification" in result.candidate_techniques


def test_select_route_ignores_disabled_routes_by_default() -> None:
    result = select_route({"intent": "credential_risk_assessment"}, _routes())

    assert result.route["route_id"] != "route_credential_risk_assessment"
    assert result.route["enabled"] is True


def test_select_route_honors_allowed_route_ids() -> None:
    result = select_route(
        {
            "intent": "basic_security_assessment",
            "constraints": {"allowed_route_ids": ["route_internal_asset_discovery"]},
        },
        _routes(),
    )

    assert result.route["route_id"] == "route_internal_asset_discovery"
    assert result.reason == "fallback_first_enabled_route"


def test_get_route_by_id() -> None:
    route = get_route_by_id(_routes(), "route_basic_exposure_assessment")

    assert route["name"] == "basic_exposure_assessment"


def test_extract_candidate_techniques_preserves_order_and_uniqueness() -> None:
    route = get_route_by_id(_routes(), "route_basic_exposure_assessment")

    techniques = extract_candidate_techniques(route)

    assert techniques == [
        "host_discovery",
        "port_discovery",
        "service_discovery",
        "web_information_discovery",
        "cve_lookup",
        "config_risk_check",
        "report_summary",
    ]
