# Operator Template Schema Notes

`data/operator_templates.yaml` defines the controlled Action source library.

## Top Level

```yaml
metadata:
  library_id: string
  version: string
operators: []
```

## Operator Required Fields

- `operator_id`
- `name`
- `display_name`
- `description`
- `category`
- `mapped_techniques`
- `required_inputs`
- `optional_inputs`
- `outputs`
- `preconditions`
- `risk_level`
- `side_effects`
- `requires_human_approval`
- `allowed_tools`
- `result_schema`

## Constraints

- `operator_id` must be unique.
- `mapped_techniques` must not be empty.
- `outputs` must not be empty.
- `result_schema` must cover all fields in `outputs`.
- `side_effects` must include all required dimensions.
- High or critical risk operators must require human approval.
- `allowed_tools` must reference tool IDs in `data/tool_registry.yaml`.

