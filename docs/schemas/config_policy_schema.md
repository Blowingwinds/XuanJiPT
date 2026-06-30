# Config Policy Schema Notes

`config/` files define runtime behavior and policy. They must not define domain knowledge templates.

## Config Files

- `settings.yaml`: global path index and feature switches.
- `safety_policy.yaml`: scope, risk, denied action categories, and LLM safety constraints.
- `execution_policy.yaml`: scheduling, timeout, retry, adapter selection, result handling.
- `approval_policy.yaml`: human approval flow for high-risk Actions.
- `validation_policy.yaml`: template and PTT-DAG validation requirements.
- `llm_policy.yaml`: LLM allowed tasks and forbidden outputs.
- `blackboard_policy.yaml`: state storage and update rules.
- `report_policy.yaml`: report output and redaction rules.

## Boundary Rules

- Config files may reference template paths, but must not embed route, Technique, Operator, or tool capability definitions.
- Prompt files may be referenced by path, but prompt text belongs in `prompts/`.
- Security and LLM policies should fail closed when outputs are invalid or policies conflict.

