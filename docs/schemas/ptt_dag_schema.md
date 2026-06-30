# PTT-DAG Schema Notes

一阶段先使用文档化 Schema，后续再落为 JSON Schema 文件。

## Top Level

```json
{
  "graph_id": "string",
  "name": "string",
  "description": "string",
  "selected_route_id": "string",
  "nodes": [],
  "edges": [],
  "metadata": {}
}
```

## Node Levels

- `Goal`
- `Tactic`
- `Technique`
- `Action`

## Edge Types

- `contains`: 只允许 `Goal -> Tactic`、`Tactic -> Technique`、`Technique -> Action`。
- `depends_on`: 只允许 `Action -> Action`，必须无环。
- `data_flow`: 可选，一阶段可暂不实现。

## Action Required Fields

- `node_id`
- `level`
- `name`
- `parent_id`
- `operator_id`
- `target`
- `inputs`
- `outputs`
- `depends_on`
- `risk_level`
- `requires_human_approval`
- `allowed_tools`
- `status`

