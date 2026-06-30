import pytest

from ptt_orchestrator.core.loaders import load_yaml
from ptt_orchestrator.core.models import OperatorTemplate
from ptt_orchestrator.core.operator_registry import OperatorRegistry


def test_operator_registry_loads_all_templates() -> None:
    data = load_yaml("data/operator_templates.yaml")
    registry = OperatorRegistry.from_dicts(data["operators"])

    assert len(registry.all()) == 15
    assert registry.exists("op_host_discovery")
    assert registry.get("op_port_scan").risk_level == "medium"


def test_operator_registry_rejects_duplicate_operator_ids() -> None:
    operator = OperatorTemplate.from_dict(
        {
            "operator_id": "op_duplicate",
            "name": "duplicate",
            "mapped_techniques": ["duplicate"],
            "required_inputs": [],
            "outputs": ["value"],
            "risk_level": "low",
            "requires_human_approval": False,
            "allowed_tools": ["mock_adapter"],
        }
    )

    with pytest.raises(ValueError, match="Duplicate operator_id"):
        OperatorRegistry([operator, operator])


def test_operator_registry_queries_by_technique() -> None:
    data = load_yaml("data/operator_templates.yaml")
    registry = OperatorRegistry.from_dicts(data["operators"])

    operators = registry.for_technique("web_information_discovery")
    operator_ids = {operator.operator_id for operator in operators}

    assert operator_ids == {"op_web_title", "op_web_header_analysis", "op_web_tech_stack"}


def test_operator_registry_static_rules_pass_for_current_templates() -> None:
    operators = load_yaml("data/operator_templates.yaml")["operators"]
    tools = load_yaml("data/tool_registry.yaml")["tools"]
    known_tool_ids = {tool["tool_id"] for tool in tools}
    registry = OperatorRegistry.from_dicts(operators)

    result = registry.validate_static_rules(known_tool_ids=known_tool_ids)

    assert result.valid, result.errors


def test_operator_registry_validates_technique_mapping() -> None:
    operators = load_yaml("data/operator_templates.yaml")["operators"]
    mapping = load_yaml("data/technique_operator_mapping.yaml")
    registry = OperatorRegistry.from_dicts(operators)

    result = registry.validate_technique_mapping(mapping)

    assert result.valid, result.errors
