from ptt_orchestrator.core.models import (
    OperatorTemplate,
    PTTEdge,
    PTTDAG,
    PTTNode,
    ToolSpec,
)


def test_ptt_node_preserves_action_attributes() -> None:
    node = PTTNode.from_dict(
        {
            "node_id": "act-001",
            "level": "Action",
            "name": "host_discovery",
            "operator_id": "op_host_discovery",
            "risk_level": "low",
        }
    )

    assert node.attributes["operator_id"] == "op_host_discovery"
    assert node.to_dict()["risk_level"] == "low"


def test_ptt_edge_accepts_json_from_to_fields() -> None:
    edge = PTTEdge.from_dict(
        {
            "edge_type": "depends_on",
            "from": "act-001",
            "to": "act-002",
            "fields": ["open_ports"],
        }
    )

    assert edge.source == "act-001"
    assert edge.target == "act-002"
    assert edge.to_dict()["fields"] == ["open_ports"]


def test_operator_template_from_dict() -> None:
    operator = OperatorTemplate.from_dict(
        {
            "operator_id": "op_host_discovery",
            "name": "host_discovery",
            "mapped_techniques": ["host_discovery"],
            "required_inputs": ["host"],
            "outputs": ["is_alive"],
            "risk_level": "low",
            "requires_human_approval": False,
            "allowed_tools": ["mock_adapter"],
        }
    )

    assert operator.operator_id == "op_host_discovery"
    assert operator.allowed_tools == ["mock_adapter"]


def test_ptt_dag_round_trip() -> None:
    dag = PTTDAG.from_dict(
        {
            "graph_id": "ptt-dag-001",
            "name": "basic",
            "selected_route_id": "route_basic_exposure_assessment",
            "nodes": [
                {
                    "node_id": "goal-001",
                    "level": "Goal",
                    "name": "basic_security_assessment",
                }
            ],
            "edges": [],
            "metadata": {"version": "0.1"},
        }
    )

    assert dag.node_by_id()["goal-001"].level == "Goal"
    assert dag.to_dict()["metadata"]["version"] == "0.1"


def test_tool_spec_from_dict() -> None:
    tool = ToolSpec.from_dict(
        {
            "tool_id": "mock_adapter",
            "name": "Mock Adapter",
            "supported_operators": ["op_host_discovery"],
        }
    )

    assert tool.supported_operators == ["op_host_discovery"]
