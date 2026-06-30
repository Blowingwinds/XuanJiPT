"""Operator registry for phase-one action templates."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .models import OperatorTemplate


REQUIRED_SIDE_EFFECT_KEYS = {
    "network_noise",
    "service_disruption",
    "credential_exposure",
    "state_change",
    "audit_log_impact",
}
VALID_RISK_LEVELS = {"low", "medium", "high", "critical"}


@dataclass(slots=True)
class RegistryValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class OperatorRegistry:
    def __init__(self, operators: list[OperatorTemplate]) -> None:
        duplicates = _duplicates(operator.operator_id for operator in operators)
        if duplicates:
            raise ValueError(f"Duplicate operator_id values: {', '.join(sorted(duplicates))}")
        self._operators = {operator.operator_id: operator for operator in operators}

    @classmethod
    def from_dicts(cls, operator_dicts: list[dict]) -> "OperatorRegistry":
        return cls([OperatorTemplate.from_dict(operator) for operator in operator_dicts])

    def get(self, operator_id: str) -> OperatorTemplate | None:
        return self._operators.get(operator_id)

    def exists(self, operator_id: str) -> bool:
        return operator_id in self._operators

    def all(self) -> list[OperatorTemplate]:
        return list(self._operators.values())

    def operator_ids(self) -> set[str]:
        return set(self._operators)

    def for_technique(self, technique_id: str) -> list[OperatorTemplate]:
        return [
            operator
            for operator in self._operators.values()
            if technique_id in operator.mapped_techniques
        ]

    def validate_static_rules(self, known_tool_ids: set[str] | None = None) -> RegistryValidationResult:
        errors: list[str] = []
        warnings: list[str] = []

        for operator in self._operators.values():
            raw = operator.raw
            _validate_operator_required_fields(operator, errors)
            _validate_operator_risk(operator, errors)
            _validate_side_effects(operator, errors)
            _validate_result_schema(operator, errors)
            if known_tool_ids is not None:
                unknown_tools = sorted(set(operator.allowed_tools) - known_tool_ids)
                if unknown_tools:
                    errors.append(
                        f"{operator.operator_id}: unknown allowed_tools: {', '.join(unknown_tools)}"
                    )
            if raw.get("description", "") == "":
                warnings.append(f"{operator.operator_id}: description is empty")

        return RegistryValidationResult(valid=not errors, errors=errors, warnings=warnings)

    def validate_technique_mapping(self, mapping: dict) -> RegistryValidationResult:
        errors: list[str] = []
        warnings: list[str] = []
        techniques = mapping.get("techniques", {})

        for technique_id, item in techniques.items():
            candidate_ids = item.get("candidate_operators", [])
            if not candidate_ids:
                errors.append(f"{technique_id}: candidate_operators is empty")
            for operator_id in candidate_ids:
                operator = self.get(operator_id)
                if operator is None:
                    errors.append(f"{technique_id}: unknown operator_id {operator_id}")
                    continue
                if technique_id not in operator.mapped_techniques:
                    warnings.append(
                        f"{technique_id}: {operator_id} does not list this technique in mapped_techniques"
                    )

        return RegistryValidationResult(valid=not errors, errors=errors, warnings=warnings)


def _validate_operator_required_fields(
    operator: OperatorTemplate,
    errors: list[str],
) -> None:
    if not operator.operator_id:
        errors.append("operator_id is empty")
    if not operator.name:
        errors.append(f"{operator.operator_id}: name is empty")
    if not operator.mapped_techniques:
        errors.append(f"{operator.operator_id}: mapped_techniques is empty")
    if not operator.outputs:
        errors.append(f"{operator.operator_id}: outputs is empty")
    if not operator.allowed_tools:
        errors.append(f"{operator.operator_id}: allowed_tools is empty")


def _validate_operator_risk(operator: OperatorTemplate, errors: list[str]) -> None:
    if operator.risk_level not in VALID_RISK_LEVELS:
        errors.append(f"{operator.operator_id}: invalid risk_level {operator.risk_level}")
    if operator.risk_level in {"high", "critical"} and not operator.requires_human_approval:
        errors.append(f"{operator.operator_id}: high or critical risk requires human approval")


def _validate_side_effects(operator: OperatorTemplate, errors: list[str]) -> None:
    side_effects = operator.raw.get("side_effects", {})
    missing = REQUIRED_SIDE_EFFECT_KEYS - set(side_effects)
    if missing:
        errors.append(f"{operator.operator_id}: missing side_effects: {', '.join(sorted(missing))}")


def _validate_result_schema(operator: OperatorTemplate, errors: list[str]) -> None:
    result_schema = operator.raw.get("result_schema", {})
    missing = set(operator.outputs) - set(result_schema)
    if missing:
        errors.append(f"{operator.operator_id}: result_schema missing outputs: {', '.join(sorted(missing))}")


def _duplicates(values: Iterable[str]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return duplicates
