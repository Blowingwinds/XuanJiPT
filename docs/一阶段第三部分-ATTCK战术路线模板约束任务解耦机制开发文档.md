# 第三部分开发文档：基于 ATT&CK 战术路线模板的 PTT-DAG 任务解耦机制

## 1. 本部分定位

本部分对应一阶段工作的第三项：基于 ATT&CK 专家知识约束的任务解耦机制。

第二部分已经定义了 `PTT-DAG 四级任务规划模型`，回答的是：

```text
PTT-DAG 长什么样？
```

第三部分需要回答的是：

```text
PTT-DAG 如何在专家知识约束下生成？
```

本部分的核心设计是：

```text
固定 ATT&CK 战术路线模板
  + LLM 在候选 Technique 集合内受限选择
  + 原子算子模板约束 Action 生成
  + 程序校验输出合法 PTT-DAG
```

该机制不是让 LLM 自由规划完整攻击链，而是通过预定义战术路线收敛搜索空间，再让 LLM 在有限候选技术集合中完成语义选择和排序。

## 2. 设计目标

本部分主要解决以下问题：

1. 如何将用户的高阶测试目标拆解为 PTT-DAG；
2. 如何使用 ATT&CK 知识约束任务规划路径；
3. 如何避免 LLM 自由发挥导致的语义幻觉和路径发散；
4. 如何保证 Technique 能够映射到合法原子算子；
5. 如何保证最终 Action 可被后续工具语义封装模块处理。

一阶段不追求完整 ATT&CK 矩阵覆盖，而是优先选择几条最常见、低风险、适合论文展示和 MVP 原型验证的战术路线。

## 3. 核心思想

### 3.1 从自由规划改为路线模板约束

如果直接让 LLM 根据目标生成完整渗透测试路径，容易出现以下问题：

- 生成不存在的技术方法；
- 跳过必要前置步骤；
- 输出不符合授权范围的动作；
- 混入高风险攻击行为；
- Action 无法映射到工具或算子模板；
- 任务链缺乏可解释性和可校验性。

因此，本研究采用路线模板约束方法：

```text
先由系统提供少量固定战术路线模板，
再让 LLM 在路线中的候选 Technique 范围内选择，
最后由程序校验器生成合法 PTT-DAG。
```

### 3.2 LLM 的角色

LLM 在本机制中不是自由规划器，而是受限选择器和语义解释器。

LLM 可以做：

- 根据用户目标选择最合适的路线模板；
- 在给定 Tactic 下从候选 Technique 中选择；
- 对候选 Technique 进行排序；
- 解释为什么选择某些 Technique；
- 辅助生成面向论文展示的任务说明。

LLM 不允许做：

- 自行新增战术路线；
- 自行新增未登记 Technique；
- 自行新增未登记 operator_id；
- 输出真实攻击命令；
- 生成超出授权范围的 Action；
- 将高风险动作标记为可自动执行。

## 4. 输入与输出

### 4.1 输入数据

任务解耦模块输入包括三类信息。

#### 4.1.1 用户目标

```json
{
  "goal": "对授权靶场主机进行基础安全评估"
}
```

#### 4.1.2 环境画像

```json
{
  "assets": [
    {
      "asset_id": "asset-001",
      "host": "192.168.56.10",
      "known_ports": [],
      "known_services": [],
      "known_findings": []
    }
  ]
}
```

#### 4.1.3 约束策略

```json
{
  "scope": ["192.168.56.10"],
  "max_risk_level": "medium",
  "allow_high_risk": false,
  "allowed_route_ids": [
    "route_basic_exposure_assessment",
    "route_web_service_risk_assessment",
    "route_internal_asset_discovery"
  ]
}
```

### 4.2 输出数据

输出为合法的 PTT-DAG 任务规划。

```json
{
  "graph_id": "ptt-dag-001",
  "selected_route_id": "route_basic_exposure_assessment",
  "nodes": [],
  "edges": [],
  "metadata": {
    "planner": "route_template_constrained_planner",
    "version": "0.1"
  }
}
```

