from bugintel.core.ai_brain import build_ai_brain_plan
from bugintel.core.brain_approval import build_brain_approval_packet, render_brain_approval_packet_markdown
from bugintel.core.brain_decision import build_brain_decision_gate
from bugintel.core.brain_prompt import build_brain_prompt_package
from bugintel.core.brain_review import build_brain_review
from bugintel.core.orchestrator import create_orchestration_plan
from bugintel.core.research_state import build_research_state_from_orchestration


def _decision_data(endpoints):
    orchestration = create_orchestration_plan(target_name="demo", endpoints=endpoints)
    research_state = build_research_state_from_orchestration(orchestration.to_dict())
    ai_brain = build_ai_brain_plan(research_state.to_dict())
    prompt = build_brain_prompt_package(ai_brain.to_dict())
    review = build_brain_review(prompt.to_dict())
    decision = build_brain_decision_gate(review.to_dict())
    return decision.to_dict()


def test_brain_approval_packet_builds_from_decision():
    data = _decision_data(["/api/accounts/123/users/{id}/permissions"])

    packet = build_brain_approval_packet(data)
    result = packet.to_dict()

    assert result["target_name"] == "demo"
    assert result["focus_endpoint"] == "/api/accounts/123/users/{id}/permissions"
    assert result["source_decision"] == "blocked-pending-scope-and-controls"
    assert result["approval_status"] == "blocked-pending-approval"
    assert result["approval_required"] is True
    assert result["reportable"] is False
    assert result["planning_only"] is True


def test_brain_approval_packet_contains_required_items():
    data = _decision_data(["/api/accounts/123/users/{id}/permissions"])

    packet = build_brain_approval_packet(data)
    item_names = {item["name"] for item in packet.to_dict()["approval_items"]}

    assert "Confirm program scope and authorization" in item_names
    assert "Confirm controlled test accounts and objects" in item_names
    assert "Approve evidence collection" in item_names
    assert "Confirm redaction plan" in item_names
    assert "Confirm non-destructive validation" in item_names


def test_brain_approval_packet_checklist_is_conservative():
    data = _decision_data(["/api/files/{id}/download"])

    packet = build_brain_approval_packet(data)
    checklist = packet.to_dict()["checklist"]

    assert "Confirm provider execution remains disabled." in checklist
    assert "Keep reportability false until manually validated evidence exists." in checklist
    assert any(step.startswith("Approve or resolve:") for step in checklist)


def test_render_brain_approval_packet_markdown():
    data = _decision_data(["/api/accounts/123/users/{id}/permissions"])

    packet = build_brain_approval_packet(data)
    markdown = render_brain_approval_packet_markdown(packet)

    assert "# Blackhole Human Approval Packet: demo" in markdown
    assert "Planning-only approval packet" in markdown
    assert "Confirm program scope and authorization" in markdown
    assert "Keep the finding unconfirmed" in markdown


def test_brain_approval_packet_handles_empty_decision():
    packet = build_brain_approval_packet({"target_name": "empty"})
    result = packet.to_dict()

    assert result["target_name"] == "empty"
    assert result["focus_endpoint"] is None
    assert result["approval_required"] is True
    assert "Select focus endpoint" in {item["name"] for item in result["approval_items"]}
