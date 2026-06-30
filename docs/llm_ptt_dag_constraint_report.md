# LLM 使用 PTT-DAG 生成渗透测试任务的约束机制报告

## 1. 报告目的

本文用于说明本项目如何约束大语言模型使用 `PTT-DAG 四级任务规划模型` 生成渗透测试任务。

本项目不采用“让 LLM 自由生成完整攻击链”的方式，而是采用：

```text
固定路线模板
  + 候选 Technique 受限选择
  + Technique-Operator 映射
  + Operator Template 实例化 Action
  + PTT-DAG 结构校验
  + 安全策略与审批策略兜底
```

因此，LLM 在系统中的定位不是自由规划器，而是受限选择器、草案生成器和解释器。最终能否进入执行链路，必须由程序校验决定。

## 2. 总体约束链路

完整约束链路如下：

```text
用户目标 / 环境画像 / 授权范围
  -> settings.yaml 加载配置路径和功能开关
  -> safety_policy.yaml / llm_policy.yaml 确定安全边界
  -> route_templates.yaml 限定可选路线
  -> route_selection_prompt.md 约束 LLM 只能选择候选路线
  -> route_selector.py 校验路线启用状态和 allowed_route_ids
  -> technique_selection_prompt.md 约束 LLM 只能选择候选 Technique
  -> technique_operator_mapping.yaml 限定 Technique -> Operator
  -> operator_templates.yaml 限定 Action 来源、输入、输出、风险、副作用
  -> ptt_dag_generation_prompt.md 约束 PTT-DAG 草案结构
  -> validation_policy.yaml + validator.py 程序校验
  -> tool_registry.yaml + execution_policy.yaml 决定工具 Adapter 调用边界
  -> approval_policy.yaml 处理高风险 Action
```

核心原则：

```text
LLM 可以选择，但不能发明；
LLM 可以解释，但不能执行；
LLM 可以生成草案，但不能绕过程序校验。
```

## 3. PTT-DAG 模型层约束

### 3.1 相关文件

- `docs/schemas/ptt_dag_schema.md`
- `一阶段第二部分-PTT-DAG四级任务规划模型开发文档.md`
- `ptt_orchestrator/core/models.py`

### 3.2 约束内容

PTT-DAG 规定任务必须由四级结构表达：

```text
Goal -> Tactic -> Technique -> Action
```

其中：

- `Goal` 表示总体测试目标；
- `Tactic` 表示战术阶段；
- `Technique` 表示技术方法；
- `Action` 表示可执行或可模拟执行的原子动作实例。

PTT-DAG 同时包含两类关键边：

```text
contains：语义包含关系；
depends_on：Action 执行依赖关系。
```

合法结构示例：

```text
Goal: 基础安全评估
  Tactic: 侦察
    Technique: 主机发现
      Action: 主机存活探测
  Tactic: 发现
    Technique: 端口发现
      Action: 端口状态识别

Action DAG:
act-host-discovery -> act-port-scan
```

### 3.3 对 LLM 的限制

LLM 不能输出普通自然语言步骤作为最终计划，必须输出可校验的 PTT-DAG 结构。

禁止输出：

```text
1. 扫描目标
2. 找漏洞
3. 尝试利用
4. 写报告
```

应输出：

```json
{
  "graph_id": "ptt-dag-001",
  "selected_route_id": "route_basic_exposure_assessment",
  "nodes": [],
  "edges": [],
  "metadata": {}
}
```

## 4. 路线模板层约束

### 4.1 相关文件

- `data/route_templates.yaml`
- `docs/schemas/route_template_schema.md`
- `ptt_orchestrator/core/route_selector.py`
- `prompts/route_selection_prompt.md`

### 4.2 约束内容

`route_templates.yaml` 固定系统允许选择的路线。当前包含：

- `route_basic_exposure_assessment`
- `route_web_service_risk_assessment`
- `route_internal_asset_discovery`
- `route_credential_risk_assessment`

