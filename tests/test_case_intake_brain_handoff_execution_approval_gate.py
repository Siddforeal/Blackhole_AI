from bugintel.core.case_intake_brain_handoff_approval_decision_recorder import (
    record_case_intake_brain_handoff_approval_decision,
)
from bugintel.core.case_intake_brain_handoff_approval_packet_exporter import (
    export_case_intake_brain_handoff_approval_packet,
)
from bugintel.core.case_intake_brain_handoff_execution_approval_gate import (
    record_case_intake_brain_handoff_execution_approval_gate,
)
from bugintel.core.case_intake_brain_handoff_manual_validation_plan_exporter import (
    export_case_intake_brain_handoff_manual_validation_plan,
)
from bugintel.core.case_intake_brain_handoff_read_only_command_proposal_exporter import (
    export_case_intake_brain_handoff_read_only_command_proposal,
)
from tests.test_case_intake_brain_handoff_answerer import _handoff


def _command_proposal() -> dict:
    plan = export_case_intake_brain_handoff_manual_validation_plan(_handoff()).to_dict()
    packet = export_case_intake_brain_handoff_approval_packet(
        plan,
        endpoint="/api/admin/users/{id}/permissions",
    ).to_dict()
    approval_decision = record_case_intake_brain_handoff_approval_decision(
        packet,
        decision="approved",
        decided_by="sidd",
        reason="Approved read-only planning only with controlled accounts.",
    ).to_dict()
    return export_case_intake_brain_handoff_read_only_command_proposal(
        approval_decision,
        command_family="curl",
    ).to_dict()


def test_execution_approval_gate_records_approved_without_execution() -> None:
    gate = record_case_intake_brain_handoff_execution_approval_gate(
        _command_proposal(),
        decision="approved",
        decided_by="sidd",
        reason="Approved only for future controlled read-only execution adapter preview.",
    )

    assert gate.gate_id == "EG-CP-AD-AP-001"
    assert gate.proposal_id == "CP-AD-AP-001"
    assert gate.execution_decision == "approved"
    assert gate.execution_gate_status == "approved-no-execution-performed"
    assert gate.approved is True
    assert gate.denied is False
    assert gate.blocked is False
    assert gate.human_execution_approval_recorded is True
    assert gate.can_execute_now is False
    assert gate.requires_runtime_scope_check is True
    assert gate.requires_final_human_confirmation is True
    assert gate.requires_adapter_safety_check is True
    assert gate.execution_allowed is False
    assert gate.validation_allowed is False
    assert gate.runtime_execution_allowed is False
    assert gate.tool_execution_allowed is False
    assert gate.browser_execution_allowed is False
    assert gate.network_requests_allowed is False
    assert gate.evidence_collection_allowed is False
    assert gate.target_mutation_allowed is False
    assert gate.report_submission_allowed is False
    assert gate.vulnerability_confirmation_allowed is False


def test_execution_approval_gate_records_denied() -> None:
    gate = record_case_intake_brain_handoff_execution_approval_gate(
        _command_proposal(),
        decision="denied",
        decided_by="sidd",
        reason="Not ready.",
    )

    assert gate.execution_decision == "denied"
    assert gate.execution_gate_status == "denied-by-human"
    assert gate.approved is False
    assert gate.denied is True
    assert gate.blocked is False
    assert gate.human_execution_approval_recorded is False
    assert gate.can_execute_now is False


def test_execution_approval_gate_records_blocked() -> None:
    gate = record_case_intake_brain_handoff_execution_approval_gate(
        _command_proposal(),
        decision="blocked",
        decided_by="sidd",
        reason="Scope unclear.",
    )

    assert gate.execution_decision == "blocked"
    assert gate.execution_gate_status == "blocked-by-human"
    assert gate.approved is False
    assert gate.denied is False
    assert gate.blocked is True
    assert gate.can_execute_now is False


def test_execution_approval_gate_blocks_invalid_decision() -> None:
    gate = record_case_intake_brain_handoff_execution_approval_gate(
        _command_proposal(),
        decision="maybe",
        decided_by="sidd",
        reason="Invalid.",
    )

    assert gate.blocked is True
    assert gate.execution_decision == "maybe"
    assert gate.execution_gate_status == "blocked"
    assert "Execution approval decision must be one of" in gate.original_proposal_block_reason
    assert gate.can_execute_now is False


def test_execution_approval_gate_blocks_invalid_input() -> None:
    gate = record_case_intake_brain_handoff_execution_approval_gate(
        {"kind": "wrong"},
        decision="approved",
        decided_by="sidd",
        reason="Invalid input.",
    )

    assert gate.blocked is True
    assert gate.gate_id == "EG-BLOCKED-CP-UNKNOWN"
    assert "not a case_intake_brain_handoff_read_only_command_proposal" in gate.original_proposal_block_reason
    assert gate.can_execute_now is False


def test_execution_approval_gate_serializes_safety_metadata() -> None:
    data = record_case_intake_brain_handoff_execution_approval_gate(
        _command_proposal(),
        decision="approved",
        decided_by="sidd",
        reason="Approved only for future adapter preview.",
    ).to_dict()

    assert data["kind"] == "case_intake_brain_handoff_execution_approval_gate"
    assert data["approved"] is True
    assert data["can_execute_now"] is False
    assert data["execution_allowed"] is False
    assert data["validation_allowed"] is False
    assert data["runtime_execution_allowed"] is False
    assert data["tool_execution_allowed"] is False
    assert data["browser_execution_allowed"] is False
    assert data["network_requests_allowed"] is False
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


def test_execution_approval_gate_markdown_contains_command_and_safety() -> None:
    markdown = record_case_intake_brain_handoff_execution_approval_gate(
        _command_proposal(),
        decision="approved",
        decided_by="sidd",
        reason="Approved only for future adapter preview.",
    ).to_markdown()

    assert "# Case Intake Brain Execution Approval Gate" in markdown
    assert "## Proposed Command Under Review" in markdown
    assert "Can execute now" in markdown
    assert "{{TARGET_BASE_URL}}" in markdown
    assert "No command execution" in markdown
