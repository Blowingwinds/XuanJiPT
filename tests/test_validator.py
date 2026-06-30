from copy import deepcopy

from ptt_orchestrator.core.loaders import load_yaml
from ptt_orchestrator.core.validator import (
    validate_ptt_dag,
    validate_route_selection,
    validate_technique_selection,
)


def _routes() -> list[dict]:
    return load_yaml("data/route_templates.yaml")["routes"]


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


def _basic_dag() -> dict:
    return {
        "graph_id": "ptt-dag-test",
        "name": "basic exposure",
        "selected_route_id": "route_basic_exposure_assessment",
        "nodes": [
            {
                "node_id": "goal-001",
                "level": "Goal",
                "name": "basic_security_assessment",
            },
            {
                "node_id": "tactic-recon",
                "level": "Tactic",
                "name": "reconnaissance",
                "tactic_id": "reconnaissance",
                "parent_id": "goal-001",
            },
            {
                "node_id": "tech-host",
                "level": "Technique",
                "name": "host_discovery",
                "technique_id": "host_discovery",
                "parent_id": "tactic-recon",
            },
            {
                "node_id": "act-host",
                "level": "Action",
                "name": "host_discovery",
                "parent_id": "tech-host",
                "operator_id": "op_host_discovery",
                "target": "192.168.56.10",
                "inputs": {"host": "192.168.56.10"},
                "outputs": ["is_alive", "response_type", "confidence"],
                "depends_on": [],
                "risk_level": "low",
                "requires_human_approval": False,
                "allowed_tools": ["mock_adapter"],
                "status": "ready",
            },
        ],
        "edges": [
            {"edge_type": "contains", "from": "goal-001", "to": "tactic-recon"},
            {"edge_type": "contains", "from": "tactic-recon", "to": "tech-host"},
            {"edge_type": "contains", "from": "tech-host", "to": "act-host"},
        ],
        "metadata": {},
    }


def _credential_dag() -> dict:
    return {
        "graph_id": "ptt-dag-credential",
        "name": "credential approval placeholder",
        "selected_route_id": "route_credential_risk_assessment",
        "nodes": [
            {
                "node_id": "goal-001",
                "level": "Goal",
                "name": "credential_risk_assessment",
            },
            {
                "node_id": "tactic-cred",
                "level": "Tactic",
                "name": "credential_risk_assessment",
                "tactic_id": "credential_risk_assessment",
                "parent_id": "goal-001",
            },
            {
                "node_id": "tech-weak",
                "level": "Technique",
                "name": "weak_credential_check",
                "technique_id": "weak_credential_check",
                "parent_id": "tactic-cred",
            },
            {
                "node_id": "act-weak",
                "level": "Action",
                "name": "weak_credential_check",
                "parent_id": "tech-weak",
                "operator_id": "op_weak_credential_check",
                "target": "192.168.56.10",
                "inputs": {
                    "host": "192.168.56.10",
                    "port": 22,
                    "service_name": "ssh",
                },
                "outputs": ["credential_risk_status", "evidence"],
                "depends_on": [],
                "risk_level": "high",
                "requires_human_approval": True,
                "allowed_tools": ["mock_adapter"],
                "status": "waiting_approval",
            },
        ],
        "edges": [
            {"edge_type": "contains", "from": "goal-001", "to": "tactic-cred"},
            {"edge_type": "contains", "from": "tactic-cred", "to": "tech-weak"},
            {"edge_type": "contains", "from": "tech-weak", "to": "act-weak"},
        ],
        "metadata": {},
    }


def _validate(dag: dict, *, allowed_route_ids=None):
    return validate_ptt_dag(
        dag,
        _routes(),
        _mapping(),
        _operators(),
        _tools(),
        validation_policy=_validation_policy(),
        safety_policy=_safety_policy(),
        approval_policy=_approval_policy(),
        allowed_route_ids=allowed_route_ids,
    )


def test_validate_route_selection_rejects_disabled_route() -> None:
    result = validate_route_selection(
        "route_credential_risk_assessment",
        _routes(),
        validation_policy=_validation_policy(),
    )

    assert not result.valid
    assert any("disabled" in error for error in result.errors)


