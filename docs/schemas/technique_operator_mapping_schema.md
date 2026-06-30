# Technique-Operator Mapping Schema Notes

`data/technique_operator_mapping.yaml` links route-level Technique identifiers to Operator Templates.

## Top Level

```yaml
metadata:
  mapping_id: string
  version: string
techniques: {}
technique_profiles: {}
```

## Technique Mapping

Each key under `techniques` is a Technique ID.

```yaml
technique_id:
  candidate_operators:
    - operator_id
```

## Technique Profile

Each key under `technique_profiles` should match a Technique ID.

Required fields:

- `display_name`
- `description`
- `primary_tactic`
- `risk_level`
- `required_context`
- `expected_outputs`

## Constraints

- Every Technique used by a route must exist in `techniques`.
- Every `candidate_operators` value must exist in `data/operator_templates.yaml`.
- High-risk Technique profiles should set `requires_human_approval: true`.

