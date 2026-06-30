# 第二部分开发文档：PTT-DAG 四级任务规划模型

## 1. 本部分定位

本部分对应一阶段工作的第二项：PTT 四级任务树模型。

经过进一步讨论，本研究不再将 PTT 模型仅定义为静态树结构，而是扩展为更适合 Agent 规划与 LangGraph 状态编排的 `PTT-DAG 四级任务规划模型`。

该模型的核心思想是：

```text
PTT 四级结构负责表达任务语义分解；
DAG 执行图负责表达 Action 之间的执行依赖。
```

因此，本部分不是要实现完整渗透测试系统，而是完成论文和后续原型所需的任务规划模型设计。

## 2. 为什么采用 PTT-DAG

传统 PTT 四级任务树可以表达如下层级关系：

```text
Goal -> Tactic -> Technique -> Action
```

这种结构适合说明任务如何从高阶目标逐层分解为原子动作，但它存在一个问题：树结构只能表达父子归属关系，不能充分表达多个 Action 之间的数据依赖、执行顺序、并行关系和条件触发关系。

例如：

```text
服务指纹识别必须依赖端口扫描结果；
CVE 匹配必须依赖服务版本识别结果；
多个目标主机的探测任务可以并行执行。
```

这些关系更适合用有向无环图 DAG 表达。

因此，本研究采用：

```text
PTT 语义层级 + Action 执行 DAG
```

即：

```text
Goal / Tactic / Technique：负责语义归类、专家知识约束和论文解释；
Action DAG：负责执行依赖、并行调度和 Agent 规划。
```

该设计天然适合后续使用 LangGraph 构建 Agent 工作流。

## 3. 模型总体定义

### 3.1 模型名称

建议在论文和开发文档中统一称为：

```text
PTT-DAG 四级任务规划模型
```

也可在首次出现时写作：

```text
Goal-Tactic-Technique-Action Directed Acyclic Graph，简称 PTT-DAG。
```

### 3.2 模型结构

PTT-DAG 包含两类关系：

1. 语义包含关系 `contains`
2. 执行依赖关系 `depends_on`

语义包含关系：

```text
Goal contains Tactic
Tactic contains Technique
Technique contains Action
```

执行依赖关系：

```text
Action A depends_on Action B
```

其中，`depends_on` 只作用于 Action 层，用于表达执行顺序、数据依赖和前置条件依赖。

### 3.3 总体示意

```text
Goal: 基础安全评估
│
├── Tactic: 侦察
│   ├── Technique: 主机发现
│   │   └── Action A: 主机存活探测
│   ├── Technique: 端口发现
│   │   └── Action B: 端口扫描
│   └── Technique: 服务识别
│       └── Action C: 服务指纹识别
│
└── Tactic: 漏洞线索分析
    └── Technique: 已知漏洞匹配
        └── Action D: CVE 匹配

Action DAG:
A -> B -> C -> D
```

该结构既保留了 PTT 的层级解释力，又具备 DAG 的执行调度能力。

## 4. 四级语义层级定义

### 4.1 Goal 层

Goal 表示一次测试任务的总体目标。

示例：

```text
对授权靶场主机进行基础安全评估。
```

Goal 层主要回答：

- 本次任务要达到什么目标；
- 目标对象是什么；
- 授权范围是什么；
- 风险边界是什么；
- 期望输出是什么。

Goal 节点不直接执行工具，也不绑定具体算子。

### 4.2 Tactic 层

Tactic 表示完成 Goal 所需的战术阶段。

示例：

```text
侦察
漏洞线索分析
风险评估
```

Tactic 层主要回答：

- 当前处于什么测试阶段；
- 该阶段对应哪些 ATT&CK 或本地 SOP 战术类别；
- 该阶段包含哪些 Technique。

Tactic 节点通常不直接执行工具。

### 4.3 Technique 层

Technique 表示在某个 Tactic 下采用的具体技术方法。

示例：

```text
主机发现
端口发现
服务识别
Web 技术栈识别
CVE 匹配
```

Technique 层主要回答：

- 该阶段采用什么技术方法；
- 该方法是否来自 ATT&CK 或本地知识库；
- 该方法可以实例化为哪些 Action。

Technique 节点不直接调用工具，但必须能够映射到一个或多个原子算子模板。

### 4.4 Action 层

Action 表示可执行或可模拟执行的最小任务单元。

