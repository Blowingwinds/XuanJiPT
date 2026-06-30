"""Rule-first PTT-DAG planner.

The planner instantiates a graph from controlled route, Technique, and
Operator Template inputs. It does not select routes, invent techniques,
generate commands, or make the final safety decision; validator.py remains
the programmatic gate before execution.
"""

from __future__ import annotations

from typing import Any

from .models import OperatorTemplate, PTTEdge, PTTDAG, PTTNode


DEFAULT_RISK_ORDER = ["low", "medium", "high", "critical"]


def plan_from_route(
    request: dict[str, Any],
    route: dict[str, Any],
    technique_mapping: dict[str, Any] | None = None,
    operator_templates: list[dict[str, Any] | OperatorTemplate] | None = None,
    *,
    safety_policy: dict[str, Any] | None = None,
    approval_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a PTT-DAG from a selected route and constrained Technique set.

    If request contains ``selected_techniques_by_tactic``, only those grouped
    selections are instantiated. Otherwise, the route's
    ``default_selected_techniques`` are grouped by the route tactics.
    """

    if technique_mapping is None:
        raise ValueError("technique_mapping is required")
    if operator_templates is None:
        raise ValueError("operator_templates is required")
    if not route.get("enabled", False) and not _disabled_route_allowed(request):
        raise ValueError(f"route is disabled: {route.get('route_id')}")

    operators_by_id = _operators_by_id(operator_templates)
    selected_groups = _selected_techniques_by_tactic(request, route)

    graph_id = request.get("graph_id") or f"ptt-dag-{_slug(route['route_id'])}"
    goal_id = "goal-001"
    goal_node = PTTNode(
        node_id=goal_id,
        level="Goal",
        name=request.get("intent") or route.get("name", route["route_id"]),
        display_name=route.get("display_name", ""),
        description=str(request.get("goal", route.get("description", ""))),
        children=[],
        status="pending",
        attributes={"route_id": route["route_id"]},
    )

    nodes: list[PTTNode] = [goal_node]
    edges: list[PTTEdge] = []
    technique_action_ids: dict[str, list[str]] = {}
    action_nodes_by_id: dict[str, PTTNode] = {}
    action_counter = 1

    for tactic in route.get("tactics", []):
        tactic_id = tactic.get("tactic_id")
        selected_techniques = selected_groups.get(tactic_id, [])
        if not selected_techniques:
            continue

        tactic_node_id = f"tactic-{_slug(tactic_id)}"
        tactic_node = PTTNode(
            node_id=tactic_node_id,
            level="Tactic",
            name=tactic_id,
            display_name=tactic.get("display_name", ""),
            parent_id=goal_id,
            children=[],
            status="pending",
            attributes={"tactic_id": tactic_id},
        )
        nodes.append(tactic_node)
        goal_node.children.append(tactic_node_id)
        edges.append(PTTEdge(edge_type="contains", source=goal_id, target=tactic_node_id))

        candidate_techniques = set(tactic.get("candidate_techniques", []))
        for technique_id in selected_techniques:
            if technique_id not in candidate_techniques:
                raise ValueError(f"{tactic_id}: technique is not a tactic candidate: {technique_id}")

            technique_node_id = f"tech-{_slug(technique_id)}"
            technique_node = PTTNode(
                node_id=technique_node_id,
                level="Technique",
                name=technique_id,
                parent_id=tactic_node_id,
                children=[],
                status="pending",
                attributes={"technique_id": technique_id},
            )
            nodes.append(technique_node)
            tactic_node.children.append(technique_node_id)
            edges.append(
                PTTEdge(edge_type="contains", source=tactic_node_id, target=technique_node_id)
            )

            operator_ids = _candidate_operator_ids(technique_mapping, technique_id)
            for operator_id in operator_ids:
                operator = operators_by_id.get(operator_id)
                if operator is None:
                    raise ValueError(f"{technique_id}: unknown operator_id {operator_id}")
                if not _risk_allowed(operator.risk_level, request, route, safety_policy or {}):
                    raise ValueError(
                        f"{operator.operator_id}: risk_level {operator.risk_level} exceeds request constraints"
                    )

                action_id = f"act-{_slug(operator.name)}-{action_counter:03d}"
                action_counter += 1
                action_node = _build_action_node(
                    action_id,
                    technique_node_id,
                    technique_id,
                    operator,
                    request,
                    safety_policy or {},
                    approval_policy or {},
                )
                nodes.append(action_node)
                action_nodes_by_id[action_id] = action_node
                technique_node.children.append(action_id)
                technique_action_ids.setdefault(technique_id, []).append(action_id)
                edges.append(
                    PTTEdge(edge_type="contains", source=technique_node_id, target=action_id)
                )

    _apply_execution_dependencies(
        route.get("execution_dependencies", []),
        technique_action_ids,
        action_nodes_by_id,
        edges,
    )

    dag = PTTDAG(
        graph_id=graph_id,
        name=route.get("name", route["route_id"]),
        description=route.get("description", ""),
        selected_route_id=route["route_id"],
        nodes=nodes,
        edges=edges,
        metadata={
            "created_by": "rule_based_planner",
            "requires_programmatic_validation": True,
            "selected_techniques_by_tactic": [
                {
                    "tactic_id": tactic_id,
                    "selected_techniques": techniques,
                }
                for tactic_id, techniques in selected_groups.items()
            ],
        },
    )
    return dag.to_dict()


def _selected_techniques_by_tactic(
    request: dict[str, Any],
    route: dict[str, Any],
) -> dict[str, list[str]]:
    if "selected_techniques" in request and "selected_techniques_by_tactic" not in request:
        raise ValueError("flat selected_techniques-only format is not allowed")

    if "selected_techniques_by_tactic" in request:
        grouped: dict[str, list[str]] = {}
        for item in request["selected_techniques_by_tactic"]:
            tactic_id = item.get("tactic_id")
            grouped[tactic_id] = list(item.get("selected_techniques", []))
        return grouped

    defaults = set(route.get("default_selected_techniques", []))
    grouped = {}
    for tactic in route.get("tactics", []):
        selected = [
            technique_id
            for technique_id in tactic.get("candidate_techniques", [])
            if technique_id in defaults
        ]
        if selected:
            grouped[tactic["tactic_id"]] = selected
    return grouped


def _candidate_operator_ids(technique_mapping: dict[str, Any], technique_id: str) -> list[str]:
    technique = technique_mapping.get("techniques", {}).get(technique_id)
    if technique is None:
        raise ValueError(f"unknown technique_id {technique_id}")
    operator_ids = list(technique.get("candidate_operators", []))
    if not operator_ids:
        raise ValueError(f"{technique_id}: candidate_operators is empty")
    return operator_ids


def _build_action_node(
    action_id: str,
    technique_node_id: str,
    technique_id: str,
    operator: OperatorTemplate,
    request: dict[str, Any],
    safety_policy: dict[str, Any],
    approval_policy: dict[str, Any],
) -> PTTNode:
    target = _primary_target(request)
    inputs = {
        field: _input_value(field, operator, request, target)
        for field in operator.required_inputs
    }
    requires_approval = _requires_approval(operator, approval_policy, safety_policy)
    waiting_status = approval_policy.get("approval", {}).get(
        "status_when_required",
        safety_policy.get("actions", {}).get("high_risk_action_status", "waiting_approval"),
    )
    status = waiting_status if requires_approval else "ready"

    return PTTNode(
        node_id=action_id,
        level="Action",
        name=operator.name,
        display_name=operator.raw.get("display_name", ""),
        description=operator.raw.get("description", ""),
        parent_id=technique_node_id,
        children=[],
        status=status,
        attributes={
            "technique_id": technique_id,
            "operator_id": operator.operator_id,
            "target": target,
            "inputs": inputs,
            "outputs": list(operator.outputs),
            "depends_on": [],
            "risk_level": operator.risk_level,
            "requires_human_approval": requires_approval,
            "allowed_tools": list(operator.allowed_tools),
            "category": operator.raw.get("category", ""),
            "side_effects": dict(operator.raw.get("side_effects", {})),
        },
    )


def _apply_execution_dependencies(
    dependencies: list[dict[str, str]],
    technique_action_ids: dict[str, list[str]],
    action_nodes_by_id: dict[str, PTTNode],
    edges: list[PTTEdge],
) -> None:
    for dependency in dependencies:
        source_actions = technique_action_ids.get(dependency.get("from"), [])
        target_actions = technique_action_ids.get(dependency.get("to"), [])
        for source_action_id in source_actions:
            for target_action_id in target_actions:
                edges.append(
                    PTTEdge(
                        edge_type="depends_on",
                        source=source_action_id,
                        target=target_action_id,
                    )
                )
                target_node = action_nodes_by_id[target_action_id]
                target_node.attributes["depends_on"].append(source_action_id)
                if target_node.status == "ready":
                    target_node.status = "pending"


def _operators_by_id(
    operator_templates: list[dict[str, Any] | OperatorTemplate],
) -> dict[str, OperatorTemplate]:
    operators: dict[str, OperatorTemplate] = {}
    for item in operator_templates:
        operator = item if isinstance(item, OperatorTemplate) else OperatorTemplate.from_dict(item)
        operators[operator.operator_id] = operator
    return operators


def _primary_target(request: dict[str, Any]) -> str:
    scope = request.get("scope", [])
    if isinstance(scope, list) and scope:
        return _target_from_value(scope[0])
    if isinstance(scope, str):
        return scope

    known_assets = request.get("known_assets", [])
    if known_assets:
        host = known_assets[0].get("host")
        if host:
            return str(host)
    raise ValueError("request must include scope or known_assets host")


def _target_from_value(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("host", "ip", "address", "url"):
            if value.get(key):
                return str(value[key])
    raise ValueError(f"unsupported scope target value: {value}")


def _input_value(
    field: str,
    operator: OperatorTemplate,
    request: dict[str, Any],
    target: str,
) -> Any:
    known_assets = request.get("known_assets", [])
    known_services = _known_services(request)

    if field == "host":
        return _host_from_target(target)
    if field == "port":
        return _first_known_port(known_assets, operator)
    if field == "url":
        return target if "://" in target else f"http://{target}"
    if field == "service_name":
        return _first_known_service_value(known_services, "service_name", "name", default="unknown")
    if field == "version":
        return _first_known_service_value(known_services, "version", default="unknown")
    if field == "services":
        return known_services
    if field == "assets":
        return known_assets or [{"host": _host_from_target(target)}]
    if field == "action_results":
        return []
    return None


def _known_services(request: dict[str, Any]) -> list[dict[str, Any]]:
    services: list[dict[str, Any]] = []
    for asset in request.get("known_assets", []):
        services.extend(asset.get("known_services", []))
    return services


def _first_known_port(known_assets: list[dict[str, Any]], operator: OperatorTemplate) -> int:
    for asset in known_assets:
        ports = asset.get("known_ports", [])
        if ports:
            return int(ports[0])
    if operator.operator_id == "op_tls_certificate":
        return 443
    return 80


def _first_known_service_value(
    known_services: list[dict[str, Any]],
    *keys: str,
    default: str,
) -> str:
    for service in known_services:
        for key in keys:
            value = service.get(key)
            if value:
                return str(value)
    return default


def _host_from_target(target: str) -> str:
    if "://" in target:
        return target.split("://", 1)[1].split("/", 1)[0].split(":", 1)[0]
    return target


def _requires_approval(
    operator: OperatorTemplate,
    approval_policy: dict[str, Any],
    safety_policy: dict[str, Any],
) -> bool:
    approval_levels = set(
        approval_policy.get("approval", {}).get(
            "required_for_risk_levels",
            safety_policy.get("risk", {}).get("require_approval_levels", []),
        )
    )
    return operator.requires_human_approval or operator.risk_level in approval_levels


def _risk_allowed(
    risk_level: str,
    request: dict[str, Any],
    route: dict[str, Any],
    safety_policy: dict[str, Any],
) -> bool:
    constraints = request.get("constraints", {})
    route_constraints = route.get("safety_constraints", {})
    if risk_level in {"high", "critical"} and not constraints.get(
        "allow_high_risk",
        route_constraints.get("allow_high_risk", False),
    ):
        return False

    max_risk = constraints.get(
        "max_risk_level",
        route_constraints.get(
            "max_risk_level",
            safety_policy.get("risk", {}).get("max_auto_execute_level"),
        ),
    )
    if not max_risk:
        return True

    risk_order = safety_policy.get("risk", {}).get("levels", DEFAULT_RISK_ORDER)
    return _risk_index(risk_level, risk_order) <= _risk_index(max_risk, risk_order)


def _risk_index(risk_level: str, risk_order: list[str]) -> int:
    try:
        return risk_order.index(risk_level)
    except ValueError:
        return len(risk_order)


def _disabled_route_allowed(request: dict[str, Any]) -> bool:
    constraints = request.get("constraints", {})
    return bool(
        request.get("allow_disabled_routes")
        or constraints.get("allow_disabled_routes")
        or constraints.get("allow_disabled_route")
    )


def _slug(value: str) -> str:
    return "".join(char if char.isalnum() else "-" for char in str(value).lower()).strip("-")
