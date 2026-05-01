from bugintel.core.ai_brain import build_ai_brain_plan
from bugintel.core.brain_decision import build_brain_decision_gate, render_brain_decision_gate_markdown
from bugintel.core.brain_prompt import build_brain_prompt_package
from bugintel.core.brain_review import build_brain_review
from bugintel.core.orchestrator import create_orchestration_plan
from bugintel.core.research_state import build_research_state_from_orchestration


def _brain_review_data(endpoints):
    orchestration = create_orchestration_plan(target_name="demo", endpoints=endpoints)
    research_state = build_research_state_from_orchestration(orchestration.to_dict())
    ai_brain = build_ai_brain_plan(research_state.to_dict())
    prompt = build_brain_prompt_package(ai_brain.to_dict())
    review = build_brain_review(prompt.to_dict())
    return review.to_dict()


def test_brain_decision_gate_builds_from_review():
    data = _brain_review_data(["/api/accounts/123/users/{id}/permissions"])

    gate = build_brain_decision_gate(data)
    result = gate.to_dict()

    assert result["target_name"] == "demo"
    assert result["focus_endpoint"] == "/api/accounts/123/users/{id}/permissions"
    assert result["decision"] == "blocked-pending-scope-and-controls"
    assert result["reportable"] is False
    assert result["planning_only"] is True
    assert result["execution_state"] == "not_executed"


def test_brain_decision_gate_contains_scope_and_approval_blockers():
    data = _brain_review_data(["/api/accounts/123/users/{id}/permissions"])

    gate = build_brain_decision_gate(data)
    blocker_names = {blocker["name"] for blocker in gate.to_dict()["blockers"]}

    assert "scope-confirmation-required" in blocker_names
    assert "controlled-accounts-required" in blocker_names
    assert "human-approval-required" in blocker_names


def test_brain_decision_gate_required_next_steps_are_conservative():
    data = _brain_review_data(["/api/files/{id}/download"])

    gate = build_brain_decision_gate(data)
    steps = gate.to_dict()["required_next_steps"]

    assert "Confirm program scope and authorization." in steps
    assert "Obtain human approval before collecting approval-gated evidence." in steps
    assert "Keep finding status as unconfirmed until manually validated evidence exists." in steps


def test_render_brain_decision_gate_markdown():
    data = _brain_review_data(["/api/accounts/123/users/{id}/permissions"])

    gate = build_brain_decision_gate(data)
    markdown = render_brain_decision_gate_markdown(gate)

    assert "# Blackhole Brain Decision Gate: demo" in markdown
    assert "Planning-only decision gate" in markdown
    assert "scope-confirmation-required" in markdown
    assert "This gate cannot mark anything as confirmed" in markdown


def test_brain_decision_gate_handles_empty_review():
    gate = build_brain_decision_gate({"target_name": "empty"})
    result = gate.to_dict()

    assert result["target_name"] == "empty"
    assert result["focus_endpoint"] is None
    assert result["decision"] == "blocked"
    assert result["reportable"] is False
    assert "missing-focus-endpoint" in {blocker["name"] for blocker in result["blockers"]}
