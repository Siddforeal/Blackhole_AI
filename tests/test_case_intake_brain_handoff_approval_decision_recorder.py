from bugintel.core.case_intake_brain_handoff_approval_decision_recorder import (
    record_case_intake_brain_handoff_approval_decision,
)
from bugintel.core.case_intake_brain_handoff_approval_packet_exporter import (
    export_case_intake_brain_handoff_approval_packet,
)
from bugintel.core.case_intake_brain_handoff_manual_validation_plan_exporter import (
    export_case_intake_brain_handoff_manual_validation_plan,
)
from tests.test_case_intake_brain_handoff_answerer import _handoff


def _approval_packet() -> dict:
    plan = export_case_intake_brain_handoff_manual_validation_plan(_handoff()).to_dict()
    return export_case_intake_brain_handoff_approval_packet(
        plan,
        endpoint="/api/admin/users/{id}/permissions",
    ).to_dict()


def test_approval_decision_records_approved_without_execution_permission() -> None:
    recorded = record_case_intake_brain_handoff_approval_decision(
        _approval_packet(),
        decision="approved",
        decided_by="sidd",
        reason="Approved read-only planning only with controlled accounts.",
    )

    assert recorded.decision_id == "AD-AP-001"
    assert recorded.approval_id == "AP-001"
    assert recorded.endpoint == "/api/admin/users/{id}/permissions"
    assert recorded.decision == "approved"
    assert recorded.decision_status == "approved-no-execution-authorized"
    assert recorded.decided_by == "sidd"
    assert recorded.approved is True
    assert recorded.denied is False
    assert recorded.blocked is False
    assert recorded.human_approval_recorded is True
    assert recorded.can_proceed_to_execution is False
    assert recorded.validation_allowed is False
    assert recorded.runtime_execution_allowed is False
    assert recorded.tool_execution_allowed is False
    assert recorded.browser_execution_allowed is False
    assert recorded.evidence_collection_allowed is False
    assert recorded.target_mutation_allowed is False
    assert recorded.report_submission_allowed is False
    assert recorded.vulnerability_confirmation_allowed is False


def test_approval_decision_records_denied() -> None:
    recorded = record_case_intake_brain_handoff_approval_decision(
        _approval_packet(),
        decision="denied",
        decided_by="sidd",
        reason="Not enough scope confidence.",
    )

    assert recorded.decision == "denied"
    assert recorded.decision_status == "denied-by-human"
    assert recorded.approved is False
    assert recorded.denied is True
    assert recorded.blocked is False
    assert recorded.human_approval_recorded is False
    assert recorded.can_proceed_to_execution is False


def test_approval_decision_records_blocked() -> None:
    recorded = record_case_intake_brain_handoff_approval_decision(
        _approval_packet(),
        decision="blocked",
        decided_by="sidd",
        reason="Program scope unclear.",
    )

    assert recorded.decision == "blocked"
    assert recorded.decision_status == "blocked-by-human"
    assert recorded.approved is False
    assert recorded.denied is False
    assert recorded.blocked is True
    assert recorded.can_proceed_to_execution is False


def test_approval_decision_blocks_invalid_decision() -> None:
    recorded = record_case_intake_brain_handoff_approval_decision(
        _approval_packet(),
        decision="maybe",
        decided_by="sidd",
        reason="Invalid.",
    )

    assert recorded.blocked is True
    assert recorded.decision == "maybe"
    assert recorded.decision_status == "blocked"
    assert "Decision must be one of" in recorded.packet_block_reason
    assert recorded.can_proceed_to_execution is False


def test_approval_decision_blocks_invalid_input() -> None:
    recorded = record_case_intake_brain_handoff_approval_decision(
        {"kind": "wrong"},
        decision="approved",
        decided_by="sidd",
        reason="Invalid input.",
    )

    assert recorded.blocked is True
    assert recorded.decision_id == "AD-BLOCKED-AP-UNKNOWN"
    assert "not a case_intake_brain_handoff_approval_packet" in recorded.packet_block_reason
    assert recorded.can_proceed_to_execution is False


def test_approval_decision_serializes_safety_metadata() -> None:
    data = record_case_intake_brain_handoff_approval_decision(
        _approval_packet(),
        decision="approved",
        decided_by="sidd",
        reason="Approved read-only planning only.",
    ).to_dict()

    assert data["kind"] == "case_intake_brain_handoff_approval_decision"
    assert data["approved"] is True
    assert data["can_proceed_to_execution"] is False
    assert data["validation_allowed"] is False
    assert data["runtime_execution_allowed"] is False
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


def test_approval_decision_markdown_contains_reason_and_safety() -> None:
    markdown = record_case_intake_brain_handoff_approval_decision(
        _approval_packet(),
        decision="approved",
        decided_by="sidd",
        reason="Approved read-only planning only.",
    ).to_markdown()

    assert "# Case Intake Brain Approval Decision" in markdown
    assert "## Reason" in markdown
    assert "Approved read-only planning only." in markdown
    assert "Can proceed to execution" in markdown
    assert "No tool execution" in markdown
