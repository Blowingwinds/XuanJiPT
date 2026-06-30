# Development Order

一阶段基础框架建议按以下顺序推进：

1. 完成静态知识库：`data/route_templates.yaml`、`data/technique_operator_mapping.yaml`、`data/operator_templates.yaml`、`data/tool_registry.yaml`。
2. 完成安全规则：`config/safety_policy.yaml`。
3. 完成数据模型：`ptt_orchestrator/core/models.py`。
4. 完成加载器和注册表：`ptt_orchestrator/core/loaders.py`、`ptt_orchestrator/core/operator_registry.py`。
5. 完成校验器：`ptt_orchestrator/core/validator.py`。
6. 完成规则版 Planner：先不接 LLM，生成可校验 PTT-DAG。
7. 完成 Scheduler 和 MockAdapter：跑通 pending -> ready -> success 的状态流。
8. 再接入 LangGraph，将 planner、validator、scheduler、adapter、blackboard、reporter 包装成状态流。