## 5. 固定 ATT&CK 战术路线模板

一阶段建议先定义 3 条默认启用路线，以及 1 条默认禁用的高风险扩展路线。

### 5.1 路线 1：基础暴露面评估路线

路线 ID：

```text
route_basic_exposure_assessment
```

路线结构：

```text
Reconnaissance -> Discovery -> Vulnerability Analysis -> Report
```

适用场景：

```text
对单个授权靶场主机或小规模资产进行基础安全评估。
```

推荐作为 MVP 默认路线。

候选 Technique：

| Tactic | Candidate Technique |
|---|---|
| Reconnaissance | host_discovery |
| Discovery | port_discovery |
| Discovery | service_discovery |
| Discovery | web_information_discovery |
| Vulnerability Analysis | cve_lookup |
| Vulnerability Analysis | config_risk_check |
| Report | report_summary |

典型 Action DAG：

```text
host_discovery
  -> port_discovery
  -> service_discovery
  -> cve_lookup
  -> report_summary

port_discovery
  -> web_information_discovery
  -> cve_lookup
```

### 5.2 路线 2：Web 服务风险评估路线

路线 ID：

```text
route_web_service_risk_assessment
```

路线结构：

```text
Reconnaissance -> Discovery -> Web Fingerprinting -> Vulnerability Analysis -> Report
```

适用场景：

```text
目标存在 Web 服务，需要评估 Web 暴露面、技术栈、TLS 和已知版本风险。
```

候选 Technique：

| Tactic | Candidate Technique |
|---|---|
| Reconnaissance | host_discovery |
| Discovery | port_discovery |
| Web Fingerprinting | web_title_detection |
| Web Fingerprinting | web_header_analysis |
| Web Fingerprinting | web_tech_stack_identification |
| Web Fingerprinting | tls_certificate_inspection |
| Vulnerability Analysis | cve_lookup |
| Vulnerability Analysis | web_config_risk_check |
| Report | report_summary |

典型 Action DAG：

```text
host_discovery
  -> port_discovery
  -> web_title_detection
  -> web_header_analysis
  -> web_tech_stack_identification
  -> cve_lookup
  -> report_summary

port_discovery
  -> tls_certificate_inspection
  -> cve_lookup
```

说明：

该路线只做 Web 风险识别和版本线索分析，不做真实漏洞利用。

### 5.3 路线 3：内网资产发现路线

路线 ID：

```text
route_internal_asset_discovery
```

路线结构：

```text
Discovery -> Service Discovery -> Asset Classification -> Report
```

适用场景：

```text
对授权内网网段或靶场网络进行资产发现与基础分类。
```

候选 Technique：

| Tactic | Candidate Technique |
|---|---|
| Discovery | host_discovery |
| Discovery | port_discovery |
| Service Discovery | service_discovery |
| Service Discovery | os_hint_detection |
| Asset Classification | asset_type_classification |
| Asset Classification | service_role_classification |
| Report | asset_inventory_summary |

典型 Action DAG：

```text
host_discovery
  -> port_discovery
  -> service_discovery
  -> asset_type_classification
  -> asset_inventory_summary

service_discovery
  -> service_role_classification
  -> asset_inventory_summary
```

说明：

该路线适合后续扩展多智能体并发扫描和目标黑板状态同步。

### 5.4 路线 4：凭据风险检查路线，默认禁用

路线 ID：

```text
route_credential_risk_assessment
```

路线结构：

```text
Discovery -> Credential Risk Assessment -> Report
```

适用场景：

```text
仅用于论文中说明系统具备高风险动作识别和人工审批能力。
```

候选 Technique：

| Tactic | Candidate Technique |
|---|---|
| Discovery | service_discovery |
| Credential Risk Assessment | weak_credential_check |
| Credential Risk Assessment | default_credential_check |
| Report | report_summary |

处理规则：

