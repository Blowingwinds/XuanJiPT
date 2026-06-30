import pytest

from ptt_orchestrator.core.loaders import load_json, load_yaml
from ptt_orchestrator.core.planner import plan_from_route
from ptt_orchestrator.core.route_selector import get_route_by_id
from ptt_orchestrator.core.validator import validate_ptt_dag


def _routes() -> list[dict]:
    return load_yaml("data/route_templates.yaml")["routes"]


def _route(route_id: str) -> dict:
    route = get_route_by_id(_routes(), route_id)
    assert route is not None
    return route


def _mapping() -> dict:
    return load_yaml("data/technique_operator_mapping.yaml")


def _operators() -> list[dict]:
    return load_yaml("data/operator_templates.yaml")["operators"]


def _tools() -> list[dict]:
    return load_yaml("data/tool_registry.yaml")["tools"]


def _validation_policy() -> dict:
    return load_yaml("config/validation_policy.yaml")


def _safety_policy() -> dict:
    return load_yaml("config/safety_policy.yaml")


def _approval_policy() -> dict:
    return load_yaml("config/approval_policy.yaml")


def _basic_request() -> dict:
    return load_json("examples/input_basic_assessment.json")


def _web_request() -> dict:
    return load_json("examples/input_web_assessment.json")


def _plan(request: dict, route: dict) -> dict:
    return plan_from_route(
        request,
        route,
        _mapping(),
        _operators(),
        safety_policy=_safety_policy(),
        approval_policy=_approval_policy(),
    )


def _validate(dag: dict) -> None:
    result = validate_ptt_dag(
        dag,
        _routes(),
        _mapping(),
        _operators(),
        _tools(),
        validation_policy=_validation_policy(),
        safety_policy=_safety_policy(),
        approval_policy=_approval_policy(),
    )
    assert result.valid, result.errors


def _nodes_by_level(dag: dict, level: str) -> list[dict]:
    return [node for node in dag["nodes"] if node["level"] == level]


def test_plan_from_route_generates_valid_basic_dag_from_defaults() -> None:
    dag = _plan(_basic_request(), _route("route_basic_exposure_assessment"))

    assert dag["selected_route_id"] == "route_basic_exposure_assessment"
    assert len(_nodes_by_level(dag, "Goal")) == 1
    assert {node["technique_id"] for node in _nodes_by_level(dag, "Technique")} == {
        "host_discovery",
        "port_discovery",
        "service_discovery",
        "web_information_discovery",
        "cve_lookup",
        "report_summary",
    }
    assert all(node["operator_id"].startswith("op_") for node in _nodes_by_level(dag, "Action"))
    _validate(dag)


def test_plan_from_route_uses_tactic_grouped_selection() -> None:
    request = _basic_request()
    request["selected_techniques_by_tactic"] = [
        {
            "tactic_id": "reconnaissance",
            "selected_techniques": ["host_discovery"],
        },
        {
            "tactic_id": "report",
            "selected_techniques": ["report_summary"],
        },
    ]

    dag = _plan(request, _route("route_basic_exposure_assessment"))

    assert {node["technique_id"] for node in _nodes_by_level(dag, "Technique")} == {
        "host_discovery",
        "report_summary",
    }
    assert {node["operator_id"] for node in _nodes_by_level(dag, "Action")} == {
        "op_host_discovery",
        "op_report_summary",
    }
    _validate(dag)


def test_plan_from_route_rejects_flat_selected_techniques_only() -> None:
    request = _basic_request()
    request["selected_techniques"] = ["host_discovery"]

    with pytest.raises(ValueError, match="flat selected_techniques-only"):
        _plan(request, _route("route_basic_exposure_assessment"))


def test_plan_from_route_expands_execution_dependencies_to_action_edges() -> None:
    dag = _plan(_basic_request(), _route("route_basic_exposure_assessment"))
    action_edges = {
        (edge["from"], edge["to"])
        for edge in dag["edges"]
        if edge["edge_type"] == "depends_on"
    }
    action_by_operator = {
        node["operator_id"]: node["node_id"]
        for node in _nodes_by_level(dag, "Action")
        if node["operator_id"] in {"op_host_discovery", "op_port_scan"}
    }

    assert (
        action_by_operator["op_host_discovery"],
        action_by_operator["op_port_scan"],
    ) in action_edges


def test_plan_from_route_generates_valid_web_dag() -> None:
    dag = _plan(_web_request(), _route("route_web_service_risk_assessment"))
    operators = {node["operator_id"] for node in _nodes_by_level(dag, "Action")}

    assert "op_web_title" in operators
    assert "op_tls_certificate" in operators
    assert "op_cve_lookup" in operators
    _validate(dag)


def test_plan_from_route_rejects_disabled_route_by_default() -> None:
    with pytest.raises(ValueError, match="route is disabled"):
        _plan(_basic_request(), _route("route_credential_risk_assessment"))


def test_plan_from_route_sets_high_risk_actions_to_waiting_approval_when_allowed() -> None:
    request = {
        "goal": "credential approval placeholder",
        "intent": "credential_risk_assessment",
        "scope": ["192.168.56.10"],
        "allow_disabled_routes": True,
        "constraints": {
            "allow_high_risk": True,
            "max_risk_level": "high",
        },
        "known_assets": [
            {
                "asset_id": "asset-001",
                "host": "192.168.56.10",
                "known_ports": [22],
                "known_services": [{"service_name": "ssh", "version": "unknown"}],
            }
        ],
        "selected_techniques_by_tactic": [
            {
                "tactic_id": "credential_risk_assessment",
                "selected_techniques": ["weak_credential_check"],
            }
        ],
    }

    dag = _plan(request, _route("route_credential_risk_assessment"))
    action = _nodes_by_level(dag, "Action")[0]

    assert action["operator_id"] == "op_weak_credential_check"
    assert action["requires_human_approval"] is True
    assert action["status"] == "waiting_approval"
