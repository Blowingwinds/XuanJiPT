"""Programmatic validation for constrained PTT-DAG planning.

The validator is the final guard between LLM drafts/templates and any
downstream scheduler. Rules are enabled by policy dictionaries loaded from
config/, while route, Technique, Operator, and tool facts come from data/.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from ipaddress import ip_address, ip_network
from typing import Any

from .models import OperatorTemplate, PTTDAG, PTTNode, ToolSpec
from .route_selector import extract_candidate_techniques, get_route_by_id


@dataclass(slots=True)
class ValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


CONTAINS_LEVEL_PAIRS = {
    ("Goal", "Tactic"),
    ("Tactic", "Technique"),
    ("Technique", "Action"),
}


def validate_scaffold() -> ValidationResult:
    return ValidationResult(valid=True)


def validate_route_selection(
    selected_route_id: str,
    routes: list[dict[str, Any]],
    *,
    allowed_route_ids: set[str] | list[str] | tuple[str, ...] | None = None,
    validation_policy: dict[str, Any] | None = None,
) -> ValidationResult:
    """Validate that a selected route exists, is enabled, and is allowed."""

    errors: list[str] = []
    policy = _dag_policy(validation_policy)
    route = get_route_by_id(routes, selected_route_id)

    if not selected_route_id:
        errors.append("selected_route_id is required")
    elif route is None and policy.get("reject_unknown_route_ids", True):
        errors.append(f"unknown selected_route_id: {selected_route_id}")

    if route is not None and not route.get("enabled", False):
        errors.append(f"selected route is disabled: {selected_route_id}")

    allowed = set(allowed_route_ids or [])
    if selected_route_id and allowed and selected_route_id not in allowed:
        errors.append(f"selected route is not in allowed_route_ids: {selected_route_id}")

    return ValidationResult(valid=not errors, errors=errors)


def validate_technique_selection(
    selection: dict[str, Any],
    selected_route: dict[str, Any],
    technique_mapping: dict[str, Any],
    *,
    validation_policy: dict[str, Any] | None = None,
) -> ValidationResult:
    """Validate LLM/rule output for tactic-grouped Technique selection."""

    errors: list[str] = []
    warnings: list[str] = []
    policy = _technique_selection_policy(validation_policy)

    has_grouped = "selected_techniques_by_tactic" in selection
    has_flat = "selected_techniques" in selection
    if policy.get("reject_flat_selected_techniques_only", True) and has_flat and not has_grouped:
        errors.append("flat selected_techniques-only format is not allowed")
    if policy.get("require_selected_techniques_by_tactic", True) and not has_grouped:
        errors.append("selected_techniques_by_tactic is required")
        return ValidationResult(valid=False, errors=errors, warnings=warnings)
    if not isinstance(selection.get("selected_techniques_by_tactic"), list):
        errors.append("selected_techniques_by_tactic must be a list")
        return ValidationResult(valid=False, errors=errors, warnings=warnings)

    if (
        policy.get("require_overall_reasoning_summary", False)
        and "overall_reasoning_summary" not in selection
    ):
        errors.append("overall_reasoning_summary is required")

    tactic_candidates = _candidate_techniques_by_tactic(selected_route)
    known_techniques = set(technique_mapping.get("techniques", {}))

    for index, item in enumerate(selection["selected_techniques_by_tactic"]):
        if not isinstance(item, dict):
            errors.append(f"selected_techniques_by_tactic[{index}] must be an object")
            continue

        tactic_id = item.get("tactic_id")
        if policy.get("require_tactic_ids_from_selected_route", True) and tactic_id not in tactic_candidates:
            errors.append(f"unknown tactic_id for selected route: {tactic_id}")
            continue

        selected = item.get("selected_techniques")
        if not isinstance(selected, list):
            errors.append(f"{tactic_id}: selected_techniques must be a list")
            continue

        allowed_for_tactic = set(tactic_candidates.get(tactic_id, []))
        for technique_id in selected:
            if (
                policy.get("require_techniques_from_matching_tactic_candidates", True)
                and technique_id not in allowed_for_tactic
            ):
                errors.append(
                    f"{tactic_id}: technique is not a candidate for this tactic: {technique_id}"
                )
            if policy.get("reject_unknown_techniques", True) and technique_id not in known_techniques:
                errors.append(f"{tactic_id}: unknown technique_id: {technique_id}")

        if item.get("requires_human_approval") is None:
            warnings.append(f"{tactic_id}: requires_human_approval is not set")

    return ValidationResult(valid=not errors, errors=errors, warnings=warnings)


def validate_ptt_dag(
    dag: PTTDAG | dict[str, Any],
    routes: list[dict[str, Any]],
    technique_mapping: dict[str, Any],
    operators: list[dict[str, Any] | OperatorTemplate],
    tools: list[dict[str, Any] | ToolSpec],
    *,
    validation_policy: dict[str, Any] | None = None,
    safety_policy: dict[str, Any] | None = None,
    approval_policy: dict[str, Any] | None = None,
    allowed_route_ids: set[str] | list[str] | tuple[str, ...] | None = None,
) -> ValidationResult:
    """Validate a generated PTT-DAG before scheduler/adapters may use it."""

    dag_obj = dag if isinstance(dag, PTTDAG) else PTTDAG.from_dict(dag)
    policy = _dag_policy(validation_policy)
    errors: list[str] = []
    warnings: list[str] = []

    if policy.get("require_graph_id", True) and not dag_obj.graph_id:
        errors.append("graph_id is required")
    if policy.get("require_selected_route_id", True) and not dag_obj.selected_route_id:
        errors.append("selected_route_id is required")

    route_result = validate_route_selection(
        dag_obj.selected_route_id,
        routes,
        allowed_route_ids=allowed_route_ids,
        validation_policy=validation_policy,
    )
    errors.extend(route_result.errors)
    warnings.extend(route_result.warnings)

    selected_route = get_route_by_id(routes, dag_obj.selected_route_id)
    allowed_route_techniques = (
        set(extract_candidate_techniques(selected_route)) if selected_route is not None else set()
    )
    tactic_ids = {tactic.get("tactic_id") for tactic in selected_route.get("tactics", [])} if selected_route else set()

    nodes_by_id = _nodes_by_id(dag_obj.nodes, errors, require_unique=policy.get("require_node_ids_unique", True))
    _validate_goal_count(dag_obj.nodes, errors, policy)
    _validate_nodes_against_route_and_mapping(
        dag_obj.nodes,
        errors,
        warnings,
        allowed_route_techniques,
        tactic_ids,
        technique_mapping,
        _operators_by_id(operators),
        _tools_by_id(tools),
        policy,
        safety_policy or {},
        approval_policy or {},
    )
    _validate_edges(dag_obj.edges, nodes_by_id, errors, policy)

    return ValidationResult(valid=not errors, errors=errors, warnings=warnings)


def _validate_goal_count(
    nodes: list[PTTNode],
    errors: list[str],
    policy: dict[str, Any],
) -> None:
    if not policy.get("require_single_goal_node", True):
        return
    goal_count = sum(1 for node in nodes if node.level == "Goal")
    if goal_count != 1:
        errors.append(f"PTT-DAG must contain exactly one Goal node, found {goal_count}")


def _validate_nodes_against_route_and_mapping(
    nodes: list[PTTNode],
    errors: list[str],
    warnings: list[str],
    allowed_route_techniques: set[str],
    tactic_ids: set[str],
    technique_mapping: dict[str, Any],
    operators_by_id: dict[str, OperatorTemplate],
    tools_by_id: dict[str, ToolSpec],
    policy: dict[str, Any],
    safety_policy: dict[str, Any],
    approval_policy: dict[str, Any],
) -> None:
    known_techniques = set(technique_mapping.get("techniques", {}))
    nodes_by_id = {node.node_id: node for node in nodes}

    for node in nodes:
        if node.level == "Tactic":
            tactic_id = _semantic_id(node, "tactic_id")
            if tactic_ids and tactic_id not in tactic_ids:
                errors.append(f"{node.node_id}: tactic_id is not in selected route: {tactic_id}")

        if node.level == "Technique":
            technique_id = _semantic_id(node, "technique_id")
            if policy.get("reject_unknown_techniques", True) and technique_id not in known_techniques:
                errors.append(f"{node.node_id}: unknown technique_id: {technique_id}")
            if allowed_route_techniques and technique_id not in allowed_route_techniques:
                errors.append(
                    f"{node.node_id}: technique is not a candidate for selected route: {technique_id}"
                )

        if node.level == "Action":
            _validate_action_node(
                node,
                nodes_by_id,
                errors,
                warnings,
                technique_mapping,
                operators_by_id,
                tools_by_id,
                policy,
                safety_policy,
                approval_policy,
            )


def _validate_action_node(
    node: PTTNode,
    nodes_by_id: dict[str, PTTNode],
    errors: list[str],
    warnings: list[str],
    technique_mapping: dict[str, Any],
    operators_by_id: dict[str, OperatorTemplate],
    tools_by_id: dict[str, ToolSpec],
    policy: dict[str, Any],
    safety_policy: dict[str, Any],
    approval_policy: dict[str, Any],
) -> None:
    operator_id = node.attributes.get("operator_id")
    if policy.get("require_action_operator_id", True) and not operator_id:
        errors.append(f"{node.node_id}: Action must bind operator_id")
        return

    operator = operators_by_id.get(operator_id)
    if policy.get("require_action_operator_exists", True) and operator is None:
        errors.append(f"{node.node_id}: unknown operator_id: {operator_id}")
        return

    if policy.get("require_action_target_in_scope", False):
        target = node.attributes.get("target")
        if target is None:
            errors.append(f"{node.node_id}: target is required for scope validation")
        elif not _target_in_scope(target, safety_policy):
            errors.append(f"{node.node_id}: target is outside authorized scope: {target}")

    if operator is not None:
        _validate_action_operator_matches_parent_technique(
            node,
            nodes_by_id,
            operator,
            technique_mapping,
            errors,
        )
        _validate_action_tools(node, operator, tools_by_id, errors, warnings, policy)
        _validate_action_risk_and_approval(
            node,
            operator,
            errors,
            policy,
            safety_policy,
            approval_policy,
        )


def _validate_action_operator_matches_parent_technique(
    node: PTTNode,
    nodes_by_id: dict[str, PTTNode],
    operator: OperatorTemplate,
    technique_mapping: dict[str, Any],
    errors: list[str],
) -> None:
    parent = nodes_by_id.get(node.parent_id or "")
    if parent is None or parent.level != "Technique":
        return

    technique_id = _semantic_id(parent, "technique_id")
    candidate_ids = set(
        technique_mapping.get("techniques", {})
        .get(technique_id, {})
        .get("candidate_operators", [])
    )
    if candidate_ids and operator.operator_id not in candidate_ids:
        errors.append(
            f"{node.node_id}: operator_id {operator.operator_id} is not a candidate for technique {technique_id}"
        )


def _validate_action_tools(
    node: PTTNode,
    operator: OperatorTemplate,
    tools_by_id: dict[str, ToolSpec],
    errors: list[str],
    warnings: list[str],
    policy: dict[str, Any],
) -> None:
    if not policy.get("require_action_allowed_tools_known", True):
        return

    known_tool_ids = set(tools_by_id)
    operator_unknown_tools = set(operator.allowed_tools) - known_tool_ids
    if operator_unknown_tools:
        errors.append(
            f"{operator.operator_id}: unknown allowed_tools: {', '.join(sorted(operator_unknown_tools))}"
        )

    action_tools = node.attributes.get("allowed_tools", operator.allowed_tools)
    if not isinstance(action_tools, list):
        errors.append(f"{node.node_id}: allowed_tools must be a list")
        return

    unknown_action_tools = set(action_tools) - known_tool_ids
    if unknown_action_tools:
        errors.append(
            f"{node.node_id}: unknown allowed_tools: {', '.join(sorted(unknown_action_tools))}"
        )

    undeclared_action_tools = set(action_tools) - set(operator.allowed_tools)
    if undeclared_action_tools:
        errors.append(
            f"{node.node_id}: allowed_tools not declared by operator template: "
            f"{', '.join(sorted(undeclared_action_tools))}"
        )

    unsupported_tools = [
        tool_id
        for tool_id in action_tools
        if tool_id in tools_by_id and operator.operator_id not in tools_by_id[tool_id].supported_operators
    ]
    if unsupported_tools:
        errors.append(
            f"{node.node_id}: tools do not support operator {operator.operator_id}: "
            f"{', '.join(sorted(unsupported_tools))}"
        )

    if not action_tools:
        warnings.append(f"{node.node_id}: allowed_tools is empty")


def _validate_action_risk_and_approval(
    node: PTTNode,
    operator: OperatorTemplate,
    errors: list[str],
    policy: dict[str, Any],
    safety_policy: dict[str, Any],
    approval_policy: dict[str, Any],
) -> None:
    if not policy.get("require_action_risk_within_policy", True):
        return

    valid_risk_levels = set(safety_policy.get("risk", {}).get("levels", []))
    action_risk = node.attributes.get("risk_level", operator.risk_level)
    if valid_risk_levels and action_risk not in valid_risk_levels:
        errors.append(f"{node.node_id}: invalid risk_level: {action_risk}")

    if _risk_index(action_risk, valid_risk_levels) < _risk_index(operator.risk_level, valid_risk_levels):
        errors.append(
            f"{node.node_id}: action risk_level {action_risk} is lower than operator risk_level {operator.risk_level}"
        )

    approval_levels = set(
        approval_policy.get("approval", {}).get(
            "required_for_risk_levels",
            safety_policy.get("risk", {}).get("require_approval_levels", []),
        )
    )
    requires_approval = (
        operator.requires_human_approval
        or bool(node.attributes.get("requires_human_approval", False))
        or action_risk in approval_levels
    )

    if policy.get("require_high_risk_waiting_approval", True) and requires_approval:
        required_status = approval_policy.get("approval", {}).get(
            "status_when_required",
            safety_policy.get("actions", {}).get("high_risk_action_status", "waiting_approval"),
        )
        if node.attributes.get("requires_human_approval", operator.requires_human_approval) is not True:
            errors.append(f"{node.node_id}: high-risk Action must set requires_human_approval true")
        if node.status != required_status:
            errors.append(f"{node.node_id}: high-risk Action must be {required_status}")


def _validate_edges(
    edges: list,
    nodes_by_id: dict[str, PTTNode],
    errors: list[str],
    policy: dict[str, Any],
) -> None:
    action_dependencies: dict[str, list[str]] = {}

    for edge in edges:
        source = nodes_by_id.get(edge.source)
        target = nodes_by_id.get(edge.target)

        if policy.get("require_edge_endpoints_exist", True) and (source is None or target is None):
            errors.append(f"{edge.edge_type}: edge endpoint does not exist: {edge.source} -> {edge.target}")
            continue

        if source is None or target is None:
            continue

        if edge.edge_type == "contains":
            if (
                policy.get("require_contains_edges_match_levels", True)
                and (source.level, target.level) not in CONTAINS_LEVEL_PAIRS
            ):
                errors.append(
                    f"contains edge has invalid levels: {source.level} -> {target.level} "
                    f"({edge.source} -> {edge.target})"
                )
        elif edge.edge_type == "depends_on":
            if policy.get("require_depends_on_action_only", True) and (
                source.level != "Action" or target.level != "Action"
            ):
                errors.append(
                    f"depends_on edge must be Action -> Action: {edge.source} -> {edge.target}"
                )
            else:
                action_dependencies.setdefault(edge.source, []).append(edge.target)

    if policy.get("require_depends_on_acyclic", True):
        cycle = _find_cycle(action_dependencies)
        if cycle:
            errors.append(f"depends_on edges must be acyclic: {' -> '.join(cycle)}")


def _nodes_by_id(
    nodes: list[PTTNode],
    errors: list[str],
    *,
    require_unique: bool,
) -> dict[str, PTTNode]:
    by_id: dict[str, PTTNode] = {}
    duplicates: set[str] = set()
    for node in nodes:
        if node.node_id in by_id:
            duplicates.add(node.node_id)
        by_id[node.node_id] = node
    if require_unique and duplicates:
        errors.append(f"duplicate node_id values: {', '.join(sorted(duplicates))}")
    return by_id


def _find_cycle(graph: dict[str, list[str]]) -> list[str]:
    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = []

    def visit(node_id: str) -> list[str]:
        if node_id in visiting:
            cycle_start = stack.index(node_id)
            return stack[cycle_start:] + [node_id]
        if node_id in visited:
            return []
        visiting.add(node_id)
        stack.append(node_id)
        for next_id in graph.get(node_id, []):
            cycle = visit(next_id)
            if cycle:
                return cycle
        stack.pop()
        visiting.remove(node_id)
        visited.add(node_id)
        return []

    for node_id in graph:
        cycle = visit(node_id)
        if cycle:
            return cycle
    return []


def _operators_by_id(operators: list[dict[str, Any] | OperatorTemplate]) -> dict[str, OperatorTemplate]:
    converted: dict[str, OperatorTemplate] = {}
    for operator in operators:
        item = operator if isinstance(operator, OperatorTemplate) else OperatorTemplate.from_dict(operator)
        converted[item.operator_id] = item
    return converted


def _tools_by_id(tools: list[dict[str, Any] | ToolSpec]) -> dict[str, ToolSpec]:
    converted: dict[str, ToolSpec] = {}
    for tool in tools:
        item = tool if isinstance(tool, ToolSpec) else ToolSpec.from_dict(tool)
        converted[item.tool_id] = item
    return converted


def _candidate_techniques_by_tactic(route: dict[str, Any]) -> dict[str, list[str]]:
    return {
        tactic.get("tactic_id"): list(tactic.get("candidate_techniques", []))
        for tactic in route.get("tactics", [])
    }


def _semantic_id(node: PTTNode, attribute_name: str) -> str:
    return str(node.attributes.get(attribute_name) or node.name)


def _target_in_scope(target: Any, safety_policy: dict[str, Any]) -> bool:
    scope = safety_policy.get("scope", {})
    allowed_targets = scope.get("allowed_targets", [])
    denied_targets = scope.get("denied_targets", [])
    require_explicit = scope.get("require_explicit_scope_match", True)
    target_values = _target_values(target)

    if not target_values:
        return False

    allowed_match = any(_value_in_networks(value, allowed_targets) for value in target_values)
    if allowed_match:
        return True

    denied_match = any(_value_in_networks(value, denied_targets) for value in target_values)
    if denied_match:
        return False

    return not require_explicit


def _target_values(target: Any) -> list[str]:
    if isinstance(target, str):
        return [target]
    if isinstance(target, dict):
        values: list[str] = []
        for key in ("host", "ip", "address", "url"):
            value = target.get(key)
            if isinstance(value, str):
                values.append(value)
        return values
    if isinstance(target, list):
        values = []
        for item in target:
            values.extend(_target_values(item))
        return values
    return []


def _value_in_networks(value: str, networks: list[str]) -> bool:
    host = value
    if "://" in host:
        host = host.split("://", 1)[1].split("/", 1)[0].split(":", 1)[0]
    try:
        address = ip_address(host)
    except ValueError:
        return host in networks
    for network in networks:
        try:
            if address in ip_network(network, strict=False):
                return True
        except ValueError:
            if host == network:
                return True
    return False


def _risk_index(risk_level: str, configured_levels: set[str]) -> int:
    ordered = ["low", "medium", "high", "critical"]
    if configured_levels:
        ordered = [level for level in ordered if level in configured_levels]
    try:
        return ordered.index(risk_level)
    except ValueError:
        return -1


def _dag_policy(validation_policy: dict[str, Any] | None) -> dict[str, Any]:
    return (validation_policy or {}).get("ptt_dag_validation", {})


def _technique_selection_policy(validation_policy: dict[str, Any] | None) -> dict[str, Any]:
    return (validation_policy or {}).get("llm_output_validation", {}).get("technique_selection", {})