示例：

```text
对 192.168.56.10 执行主机存活探测。
对 192.168.56.10 扫描常见 TCP 端口。
对 192.168.56.10:80 执行服务指纹识别。
根据识别出的 Apache 版本匹配本地 CVE 知识库。
```

Action 层主要回答：

- 要对哪个目标执行什么动作；
- 执行该动作需要哪些输入；
- 执行前依赖哪些 Action 的结果；
- 该 Action 对应哪个原子算子模板；
- 该 Action 可由哪些工具 Adapter 执行；
- 执行结果如何结构化回填。

Action 是 DAG 的基本执行节点。

## 5. 节点字段设计

### 5.1 通用节点字段

所有节点建议包含以下通用字段：

```json
{
  "node_id": "string",
  "level": "Goal | Tactic | Technique | Action",
  "name": "string",
  "display_name": "string",
  "description": "string",
  "parent_id": "string | null",
  "children": ["string"],
  "status": "pending | ready | running | success | failed | skipped | waiting_approval"
}
```

字段说明：

| 字段 | 含义 |
|---|---|
| node_id | 节点唯一标识 |
| level | 节点层级 |
| name | 机器可读名称 |
| display_name | 人类可读名称 |
| description | 节点说明 |
| parent_id | 语义父节点 ID |
| children | 语义子节点 ID 列表 |
| status | 节点状态 |

### 5.2 Goal 节点字段

```json
{
  "node_id": "goal-001",
  "level": "Goal",
  "name": "basic_security_assessment",
  "display_name": "基础安全评估",
  "description": "对授权靶场主机进行基础安全评估",
  "scope": ["192.168.56.10"],
  "constraints": {
    "max_risk_level": "medium",
    "allow_high_risk": false
  },
  "expected_outputs": ["asset_summary", "service_summary", "risk_findings"],
  "children": ["tac-recon-001", "tac-vuln-analysis-001"],
  "status": "pending"
}
```

### 5.3 Tactic 节点字段

```json
{
  "node_id": "tac-recon-001",
  "level": "Tactic",
  "name": "reconnaissance",
  "display_name": "侦察",
  "description": "收集目标资产、端口和服务信息",
  "parent_id": "goal-001",
  "knowledge_ref": {
    "source": "ATTACK_or_local_SOP",
    "id": "TA0043_or_local_recon"
  },
  "children": ["tech-host-discovery-001", "tech-port-discovery-001"],
  "status": "pending"
}
```

### 5.4 Technique 节点字段

```json
{
  "node_id": "tech-service-discovery-001",
  "level": "Technique",
  "name": "service_discovery",
  "display_name": "服务识别",
  "description": "识别开放端口对应的服务名称和版本信息",
  "parent_id": "tac-recon-001",
  "knowledge_ref": {
    "source": "ATTACK_or_local_SOP",
    "id": "local_service_discovery"
  },
  "candidate_operators": ["op_service_fingerprint"],
  "children": ["act-service-fingerprint-001"],
  "status": "pending"
}
```

### 5.5 Action 节点字段

Action 节点字段需要同时支持语义归属和 DAG 执行依赖。

```json
{
  "node_id": "act-service-fingerprint-001",
  "level": "Action",
  "name": "service_fingerprint",
  "display_name": "服务指纹识别",
  "description": "识别目标端口对应的服务名称和版本信息",
  "parent_id": "tech-service-discovery-001",
  "target": {
    "asset_id": "asset-001",
    "host": "192.168.56.10",
    "port": 80,
    "protocol": "tcp"
  },
  "operator_id": "op_service_fingerprint",
  "inputs": {
    "host": "192.168.56.10",
    "port": 80,
    "protocol": "tcp"
  },
  "outputs": ["service_name", "version", "banner", "confidence"],
  "preconditions": ["target_in_scope", "port_open"],
  "depends_on": ["act-port-scan-001"],
  "produces": ["service_name", "version", "banner"],
  "consumes": ["host", "port"],
  "risk_level": "low",
  "allowed_tools": ["nmap_adapter", "web_probe_adapter"],
  "requires_human_approval": false,
  "status": "pending",
  "result": null
}
```

关键字段说明：

