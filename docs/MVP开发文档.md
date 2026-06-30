# 基于大语言模型与知识约束的多体协同渗透测试 MVP 开发文档

## 1. 文档目的

本文档用于指导中期考核阶段的 MVP 原型开发。目标不是一次性实现完整的自动化渗透测试系统，而是优先完成开题报告中已经规划的核心基础模块，形成一个可演示、可扩展、可写入论文中期成果的原型系统。

MVP 应重点证明以下链路可行：

```text
测试目标输入
  -> 环境画像结构化
  -> ATT&CK/本地知识约束检索
  -> PTT 四级任务树生成
  -> 原子算子模板匹配
  -> 工具语义适配与自适应调用
  -> 执行结果结构化回填
  -> 简要报告输出
```

截至 2026 年 6 月底，按照原研究计划，应优先补齐以下内容：

- 总体架构设计
- PTT 四级任务树模型
- 任务解耦模块
- 原子算子模板库
- 工具语义封装与自适应调用模块

## 2. MVP 定位

### 2.1 MVP 名称

建议暂定为：`PTT-Orchestrator-MVP`

### 2.2 MVP 核心目标

构建一个知识约束下的渗透测试任务编排原型系统，实现从自然语言或结构化测试目标到工具调用计划的自动化生成。

MVP 不追求完整攻击闭环，不做高风险真实攻击动作，重点展示：

1. 任务能否被规范化拆解为 PTT 四级任务树；
2. 生成过程是否受到 ATT&CK 与本地算子模板约束；
3. 原子动作是否能够匹配到标准化算子模板；
4. 算子是否能够根据语义能力选择合适工具；
5. 工具结果是否能够被统一解析并回填到任务树状态中。

### 2.3 MVP 边界

MVP 阶段建议只支持授权靶场、内网实验环境或模拟目标，不支持公网未授权目标。

建议优先实现低风险动作：

- 资产存活探测
- 端口状态识别
- 服务指纹识别
- Web 标题识别
- Web 技术栈识别
- TLS 证书信息提取
- CVE 信息匹配
- 配置风险检查占位
- 弱口令风险检查占位
- 结果汇总与报告生成

高风险动作只建立模板，不执行真实操作，并标记为需要人工审批。

## 3. 总体架构设计

### 3.1 架构分层

MVP 建议采用六层架构。

```text
┌──────────────────────────────┐
│ 1. 用户输入层                 │
│ 目标、范围、规则、环境信息     │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ 2. 环境画像层                 │
│ 资产、端口、服务、漏洞线索     │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ 3. 知识约束层                 │
│ ATT&CK、本地 SOP、算子模板库   │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ 4. 任务编排层                 │
│ PTT 四级任务树、任务解耦       │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ 5. 执行适配层                 │
│ 工具 Adapter、自适应选择       │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ 6. 状态反馈层                 │
│ 结果解析、状态更新、报告输出   │
└──────────────────────────────┘
```

### 3.2 核心模块划分

建议代码层面按以下模块划分：

```text
ptt_orchestrator/
  app.py                         # CLI 或 Web API 入口
  config/
    settings.yaml                # 系统配置
    safety_policy.yaml           # 授权范围与风险策略
  data/
    attack_mapping.yaml          # 精简版 ATT&CK 映射
    operator_templates.yaml      # 原子算子模板库
    tool_registry.yaml           # 工具能力注册表
  core/
    models.py                    # PTT 节点、算子、工具、结果等数据模型
    planner.py                   # 任务解耦与 PTT 树生成
    retriever.py                 # 知识检索与候选模板召回
    validator.py                 # 范围、风险、前置条件校验
    scheduler.py                 # Action 调度与工具选择
    blackboard.py                # MVP 阶段的轻量状态黑板
  adapters/
    base.py                      # 工具适配器基类
    nmap_adapter.py              # 示例真实或半真实适配器
    web_probe_adapter.py         # Web 探测适配器
    mock_adapter.py              # 模拟执行适配器
  outputs/
    report_generator.py          # 报告生成
  tests/
    test_planner.py
    test_operator_templates.py
    test_tool_selection.py
```

## 4. PTT 四级任务树模型

### 4.1 四级定义

PTT 任务树采用 `Goal-Tactic-Technique-Action` 四级结构。