每条路线定义：

- `enabled`
- `risk_level`
- `recommended_for`
- `selection_hints`
- `expected_outputs`
- `default_selected_techniques`
- `tactics`
- `execution_dependencies`
- `safety_constraints`

### 4.3 约束机制

LLM 不能新增路线，只能从系统提供的候选路线中选择。

默认规则：

- 只允许选择 `enabled: true` 的路线；
- 禁用路线默认不可选；
- 高风险路线不能自动执行；
- 路线中的 `candidate_techniques` 是后续 Technique 选择的最大边界。

例如凭据风险路线：

```yaml
route_id: route_credential_risk_assessment
enabled: false
risk_level: high
safety_constraints:
  requires_human_approval: true
  auto_execute_allowed: false
```

这意味着该路线即使存在，也只是用于论文说明高风险审批机制，不能在默认 MVP 中自动规划执行。

## 5. Technique 选择层约束

### 5.1 相关文件

- `data/technique_operator_mapping.yaml`
- `docs/schemas/technique_operator_mapping_schema.md`
- `prompts/technique_selection_prompt.md`

### 5.2 约束内容

每条路线只暴露自己的候选 Technique，并且候选 Technique 必须挂在具体 Tactic 下。

例如基础暴露面评估路线可选：

```text
host_discovery
port_discovery
service_discovery
web_information_discovery
cve_lookup
config_risk_check
report_summary
```

LLM 不能只输出一个平铺 Technique 列表，而必须按 Tactic 分组选择。

要求输出结构为：

```json
{
  "selected_techniques_by_tactic": [
    {
      "tactic_id": "reconnaissance",
      "selected_techniques": ["host_discovery"],
      "reasoning_summary": "先确认授权目标是否存活。",
      "requires_human_approval": false
    }
  ],
  "overall_reasoning_summary": ""
}
```

这会强制模型沿着：

```text
Route -> Tactic -> Technique
```

进行选择，而不是从全局 Technique 池中随意挑选。

禁止 LLM 生成路线外 Technique，例如：

```text
privilege_escalation
credential_dumping
lateral_movement
persistence
```

### 5.3 Technique Profile

`technique_operator_mapping.yaml` 中的 `technique_profiles` 为每个 Technique 说明：

- `display_name`
- `description`
- `primary_tactic`
- `risk_level`
- `required_context`
- `expected_outputs`
- `requires_human_approval`

这使 Technique 选择不仅是字符串匹配，而是可解释、可审核的受控选择。

## 6. Operator 模板层约束

### 6.1 相关文件

- `data/operator_templates.yaml`
- `docs/schemas/operator_template_schema.md`
- `ptt_orchestrator/core/operator_registry.py`

### 6.2 核心关系

本项目强制采用：

```text
Technique -> Operator Template -> Action Instance
```

也就是说：

- Technique 是技术方法；
- Operator Template 是标准动作模板；
- Action Instance 是绑定具体目标后的任务图节点。

示例：

```text
service_discovery
  -> op_service_fingerprint
  -> act-service-fingerprint-001
```

### 6.3 对 LLM 的限制

LLM 不能直接生成工具命令，也不能直接发明 Action。

Action 必须来自 `operator_templates.yaml` 中登记的 `operator_id`。

每个 Operator Template 定义：

- `required_inputs`
- `optional_inputs`
- `outputs`
- `preconditions`
- `risk_level`
- `side_effects`
- `requires_human_approval`
- `allowed_tools`
- `result_schema`

例如：

```yaml
operator_id: op_service_fingerprint
required_inputs:
  - host
  - port
outputs:
  - service_name
  - version
  - banner
risk_level: low
allowed_tools:
  - nmap_adapter
  - web_probe_adapter
  - mock_adapter
```

这保证 Action 的来源、输入、输出、风险和工具边界都可追溯。

## 7. 工具注册层约束

### 7.1 相关文件

- `data/tool_registry.yaml`
- `docs/schemas/tool_registry_schema.md`
- `config/execution_policy.yaml`

