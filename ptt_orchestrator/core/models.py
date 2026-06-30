"""Shared data models for the PTT-DAG prototype.

The model layer defines shape only. Runtime policy belongs in config/,
and knowledge templates belong in data/.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


NodeLevel = Literal["Goal", "Tactic", "Technique", "Action"]
EdgeType = Literal["contains", "depends_on", "data_flow"]
RiskLevel = Literal["low", "medium", "high", "critical"]
NodeStatus = Literal[
    "pending",
    "ready",
    "running",
    "success",
    "failed",
    "skipped",
    "waiting_approval",
]


@dataclass(slots=True)
class PTTNode:
    node_id: str
    level: NodeLevel
    name: str
    display_name: str = ""
    description: str = ""
    parent_id: str | None = None
    children: list[str] = field(default_factory=list)
    status: NodeStatus = "pending"
    attributes: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PTTNode":
        known_fields = {
            "node_id",
            "level",
            "name",
            "display_name",
            "description",
            "parent_id",
            "children",
            "status",
        }
        attributes = {key: value for key, value in data.items() if key not in known_fields}
        return cls(
            node_id=data["node_id"],
            level=data["level"],
            name=data["name"],
            display_name=data.get("display_name", ""),
            description=data.get("description", ""),
            parent_id=data.get("parent_id"),
            children=list(data.get("children", [])),
            status=data.get("status", "pending"),
            attributes=attributes,
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "node_id": self.node_id,
            "level": self.level,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "parent_id": self.parent_id,
            "children": self.children,
            "status": self.status,
        }
        data.update(self.attributes)
        return data


@dataclass(slots=True)
class PTTEdge:
    edge_type: EdgeType
    source: str
    target: str
    attributes: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PTTEdge":
        known_fields = {"edge_type", "from", "source", "to", "target"}
        attributes = {key: value for key, value in data.items() if key not in known_fields}
        return cls(
            edge_type=data["edge_type"],
            source=data.get("source", data.get("from")),
            target=data.get("target", data.get("to")),
            attributes=attributes,
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "edge_type": self.edge_type,
            "from": self.source,
            "to": self.target,
        }
        data.update(self.attributes)
        return data


@dataclass(slots=True)
class OperatorTemplate:
    operator_id: str
    name: str
    mapped_techniques: list[str]
    required_inputs: list[str]
    outputs: list[str]
    risk_level: RiskLevel
    requires_human_approval: bool
    allowed_tools: list[str]
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OperatorTemplate":
        return cls(
            operator_id=data["operator_id"],
            name=data["name"],
            mapped_techniques=list(data.get("mapped_techniques", [])),
            required_inputs=list(data.get("required_inputs", [])),
            outputs=list(data.get("outputs", [])),
            risk_level=data["risk_level"],
            requires_human_approval=bool(data.get("requires_human_approval", False)),
            allowed_tools=list(data.get("allowed_tools", [])),
            raw=dict(data),
        )

    def to_dict(self) -> dict[str, Any]:
        if self.raw:
            return dict(self.raw)
        return {
            "operator_id": self.operator_id,
            "name": self.name,
            "mapped_techniques": self.mapped_techniques,
            "required_inputs": self.required_inputs,
            "outputs": self.outputs,
            "risk_level": self.risk_level,
            "requires_human_approval": self.requires_human_approval,
            "allowed_tools": self.allowed_tools,
        }


@dataclass(slots=True)
class PTTDAG:
    graph_id: str
    name: str
    selected_route_id: str
    description: str = ""
    nodes: list[PTTNode] = field(default_factory=list)
    edges: list[PTTEdge] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PTTDAG":
        return cls(
            graph_id=data["graph_id"],
            name=data.get("name", ""),
            selected_route_id=data.get("selected_route_id", ""),
            description=data.get("description", ""),
            nodes=[PTTNode.from_dict(node) for node in data.get("nodes", [])],
            edges=[PTTEdge.from_dict(edge) for edge in data.get("edges", [])],
            metadata=dict(data.get("metadata", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "graph_id": self.graph_id,
            "name": self.name,
            "description": self.description,
            "selected_route_id": self.selected_route_id,
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
            "metadata": self.metadata,
        }

    def node_by_id(self) -> dict[str, PTTNode]:
        return {node.node_id: node for node in self.nodes}


@dataclass(slots=True)
class ToolSpec:
    tool_id: str
    name: str
    supported_operators: list[str]
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ToolSpec":
        return cls(
            tool_id=data["tool_id"],
            name=data.get("name", data["tool_id"]),
            supported_operators=list(data.get("supported_operators", [])),
            raw=dict(data),
        )