- 默认不启用；
- 若被规划，相关 Action 必须设置 `risk_level: high`；
- 必须设置 `requires_human_approval: true`；
- 状态必须为 `waiting_approval`；
- 不允许自动执行。

## 6. 路线模板数据结构

建议路线模板采用 YAML 或 JSON 维护。

示例：

```yaml
route_id: route_basic_exposure_assessment
name: basic_exposure_assessment
display_name: 基础暴露面评估路线
description: 对授权目标进行主机、端口、服务和初步漏洞线索识别
enabled: true
risk_level: low
recommended_for:
  - basic_security_assessment
  - exposure_assessment
  - mvp_demo
tactics:
  - tactic_id: reconnaissance
    display_name: 侦察
    candidate_techniques:
      - host_discovery
  - tactic_id: discovery
    display_name: 发现
    candidate_techniques:
      - port_discovery
      - service_discovery
      - web_information_discovery
  - tactic_id: vulnerability_analysis
    display_name: 漏洞线索分析
    candidate_techniques:
      - cve_lookup
      - config_risk_check
  - tactic_id: report
    display_name: 报告汇总
    candidate_techniques:
      - report_summary
execution_dependencies:
  - from: host_discovery
    to: port_discovery
  - from: port_discovery
    to: service_discovery
  - from: port_discovery
    to: web_information_discovery
  - from: service_discovery
    to: cve_lookup
  - from: web_information_discovery
    to: cve_lookup
  - from: cve_lookup
    to: report_summary
```

## 7. Technique 到 Operator 的映射

第三部分只定义映射关系，不展开完整算子模板字段。完整算子设计放在第四部分。

建议维护一个 Technique 到 Operator 的映射表：

```yaml
host_discovery:
  candidate_operators:
    - op_host_discovery

port_discovery:
  candidate_operators:
    - op_port_scan

service_discovery:
  candidate_operators:
    - op_service_fingerprint

web_information_discovery:
  candidate_operators:
    - op_web_title
    - op_web_tech_stack

tls_certificate_inspection:
  candidate_operators:
    - op_tls_certificate

cve_lookup:
  candidate_operators:
    - op_cve_lookup

config_risk_check:
  candidate_operators:
    - op_config_risk_check

weak_credential_check:
  candidate_operators:
    - op_weak_credential_check

report_summary:
  candidate_operators:
    - op_report_summary
```

约束规则：

```text
Technique 必须至少映射到一个 operator_id；
Action 必须从 Technique 对应的 operator_id 实例化；
不存在 operator_id 的 Technique 不允许进入最终 PTT-DAG；
operator_id 必须存在于第四部分定义的原子算子模板库中。
```

## 8. 任务解耦流程

本机制建议分为七步。

### Step 1：目标解析

从用户目标中提取：

- 测试意图；
- 测试对象；
- 授权范围；
- 期望输出；
- 风险边界。

示例：

```json
{
  "intent": "basic_security_assessment",
  "targets": ["192.168.56.10"],
  "expected_outputs": ["asset_summary", "service_summary", "risk_findings"],
  "risk_boundary": "medium"
}
```

### Step 2：环境画像归一化

将输入资产信息转化为统一结构。

```json
{
  "asset_id": "asset-001",
  "host": "192.168.56.10",
  "ports": [],
  "services": [],
  "known_findings": []
}
```

### Step 3：战术路线模板匹配

根据用户目标和策略，从启用路线中选择最合适路线。

匹配依据：

- 用户意图；
- 资产类型；
- 是否存在 Web 服务；
- 授权范围；
- 风险边界；
- 路线是否 enabled。

示例：

```text
basic_security_assessment -> route_basic_exposure_assessment
web_security_assessment -> route_web_service_risk_assessment
internal_asset_inventory -> route_internal_asset_discovery
```

### Step 4：候选 Technique 选择

在选定路线模板内，LLM 只能从候选 Technique 中选择。

输入给 LLM 的不是完整 ATT&CK 矩阵，而是经过路线模板过滤后的候选列表。

示例：

