from pathlib import Path

import pytest

from ptt_orchestrator.core.loaders import load_yaml


ROOT = Path(__file__).resolve().parents[1]


def test_settings_paths_exist() -> None:
    settings = load_yaml("config/settings.yaml")

    for key, relative_path in settings["paths"].items():
        if key == "output_dir":
            continue
        assert (ROOT / relative_path).is_file(), f"Missing settings path {key}: {relative_path}"


def test_approval_policy_matches_safety_policy_risk_levels() -> None:
    safety_policy = load_yaml("config/safety_policy.yaml")
    approval_policy = load_yaml("config/approval_policy.yaml")

    safety_required = set(safety_policy["risk"]["require_approval_levels"])
    approval_required = set(approval_policy["approval"]["required_for_risk_levels"])

    assert approval_required == safety_required


def test_llm_policy_matches_safety_policy_forbidden_outputs() -> None:
    safety_policy = load_yaml("config/safety_policy.yaml")
    llm_policy = load_yaml("config/llm_policy.yaml")

    assert llm_policy["forbidden_outputs"]["allow_command_generation"] == safety_policy["llm"]["allow_command_generation"]
    assert llm_policy["forbidden_outputs"]["allow_freeform_attack_chain"] == safety_policy["llm"]["allow_freeform_attack_chain"]
    assert llm_policy["forbidden_outputs"]["allow_new_route_ids"] == safety_policy["llm"]["allow_new_route_ids"]
    assert llm_policy["forbidden_outputs"]["allow_new_techniques"] == safety_policy["llm"]["allow_new_techniques"]
    assert llm_policy["forbidden_outputs"]["allow_new_operator_ids"] == safety_policy["llm"]["allow_new_operator_ids"]
    assert llm_policy["output_constraints"]["require_tactic_grouped_technique_selection"] is True


def test_execution_policy_weights_sum_to_one() -> None:
    execution_policy = load_yaml("config/execution_policy.yaml")
    weights = execution_policy["adapter_selection"]["weights"]

    assert sum(weights.values()) == pytest.approx(1.0)


def test_validation_policy_requires_core_dag_guards() -> None:
    validation_policy = load_yaml("config/validation_policy.yaml")
    dag_policy = validation_policy["ptt_dag_validation"]

    assert dag_policy["require_depends_on_action_only"] is True
    assert dag_policy["require_depends_on_acyclic"] is True
    assert dag_policy["require_action_operator_exists"] is True
    assert dag_policy["require_action_target_in_scope"] is True


def test_validation_policy_rejects_flat_technique_selection() -> None:
    validation_policy = load_yaml("config/validation_policy.yaml")
    technique_policy = validation_policy["llm_output_validation"]["technique_selection"]

    assert technique_policy["require_selected_techniques_by_tactic"] is True
    assert technique_policy["reject_flat_selected_techniques_only"] is True


def test_blackboard_and_report_redaction_enabled() -> None:
    blackboard_policy = load_yaml("config/blackboard_policy.yaml")
    report_policy = load_yaml("config/report_policy.yaml")

    assert blackboard_policy["redaction"]["enabled"] is True
    assert report_policy["redaction"]["enabled"] is True
    assert report_policy["sections"]["include_raw_tool_output"] is False
