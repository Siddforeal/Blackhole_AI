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
from bugintel.core.case_intake_brain_handoff_scoped_adapter_implementation_blueprint import export_case_intake_brain_handoff_scoped_adapter_implementation_blueprint
from tests.test_case_intake_brain_handoff_answerer import _handoff


def _readiness_review() -> dict:
    plan = export_case_intake_brain_handoff_manual_validation_plan(_handoff()).to_dict()
    packet = export_case_intake_brain_handoff_approval_packet(plan, endpoint="/api/admin/users/{id}/permissions").to_dict()
    decision = record_case_intake_brain_handoff_approval_decision(packet, decision="approved", decided_by="human-reviewer", reason="Approved read-only planning only with controlled accounts.").to_dict()
    proposal = export_case_intake_brain_handoff_read_only_command_proposal(decision, command_family="curl").to_dict()
    gate = record_case_intake_brain_handoff_execution_approval_gate(proposal, decision="approved", decided_by="human-reviewer", reason="Approved only for future controlled read-only execution adapter preview.").to_dict()
    manifest = export_case_intake_brain_handoff_runtime_safety_manifest(gate, adapter_family="curl").to_dict()
    preview = export_case_intake_brain_handoff_adapter_dry_run_preview(manifest, target_base_url="https://example-program.test", controlled_account_token_placeholder="CONTROLLED_TOKEN_ONLY", path_parameters=["id=SYNTHETIC_USER_ID"]).to_dict()
    confirmation = record_case_intake_brain_handoff_adapter_final_confirmation(preview, decision="confirmed", confirmed_by="human-reviewer", reason="Final human review confirms dry-run preview is ready for future scoped adapter only.").to_dict()
    request = export_case_intake_brain_handoff_scoped_adapter_execution_request(confirmation, request_purpose="future-scoped-curl-adapter-review").to_dict()
    runtime_review = export_case_intake_brain_handoff_scoped_adapter_runtime_scope_review(request, allowed_host="example-program.test", allowed_scheme="https", allowed_method="GET").to_dict()
    safety_review = export_case_intake_brain_handoff_scoped_adapter_safety_review(runtime_review).to_dict()
    final_gate = record_case_intake_brain_handoff_scoped_adapter_final_execution_gate(safety_review, decision="approved", decided_by="human-reviewer", reason="Approved for future adapter execution path only after separate explicit runtime confirmation.").to_dict()
    runtime_confirmation = record_case_intake_brain_handoff_scoped_adapter_runtime_confirmation_packet(final_gate, confirmed_by="human-reviewer", confirmation_text="I confirm the exact scoped adapter context was reviewed for a future runtime path only.").to_dict()
    execution_plan = export_case_intake_brain_handoff_scoped_adapter_execution_plan_packet(runtime_confirmation, planned_by="human-reviewer", plan_purpose="Prepare a future scoped adapter execution plan without executing anything.").to_dict()
    return review_case_intake_brain_handoff_scoped_adapter_execution_readiness(execution_plan, reviewed_by="human-reviewer", readiness_note="Reviewed for future scoped adapter implementation readiness only; no execution authorized.").to_dict()


