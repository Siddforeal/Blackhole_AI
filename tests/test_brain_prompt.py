from bugintel.core.ai_brain import build_ai_brain_plan
from bugintel.core.brain_prompt import build_brain_prompt_package, render_brain_prompt_package_markdown
from bugintel.core.orchestrator import create_orchestration_plan
from bugintel.core.research_state import build_research_state_from_orchestration


def _ai_brain_plan_data(endpoints):
    orchestration = create_orchestration_plan(target_name="demo", endpoints=endpoints)
    research_state = build_research_state_from_orchestration(orchestration.to_dict())
    return build_ai_brain_plan(research_state.to_dict()).to_dict()


def test_brain_prompt_package_builds_from_ai_brain_plan():
    data = _ai_brain_plan_data(
        [
            "/api/accounts/123/users/{id}/permissions",
            "/api/status",
        ]
    )

    package = build_brain_prompt_package(data)
    result = package.to_dict()

    assert result["target_name"] == "demo"
    assert result["planning_only"] is True
    assert result["execution_state"] == "not_executed"
    assert result["provider_execution_enabled"] is False
    assert result["focus_endpoint"] == "/api/accounts/123/users/{id}/permissions"
    assert result["message_count"] == 4


def test_brain_prompt_package_contains_safety_and_focus_context():
    data = _ai_brain_plan_data(["/api/accounts/123/users/{id}/permissions"])

    package = build_brain_prompt_package(data)
    all_content = "\n".join(message.content for message in package.messages)

    assert "planning-only" in all_content
    assert "scope and authorization" in all_content
    assert "/api/accounts/123/users/{id}/permissions" in all_content
    assert "authorization-boundary-hypothesis" in all_content
    assert "controlled-account-role-matrix" in all_content
    assert "Do not write executable exploit code" in all_content


def test_brain_prompt_package_exposes_safety_gates():
    data = _ai_brain_plan_data(["/api/files/{id}/download"])

    package = build_brain_prompt_package(data)
    result = package.to_dict()

    assert "scope-confirmation" in result["safety_gates"]
    assert "no-llm-provider-execution" in result["safety_gates"]
    assert "no-network-execution" in result["safety_gates"]


def test_render_brain_prompt_package_markdown():
    data = _ai_brain_plan_data(["/api/accounts/123/users/{id}/permissions"])

    package = build_brain_prompt_package(data)
    markdown = render_brain_prompt_package_markdown(package)

    assert "# Blackhole LLM Brain Prompt Package: demo" in markdown
    assert "Provider execution is disabled" in markdown
    assert "Message 1" in markdown
    assert "assistant_task" in markdown
    assert "Recommended focus endpoint" in markdown


def test_brain_prompt_package_handles_empty_plan():
    package = build_brain_prompt_package({"target_name": "empty"})
    result = package.to_dict()

    assert result["target_name"] == "empty"
    assert result["focus_endpoint"] is None
    assert result["message_count"] == 4
    assert result["planning_only"] is True