| 层级 | 含义 | 示例 |
|---|---|---|
| Goal | 总体测试目标 | 完成目标资产暴露面评估 |
| Tactic | 战术阶段 | 侦察、发现、漏洞验证、风险评估 |
| Technique | 技术方法 | 端口发现、服务识别、Web 技术栈识别 |
| Action | 原子动作 | 对 192.168.1.10:80 执行服务指纹识别 |

### 4.2 PTT 节点数据结构

建议定义统一节点结构：

```json
{
  "node_id": "act-001",
  "level": "Action",
  "name": "service_fingerprint",
  "display_name": "服务指纹识别",
  "parent_id": "tech-001",
  "target": {
    "asset_id": "asset-001",
    "host": "192.168.56.10",
    "port": 80,
    "protocol": "tcp"
  },
  "preconditions": ["target_in_scope", "port_open"],
  "inputs": {
    "host": "192.168.56.10",
    "port": 80
  },
  "expected_outputs": ["service_name", "version", "confidence"],
  "risk_level": "low",
  "status": "pending",
  "operator_id": "op_service_fingerprint",
  "allowed_tools": ["nmap_adapter", "web_probe_adapter"],
  "result": null
}
```

### 4.3 状态流转

Action 节点至少支持以下状态：

```text
pending -> ready -> running -> success
                         └──> failed
                         └──> skipped
                         └──> waiting_approval
```

状态含义：

- `pending`：任务已生成，但尚未检查前置条件；
- `ready`：前置条件满足，可以执行；
- `running`：正在执行；
- `success`：执行成功，并产生结构化结果；
- `failed`：执行失败；
- `skipped`：因范围、风险或依赖不满足而跳过；
- `waiting_approval`：高风险动作需要人工审批。

## 5. 任务解耦模块

### 5.1 模块目标

任务解耦模块负责把用户输入的测试目标拆解为 PTT 四级任务树。

输入示例：

```json
{
  "goal": "对靶场主机进行基础安全评估",
  "scope": ["192.168.56.10"],
  "constraints": {
    "allow_high_risk": false,
    "max_risk_level": "medium"
  },
  "known_assets": [
    {
      "asset_id": "asset-001",
      "host": "192.168.56.10",
      "ports": [80, 443]
    }
  ]
}
```

输出为 PTT 任务树。

### 5.2 解耦流程

建议采用“检索 + 约束 + 生成 + 校验”的流程。

```text
Step 1: 解析目标
  -> 提取目标资产、测试范围、风险边界、期望输出

Step 2: 选择 Tactic
  -> 从 attack_mapping.yaml 中召回候选战术阶段
  -> 过滤掉超出授权范围的阶段

Step 3: 映射 Technique
  -> 根据资产信息、端口信息、服务信息选择技术方法
  -> 每个 Technique 必须能映射到一个或多个原子算子模板

Step 4: 实例化 Action
  -> 将 Technique 与具体资产绑定
  -> 填充 host、port、protocol 等参数

Step 5: 校验任务树
  -> 检查节点层级合法性
  -> 检查 Action 是否存在算子模板
  -> 检查风险等级是否满足策略
  -> 检查目标是否在授权范围内
```

### 5.3 MVP 阶段的 LLM 使用方式

如果接入大语言模型，不建议让模型自由生成完整任务树。建议让模型只做候选选择和解释，最终结构由程序生成。

推荐方式：

```text
系统提供候选 Tactic/Technique/Operator
  -> LLM 根据目标和环境选择候选项
  -> 程序校验候选项是否合法
  -> 程序实例化标准 Action
```

这样能够体现论文中的“专家知识约束”，也能降低幻觉风险。

## 6. 原子算子模板库

### 6.1 模板库作用

原子算子模板库是 MVP 的核心知识资产。它规定系统允许生成哪些 Action，以及每个 Action 的输入、输出、风险、前置条件和可用工具。

任务编排层不能凭空生成 Action，所有 Action 都必须来自算子模板库。

### 6.2 算子模板结构

```json
{
  "operator_id": "op_service_fingerprint",
  "name": "service_fingerprint",
  "display_name": "服务指纹识别",
  "category": "reconnaissance",
  "mapped_tactic": "Reconnaissance",
  "mapped_technique": "Service Discovery",
  "description": "识别目标端口对应的服务名称和版本信息",
  "required_inputs": ["host", "port"],
  "optional_inputs": ["timeout", "protocol"],
  "outputs": ["service_name", "version", "banner", "confidence"],
  "preconditions": ["target_in_scope", "port_open"],
  "risk_level": "low",
  "requires_human_approval": false,
  "side_effects": {
    "network_noise": "low",
    "service_disruption": "none",
    "credential_exposure": "none"
  },
  "allowed_tools": ["nmap_adapter", "web_probe_adapter"],
  "result_schema": {
    "service_name": "string",
    "version": "string",
    "banner": "string",
    "confidence": "number"
  }
}
```

