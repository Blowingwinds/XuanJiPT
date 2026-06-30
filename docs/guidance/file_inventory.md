# File Inventory

本清单用于后续逐个文件审核。它说明每个文件的存放位置、核心意义和审核重点，不作为运行时配置读取。

## 顶层文档

| 文件 | 核心意义 | 后续审核重点 |
|---|---|---|
| `一阶段开发指导.md` | 一阶段总体目标、边界、交付物和最低验收标准。 | 是否与代码实现范围一致，是否仍是阶段总纲。 |
| `MVP开发文档.md` | MVP 原型链路和模块划分说明。 | 是否与当前目录结构、模块顺序一致。 |
| `docs/llm_ptt_dag_constraint_report.md` | 大模型使用 PTT-DAG 生成任务时的文件约束、策略约束、提示词约束和程序校验机制说明。 | 是否准确表达 LLM 的受限角色和后续 Validator 兜底机制。 |
| `一阶段第二部分-PTT-DAG四级任务规划模型开发文档.md` | PTT-DAG 模型定义、节点、边、状态和 LangGraph 映射。 | `models.py`、`validator.py`、`scheduler.py` 是否按此实现。 |
| `一阶段第三部分-ATTCK战术路线模板约束任务解耦机制开发文档.md` | ATT&CK 路线模板、受限 Technique 选择、任务解耦流程。 | `route_templates.yaml`、`route_selector.py`、`planner.py` 是否按此实现。 |
| `一阶段第四部分-原子算子模板库与动作副作用建模开发文档.md` | Operator Template、Action 实例化、风险和副作用模型。 | `operator_templates.yaml`、`operator_registry.py`、`validator.py` 是否按此实现。 |

## 配置规则文件

| 文件 | 核心意义 | 后续审核重点 |
|---|---|---|
| `config/settings.yaml` | 全局运行配置，包括路径索引、功能开关、LLM 开关、日志设置。 | 是否只放运行时设置，不放知识模板、算子定义或提示词正文。 |
| `config/safety_policy.yaml` | 运行时安全边界，包括授权范围、风险等级、审批策略和 LLM 禁止行为。 | 是否只放规则，不放路线模板、算子模板或提示词。 |
| `config/execution_policy.yaml` | Action 调度、超时、重试、Adapter 选择和结果处理规则。 | 是否只描述执行策略，不直接声明工具能力。 |
| `config/approval_policy.yaml` | 高风险 Action 的人工审批状态流和记录要求。 | 是否与 `safety_policy.yaml` 的风险审批规则一致。 |
| `config/validation_policy.yaml` | 模板、注册表和 PTT-DAG 的合法性校验规则。 | 是否覆盖路线、Technique、Operator、工具、风险和 DAG 无环校验。 |
| `config/llm_policy.yaml` | LLM 使用边界，包括允许任务、禁止输出、输入输出约束和失败回退。 | 是否只描述 LLM 策略，不放提示词正文。 |
| `config/blackboard_policy.yaml` | 轻量黑板存储、命名空间、更新、保留和脱敏规则。 | 是否只管理状态回填规则，不参与任务规划。 |
| `config/report_policy.yaml` | 报告输出格式、章节、发现呈现和脱敏规则。 | 是否只管理报告呈现，不参与执行决策。 |

## 知识与模板文件

| 文件 | 核心意义 | 后续审核重点 |
|---|---|---|
| `data/route_templates.yaml` | 固定 ATT&CK/本地 SOP 战术路线模板。 | 路线是否启用合理，禁用高风险路线是否默认不可选，依赖是否可形成 DAG。 |
| `data/technique_operator_mapping.yaml` | Technique 到 Operator 的候选映射。 | 每个 Technique 是否至少映射一个合法 `operator_id`。 |
| `data/operator_templates.yaml` | 原子算子模板库，定义 Action 来源、输入、输出、风险、副作用和候选工具。 | 字段是否完整，风险和审批是否一致，`result_schema` 是否覆盖输出。 |
| `data/tool_registry.yaml` | 工具能力注册表，声明 Adapter 支持哪些 Operator。 | `tool_id` 是否被算子引用，支持能力是否和 Adapter 设计一致。 |

## 提示词文件

| 文件 | 核心意义 | 后续审核重点 |
|---|---|---|
| `prompts/route_selection_prompt.md` | LLM 在候选路线中受限选择的提示词。 | 是否禁止新增路线和默认选择禁用路线。 |
| `prompts/technique_selection_prompt.md` | LLM 在候选 Technique 内受限选择的提示词。 | 是否禁止新增 Technique、命令、payload 和真实利用步骤。 |
| `prompts/ptt_dag_generation_prompt.md` | LLM 生成 PTT-DAG 草案的提示词。 | 是否要求绑定合法 `operator_id`，是否强调程序校验。 |
| `prompts/validation_explanation_prompt.md` | 将程序校验结果解释为可读修复建议的提示词。 | 是否禁止绕过策略或建议危险修复。 |
| `prompts/report_summary_prompt.md` | 基于结构化结果生成报告摘要的提示词。 | 是否避免夸大风险和输出利用步骤。 |

