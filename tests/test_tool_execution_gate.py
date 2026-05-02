from bugintel.core.ai_brain import build_ai_brain_plan
from bugintel.core.brain_approval import build_brain_approval_packet
from bugintel.core.brain_decision import build_brain_decision_gate
from bugintel.core.brain_prompt import build_brain_prompt_package
from bugintel.core.brain_review import build_brain_review
from bugintel.core.orchestrator import create_orchestration_plan
from bugintel.core.research_state import build_research_state_from_orchestration
from bugintel.core.tool_execution_gate import (
    build_tool_execution_gate,
    render_tool_execution_gate_markdown,
)
from bugintel.core.tool_request_manifest import build_tool_request_manifest


def _tool_manifest_data(endpoints):
    orchestration = create_orchestration_plan(target_name="demo", endpoints=endpoints)
    research_state = build_research_state_from_orchestration(orchestration.to_dict())
    ai_brain = build_ai_brain_plan(research_state.to_dict())
    prompt = build_brain_prompt_package(ai_brain.to_dict())
    review = build_brain_review(prompt.to_dict())
    decision = build_brain_decision_gate(review.to_dict())
    approval = build_brain_approval_packet(decision.to_dict())
    manifest = build_tool_request_manifest(approval.to_dict())
    return manifest.to_dict()


def test_tool_execution_gate_builds_from_manifest():
    data = _tool_manifest_data(["/api/accounts/123/users/{id}/permissions"])

    gate = build_tool_execution_gate(data)
    result = gate.to_dict()

    assert result["target_name"] == "demo"
    assert result["focus_endpoint"] == "/api/accounts/123/users/{id}/permissions"
    assert result["gate_decision"] == "blocked-manifest-execution-disabled"
    assert result["execution_allowed"] is False
    assert result["provider_execution_enabled"] is False
    assert result["planning_only"] is True
    assert result["execution_state"] == "not_executed"


def test_tool_execution_gate_items_block_execution():
    data = _tool_manifest_data(["/api/files/{id}/download"])

    gate = build_tool_execution_gate(data)
    result = gate.to_dict()

    assert result["gate_items"]
    assert all(item["gate_status"].startswith("blocked") for item in result["gate_items"])
    assert all("confirm-scope" in item["required_confirmations"] for item in result["gate_items"])


def test_tool_execution_gate_global_confirmations_are_conservative():
    data = _tool_manifest_data(["/api/accounts/123/users/{id}/permissions"])

    gate = build_tool_execution_gate(data)
    confirmations = gate.to_dict()["required_global_confirmations"]

    assert "Confirm program scope and authorization." in confirmations
    assert "Confirm non-destructive mode." in confirmations
    assert "Confirm no finding is treated as reportable without manually validated evidence." in confirmations


def test_render_tool_execution_gate_markdown():
    data = _tool_manifest_data(["/api/accounts/123/users/{id}/permissions"])

    gate = build_tool_execution_gate(data)
    markdown = render_tool_execution_gate_markdown(gate)

    assert "# Blackhole Tool Execution Gate: demo" in markdown
    assert "Planning-only execution gate" in markdown
    assert "Gate Items" in markdown
    assert "execution disabled" in markdown


def test_tool_execution_gate_handles_empty_manifest():
    gate = build_tool_execution_gate({"target_name": "empty"})
    result = gate.to_dict()

    assert result["target_name"] == "empty"
    assert result["focus_endpoint"] is None
    assert result["gate_decision"] == "blocked-missing-focus-endpoint"
    assert result["execution_allowed"] is False