### 6.3 MVP 首批算子建议

建议先实现以下 10 个算子：

| 算子 ID | 名称 | 风险 | 执行方式 |
|---|---|---|---|
| op_host_discovery | 主机存活探测 | low | 真实或模拟 |
| op_port_scan | 端口状态识别 | low/medium | 真实或模拟 |
| op_service_fingerprint | 服务指纹识别 | low | 真实或模拟 |
| op_web_title | Web 标题识别 | low | 真实或模拟 |
| op_web_tech_stack | Web 技术栈识别 | low | 真实或模拟 |
| op_tls_certificate | TLS 证书信息提取 | low | 真实或模拟 |
| op_cve_lookup | 已知漏洞库匹配 | low | 本地数据匹配 |
| op_config_risk_check | 配置风险检查 | low | 模拟 |
| op_weak_credential_check | 弱凭据风险检查 | high | 仅模板，不执行 |
| op_report_summary | 结果汇总 | low | 本地生成 |

## 7. 工具语义封装模块

### 7.1 模块目标

工具语义封装模块用于解决不同工具接口不同、参数不同、输出格式不同的问题。

每个工具都通过 Adapter 暴露统一接口：

```text
Action 输入
  -> Adapter 参数转换
  -> 工具执行或模拟执行
  -> 原始输出解析
  -> 标准 JSON 结果
```

### 7.2 工具注册表结构

```json
{
  "tool_id": "nmap_adapter",
  "name": "Nmap Adapter",
  "type": "command_adapter",
  "supported_operators": [
    "op_host_discovery",
    "op_port_scan",
    "op_service_fingerprint"
  ],
  "input_schema": ["host", "ports", "scan_mode"],
  "output_schema": ["open_ports", "services", "raw_output"],
  "risk_profile": {
    "network_noise": "medium",
    "service_disruption": "low"
  },
  "constraints": {
    "requires_scope_check": true,
    "requires_approval": false
  },
  "runtime": {
    "mode": "mock_first",
    "timeout_seconds": 30
  }
}
```

### 7.3 Adapter 统一接口

Python 中可以设计如下基类：

```python
class BaseToolAdapter:
    tool_id: str

    def supports(self, operator_id: str) -> bool:
        raise NotImplementedError

    def build_command(self, action: dict) -> dict:
        raise NotImplementedError

    def execute(self, command: dict) -> dict:
        raise NotImplementedError

    def parse_result(self, raw_result: dict) -> dict:
        raise NotImplementedError
```

MVP 阶段建议至少实现：

- `MockAdapter`：用于返回固定或半随机模拟结果；
- `NmapAdapter`：用于低风险主机发现、端口识别、服务识别；
- `WebProbeAdapter`：用于 Web 标题、响应头、技术栈识别。

## 8. 自适应调用模块

### 8.1 模块目标

自适应调用模块负责为每个 Action 选择最合适的工具 Adapter。

选择依据包括：

- 工具是否支持该算子；
- 输入参数是否满足；
- 风险等级是否符合策略；
- 工具输出是否覆盖期望字段；
- 工具执行成本；
- 是否需要人工审批。

### 8.2 工具选择流程

```text
输入 Action
  -> 查询 operator.allowed_tools
  -> 从 tool_registry 中取候选工具
  -> 校验工具能力与输入参数
  -> 计算工具评分
  -> 选择最高分工具
  -> 调用 Adapter
  -> 解析结果
  -> 回填 Action.result
```

### 8.3 简单评分公式

MVP 可使用简单线性评分：

```text
score = capability_match * 0.4
      + output_coverage * 0.3
      + safety_score * 0.2
      + cost_score * 0.1
```

字段含义：

- `capability_match`：工具是否明确支持该算子；
- `output_coverage`：工具输出字段是否覆盖 Action 期望输出；
- `safety_score`：工具风险是否低于系统策略；
- `cost_score`：执行时间、依赖复杂度、资源消耗。

MVP 阶段不需要复杂优化算法，重点是体现“语义能力匹配”而不是硬编码调用某个工具。

## 9. 轻量黑板设计

虽然完整目标黑板是 2026 年 7-8 月计划内容，但 MVP 可以提前实现一个轻量版本，作为状态反馈层。

