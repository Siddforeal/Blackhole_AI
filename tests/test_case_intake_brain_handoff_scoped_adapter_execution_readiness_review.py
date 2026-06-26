from bugintel.core.case_intake_brain_handoff_adapter_dry_run_preview import export_case_intake_brain_handoff_adapter_dry_run_preview
from bugintel.core.case_intake_brain_handoff_adapter_final_confirmation_packet import record_case_intake_brain_handoff_adapter_final_confirmation
from bugintel.core.case_intake_brain_handoff_approval_decision_recorder import record_case_intake_brain_handoff_approval_decision
from bugintel.core.case_intake_brain_handoff_approval_packet_exporter import export_case_intake_brain_handoff_approval_packet
from bugintel.core.case_intake_brain_handoff_execution_approval_gate import record_case_intake_brain_handoff_execution_approval_gate
from bugintel.core.case_intake_brain_handoff_manual_validation_plan_exporter import export_case_intake_brain_handoff_manual_validation_plan
from bugintel.core.case_intake_brain_handoff_read_only_command_proposal_exporter import export_case_intake_brain_handoff_read_only_command_proposal
from bugintel.core.case_intake_brain_handoff_runtime_safety_manifest import export_case_intake_brain_handoff_runtime_safety_manifest
from bugintel.core.case_intake_brain_handoff_scoped_adapter_execution_request import export_case_intake_brain_handoff_scoped_adapter_execution_request
from bugintel.core.case_intake_brain_handoff_scoped_adapter_runtime_scope_review import export_case_intake_brain_handoff_scoped_adapter_runtime_scope_review
from bugintel.core.case_intake_brain_handoff_scoped_adapter_safety_review import export_case_intake_brain_handoff_scoped_adapter_safety_review
from bugintel.core.case_intake_brain_handoff_scoped_adapter_final_execution_gate import record_case_intake_brain_handoff_scoped_adapter_final_execution_gate
from bugintel.core.case_intake_brain_handoff_scoped_adapter_runtime_confirmation_packet import record_case_intake_brain_handoff_scoped_adapter_runtime_confirmation_packet
from bugintel.core.case_intake_brain_handoff_scoped_adapter_execution_plan_packet import export_case_intake_brain_handoff_scoped_adapter_execution_plan_packet
from bugintel.core.case_intake_brain_handoff_scoped_adapter_execution_readiness_review import review_case_intake_brain_handoff_scoped_adapter_execution_readiness
from tests.test_case_intake_brain_handoff_answerer import _handoff


def _execution_plan() -> dict:
    plan = export_case_intake_brain_handoff_manual_validation_plan(_handoff()).to_dict()
    packet = export_case_intake_brain_handoff_approval_packet(plan, endpoint="/api/admin/users/{id}/permissions").to_dict()
    approval_decision = record_case_intake_brain_handoff_approval_decision(packet, decision="approved", decided_by="human-reviewer", reason="Approved read-only planning only with controlled accounts.").to_dict()
    command_proposal = export_case_intake_brain_handoff_read_only_command_proposal(approval_decision, command_family="curl").to_dict()
    execution_gate = record_case_intake_brain_handoff_execution_approval_gate(command_proposal, decision="approved", decided_by="human-reviewer", reason="Approved only for future controlled read-only execution adapter preview.").to_dict()
    runtime_manifest = export_case_intake_brain_handoff_runtime_safety_manifest(execution_gate, adapter_family="curl").to_dict()
    preview = export_case_intake_brain_handoff_adapter_dry_run_preview(runtime_manifest, target_base_url="https://example-program.test", controlled_account_token_placeholder="CONTROLLED_TOKEN_ONLY", path_parameters=["id=SYNTHETIC_USER_ID"]).to_dict()
    confirmation = record_case_intake_brain_handoff_adapter_final_confirmation(preview, decision="confirmed", confirmed_by="human-reviewer", reason="Final human review confirms dry-run preview is ready for future scoped adapter only.").to_dict()
    request = export_case_intake_brain_handoff_scoped_adapter_execution_request(confirmation, request_purpose="future-scoped-curl-adapter-review").to_dict()
    runtime_review = export_case_intake_brain_handoff_scoped_adapter_runtime_scope_review(request, allowed_host="example-program.test", allowed_scheme="https", allowed_method="GET").to_dict()
    safety_review = export_case_intake_brain_handoff_scoped_adapter_safety_review(runtime_review).to_dict()
    final_gate = record_case_intake_brain_handoff_scoped_adapter_final_execution_gate(safety_review, decision="approved", decided_by="human-reviewer", reason="Approved for future adapter execution path only after separate explicit runtime confirmation.").to_dict()
    runtime_confirmation = record_case_intake_brain_handoff_scoped_adapter_runtime_confirmation_packet(final_gate, confirmed_by="human-reviewer", confirmation_text="I confirm the exact scoped adapter context was reviewed for a future runtime path only.").to_dict()
    return export_case_intake_brain_handoff_scoped_adapter_execution_plan_packet(runtime_confirmation, planned_by="human-reviewer", plan_purpose="Prepare a future scoped adapter execution plan without executing anything.").to_dict()