```json
{
  "selected_route": "route_basic_exposure_assessment",
  "candidate_techniques": [
    "host_discovery",
    "port_discovery",
    "service_discovery",
    "web_information_discovery",
    "cve_lookup",
    "config_risk_check",
    "report_summary"
  ]
}
```

LLM 输出：

```json
{
  "selected_techniques": [
    "host_discovery",
    "port_discovery",
    "service_discovery",
    "web_information_discovery",
    "cve_lookup",
    "report_summary"
  ],
  "reasoning_summary": "目标为基础安全评估，优先选择低风险的信息收集与版本风险分析技术。"
}
```

### Step 5：Technique 映射 Operator

程序根据映射表将 Technique 转换为 operator_id。

示例：

```text
service_discovery -> op_service_fingerprint
web_information_discovery -> op_web_title + op_web_tech_stack
cve_lookup -> op_cve_lookup
```

### Step 6：Action 实例化

将 operator_id 与目标资产、端口、服务等信息结合，实例化为 Action 节点。

示例：

```json
{
  "node_id": "act-service-fingerprint-001",
  "level": "Action",
  "name": "service_fingerprint",
  "parent_id": "tech-service-discovery-001",
  "operator_id": "op_service_fingerprint",
  "target": {
    "asset_id": "asset-001",
    "host": "192.168.56.10"
  },
  "depends_on": ["act-port-scan-001"],
  "risk_level": "low",
  "status": "pending"
}
```

一阶段建议采用静态规划依赖，即先按照路线模板中的 `execution_dependencies` 建立 DAG。后续可以在执行过程中根据结果动态扩展 Action。

### Step 7：合法性校验与 PTT-DAG 输出

生成初始 PTT-DAG 后必须执行校验。

校验通过后，输出最终任务规划。

## 9. 合法性校验规则

校验器至少应检查以下内容：

1. 路线合法性
   - route_id 是否存在；
   - route 是否 enabled；
   - route 是否在 allowed_route_ids 内。

2. Technique 合法性
   - Technique 是否属于选定路线候选集合；
   - LLM 是否新增了未授权 Technique；
   - Technique 是否能映射到 operator_id。

3. Operator 合法性
   - operator_id 是否存在于原子算子模板库；
   - operator_id 风险等级是否符合策略。

4. PTT 层级合法性
   - Goal -> Tactic -> Technique -> Action 结构是否完整；
   - contains 边是否合法。

5. DAG 合法性
   - depends_on 是否只存在于 Action 之间；
   - 是否存在循环依赖；
   - 依赖节点是否存在。

6. 范围与风险合法性
   - target 是否在授权 scope 内；
   - risk_level 是否超过 max_risk_level；
   - high / critical 动作是否被设置为 waiting_approval。

7. 可执行性合法性
   - Action 是否有 operator_id；
   - Action 是否有至少一个候选工具；
   - Action 所需输入是否能由目标或上游 Action 结果提供。

## 10. LLM 提示词草案

以下是第三部分的受限 Technique 选择提示词草案。

```text
你是一个渗透测试任务规划助手。你的任务不是生成攻击命令，而是在给定的 ATT&CK 战术路线模板和候选 Technique 集合中，选择适合当前授权测试目标的 Technique。

必须遵守以下规则：
1. 只能从 candidate_techniques 中选择，不允许新增 Technique。
2. 不允许输出任何真实攻击命令、payload 或漏洞利用步骤。
3. 若候选 Technique 涉及 high 或 critical 风险，只能标记为 requires_human_approval，不允许自动执行。
4. 输出必须是合法 JSON。
5. 只输出 selected_techniques 和 reasoning_summary。

输入信息：
- 用户目标：{{goal}}
- 授权范围：{{scope}}
- 选定路线：{{selected_route}}
- 候选 Technique：{{candidate_techniques}}
- 风险边界：{{risk_policy}}

请输出：
{
  "selected_techniques": [],
  "reasoning_summary": ""
}
```

注意：

