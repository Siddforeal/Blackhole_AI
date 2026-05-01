from bugintel.core.ai_brain import build_ai_brain_plan
from bugintel.core.brain_prompt import build_brain_prompt_package
from bugintel.core.brain_review import build_brain_review, render_brain_review_markdown
from bugintel.core.orchestrator import create_orchestration_plan
from bugintel.core.research_state import build_research_state_from_orchestration


def _prompt_package_data(endpoints):
    orchestration = create_orchestration_plan(target_name="demo", endpoints=endpoints)
    research_state = build_research_state_from_orchestration(orchestration.to_dict())
    ai_brain = build_ai_brain_plan(research_state.to_dict())
    return build_brain_prompt_package(ai_brain.to_dict()).to_dict()


def test_brain_review_builds_from_prompt_package():
    data = _prompt_package_data(
        [
            "/api/accounts/123/users/{id}/permissions",
            "/api/status",
        ]
    )

    review = build_brain_review(data)
    result = review.to_dict()

    assert result["target_name"] == "demo"
    assert result["focus_endpoint"] == "/api/accounts/123/users/{id}/permissions"
    assert result["planning_only"] is True
    assert result["execution_state"] == "not_executed"
    assert result["provider_execution_enabled"] is False
    assert result["sections"]


def test_brain_review_contains_expected_sections_and_context():
    data = _prompt_package_data(["/api/accounts/123/users/{id}/permissions"])

    review = build_brain_review(data)
    result = review.to_dict()
    section_titles = {section["title"] for section in result["sections"]}
    markdown = result["markdown"]

    assert "Recommended Focus Endpoint" in section_titles
    assert "Why This Endpoint Is Highest Signal" in section_titles
    assert "Open Hypotheses To Review" in section_titles
    assert "Evidence Artifacts Needed" in section_titles
    assert "Human Approvals Required" in section_titles
    assert "Safety Gates Still Blocking Execution" in section_titles
    assert "Next Manual Validation Step" in section_titles
    assert "Stop Conditions" in section_titles
    assert "Research State Updates After Validation" in section_titles
    assert "authorization-boundary-hypothesis" in markdown
    assert "controlled-account-role-matrix" in markdown


def test_brain_review_keeps_safety_gates():
    data = _prompt_package_data(["/api/files/{id}/download"])

    review = build_brain_review(data)
    result = review.to_dict()

    assert "scope-confirmation" in result["safety_gates"]
    assert "no-llm-provider-execution" in result["safety_gates"]
    assert "no-network-execution" in result["safety_gates"]


def test_render_brain_review_markdown():
    data = _prompt_package_data(["/api/accounts/123/users/{id}/permissions"])

    review = build_brain_review(data)
    markdown = render_brain_review_markdown(review)

    assert "# Blackhole Brain Review: demo" in markdown
    assert "Planning-only reasoning review" in markdown
    assert "Recommended Focus Endpoint" in markdown
    assert "Stop Conditions" in markdown
    assert "Do not execute requests" in markdown


def test_brain_review_handles_empty_prompt_package():
    review = build_brain_review({"target_name": "empty"})
    result = review.to_dict()

    assert result["target_name"] == "empty"
    assert result["focus_endpoint"] is None
    assert result["planning_only"] is True
    assert "No focus endpoint" in result["markdown"]
