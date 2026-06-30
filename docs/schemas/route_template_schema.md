# Route Template Schema Notes

`data/route_templates.yaml` defines fixed route templates. A Planner may select only routes declared in this file.

## Top Level

```yaml
metadata:
  library_id: string
  version: string
  route_selection_rule: string
routes: []
```

## Route Required Fields

- `route_id`
- `name`
- `display_name`
- `description`
- `enabled`
- `risk_level`
- `route_type`
- `knowledge_refs`
- `recommended_for`
- `selection_hints`
- `expected_outputs`
- `default_selected_techniques`
- `tactics`
- `execution_dependencies`
- `safety_constraints`

## Route Constraints

- `route_id` must be unique.
- Enabled routes may be selected by default.
- Disabled routes require explicit approval flow.
- `default_selected_techniques` must be a subset of all route `candidate_techniques`.
- `execution_dependencies.from` and `execution_dependencies.to` must reference candidate Technique IDs.
- High-risk routes must not be auto executable.