LLM 输出的 Technique 选择结果不能直接使用，必须交由程序校验。

## 11. 示例：从目标到 PTT-DAG

输入目标：

```text
对授权靶场主机 192.168.56.10 进行基础安全评估，输出资产、服务和初步漏洞线索。
```

路线匹配：

```text
route_basic_exposure_assessment
```

LLM 在候选集合中选择：

```text
host_discovery
port_discovery
service_discovery
web_information_discovery
cve_lookup
report_summary
```

Technique 到 Operator 映射：

```text
host_discovery -> op_host_discovery
port_discovery -> op_port_scan
service_discovery -> op_service_fingerprint
web_information_discovery -> op_web_title, op_web_tech_stack
cve_lookup -> op_cve_lookup
report_summary -> op_report_summary
```

生成 Action DAG：

```text
act-host-discovery-001
  -> act-port-scan-001
  -> act-service-fingerprint-001
  -> act-cve-lookup-001
  -> act-report-summary-001

act-port-scan-001
  -> act-web-title-001
  -> act-web-tech-stack-001
  -> act-cve-lookup-001
```

最终输出为 PTT-DAG，其中：

- Goal 描述基础安全评估目标；
- Tactic 由路线模板给出；
- Technique 由 LLM 在候选集合内选择；
- Action 由 operator_id 实例化；
- DAG 依赖由路线模板和 Technique 映射规则生成。

## 12. 与第二部分的关系

第二部分定义：

```text
PTT-DAG 的数据结构和图模型。
```

第三部分定义：

```text
如何基于 ATT&CK 战术路线模板生成 PTT-DAG。
```

因此，第三部分重点是任务解耦流程、路线模板、Technique 选择和合法性校验，不重复展开 PTT-DAG 节点完整字段。

## 13. 与第四部分的关系

第四部分将详细设计原子算子模板库。

第三部分只要求：

```text
Technique 必须能映射到 operator_id；
operator_id 必须存在于原子算子模板库；
没有合法 operator_id 的 Technique 不允许进入最终 PTT-DAG。
```

## 14. 本部分交付物

第三部分完成后，应形成以下交付物：

1. ATT&CK 战术路线模板说明；
2. 至少 3 条默认启用路线；
3. 1 条默认禁用高风险路线；
4. 路线模板 YAML/JSON 结构；
5. Technique 到 Operator 映射规则；
6. 任务解耦流程说明；
7. 合法性校验规则；
8. 受限 Technique 选择提示词草案；
9. 从用户目标到 PTT-DAG 的完整示例。

## 15. 最低验收标准

本部分至少满足：

- 能说明为什么不让 LLM 自由生成完整任务链；
- 能定义固定战术路线模板；
- 能给出 3 条低风险路线和 1 条高风险禁用路线；
- 能说明 LLM 如何在候选 Technique 中受限选择；
- 能说明 Technique 如何映射到 operator_id；
- 能说明如何校验 LLM 输出；
- 能给出完整任务解耦示例。

## 16. 可写入论文的表述

可在论文中表述为：

> 为降低大语言模型在渗透测试任务规划中的路径发散与语义幻觉风险，本文设计了一种基于 ATT&CK 战术路线模板的 PTT-DAG 任务解耦机制。该机制不直接让大语言模型自由生成完整攻击链，而是首先从 ATT&CK 知识矩阵与本地渗透测试 SOP 中抽取若干常见、低风险且适合授权测试场景的战术路线模板，如基础暴露面评估路线、Web 服务风险评估路线和内网资产发现路线。系统根据用户目标与环境画像匹配合适路线，并在路线限定的候选 Technique 集合内引入大语言模型进行受限选择与排序。随后，程序根据 Technique-Operator 映射表将所选技术实例化为 Action 节点，并结合路线模板中的执行依赖生成 PTT-DAG。最终通过合法性校验器检查路线、Technique、Operator、授权范围、风险等级和 DAG 无环性，从而保证生成的任务规划具备可解释性、可追溯性和安全边界。
