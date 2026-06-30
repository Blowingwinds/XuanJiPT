# File Boundary Guidance

本项目将配置规则、知识模板、提示词、开发指导和代码严格分离。

## 目录职责

- `config/`: 系统运行规则和安全策略，例如授权范围、风险阈值、审批策略。
- `data/`: 可版本化的知识与模板，例如路线模板、Technique-Operator 映射、算子模板、工具注册表。
- `prompts/`: LLM 提示词模板。提示词只能引用候选集合，不应内嵌真实攻击命令。
- `docs/guidance/`: 开发指导、文件边界说明、人工流程说明。
- `docs/schemas/`: JSON Schema 或字段约束文档。
- `ptt_orchestrator/core/`: 任务规划、校验、调度、状态回填等核心逻辑。
- `ptt_orchestrator/adapters/`: 工具适配器实现。Adapter 不负责决定任务是否合法。
- `ptt_orchestrator/outputs/`: 报告生成与输出格式化。
- `examples/`: 示例输入、示例 PTT-DAG 和演示数据。
- `tests/`: 单元测试和集成测试。

## 禁止混用规则

- 不在 `prompts/` 中定义安全策略，提示词只表达模型约束。
- 不在 `data/` 中定义运行时授权范围，授权范围属于 `config/`。
- 不在代码中硬编码路线、Technique、Operator 清单，应从 `data/` 加载。
- 不在 Adapter 中绕过 Validator 直接执行 Action。
- 不将论文开发指导文件当作运行时配置读取。

