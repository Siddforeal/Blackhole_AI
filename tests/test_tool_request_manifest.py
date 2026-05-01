from bugintel.core.ai_brain import build_ai_brain_plan
from bugintel.core.brain_approval import build_brain_approval_packet
from bugintel.core.brain_decision import build_brain_decision_gate
from bugintel.core.brain_prompt import build_brain_prompt_package
from bugintel.core.brain_review import build_brain_review
from bugintel.core.orchestrator import create_orchestration_plan
from bugintel.core.research_state import build_research_state_from_orchestration
from bugintel.core.tool_request_manifest import (
    build_tool_request_manifest,
    render_tool_request_manifest_markdown,
)


def _approval_packet_data(endpoints):
    orchestration = create_orchestration_plan(target_name="demo", endpoints=endpoints)
    research_state = build_research_state_from_orchestration(orchestration.to_dict())
    ai_brain = build_ai_brain_plan(research_state.to_dict())
    prompt = build_brain_prompt_package(ai_brain.to_dict())
    review = build_brain_review(prompt.to_dict())
    decision = build_brain_decision_gate(review.to_dict())
    approval = build_brain_approval_packet(decision.to_dict())
    return approval.to_dict()


def test_tool_request_manifest_builds_from_approval_packet():
    data = _approval_packet_data(["/api/accounts/123/users/{id}/permissions"])

    manifest = build_tool_request_manifest(data)
    result = manifest.to_dict()

    assert result["target_name"] == "demo"
    assert result["focus_endpoint"] == "/api/accounts/123/users/{id}/permissions"
    assert result["execution_allowed"] is False
    assert result["provider_execution_enabled"] is False
    assert result["planning_only"] is True
    assert result["execution_state"] == "not_executed"
    assert result["requests"]


def test_tool_request_manifest_contains_safety_requests():
    data = _approval_packet_data(["/api/accounts/123/users/{id}/permissions"])

    manifest = build_tool_request_manifest(data)
    request_names = {request["name"] for request in manifest.to_dict()["requests"]}

    assert "Prepare scope confirmation request" in request_names
    assert "Prepare redaction review request" in request_names
    assert "Verify provider execution remains disabled" in request_names
    assert "Verify reportability remains false" in request_names


def test_tool_request_manifest_requests_do_not_allow_execution():
    data = _approval_packet_data(["/api/files/{id}/download"])

    manifest = build_tool_request_manifest(data)

    assert all(request["execution_allowed"] is False for request in manifest.to_dict()["requests"])


def test_render_tool_request_manifest_markdown():
    data = _approval_packet_data(["/api/accounts/123/users/{id}/permissions"])

    manifest = build_tool_request_manifest(data)
    markdown = render_tool_request_manifest_markdown(manifest)

    assert "# Blackhole Tool Request Manifest: demo" in markdown
    assert "Planning-only tool request manifest" in markdown
    assert "Tool Requests" in markdown
    assert "Execution remains disabled" in markdown


def test_tool_request_manifest_handles_empty_approval_packet():
    manifest = build_tool_request_manifest({"target_name": "empty"})
    result = manifest.to_dict()

    assert result["target_name"] == "empty"
    assert result["focus_endpoint"] is None
    assert result["execution_allowed"] is False
    assert result["requests"]
