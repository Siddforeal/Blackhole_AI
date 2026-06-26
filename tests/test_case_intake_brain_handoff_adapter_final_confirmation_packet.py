from bugintel.core.case_intake_brain_handoff_adapter_dry_run_preview import (
    export_case_intake_brain_handoff_adapter_dry_run_preview,
)
from bugintel.core.case_intake_brain_handoff_adapter_final_confirmation_packet import (
    record_case_intake_brain_handoff_adapter_final_confirmation,
)
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
from bugintel.core.case_intake_brain_handoff_runtime_safety_manifest import (
    export_case_intake_brain_handoff_runtime_safety_manifest,
)
from tests.test_case_intake_brain_handoff_answerer import _handoff


def _dry_run_preview() -> dict:
    plan = export_case_intake_brain_handoff_manual_validation_plan(_handoff()).to_dict()
    packet = export_case_intake_brain_handoff_approval_packet(
        plan,
        endpoint="/api/admin/users/{id}/permissions",
    ).to_dict()
    approval_decision = record_case_intake_brain_handoff_approval_decision(
        packet,
        decision="approved",
        decided_by="human-reviewer",
        reason="Approved read-only planning only with controlled accounts.",
    ).to_dict()
    command_proposal = export_case_intake_brain_handoff_read_only_command_proposal(
        approval_decision,
        command_family="curl",
    ).to_dict()
    execution_gate = record_case_intake_brain_handoff_execution_approval_gate(
        command_proposal,
        decision="approved",
        decided_by="human-reviewer",
        reason="Approved only for future controlled read-only execution adapter preview.",
    ).to_dict()
    runtime_manifest = export_case_intake_brain_handoff_runtime_safety_manifest(
        execution_gate,
        adapter_family="curl",
    ).to_dict()
    return export_case_intake_brain_handoff_adapter_dry_run_preview(
        runtime_manifest,
        target_base_url="https://example-program.test",
        controlled_account_token_placeholder="CONTROLLED_TOKEN_ONLY",
        path_parameters=["id=SYNTHETIC_USER_ID"],
    ).to_dict()


def test_adapter_final_confirmation_records_confirmed_without_execution() -> None:
    packet = record_case_intake_brain_handoff_adapter_final_confirmation(
        _dry_run_preview(),
        decision="confirmed",
        confirmed_by="human-reviewer",
        reason="Final human review confirms dry-run preview is ready for future scoped adapter only.",
    )

    assert packet.confirmation_id == "AFC-ADP-RSM-EG-CP-AD-AP-001"
    assert packet.preview_id == "ADP-RSM-EG-CP-AD-AP-001"
    assert packet.final_confirmation_decision == "confirmed"
    assert packet.final_confirmation_status == "confirmed-no-execution-authorized"
    assert packet.confirmed is True
    assert packet.denied is False
    assert packet.blocked is False
    assert packet.human_final_confirmation_recorded is True
    assert packet.dry_run_only is True
    assert packet.source_preview_ready is True
    assert packet.can_execute_now is False
    assert packet.final_confirmation_allows_execution is False
    assert packet.execution_allowed is False
    assert packet.validation_allowed is False
    assert packet.runtime_execution_allowed is False
    assert packet.tool_execution_allowed is False
    assert packet.browser_execution_allowed is False
    assert packet.network_requests_allowed is False
    assert packet.evidence_collection_allowed is False
    assert packet.target_mutation_allowed is False
    assert packet.report_submission_allowed is False
    assert packet.vulnerability_confirmation_allowed is False
    assert "https://example-program.test/api/admin/users/SYNTHETIC_USER_ID/permissions" in packet.resolved_command_preview


def test_adapter_final_confirmation_records_denied() -> None:
    packet = record_case_intake_brain_handoff_adapter_final_confirmation(
        _dry_run_preview(),
        decision="denied",
        confirmed_by="human-reviewer",
        reason="Not ready.",
    )

    assert packet.final_confirmation_decision == "denied"
    assert packet.final_confirmation_status == "denied-by-human"
    assert packet.confirmed is False
    assert packet.denied is True
    assert packet.blocked is False
    assert packet.human_final_confirmation_recorded is False
    assert packet.can_execute_now is False


