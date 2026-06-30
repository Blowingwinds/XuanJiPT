"""Route selection helpers.

Route selection chooses a route template only. It does not instantiate
operators or actions; that belongs in planner.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class RouteSelectionResult:
    route: dict[str, Any] | None
    reason: str
    candidate_techniques: list[str] = field(default_factory=list)


def select_route(request: dict[str, Any], routes: list[dict[str, Any]]) -> RouteSelectionResult:
    allowed_route_ids = set(request.get("constraints", {}).get("allowed_route_ids", []))
    enabled_routes = _enabled_routes(routes, allowed_route_ids=allowed_route_ids)
    if not enabled_routes:
        return RouteSelectionResult(route=None, reason="no_enabled_route")

    intent = request.get("intent")
    for route in enabled_routes:
        if intent and intent in route.get("recommended_for", []):
            return RouteSelectionResult(
                route=route,
                reason=f"intent_matched:{intent}",
                candidate_techniques=extract_candidate_techniques(route),
            )

    return RouteSelectionResult(
        route=enabled_routes[0],
        reason="fallback_first_enabled_route",
        candidate_techniques=extract_candidate_techniques(enabled_routes[0]),
    )


def get_route_by_id(routes: list[dict[str, Any]], route_id: str) -> dict[str, Any] | None:
    for route in routes:
        if route.get("route_id") == route_id:
            return route
    return None


def extract_candidate_techniques(route: dict[str, Any]) -> list[str]:
    seen: set[str] = set()
    techniques: list[str] = []
    for tactic in route.get("tactics", []):
        for technique in tactic.get("candidate_techniques", []):
            if technique not in seen:
                techniques.append(technique)
                seen.add(technique)
    return techniques


def _enabled_routes(
    routes: list[dict[str, Any]],
    allowed_route_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    enabled = [route for route in routes if route.get("enabled")]
    if allowed_route_ids:
        enabled = [route for route in enabled if route.get("route_id") in allowed_route_ids]
    return enabled