def test_implementation_blueprint_defines_future_files_without_execution() -> None:
    blueprint = export_case_intake_brain_handoff_scoped_adapter_implementation_blueprint(
        _readiness_review(),
        blueprinted_by="human-reviewer",
        blueprint_note="Define future scoped adapter implementation files and interfaces only; no execution authorized.",
    )

    assert blueprint.implementation_blueprint_id == "SIB-ERR-SEP-RCP-FEG-ASR-RSR-SAER-AFC-ADP-RSM-EG-CP-AD-AP-001"
    assert blueprint.readiness_review_id == "ERR-SEP-RCP-FEG-ASR-RSR-SAER-AFC-ADP-RSM-EG-CP-AD-AP-001"
    assert blueprint.implementation_blueprint_status == "blueprinted-for-future-scoped-adapter-implementation-no-execution"
    assert blueprint.implementation_blueprint_state == "blueprinted_local_only"
    assert blueprint.blueprinted_by == "human-reviewer"
    assert blueprint.proposed_module_files
    assert blueprint.proposed_interfaces
    assert blueprint.proposed_dataclasses
    assert blueprint.proposed_validation_guards
    assert blueprint.proposed_test_files
    assert blueprint.blueprint_findings
    assert blueprint.blocking_findings == ()
    assert blueprint.adapter_execution_state == "not_executed"
    assert blueprint.blocked is False
    assert blueprint.dry_run_only is True
    assert blueprint.can_execute_now is False
    assert blueprint.implementation_blueprint_allows_execution is False
    assert blueprint.execution_allowed is False
    assert blueprint.validation_allowed is False
    assert blueprint.runtime_execution_allowed is False
    assert blueprint.tool_execution_allowed is False
    assert blueprint.browser_execution_allowed is False
    assert blueprint.network_requests_allowed is False
    assert blueprint.evidence_collection_allowed is False
    assert blueprint.target_mutation_allowed is False
    assert blueprint.report_submission_allowed is False
    assert blueprint.vulnerability_confirmation_allowed is False


def test_implementation_blueprint_blocks_missing_note() -> None:
    blueprint = export_case_intake_brain_handoff_scoped_adapter_implementation_blueprint(
        _readiness_review(),
        blueprinted_by="human-reviewer",
        blueprint_note="",
    )

    assert blueprint.blocked is True
    assert "Implementation blueprint note is required" in blueprint.block_reason
    assert blueprint.can_execute_now is False


def test_implementation_blueprint_blocks_invalid_input() -> None:
    blueprint = export_case_intake_brain_handoff_scoped_adapter_implementation_blueprint(
        {"kind": "wrong"},
        blueprinted_by="human-reviewer",
        blueprint_note="Blueprint.",
    )

    assert blueprint.blocked is True
    assert "not a case_intake_brain_handoff_scoped_adapter_execution_readiness_review" in blueprint.block_reason
    assert blueprint.can_execute_now is False


def test_implementation_blueprint_blocks_unready_review() -> None:
    review = _readiness_review()
    review["implementation_readiness"] = "not_ready"

    blueprint = export_case_intake_brain_handoff_scoped_adapter_implementation_blueprint(
        review,
        blueprinted_by="human-reviewer",
        blueprint_note="Blueprint.",
    )

    assert blueprint.blocked is True
    assert "implementation readiness must be ready-for-future-implementation-only" in blueprint.block_reason
    assert blueprint.can_execute_now is False


def test_implementation_blueprint_blocks_unsafe_review_flags() -> None:
    review = _readiness_review()
    review["network_requests_allowed"] = True

    blueprint = export_case_intake_brain_handoff_scoped_adapter_implementation_blueprint(
        review,
        blueprinted_by="human-reviewer",
        blueprint_note="Blueprint.",
    )

    assert blueprint.blocked is True
    assert "reports execution" in blueprint.block_reason
    assert blueprint.can_execute_now is False


def test_implementation_blueprint_serializes_safety_metadata() -> None:
    data = export_case_intake_brain_handoff_scoped_adapter_implementation_blueprint(
        _readiness_review(),
        blueprinted_by="human-reviewer",
        blueprint_note="Define future scoped adapter implementation files and interfaces only; no execution authorized.",
    ).to_dict()

    assert data["kind"] == "case_intake_brain_handoff_scoped_adapter_implementation_blueprint"
    assert data["dry_run_only"] is True
    assert data["can_execute_now"] is False
    assert data["implementation_blueprint_allows_execution"] is False
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


def test_implementation_blueprint_markdown_contains_blueprint_and_safety() -> None:
    markdown = export_case_intake_brain_handoff_scoped_adapter_implementation_blueprint(
        _readiness_review(),
        blueprinted_by="human-reviewer",
        blueprint_note="Define future scoped adapter implementation files and interfaces only; no execution authorized.",
    ).to_markdown()

    assert "# Case Intake Brain Scoped Adapter Implementation Blueprint" in markdown
    assert "Implementation blueprint allows execution" in markdown
    assert "Proposed Module Files" in markdown
    assert "No command execution" in markdown