## 指导与 Schema 文件

| 文件 | 核心意义 | 后续审核重点 |
|---|---|---|
| `docs/guidance/file_boundaries.md` | 文件职责边界说明，防止配置、模板、提示词和代码混用。 | 是否需要随着目录变化同步更新。 |
| `docs/guidance/development_order.md` | 开发顺序建议。 | 是否仍符合当前实现进度。 |
| `docs/guidance/file_inventory.md` | 本文件，作为后续逐个审核索引。 | 每新增或删除文件后都应同步更新。 |
| `docs/schemas/ptt_dag_schema.md` | PTT-DAG 字段结构说明。 | 后续是否需要升级为正式 JSON Schema。 |
| `docs/schemas/route_template_schema.md` | 路线模板字段和约束说明。 | 是否与 `data/route_templates.yaml` 保持一致。 |
| `docs/schemas/technique_operator_mapping_schema.md` | Technique-Operator 映射字段和约束说明。 | 是否与 `data/technique_operator_mapping.yaml` 保持一致。 |
| `docs/schemas/operator_template_schema.md` | Operator Template 字段和约束说明。 | 是否与 `data/operator_templates.yaml` 保持一致。 |
| `docs/schemas/tool_registry_schema.md` | Tool Registry 字段和约束说明。 | 是否与 `data/tool_registry.yaml` 保持一致。 |
| `docs/schemas/config_policy_schema.md` | 配置策略文件边界和职责说明。 | 是否与 `config/` 文件保持一致。 |

## 示例文件

| 文件 | 核心意义 | 后续审核重点 |
|---|---|---|
| `examples/input_basic_assessment.json` | 基础安全评估路线的示例输入。 | 是否能驱动 Planner 生成基础暴露面评估 PTT-DAG。 |
| `examples/input_web_assessment.json` | Web 风险评估路线的示例输入。 | 是否能驱动 Planner 生成 Web 服务风险评估 PTT-DAG。 |

## 核心代码文件

| 文件 | 核心意义 | 后续审核重点 |
|---|---|---|
| `ptt_orchestrator/app.py` | CLI 入口占位。 | 后续是否只负责入口编排，不内嵌业务规则。 |
| `ptt_orchestrator/core/loaders.py` | YAML、JSON、文本统一加载。 | 是否保持通用加载职责，不做业务校验。 |
| `ptt_orchestrator/core/models.py` | PTT-DAG、节点、边、算子和工具数据模型。 | 是否只定义数据形状，不混入安全策略。 |
| `ptt_orchestrator/core/operator_registry.py` | Operator 注册、查询和静态一致性校验。 | 是否能覆盖算子模板、工具引用和 Technique 映射校验。 |
| `ptt_orchestrator/core/route_selector.py` | 路线选择和候选 Technique 提取。 | 是否默认忽略禁用路线，是否遵守 allowed_route_ids。 |
| `ptt_orchestrator/core/planner.py` | 任务规划器占位，后续生成 PTT-DAG。 | 是否严格从路线、Technique 映射和算子模板生成 Action。 |
| `ptt_orchestrator/core/validator.py` | PTT-DAG 合法性校验占位。 | 是否覆盖路线、Technique、Operator、风险、scope、DAG 无环。 |
| `ptt_orchestrator/core/scheduler.py` | Action 就绪调度占位。 | 是否只根据状态和依赖选 ready Action。 |
| `ptt_orchestrator/core/blackboard.py` | 轻量状态黑板。 | 是否统一保存资产、服务、发现和 Action 结果。 |
| `ptt_orchestrator/adapters/base.py` | 工具 Adapter 抽象接口。 | 是否保持统一 `supports/build_command/execute/parse_result` 接口。 |
| `ptt_orchestrator/adapters/mock_adapter.py` | Mock 执行适配器。 | 是否用于安全演示和测试，不做真实扫描。 |
| `ptt_orchestrator/outputs/report_generator.py` | 报告生成占位。 | 是否只做输出汇总，不参与规划和执行决策。 |

## 测试与工程文件

| 文件 | 核心意义 | 后续审核重点 |
|---|---|---|
| `tests/test_scaffold.py` | 检查基础文件是否存在。 | 新增关键文件后是否补充检查。 |
| `tests/test_loaders.py` | 检查加载器能读取配置、模板、提示词和示例输入。 | 是否覆盖新格式文件。 |
| `tests/test_models.py` | 检查数据模型转换。 | 是否覆盖新增模型字段。 |
| `tests/test_operator_registry.py` | 检查算子注册表和模板一致性。 | 是否覆盖新增算子和工具。 |
| `tests/test_route_selector.py` | 检查路线选择逻辑。 | 是否覆盖新增路线策略。 |
| `pytest.ini` | pytest 运行配置。 | 是否保持测试路径和缓存策略清晰。 |
| `.gitignore` | 忽略运行缓存和构建产物。 | 是否覆盖新增工具产生的临时文件。 |