def test_validate_technique_selection_accepts_tactic_grouped_output() -> None:
    selected_route = _routes()[0]
    selection = {
        "selected_techniques_by_tactic": [
            {
                "tactic_id": "reconnaissance",
                "selected_techniques": ["host_discovery"],
                "reasoning_summary": "low risk discovery",
                "requires_human_approval": False,
            },
            {
                "tactic_id": "discovery",
                "selected_techniques": ["port_discovery"],
                "reasoning_summary": "identify open ports",
                "requires_human_approval": False,
            },
        ],
        "overall_reasoning_summary": "bounded route technique selection",
    }

    result = validate_technique_selection(
        selection,
        selected_route,
        _mapping(),
        validation_policy=_validation_policy(),
    )

    assert result.valid, result.errors


def test_validate_technique_selection_rejects_flat_only_output() -> None:
    selected_route = _routes()[0]
    selection = {
        "selected_techniques": ["host_discovery"],
        "overall_reasoning_summary": "legacy output",
    }

    result = validate_technique_selection(
        selection,
        selected_route,
        _mapping(),
        validation_policy=_validation_policy(),
    )

    assert not result.valid
    assert any("flat selected_techniques-only" in error for error in result.errors)


def test_validate_technique_selection_rejects_wrong_tactic_candidate() -> None:
    selected_route = _routes()[0]
    selection = {
        "selected_techniques_by_tactic": [
            {
                "tactic_id": "reconnaissance",
                "selected_techniques": ["port_discovery"],
                "reasoning_summary": "wrong tactic",
                "requires_human_approval": False,
            }
        ],
        "overall_reasoning_summary": "bounded route technique selection",
    }

    result = validate_technique_selection(
        selection,
        selected_route,
        _mapping(),
        validation_policy=_validation_policy(),
    )

    assert not result.valid
    assert any("not a candidate for this tactic" in error for error in result.errors)


def test_validate_ptt_dag_accepts_valid_basic_dag() -> None:
    result = _validate(_basic_dag())

    assert result.valid, result.errors


def test_validate_ptt_dag_rejects_unknown_operator_id() -> None:
    dag = _basic_dag()
    dag["nodes"][3]["operator_id"] = "op_not_registered"

    result = _validate(dag)

    assert not result.valid
    assert any("unknown operator_id" in error for error in result.errors)


def test_validate_ptt_dag_rejects_invalid_contains_level() -> None:
    dag = _basic_dag()
    dag["edges"][0] = {"edge_type": "contains", "from": "goal-001", "to": "act-host"}

    result = _validate(dag)

    assert not result.valid
    assert any("contains edge has invalid levels" in error for error in result.errors)


def test_validate_ptt_dag_rejects_depends_on_between_non_actions() -> None:
    dag = _basic_dag()
    dag["edges"].append({"edge_type": "depends_on", "from": "tech-host", "to": "act-host"})

    result = _validate(dag)

    assert not result.valid
    assert any("depends_on edge must be Action -> Action" in error for error in result.errors)


def test_validate_ptt_dag_rejects_depends_on_cycle() -> None:
    dag = _basic_dag()
    action = deepcopy(dag["nodes"][3])
    action["node_id"] = "act-host-2"
    dag["nodes"].append(action)
    dag["edges"].extend(
        [
            {"edge_type": "contains", "from": "tech-host", "to": "act-host-2"},
            {"edge_type": "depends_on", "from": "act-host", "to": "act-host-2"},
            {"edge_type": "depends_on", "from": "act-host-2", "to": "act-host"},
        ]
    )

    result = _validate(dag)

    assert not result.valid
    assert any("acyclic" in error for error in result.errors)


def test_validate_ptt_dag_rejects_high_risk_action_without_waiting_approval() -> None:
    dag = _credential_dag()
    dag["nodes"][3]["status"] = "ready"

    result = _validate(
        dag,
        allowed_route_ids=["route_credential_risk_assessment"],
    )

    assert not result.valid
    assert any("waiting_approval" in error for error in result.errors)


def test_validate_ptt_dag_rejects_unknown_allowed_tool() -> None:
    dag = _basic_dag()
    dag["nodes"][3]["allowed_tools"] = ["missing_adapter"]

    result = _validate(dag)

    assert not result.valid
    assert any("unknown allowed_tools" in error for error in result.errors)


def test_validate_ptt_dag_rejects_target_outside_scope() -> None:
    dag = _basic_dag()
    dag["nodes"][3]["target"] = "10.0.0.1"

    result = _validate(dag)

    assert not result.valid
    assert any("outside authorized scope" in error for error in result.errors)
