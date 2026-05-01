from bugintel.core.ai_brain import build_ai_brain_plan, render_ai_brain_plan_markdown
from bugintel.core.orchestrator import create_orchestration_plan
from bugintel.core.research_state import build_research_state_from_orchestration


def _research_state_data(endpoints):
    plan = create_orchestration_plan(target_name="demo", endpoints=endpoints)
    return build_research_state_from_orchestration(plan.to_dict()).to_dict()


def test_ai_brain_plan_builds_focus_queue_from_research_state():
    data = _research_state_data(
        [
            "/api/status",
            "/api/accounts/123/users/{id}/permissions",
            "/api/files/{id}/download",
        ]
    )

    plan = build_ai_brain_plan(data)
    result = plan.to_dict()

    assert result["target_name"] == "demo"
    assert result["planning_only"] is True
    assert result["execution_state"] == "not_executed"
    assert result["provider_execution_enabled"] is False
    assert result["focus_queue"][0]["endpoint"] == "/api/accounts/123/users/{id}/permissions"
    assert result["focus_queue"][0]["triage_state"] == "ready-for-manual-validation"


def test_ai_brain_focus_item_contains_hypotheses_artifacts_and_actions():
    data = _research_state_data(["/api/accounts/123/users/{id}/permissions"])

    plan = build_ai_brain_plan(data)
    item = plan.to_dict()["focus_queue"][0]

    assert "authorization-boundary-hypothesis" in item["hypotheses"]
    assert "controlled-account-role-matrix" in item["required_artifacts"]
    action_names = {action["name"] for action in item["next_actions"]}
    assert "Review endpoint memory" in action_names
    assert "Select strongest open hypothesis" in action_names
    assert "Prepare approval-gated evidence collection" in action_names
    assert "Update research state after manual validation" in action_names


def test_ai_brain_low_signal_endpoint_is_deprioritized():
    data = _research_state_data(["/api/status"])

    plan = build_ai_brain_plan(data)
    item = plan.to_dict()["focus_queue"][0]
    action_names = {action["name"] for action in item["next_actions"]}

    assert item["triage_state"] == "deprioritized"
    assert "Keep low-signal route on watchlist" in action_names


def test_ai_brain_plan_contains_global_actions_and_safety_gates():
    data = _research_state_data(["/api/files/{id}/download"])

    plan = build_ai_brain_plan(data)
    result = plan.to_dict()

    action_names = {action["name"] for action in result["global_actions"]}

    assert "Confirm scope and authorization" in action_names
    assert "Review approval-gated artifacts" in action_names
    assert "scope-confirmation" in result["safety_gates"]
    assert "no-llm-provider-execution" in result["safety_gates"]
    assert "no-network-execution" in result["safety_gates"]


def test_render_ai_brain_plan_markdown_contains_focus_queue():
    data = _research_state_data(["/api/accounts/123/users/{id}/permissions"])

    plan = build_ai_brain_plan(data)
    markdown = render_ai_brain_plan_markdown(plan)

    assert "# Blackhole AI Brain Plan: demo" in markdown
    assert "Planning-only AI brain interface" in markdown
    assert "Focus Queue" in markdown
    assert "authorization-boundary-hypothesis" in markdown
    assert "Prepare approval-gated evidence collection" in markdown