def test_readiness_review_marks_plan_ready_without_execution() -> None:
    review = review_case_intake_brain_handoff_scoped_adapter_execution_readiness(
        _execution_plan(),
        reviewed_by="human-reviewer",
        readiness_note="Reviewed for future scoped adapter implementation readiness only; no execution authorized.",
    )

    assert review.readiness_review_id == "ERR-SEP-RCP-FEG-ASR-RSR-SAER-AFC-ADP-RSM-EG-CP-AD-AP-001"
    assert review.execution_plan_id == "SEP-RCP-FEG-ASR-RSR-SAER-AFC-ADP-RSM-EG-CP-AD-AP-001"
    assert review.readiness_review_status == "ready-for-future-scoped-adapter-implementation-no-execution"
    assert review.readiness_review_state == "reviewed_local_only"
    assert review.implementation_readiness == "ready-for-future-implementation-only"
    assert review.reviewed_by == "human-reviewer"
    assert review.readiness_findings
    assert review.blocking_findings == ()
    assert review.adapter_execution_state == "not_executed"
    assert review.blocked is False
    assert review.dry_run_only is True
    assert review.can_execute_now is False
    assert review.readiness_review_allows_execution is False
    assert review.execution_allowed is False
    assert review.validation_allowed is False
    assert review.runtime_execution_allowed is False
    assert review.tool_execution_allowed is False
    assert review.browser_execution_allowed is False
    assert review.network_requests_allowed is False
    assert review.evidence_collection_allowed is False
    assert review.target_mutation_allowed is False
    assert review.report_submission_allowed is False
    assert review.vulnerability_confirmation_allowed is False


def test_readiness_review_blocks_missing_note() -> None:
    review = review_case_intake_brain_handoff_scoped_adapter_execution_readiness(
        _execution_plan(),
        reviewed_by="human-reviewer",
        readiness_note="",
    )

    assert review.blocked is True
    assert "Execution readiness review note is required" in review.block_reason
    assert review.can_execute_now is False


def test_readiness_review_blocks_invalid_input() -> None:
    review = review_case_intake_brain_handoff_scoped_adapter_execution_readiness(
        {"kind": "wrong"},
        reviewed_by="human-reviewer",
        readiness_note="Reviewed.",
    )

    assert review.blocked is True
    assert "not a case_intake_brain_handoff_scoped_adapter_execution_plan_packet" in review.block_reason
    assert review.can_execute_now is False


def test_readiness_review_blocks_incomplete_plan() -> None:
    plan = _execution_plan()
    plan["execution_plan_steps"] = []

    review = review_case_intake_brain_handoff_scoped_adapter_execution_readiness(
        plan,
        reviewed_by="human-reviewer",
        readiness_note="Reviewed.",
    )

    assert review.blocked is True
    assert "execution plan steps are required" in review.block_reason
    assert review.can_execute_now is False


def test_readiness_review_blocks_unsafe_plan_flags() -> None:
    plan = _execution_plan()
    plan["network_requests_allowed"] = True

    review = review_case_intake_brain_handoff_scoped_adapter_execution_readiness(
        plan,
        reviewed_by="human-reviewer",
        readiness_note="Reviewed.",
    )

    assert review.blocked is True
    assert "reports execution" in review.block_reason
    assert review.can_execute_now is False


def test_readiness_review_serializes_safety_metadata() -> None:
    data = review_case_intake_brain_handoff_scoped_adapter_execution_readiness(
        _execution_plan(),
        reviewed_by="human-reviewer",
        readiness_note="Reviewed for future scoped adapter implementation readiness only; no execution authorized.",
    ).to_dict()

    assert data["kind"] == "case_intake_brain_handoff_scoped_adapter_execution_readiness_review"
    assert data["dry_run_only"] is True
    assert data["can_execute_now"] is False
    assert data["readiness_review_allows_execution"] is False
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


def test_readiness_review_markdown_contains_readiness_and_safety() -> None:
    markdown = review_case_intake_brain_handoff_scoped_adapter_execution_readiness(
        _execution_plan(),
        reviewed_by="human-reviewer",
        readiness_note="Reviewed for future scoped adapter implementation readiness only; no execution authorized.",
    ).to_markdown()

    assert "# Case Intake Brain Scoped Adapter Execution Readiness Review" in markdown
    assert "Readiness review allows execution" in markdown
    assert "No command execution" in markdown
    assert "Readiness Findings" in markdown
