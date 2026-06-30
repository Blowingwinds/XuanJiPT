# 玄机 XuanJiPT

`玄机 XuanJiPT` is a paper-oriented PTT-DAG penetration testing task planning prototype.

The project explores a constrained planning pipeline:

```text
User goal / environment profile
  -> fixed route template
  -> tactic-grouped Technique selection
  -> Technique to Operator Template mapping
  -> Operator-instantiated Action
  -> PTT-DAG generation
  -> Validator checks
  -> Scheduler / Adapter / Blackboard / Reporter execution loop
```

## Core Design

- LLMs do not freely generate complete attack chains.
- LLMs do not generate tool commands, payloads, exploit steps, or credential guessing steps.
- Routes, Tactics, Techniques, Operators, and tools are constrained by local templates and policies.
- Actions must come from `data/operator_templates.yaml`.
- PTT-DAG output must pass programmatic validation before downstream use.
- High-risk Actions must enter `waiting_approval`.

## Current Status

Implemented:

- Config, data, prompt, and schema documentation scaffolding.
- Route selection helpers.
- Operator registry and template consistency checks.
- Rule-first PTT-DAG planner.
- PTT-DAG validator.

Current test status:

```text
python -m pytest
66 passed
```

Next planned module:

```text
ptt_orchestrator/core/scheduler.py
```
