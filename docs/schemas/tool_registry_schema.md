# Tool Registry Schema Notes

`data/tool_registry.yaml` declares Adapter capabilities. It does not implement Adapter behavior.

## Top Level

```yaml
metadata:
  registry_id: string
  version: string
tools: []
```

## Tool Required Fields

- `tool_id`
- `name`
- `type`
- `description`
- `supported_operators`
- `risk_profile`
- `runtime`
- `selection_profile`

## Constraints

- `tool_id` must be unique.
- `supported_operators` must not be empty.
- Each `supported_operators` value must exist in `data/operator_templates.yaml`.
- Runtime mode controls whether the Adapter may execute for real.
- Tool registry must not contain command templates or exploit payloads.

