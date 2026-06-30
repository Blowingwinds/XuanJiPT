from ptt_orchestrator.core.loaders import load_file, load_json, load_text, load_yaml


def test_load_yaml_reads_config() -> None:
    policy = load_yaml("config/safety_policy.yaml")

    assert policy["policy_id"] == "default_mvp_safety_policy"
    assert policy["llm"]["allow_command_generation"] is False


def test_load_yaml_reads_runtime_settings() -> None:
    settings = load_yaml("config/settings.yaml")

    assert settings["app"]["name"] == "XuanJiPT"
    assert settings["features"]["enable_real_adapters"] is False
    assert settings["paths"]["operator_templates"] == "data/operator_templates.yaml"


def test_load_yaml_reads_execution_policy() -> None:
    policy = load_yaml("config/execution_policy.yaml")

    assert policy["scheduler"]["max_parallel_actions"] == 1
    assert policy["adapter_selection"]["weights"]["capability_match"] == 0.4


def test_load_yaml_reads_approval_policy() -> None:
    policy = load_yaml("config/approval_policy.yaml")

    assert "high" in policy["approval"]["required_for_risk_levels"]
    assert policy["execution_after_approval"]["allow_high_risk_auto_resume"] is False


def test_load_yaml_reads_validation_policy() -> None:
    policy = load_yaml("config/validation_policy.yaml")

    assert policy["ptt_dag_validation"]["require_depends_on_acyclic"] is True
    assert policy["template_validation"]["operator_templates"]["require_allowed_tools"] is True


def test_load_yaml_reads_llm_policy() -> None:
    policy = load_yaml("config/llm_policy.yaml")

    assert policy["runtime"]["enabled"] is False
    assert policy["forbidden_outputs"]["allow_command_generation"] is False


def test_load_yaml_reads_blackboard_policy() -> None:
    policy = load_yaml("config/blackboard_policy.yaml")

    assert policy["storage"]["mode"] == "in_memory"
    assert policy["redaction"]["enabled"] is True


def test_load_yaml_reads_report_policy() -> None:
    policy = load_yaml("config/report_policy.yaml")

    assert policy["output"]["default_format"] == "markdown"
    assert policy["sections"]["include_raw_tool_output"] is False


def test_load_yaml_reads_route_templates() -> None:
    routes = load_yaml("data/route_templates.yaml")

    assert "routes" in routes
    assert routes["routes"][0]["route_id"] == "route_basic_exposure_assessment"


def test_load_json_reads_example_input() -> None:
    example = load_json("examples/input_basic_assessment.json")

    assert example["intent"] == "basic_security_assessment"
    assert example["scope"] == ["192.168.56.10"]


def test_load_text_reads_prompt() -> None:
    prompt = load_text("prompts/technique_selection_prompt.md")

    assert "candidate_techniques" in prompt
    assert "selected_techniques_by_tactic" in prompt
    assert "每个输出项的 `tactic_id` 必须来自" in prompt


def test_load_file_dispatches_by_suffix() -> None:
    yaml_data = load_file("data/tool_registry.yaml")
    json_data = load_file("examples/input_web_assessment.json")
    text_data = load_file("docs/guidance/file_boundaries.md")

    assert "tools" in yaml_data
    assert json_data["intent"] == "web_security_assessment"
    assert "目录职责" in text_data
