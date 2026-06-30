from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_scaffold_files_exist() -> None:
    required = [
        "config/settings.yaml",
        "config/safety_policy.yaml",
        "config/execution_policy.yaml",
        "config/approval_policy.yaml",
        "config/validation_policy.yaml",
        "config/llm_policy.yaml",
        "config/blackboard_policy.yaml",
        "config/report_policy.yaml",
        "data/route_templates.yaml",
        "data/technique_operator_mapping.yaml",
        "data/operator_templates.yaml",
        "data/tool_registry.yaml",
        "prompts/technique_selection_prompt.md",
        "prompts/ptt_dag_generation_prompt.md",
        "prompts/route_selection_prompt.md",
        "prompts/validation_explanation_prompt.md",
        "prompts/report_summary_prompt.md",
        "docs/guidance/file_boundaries.md",
        "docs/guidance/file_inventory.md",
        "docs/llm_ptt_dag_constraint_report.md",
        "docs/schemas/route_template_schema.md",
        "docs/schemas/technique_operator_mapping_schema.md",
        "docs/schemas/operator_template_schema.md",
        "docs/schemas/tool_registry_schema.md",
        "docs/schemas/config_policy_schema.md",
        "examples/input_basic_assessment.json",
        "ptt_orchestrator/core/models.py",
    ]

    for relative_path in required:
        assert (ROOT / relative_path).exists()
