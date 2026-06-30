# 玄机 XuanJiPT Development Progress

Date: 2026-06-30
Workspace: `C:\ptprojects`

## Project Goal

Build 玄机 XuanJiPT, a paper-oriented PTT-DAG penetration testing task planning prototype based on constrained LLM selection and knowledge-backed validation.

Core flow:

```text
User goal / environment profile
  -> fixed route template
  -> LLM or rule-based tactic-grouped Technique selection
  -> Technique to Operator Template mapping
  -> Operator-instantiated Action
  -> PTT-DAG generation
  -> Validator checks
  -> Scheduler / Adapter / Blackboard / Reporter execution loop
```

Key constraints:

- LLM must not freely generate a full attack chain.
- LLM must not generate tool commands, payloads, exploit steps, or credential guessing steps.
- LLM may only select from candidate routes, tactics, techniques, and registered operators.
- Every Action must come from `data/operator_templates.yaml`.
- Generated PTT-DAGs must pass programmatic validation before downstream use.
- High-risk Actions must enter `waiting_approval` and must not auto-execute.

## Completed Before This Pause

### Config / Data / Prompt / Docs Baseline

The following areas already exist and are aligned with the constrained PTT-DAG design:

- `config/`
  - `settings.yaml`
  - `safety_policy.yaml`
  - `execution_policy.yaml`
  - `approval_policy.yaml`
  - `validation_policy.yaml`
  - `llm_policy.yaml`
  - `blackboard_policy.yaml`
  - `report_policy.yaml`
- `data/`
  - `route_templates.yaml`
  - `technique_operator_mapping.yaml`
  - `operator_templates.yaml`
  - `tool_registry.yaml`
- `prompts/`
  - Route selection
  - Tactic-grouped Technique selection
  - PTT-DAG generation
  - Validation explanation
  - Report summary
- `docs/`
  - File inventory
  - LLM PTT-DAG constraint report
  - Schema notes under `docs/schemas/`

### Implemented Python Modules

- `ptt_orchestrator/core/loaders.py`
  - Generic YAML / JSON / text loading.
- `ptt_orchestrator/core/models.py`
  - `PTTNode`, `PTTEdge`, `PTTDAG`, `OperatorTemplate`, `ToolSpec`.
- `ptt_orchestrator/core/operator_registry.py`
  - Operator registry, lookup, static rules, Technique mapping consistency.
- `ptt_orchestrator/core/route_selector.py`
  - Enabled route filtering, allowed route restriction, route lookup, candidate Technique extraction.
- `ptt_orchestrator/core/validator.py`
  - Implemented this session.
  - Validates route selection.
  - Validates tactic-grouped Technique selection.
  - Rejects flat `selected_techniques` only format.
  - Validates PTT-DAG route, Technique, Operator, Action, edge hierarchy, dependencies, acyclicity, tools, scope, risk, and approval status.
- `ptt_orchestrator/core/planner.py`
  - Implemented this session.
  - Generates rule-first PTT-DAGs from a selected route, Technique selection, Technique-Operator mapping, and Operator Templates.
  - Defaults to route `default_selected_techniques` when no grouped Technique selection is supplied.
  - Rejects disabled routes unless explicitly allowed.
  - Rejects legacy flat Technique selection.
  - Expands route Technique dependencies into Action `depends_on` edges.
  - Sets high-risk Actions to `waiting_approval` when high-risk planning is explicitly allowed.

## Tests

Last full test run:

```text
python -m pytest
66 passed
```

New tests added this session:

- `tests/test_validator.py`
  - 12 tests for route selection, Technique selection, DAG structure, dependencies, tools, scope, and approval.
- `tests/test_planner.py`
  - 7 tests for basic route planning, grouped Technique selection, legacy format rejection, dependency expansion, web route planning, disabled route rejection, and high-risk approval state.

## Important Current Interfaces

### Planner

```python
plan_from_route(
    request,
    route,
    technique_mapping,
    operator_templates,
    safety_policy=safety_policy,
    approval_policy=approval_policy,
)
```

Returns a PTT-DAG dictionary.

### Validator

```python
validate_route_selection(...)
validate_technique_selection(...)
validate_ptt_dag(...)
```

`validate_ptt_dag` should be called before scheduler / adapter use.

## Suggested Next Step

Implement:

```text
ptt_orchestrator/core/scheduler.py
```

Recommended scope:

- Select ready Action nodes from a validated PTT-DAG.
- Only schedule nodes with `level == "Action"`.
- Respect `config/execution_policy.yaml`:
  - `scheduler.ready_status`
  - `scheduler.max_parallel_actions`
  - `scheduler.dependency_success_status`
  - `scheduler.terminal_statuses`
- Do not schedule `waiting_approval`.
- Do not execute tools yet.
- Use Action `depends_on` or `depends_on` edges to determine readiness.

Add:

```text
tests/test_scheduler.py
```

Suggested tests:

- Action with no dependencies and `ready` status is schedulable.
- Action with unmet dependencies is not schedulable.
- Action becomes schedulable when dependencies have `success` status.
- `waiting_approval` is never schedulable.
- `max_parallel_actions` is enforced.
- Non-Action nodes are ignored.

## Files Changed In This Session

- `ptt_orchestrator/core/validator.py`
- `ptt_orchestrator/core/planner.py`
- `tests/test_validator.py`
- `tests/test_planner.py`
- `DEVELOPMENT_PROGRESS.md`