| 字段 | 含义 |
|---|---|
| parent_id | 语义父节点，表示该 Action 属于哪个 Technique |
| depends_on | 执行依赖，表示执行前必须完成哪些 Action |
| operator_id | 对应的原子算子模板 ID |
| produces | 执行后产生的数据字段 |
| consumes | 执行时消耗的数据字段 |
| allowed_tools | 可执行该 Action 的工具 Adapter |
| result | 执行完成后的结构化结果 |

## 6. 边类型设计

PTT-DAG 中建议定义三类边。

### 6.1 contains 语义包含边

用于表达 PTT 层级结构。

```json
{
  "edge_type": "contains",
  "from": "goal-001",
  "to": "tac-recon-001"
}
```

语义：`from` 节点包含 `to` 节点。

合法层级：

```text
Goal -> Tactic
Tactic -> Technique
Technique -> Action
```

### 6.2 depends_on 执行依赖边

用于表达 Action 之间的执行顺序。

```json
{
  "edge_type": "depends_on",
  "from": "act-port-scan-001",
  "to": "act-service-fingerprint-001"
}
```

语义：`to` 节点依赖 `from` 节点先执行完成。

注意：

- `depends_on` 只允许出现在 Action 与 Action 之间；
- `depends_on` 必须构成有向无环图；
- 不允许出现循环依赖。

### 6.3 data_flow 数据流边

可选字段，用于表达某个 Action 产生的数据被另一个 Action 消耗。

```json
{
  "edge_type": "data_flow",
  "from": "act-service-fingerprint-001",
  "to": "act-cve-lookup-001",
  "fields": ["service_name", "version"]
}
```

MVP 阶段可以先不单独实现 `data_flow`，而通过 Action 的 `produces` 和 `consumes` 字段间接表达。

## 7. 状态与风险规则

### 7.1 节点状态

建议使用以下状态集合：

```text
pending
ready
running
success
failed
skipped
waiting_approval
```

含义如下：

| 状态 | 含义 |
|---|---|
| pending | 已生成但尚未满足执行条件 |
| ready | 依赖已满足，可以执行 |
| running | 正在执行 |
| success | 执行成功 |
| failed | 执行失败 |
| skipped | 因范围、风险或条件不满足而跳过 |
| waiting_approval | 需要人工审批 |

### 7.2 风险等级

建议使用以下风险等级：

```text
low
medium
high
critical
```

规则：

- `low`：默认允许自动执行；
- `medium`：在授权范围内可自动执行；
- `high`：默认不自动执行，进入 `waiting_approval`；
- `critical`：默认不自动执行，只保留规划，不进入执行队列。

### 7.3 Action 就绪规则

一个 Action 可进入 `ready` 状态，需要满足：

```text
1. 所有 depends_on 指向的 Action 均为 success；
2. target 在授权 scope 内；
3. risk_level 未超过策略允许值；
4. preconditions 已满足；
5. operator_id 能匹配到算子模板；
6. 至少存在一个 allowed_tools 可用。
```

## 8. PTT-DAG JSON 结构建议

完整 PTT-DAG 可采用如下顶层结构：

```json
{
  "graph_id": "ptt-dag-001",
  "name": "basic_security_assessment_plan",
  "description": "对授权靶场主机进行基础安全评估的 PTT-DAG 任务规划",
  "nodes": [
    {
      "node_id": "goal-001",
      "level": "Goal",
      "name": "basic_security_assessment",
      "display_name": "基础安全评估"
    }
  ],
  "edges": [
    {
      "edge_type": "contains",
      "from": "goal-001",
      "to": "tac-recon-001"
    }
  ],
  "metadata": {
    "created_by": "planner_agent",
    "version": "0.1",
    "scope": ["192.168.56.10"]
  }
}
```

## 9. 示例 PTT-DAG

输入目标：

```text
对授权靶场主机 192.168.56.10 进行基础安全评估，输出资产、服务和初步漏洞线索。
```

示例任务规划：

```text
Goal: 基础安全评估
  Tactic: 侦察
    Technique: 主机发现
      Action A: 主机存活探测
    Technique: 端口发现
      Action B: 端口扫描
    Technique: 服务识别
      Action C: 服务指纹识别
    Technique: Web 信息识别
      Action D: Web 标题识别
  Tactic: 漏洞线索分析
    Technique: 已知漏洞匹配
      Action E: CVE 匹配

Action DAG:
A -> B -> C -> E
B -> D -> E
```

解释：

