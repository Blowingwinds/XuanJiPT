# PTT-DAG Generation Prompt

该提示词仅用于生成可校验的 PTT-DAG 草案。模型不得生成工具命令，不得新增路线、Tactic、Technique 或 `operator_id`。

你必须使用以下任务规划结构：

```text
Goal -> Tactic -> Technique -> Action
```

其中：

- `Goal` 来自用户目标；
- `Tactic` 必须来自 `route_template.tactics`；
- `Technique` 必须来自 `selected_techniques_by_tactic`；
- `Action` 必须由合法 `operator_id` 对应的 Operator Template 实例化；
- `depends_on` 只能存在于 Action 与 Action 之间。

## 必须遵守的规则

1. 不允许新增路线。
2. 不允许新增 Tactic。
3. 不允许新增 Technique。
4. 不允许新增 Operator。
5. 不允许输出任何真实攻击命令、payload、漏洞利用步骤或凭据尝试步骤。
6. `contains` 边只能表达 `Goal -> Tactic -> Technique -> Action`。
7. `depends_on` 边只能表达 Action 之间的执行依赖。
8. Action 必须绑定已提供的 `operator_id`。
9. Action 只能由候选 Operator Template 实例化。
10. high 或 critical 风险 Action 必须设置 `requires_human_approval: true` 和 `status: waiting_approval`。
11. 输出必须是合法 JSON。
12. 输出后仍必须经过程序校验，不能直接执行。

## 输入信息

```json
{
  "goal": {{goal}},
  "route_template": {{route_template}},
  "selected_techniques_by_tactic": {{selected_techniques_by_tactic}},
  "technique_operator_mapping": {{technique_operator_mapping}},
  "operator_templates": {{operator_templates}},
  "policy": {{policy}}
}
```

## 输出格式

只输出 PTT-DAG JSON 草案，不要输出 Markdown 或额外解释：

```json
{
  "graph_id": "",
  "selected_route_id": "",
  "nodes": [],
  "edges": [],
  "metadata": {
    "created_by": "llm_draft",
    "requires_programmatic_validation": true
  }
}
```