### 7.2 约束内容

`tool_registry.yaml` 声明每个 Adapter 支持哪些 Operator。

示例：

```yaml
tool_id: nmap_adapter
supported_operators:
  - op_host_discovery
  - op_port_scan
  - op_service_fingerprint
```

工具调用边界由系统决定，而不是由 LLM 决定。

LLM 不允许输出：

```text
nmap -sV 192.168.56.10
```

系统只允许 LLM 参与上层选择，实际工具选择由以下内容共同决定：

- Action 的 `operator_id`
- Operator 的 `allowed_tools`
- Tool Registry 的 `supported_operators`
- Execution Policy 的评分规则
- Safety Policy 的安全边界

## 8. 提示词层约束

### 8.1 相关文件

- `prompts/route_selection_prompt.md`
- `prompts/technique_selection_prompt.md`
- `prompts/ptt_dag_generation_prompt.md`
- `prompts/validation_explanation_prompt.md`
- `prompts/report_summary_prompt.md`

### 8.2 路线选择提示词

`route_selection_prompt.md` 要求：

- 只能从 `candidate_routes` 中选择；
- 不允许新增路线；
- 禁用路线不能默认选择；
- 不允许输出命令、payload 或利用步骤；
- 输出必须是 JSON。

### 8.3 Technique 选择提示词

`technique_selection_prompt.md` 要求：

- 必须输出 `selected_techniques_by_tactic`；
- 每个 `tactic_id` 必须来自选定路线；
- 每个 Technique 必须来自对应 Tactic 的 `candidate_techniques`；
- 不允许新增 Technique；
- 不允许新增 Tactic；
- 不允许输出攻击命令；
- 高风险 Technique 只能进入审批；
- 输出必须是 JSON。

### 8.4 PTT-DAG 草案生成提示词

`ptt_dag_generation_prompt.md` 要求：

- 必须输出 PTT-DAG JSON；
- Action 必须绑定合法 `operator_id`；
- `depends_on` 只能存在于 Action 之间；
- 高风险 Action 必须设置 `waiting_approval`；
- 输出后必须经过程序校验。

### 8.5 提示词的边界

提示词只是软约束，不是最终安全边界。

最终安全边界由：

```text
validation_policy.yaml + validator.py
```

实现。

## 9. 配置策略层约束

### 9.1 相关文件

- `config/settings.yaml`
- `config/safety_policy.yaml`
- `config/llm_policy.yaml`
- `config/validation_policy.yaml`
- `config/execution_policy.yaml`
- `config/approval_policy.yaml`

### 9.2 Safety Policy

`safety_policy.yaml` 规定：

```yaml
llm:
  allow_freeform_attack_chain: false
  allow_command_generation: false
  allow_new_route_ids: false
  allow_new_techniques: false
  allow_new_operator_ids: false
```

这从策略层明确禁止 LLM 自由规划攻击链、生成命令或新增未登记对象。

### 9.3 LLM Policy

`llm_policy.yaml` 进一步规定：

- LLM 默认关闭；
- 允许任务是受限选择和解释；
- 禁止命令、payload、利用步骤、凭据尝试步骤；
- 输入只提供候选集合；
- 输出必须是 JSON；
- 无效输出时 fail closed。

### 9.4 Validation Policy

`validation_policy.yaml` 规定程序校验必须覆盖：

- 路线是否合法；
- Technique 是否属于候选集合；
- Operator 是否存在；
- Action 是否绑定合法 Operator；
- contains 边层级是否合法；
- depends_on 是否只存在于 Action 之间；
- DAG 是否无环；
- target 是否在 scope 内；
- risk 是否符合策略；
- high / critical 是否进入 waiting_approval；
- allowed_tools 是否存在。

## 10. 程序机制约束

### 10.1 当前已有机制

当前已实现：

- `ptt_orchestrator/core/loaders.py`
  - 统一读取 YAML、JSON 和文本文件。