### 9.1 黑板存储内容

```json
{
  "assets": {},
  "services": {},
  "findings": [],
  "task_tree": {},
  "action_results": {},
  "events": []
}
```

### 9.2 黑板作用

- 保存资产状态；
- 保存端口和服务识别结果；
- 保存 Action 执行结果；
- 为后续任务剪枝提供依据；
- 为报告生成提供统一数据源。

MVP 中可以先用本地 JSON 文件或 SQLite 实现，不需要分布式一致性。

## 10. 安全策略

MVP 必须内置安全边界，避免系统被理解为无约束攻击工具。

建议 `safety_policy.yaml` 至少包含：

```yaml
scope:
  allowed_targets:
    - 192.168.56.0/24
  denied_targets:
    - 0.0.0.0/0

risk:
  max_auto_execute_level: medium
  require_approval_levels:
    - high
    - critical

actions:
  deny:
    - persistence
    - destructive_operation
    - credential_dumping
  allow:
    - host_discovery
    - port_scan
    - service_fingerprint
    - web_probe
    - cve_lookup
```

所有 Action 执行前必须经过：

1. 目标范围检查；
2. 风险等级检查；
3. 前置条件检查；
4. 工具约束检查。

## 11. MVP 开发顺序

建议按以下顺序推进，避免陷入工程细节。

### 阶段一：静态知识库

目标：先把系统允许做什么定义清楚。

产物：

- `attack_mapping.yaml`
- `operator_templates.yaml`
- `tool_registry.yaml`
- `safety_policy.yaml`

### 阶段二：数据模型

目标：定义 PTT 节点、算子模板、工具能力、执行结果等核心数据结构。

产物：

- `core/models.py`
- 基础单元测试

### 阶段三：任务解耦

目标：输入结构化任务，输出 PTT 四级任务树。

产物：

- `core/planner.py`
- `core/retriever.py`
- `core/validator.py`

### 阶段四：工具适配

目标：让 Action 能够匹配工具并执行。

产物：

- `adapters/base.py`
- `adapters/mock_adapter.py`
- `adapters/web_probe_adapter.py`
- 可选 `adapters/nmap_adapter.py`

### 阶段五：状态回填与报告

目标：执行结果能回填黑板，并生成简单报告。

产物：

- `core/blackboard.py`
- `outputs/report_generator.py`
- `outputs/report.md`

### 阶段六：演示脚本

目标：一条命令跑通完整流程。

建议命令：

```bash
python app.py --target 192.168.56.10 --profile basic_recon
```

输出：

- PTT 任务树 JSON；
- Action 与算子模板匹配结果；
- 工具选择结果；
- 执行结果 JSON；
- 简要 Markdown 报告。

## 12. 中期考核可展示成果

完成 MVP 后，中期考核可以展示以下内容：

1. 系统总体架构图；
2. PTT 四级任务树数据结构；
3. 从测试目标到任务树的自动拆解示例；
4. 原子算子模板库样例；
5. 工具语义封装样例；
6. 自适应工具选择过程；
7. 一次完整的低风险靶场演示；
8. 生成的结构化结果和简要报告。

## 13. 论文表述建议

中期报告中可以将 MVP 表述为：

> 本阶段已完成基于专家知识约束的协同渗透测试 MVP 原型设计与初步实现。系统围绕 Goal-Tactic-Technique-Action 四级任务树模型，构建了从测试目标解析、专家知识约束检索、原子算子模板匹配到工具语义适配调用的完整链路。通过标准化算子模板库限制任务生成空间，降低大语言模型在安全任务编排过程中的语义幻觉风险；通过工具能力注册表与 Adapter 机制，实现抽象渗透动作到异构工具调用参数的动态映射，为后续目标黑板驱动的多智能体协同执行奠定基础。

## 14. 最小验收标准

MVP 至少满足以下条件，才适合写入中期成果：

- 能加载 ATT&CK/本地知识映射；
- 能加载不少于 10 个原子算子模板；
- 能根据输入目标生成 PTT 四级任务树；
- 每个 Action 都能追溯到一个算子模板；
- 每个可执行 Action 都能匹配到工具 Adapter；
- 至少 3 个 Adapter 可用，其中允许 1-2 个为模拟 Adapter；
- 执行结果能统一为 JSON；
- 能生成一份简要 Markdown 报告；
- 高风险动作不会自动执行，并进入 `waiting_approval` 状态。