- 端口扫描依赖主机存活探测；
- 服务指纹识别依赖端口扫描；
- Web 标题识别依赖端口扫描；
- CVE 匹配依赖服务指纹识别和 Web 信息识别；
- C 和 D 可在 B 完成后并行执行。

## 10. 与 LangGraph 的映射关系

PTT-DAG 可以自然映射到 LangGraph 的状态图执行逻辑。

### 10.1 状态对象

LangGraph 中的全局 State 可以包含：

```python
class PTTState(TypedDict):
    graph: dict
    action_results: dict
    ready_queue: list[str]
    completed_actions: list[str]
    failed_actions: list[str]
    blackboard: dict
```

### 10.2 Agent 节点映射

| LangGraph 节点 | 对应功能 |
|---|---|
| Planner Agent | 生成 PTT-DAG |
| Validator Agent | 校验范围、风险、依赖和模板合法性 |
| Scheduler Agent | 根据 DAG 选择 ready Action |
| Tool Agent | 调用工具 Adapter |
| Parser Agent | 解析工具输出为标准 JSON |
| Blackboard Updater | 回填结果并更新任务状态 |
| Reporter Agent | 生成阶段报告 |

### 10.3 执行逻辑

```text
Planner Agent
  -> Validator Agent
  -> Scheduler Agent
  -> Tool Agent
  -> Parser Agent
  -> Blackboard Updater
  -> Scheduler Agent
  -> ...
  -> Reporter Agent
```

其中，`Scheduler Agent -> Tool Agent -> Parser Agent -> Blackboard Updater` 可以循环执行，直到所有 Action 状态为 `success`、`failed`、`skipped` 或 `waiting_approval`。

## 11. 提示词设计要求

提示词不应让模型自由生成渗透命令，而应要求模型在给定候选知识和算子模板范围内输出合法 PTT-DAG。

### 11.1 提示词必须包含

- PTT-DAG 四级定义；
- 每个层级的职责；
- 输出 JSON 结构；
- 合法边类型；
- 风险等级规则；
- Action 必须绑定 `operator_id`；
- Action 只能来自候选算子模板；
- `depends_on` 必须是 Action 之间的无环依赖；
- 不允许输出真实攻击命令；
- 高风险 Action 必须设置 `requires_human_approval: true`；
- 输出必须是合法 JSON。

### 11.2 模型输出后必须程序校验

LLM 输出不能直接用于执行，必须经过程序校验：

```text
1. JSON 格式校验；
2. 节点层级校验；
3. contains 边合法性校验；
4. depends_on 无环校验；
5. operator_id 是否存在于算子模板库；
6. target 是否在授权范围；
7. risk_level 是否超过策略；
8. allowed_tools 是否存在于工具注册表。
```

## 12. 本部分交付物

第二部分完成后，应形成以下交付物：

1. PTT-DAG 四级任务规划模型说明；
2. 四级节点字段定义；
3. 边类型定义；
4. 状态与风险规则；
5. 示例 PTT-DAG；
6. PTT-DAG JSON Schema；
7. 面向 LLM 的 PTT-DAG 生成提示词草案；
8. 后续与 LangGraph 映射说明。

## 13. 最低验收标准

本部分至少应满足：

- 能说明 PTT 树和 DAG 图的区别；
- 能解释为什么采用 PTT-DAG；
- 能定义 Goal、Tactic、Technique、Action 四级含义；
- 能说明 Action 层如何表达 DAG 依赖；
- 能给出节点字段和边字段；
- 能给出一个完整示例；
- 能说明该模型如何与 LangGraph Agent 编排衔接。

## 14. 可写入论文的表述

可在论文中表述为：

> 为兼顾渗透测试任务的语义分解与执行依赖表达，本文在 Goal-Tactic-Technique-Action 四级任务树基础上，引入 Action 层有向无环图结构，提出 PTT-DAG 四级任务规划模型。其中，Goal、Tactic 与 Technique 层用于描述任务目标、战术阶段和技术方法，并与 ATT&CK 专家知识及本地渗透测试 SOP 建立映射关系；Action 层用于描述可执行原子动作，并通过 depends_on 依赖边构建有向无环执行图。该模型既保留了任务树的层级解释能力，又能够表达数据依赖、执行顺序和并行调度关系，为后续基于 LangGraph 的智能体任务编排与目标黑板状态回填提供统一任务表示。