- `ptt_orchestrator/core/models.py`
  - 定义 PTTNode、PTTEdge、PTTDAG、OperatorTemplate、ToolSpec。

- `ptt_orchestrator/core/route_selector.py`
  - 默认只选择启用路线；
  - 支持按 `intent` 选择路线；
  - 支持 `allowed_route_ids` 限制路线；
  - 提取路线候选 Technique。

- `ptt_orchestrator/core/operator_registry.py`
  - 拒绝重复 `operator_id`；
  - 支持按 Technique 查询 Operator；
  - 校验 Operator 模板静态规则；
  - 校验 Technique-Operator 映射一致性。

### 10.2 待实现关键机制

后续必须实现：

- `ptt_orchestrator/core/validator.py`
  - PTT-DAG 合法性校验；
  - scope 校验；
  - 风险和审批校验；
  - DAG 无环校验；
  - 工具引用校验。

- `ptt_orchestrator/core/planner.py`
  - 根据路线模板、Technique 选择结果和 Operator 模板实例化 Action；
  - 不允许直接使用 LLM 输出的 Action 作为最终结果。

- `ptt_orchestrator/core/scheduler.py`
  - 根据 Action 的 `depends_on` 和状态选择 ready Action。

## 11. 推荐生成流程

推荐的一阶段任务生成流程如下：

```text
Step 1: 读取用户目标、环境画像、授权范围

Step 2: 从 route_templates.yaml 中召回 enabled 路线

Step 3: 可选使用 route_selection_prompt.md
        让 LLM 从候选路线中选择 route_id

Step 4: route_selector.py 校验 route_id 是否存在、启用、允许

Step 5: 从选定路线提取 candidate_techniques

Step 6: 可选使用 technique_selection_prompt.md
        让 LLM 按 Tactic 分组选择 Technique

Step 7: 校验 selected_techniques_by_tactic
        - tactic_id 是否来自 selected_route.tactics
        - selected_techniques 是否来自对应 Tactic 的 candidate_techniques

Step 8: 根据 technique_operator_mapping.yaml 映射 operator_id

Step 9: 根据 operator_templates.yaml 实例化 Action

Step 10: 根据 route execution_dependencies 生成 Action depends_on

Step 11: 输出 PTT-DAG 草案

Step 12: validator.py 按 validation_policy.yaml 做程序校验

Step 13: 校验通过后，进入 Scheduler / Adapter / Blackboard / Reporter
```

## 12. 关键安全结论

本系统约束 LLM 的方式不是单靠提示词，而是多层约束共同生效：

```text
Prompt 约束：告诉模型只能做什么；
Template 约束：限制模型能选择什么；
Policy 约束：规定系统允许什么；
Program 约束：最终校验并拒绝非法输出。
```

最终设计目标是：

```text
LLM 不直接生成工具命令；
LLM 不自由生成完整攻击链；
LLM 不新增路线、Technique 或 Operator；
LLM 只在候选集合内选择；
Action 只能来自 Operator Template；
高风险动作进入 waiting_approval；
所有输出必须通过程序校验。
```

## 13. 后续审核重点

建议后续优先审核以下文件：

1. `config/safety_policy.yaml`
   - 是否准确表达项目安全边界。

2. `config/llm_policy.yaml`
   - 是否充分限制 LLM 输出类型。

3. `data/route_templates.yaml`
   - 路线是否覆盖一阶段目标，是否存在过宽路线。

4. `data/technique_operator_mapping.yaml`
   - Technique 是否过多或过少，是否存在高风险遗漏。

5. `data/operator_templates.yaml`
   - 算子风险、副作用、审批字段是否合理。

6. `prompts/technique_selection_prompt.md`
   - 是否足够明确地限制 LLM 只做候选选择。

7. `config/validation_policy.yaml`
   - Validator 是否具备足够的强制校验项。

8. `ptt_orchestrator/core/validator.py`
   - 后续必须实现为最终兜底机制。