def test_adapter_final_confirmation_records_blocked() -> None:
    packet = record_case_intake_brain_handoff_adapter_final_confirmation(
        _dry_run_preview(),
        decision="blocked",
        confirmed_by="human-reviewer",
        reason="Scope unclear.",
    )

    assert packet.final_confirmation_decision == "blocked"
    assert packet.final_confirmation_status == "blocked-by-human"
    assert packet.confirmed is False
    assert packet.denied is False
    assert packet.blocked is True
    assert packet.can_execute_now is False


def test_adapter_final_confirmation_blocks_invalid_decision() -> None:
    packet = record_case_intake_brain_handoff_adapter_final_confirmation(
        _dry_run_preview(),
        decision="maybe",
        confirmed_by="human-reviewer",
        reason="Invalid.",
    )

    assert packet.blocked is True
    assert packet.final_confirmation_decision == "maybe"
    assert packet.final_confirmation_status == "blocked"
    assert "Final confirmation decision must be one of" in packet.source_preview_block_reason
    assert packet.can_execute_now is False


def test_adapter_final_confirmation_blocks_invalid_input() -> None:
    packet = record_case_intake_brain_handoff_adapter_final_confirmation(
        {"kind": "wrong"},
        decision="confirmed",
        confirmed_by="human-reviewer",
        reason="Invalid input.",
    )

    assert packet.blocked is True
    assert packet.confirmation_id == "AFC-BLOCKED-ADP-UNKNOWN"
    assert "not a case_intake_brain_handoff_adapter_dry_run_preview" in packet.source_preview_block_reason
    assert packet.can_execute_now is False


def test_adapter_final_confirmation_blocks_unready_preview() -> None:
    preview = _dry_run_preview()
    preview["preview_ready"] = False

    packet = record_case_intake_brain_handoff_adapter_final_confirmation(
        preview,
        decision="confirmed",
        confirmed_by="human-reviewer",
        reason="Preview not ready.",
    )

    assert packet.blocked is True
    assert "dry_run_only and preview_ready" in packet.source_preview_block_reason
    assert packet.can_execute_now is False


def test_adapter_final_confirmation_serializes_safety_metadata() -> None:
    data = record_case_intake_brain_handoff_adapter_final_confirmation(
        _dry_run_preview(),
        decision="confirmed",
        confirmed_by="human-reviewer",
        reason="Final human review confirms dry-run preview.",
    ).to_dict()

    assert data["kind"] == "case_intake_brain_handoff_adapter_final_confirmation_packet"
    assert data["confirmed"] is True
    assert data["human_final_confirmation_recorded"] is True
    assert data["dry_run_only"] is True
    assert data["can_execute_now"] is False
    assert data["final_confirmation_allows_execution"] is False
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
    assert data["safety"]["dry_run_only"] is True
    assert data["safety"]["network_requests"] is False
    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["browser_execution"] is False
    assert data["safety"]["evidence_collection"] is False
    assert data["safety"]["target_mutation"] is False
    assert data["safety"]["report_submission"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_adapter_final_confirmation_markdown_contains_preview_and_safety() -> None:
    markdown = record_case_intake_brain_handoff_adapter_final_confirmation(
        _dry_run_preview(),
        decision="confirmed",
        confirmed_by="human-reviewer",
        reason="Final human review confirms dry-run preview.",
    ).to_markdown()

    assert "# Case Intake Brain Adapter Final Confirmation Packet" in markdown
    assert "## Resolved Dry-Run Command Reviewed" in markdown
    assert "https://example-program.test/api/admin/users/SYNTHETIC_USER_ID/permissions" in markdown
    assert "Final confirmation allows execution" in markdown
    assert "No command execution" in markdown
