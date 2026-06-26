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
from bugintel.core.case_intake_brain_handoff_scoped_adapter_execution_request import (
    export_case_intake_brain_handoff_scoped_adapter_execution_request,
)
from tests.test_case_intake_brain_handoff_answerer import _handoff


def _final_confirmation(decision: str = "confirmed") -> dict:
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
    preview = export_case_intake_brain_handoff_adapter_dry_run_preview(
        runtime_manifest,
        target_base_url="https://example-program.test",
        controlled_account_token_placeholder="CONTROLLED_TOKEN_ONLY",
        path_parameters=["id=SYNTHETIC_USER_ID"],
    ).to_dict()
    return record_case_intake_brain_handoff_adapter_final_confirmation(
        preview,
        decision=decision,
        confirmed_by="human-reviewer",
        reason="Final human review confirms dry-run preview is ready for future scoped adapter only.",
    ).to_dict()


def test_scoped_adapter_execution_request_exports_confirmed_request_without_execution() -> None:
    request = export_case_intake_brain_handoff_scoped_adapter_execution_request(
        _final_confirmation(),
        request_purpose="future-scoped-curl-adapter-review",
    )

    assert request.request_id == "SAER-AFC-ADP-RSM-EG-CP-AD-AP-001"
    assert request.confirmation_id == "AFC-ADP-RSM-EG-CP-AD-AP-001"
    assert request.adapter_family == "curl"
    assert request.command_family == "curl"
    assert request.request_purpose == "future-scoped-curl-adapter-review"
    assert request.requested_action == "future-scoped-adapter-execution-review"
    assert request.request_status == "ready-for-future-scoped-adapter-review-no-execution"
    assert request.scope_validation_state == "not_performed"
    assert request.adapter_execution_state == "not_executed"
    assert request.final_confirmation_decision == "confirmed"
    assert request.human_final_confirmation_recorded is True
    assert request.confirmed_by == "human-reviewer"
    assert request.resolved_target_url == "https://example-program.test/api/admin/users/SYNTHETIC_USER_ID/permissions"
    assert "https://example-program.test/api/admin/users/SYNTHETIC_USER_ID/permissions" in request.reviewed_command
    assert request.required_runtime_checks
    assert request.unresolved_placeholders == ()
    assert request.blocked is False
    assert request.dry_run_only is True
    assert request.can_execute_now is False
    assert request.execution_request_allows_execution is False
    assert request.execution_allowed is False
    assert request.validation_allowed is False
    assert request.runtime_execution_allowed is False
    assert request.tool_execution_allowed is False
    assert request.browser_execution_allowed is False
    assert request.network_requests_allowed is False
    assert request.evidence_collection_allowed is False
    assert request.target_mutation_allowed is False
    assert request.report_submission_allowed is False
    assert request.vulnerability_confirmation_allowed is False


def test_scoped_adapter_execution_request_blocks_denied_confirmation() -> None:
    request = export_case_intake_brain_handoff_scoped_adapter_execution_request(
        _final_confirmation(decision="denied"),
        request_purpose="future-scoped-curl-adapter-review",
    )

    assert request.blocked is True
    assert "must be confirmed" in request.block_reason
    assert request.can_execute_now is False


def test_scoped_adapter_execution_request_blocks_invalid_input() -> None:
    request = export_case_intake_brain_handoff_scoped_adapter_execution_request(
        {"kind": "wrong"},
        request_purpose="future-scoped-curl-adapter-review",
    )

    assert request.blocked is True
    assert "not a case_intake_brain_handoff_adapter_final_confirmation_packet" in request.block_reason
    assert request.can_execute_now is False


def test_scoped_adapter_execution_request_blocks_unsupported_adapter() -> None:
    packet = _final_confirmation()
    packet["adapter_family"] = "burp"

    request = export_case_intake_brain_handoff_scoped_adapter_execution_request(
        packet,
        request_purpose="future-scoped-curl-adapter-review",
    )

    assert request.blocked is True
    assert "Unsupported adapter family" in request.block_reason
    assert request.adapter_family == "burp"
    assert request.can_execute_now is False


def test_scoped_adapter_execution_request_blocks_empty_request_purpose() -> None:
    request = export_case_intake_brain_handoff_scoped_adapter_execution_request(
        _final_confirmation(),
        request_purpose="",
    )

    assert request.blocked is True
    assert "Request purpose is required" in request.block_reason
    assert request.can_execute_now is False


def test_scoped_adapter_execution_request_serializes_safety_metadata() -> None:
    data = export_case_intake_brain_handoff_scoped_adapter_execution_request(
        _final_confirmation(),
        request_purpose="future-scoped-curl-adapter-review",
    ).to_dict()

    assert data["kind"] == "case_intake_brain_handoff_scoped_adapter_execution_request"
    assert data["dry_run_only"] is True
    assert data["can_execute_now"] is False
    assert data["execution_request_allows_execution"] is False
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


def test_scoped_adapter_execution_request_markdown_contains_request_and_safety() -> None:
    markdown = export_case_intake_brain_handoff_scoped_adapter_execution_request(
        _final_confirmation(),
        request_purpose="future-scoped-curl-adapter-review",
    ).to_markdown()

    assert "# Case Intake Brain Scoped Adapter Execution Request" in markdown
    assert "## Reviewed Command Packaged for Future Adapter" in markdown
    assert "https://example-program.test/api/admin/users/SYNTHETIC_USER_ID/permissions" in markdown
    assert "Execution request allows execution" in markdown
    assert "No command execution" in markdown
