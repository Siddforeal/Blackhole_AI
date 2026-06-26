from bugintel.core.case_intake_brain_handoff_approval_packet_exporter import (
    export_case_intake_brain_handoff_approval_packet,
)
from bugintel.core.case_intake_brain_handoff_manual_validation_plan_exporter import (
    export_case_intake_brain_handoff_manual_validation_plan,
)
from tests.test_case_intake_brain_handoff_answerer import _handoff


def _manual_plan() -> dict:
    return export_case_intake_brain_handoff_manual_validation_plan(_handoff()).to_dict()


def test_approval_packet_exports_selected_endpoint() -> None:
    packet = export_case_intake_brain_handoff_approval_packet(
        _manual_plan(),
        endpoint="/api/admin/users/{id}/permissions",
    )

    assert packet.approval_id == "AP-001"
    assert packet.target_name == "demo-program"
    assert packet.endpoint == "/api/admin/users/{id}/permissions"
    assert packet.proposed_action == "manual-read-only-validation-review"
    assert packet.human_approval_required is True
    assert packet.approved is False
    assert packet.approval_status == "pending-human-approval"
    assert packet.read_only_required is True
    assert packet.blocked is False
    assert packet.validation_allowed is False
    assert packet.runtime_execution_allowed is False
    assert packet.tool_execution_allowed is False
    assert packet.browser_execution_allowed is False
    assert packet.evidence_collection_allowed is False
    assert packet.target_mutation_allowed is False
    assert packet.report_submission_allowed is False
    assert packet.vulnerability_confirmation_allowed is False
    assert packet.account_matrix
    assert packet.validation_steps
    assert packet.evidence_targets
    assert packet.checklist_ids[0] == "EC-001"
    assert packet.stop_conditions
    assert packet.redaction_requirements


def test_approval_packet_defaults_to_first_endpoint() -> None:
    packet = export_case_intake_brain_handoff_approval_packet(_manual_plan())

    assert packet.approval_id == "AP-001"
    assert packet.endpoint == "/api/admin/users/{id}/permissions"
    assert packet.blocked is False


def test_approval_packet_blocks_unknown_endpoint() -> None:
    packet = export_case_intake_brain_handoff_approval_packet(
        _manual_plan(),
        endpoint="/api/missing",
    )

    assert packet.blocked is True
    assert packet.approval_status == "blocked"
    assert packet.block_reason == "Requested endpoint was not found in the manual validation plan."
    assert packet.validation_allowed is False
    assert packet.tool_execution_allowed is False


def test_approval_packet_blocks_invalid_input() -> None:
    packet = export_case_intake_brain_handoff_approval_packet({"kind": "wrong"})

    assert packet.blocked is True
    assert packet.approval_id == "AP-BLOCKED"
    assert packet.approval_status == "blocked"
    assert "not a case_intake_brain_handoff_manual_validation_plan" in packet.block_reason


def test_approval_packet_serializes_safety_metadata() -> None:
    data = export_case_intake_brain_handoff_approval_packet(_manual_plan()).to_dict()

    assert data["kind"] == "case_intake_brain_handoff_approval_packet"
    assert data["approved"] is False
    assert data["validation_allowed"] is False
    assert data["tool_execution_allowed"] is False
    assert data["browser_execution_allowed"] is False
    assert data["evidence_collection_allowed"] is False
    assert data["target_mutation_allowed"] is False
    assert data["report_submission_allowed"] is False
    assert data["vulnerability_confirmation_allowed"] is False
    assert data["safety"]["network_requests"] is False
    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["browser_execution"] is False
    assert data["safety"]["evidence_collection"] is False
    assert data["safety"]["target_mutation"] is False
    assert data["safety"]["report_submission"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_approval_packet_markdown_contains_checkbox_and_stop_conditions() -> None:
    markdown = export_case_intake_brain_handoff_approval_packet(_manual_plan()).to_markdown()

    assert "# Case Intake Brain Approval Packet" in markdown
    assert "## Approval Checkbox" in markdown
    assert "- [ ] Approve planning the next read-only manual validation review" in markdown
    assert "## Stop Conditions" in markdown
    assert "No tool execution" in markdown
