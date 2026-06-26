from bugintel.core.case_intake_brain_handoff_approval_decision_recorder import (
    record_case_intake_brain_handoff_approval_decision,
)
from bugintel.core.case_intake_brain_handoff_approval_packet_exporter import (
    export_case_intake_brain_handoff_approval_packet,
)
from bugintel.core.case_intake_brain_handoff_manual_validation_plan_exporter import (
    export_case_intake_brain_handoff_manual_validation_plan,
)
from bugintel.core.case_intake_brain_handoff_read_only_command_proposal_exporter import (
    export_case_intake_brain_handoff_read_only_command_proposal,
)
from tests.test_case_intake_brain_handoff_answerer import _handoff


def _approval_decision(decision: str = "approved") -> dict:
    plan = export_case_intake_brain_handoff_manual_validation_plan(_handoff()).to_dict()
    packet = export_case_intake_brain_handoff_approval_packet(
        plan,
        endpoint="/api/admin/users/{id}/permissions",
    ).to_dict()
    return record_case_intake_brain_handoff_approval_decision(
        packet,
        decision=decision,
        decided_by="sidd",
        reason="Approved read-only planning only with controlled accounts.",
    ).to_dict()


def test_read_only_command_proposal_exports_curl_proposal() -> None:
    proposal = export_case_intake_brain_handoff_read_only_command_proposal(
        _approval_decision(),
        command_family="curl",
    )

    assert proposal.proposal_id == "CP-AD-AP-001"
    assert proposal.decision_id == "AD-AP-001"
    assert proposal.approval_id == "AP-001"
    assert proposal.endpoint == "/api/admin/users/{id}/permissions"
    assert proposal.command_family == "curl"
    assert proposal.command_purpose == "read-only-controlled-baseline-request-proposal"
    assert "{{TARGET_BASE_URL}}" in proposal.proposed_command
    assert "{{CONTROLLED_ACCOUNT_TOKEN}}" in proposal.proposed_command
    assert proposal.blocked is False
    assert proposal.requires_separate_execution_approval is True
    assert proposal.human_review_required is True
    assert proposal.execution_allowed is False
    assert proposal.validation_allowed is False
    assert proposal.runtime_execution_allowed is False
    assert proposal.tool_execution_allowed is False
    assert proposal.browser_execution_allowed is False
    assert proposal.network_requests_allowed is False
    assert proposal.evidence_collection_allowed is False
    assert proposal.target_mutation_allowed is False
    assert proposal.report_submission_allowed is False
    assert proposal.vulnerability_confirmation_allowed is False


def test_read_only_command_proposal_blocks_denied_decision() -> None:
    proposal = export_case_intake_brain_handoff_read_only_command_proposal(
        _approval_decision(decision="denied"),
        command_family="curl",
    )

    assert proposal.blocked is True
    assert "must be approved" in proposal.block_reason
    assert proposal.execution_allowed is False
    assert proposal.tool_execution_allowed is False


def test_read_only_command_proposal_blocks_invalid_input() -> None:
    proposal = export_case_intake_brain_handoff_read_only_command_proposal(
        {"kind": "wrong"},
        command_family="curl",
    )

    assert proposal.blocked is True
    assert "not a case_intake_brain_handoff_approval_decision" in proposal.block_reason
    assert proposal.execution_allowed is False


def test_read_only_command_proposal_blocks_unsupported_family() -> None:
    proposal = export_case_intake_brain_handoff_read_only_command_proposal(
        _approval_decision(),
        command_family="bash",
    )

    assert proposal.blocked is True
    assert "Unsupported command family" in proposal.block_reason
    assert proposal.command_family == "bash"
    assert proposal.execution_allowed is False


def test_read_only_command_proposal_serializes_safety_metadata() -> None:
    data = export_case_intake_brain_handoff_read_only_command_proposal(
        _approval_decision(),
        command_family="curl",
    ).to_dict()

    assert data["kind"] == "case_intake_brain_handoff_read_only_command_proposal"
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


def test_read_only_command_proposal_markdown_contains_command_and_safety() -> None:
    markdown = export_case_intake_brain_handoff_read_only_command_proposal(
        _approval_decision(),
        command_family="curl",
    ).to_markdown()

    assert "# Case Intake Brain Read-Only Command Proposal" in markdown
    assert "## Proposed Command" in markdown
    assert "{{TARGET_BASE_URL}}" in markdown
    assert "Separate execution approval required" in markdown
    assert "No command execution" in markdown
