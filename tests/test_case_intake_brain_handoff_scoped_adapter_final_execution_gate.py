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
from bugintel.core.case_intake_brain_handoff_scoped_adapter_runtime_scope_review import (
    export_case_intake_brain_handoff_scoped_adapter_runtime_scope_review,
)
from bugintel.core.case_intake_brain_handoff_scoped_adapter_safety_review import (
    export_case_intake_brain_handoff_scoped_adapter_safety_review,
)
from bugintel.core.case_intake_brain_handoff_scoped_adapter_final_execution_gate import (
    record_case_intake_brain_handoff_scoped_adapter_final_execution_gate,
)
from tests.test_case_intake_brain_handoff_answerer import _handoff


def _safety_review() -> dict:
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
    confirmation = record_case_intake_brain_handoff_adapter_final_confirmation(
        preview,
        decision="confirmed",
        confirmed_by="human-reviewer",
        reason="Final human review confirms dry-run preview is ready for future scoped adapter only.",
    ).to_dict()
    request = export_case_intake_brain_handoff_scoped_adapter_execution_request(
        confirmation,
        request_purpose="future-scoped-curl-adapter-review",
    ).to_dict()
    runtime_review = export_case_intake_brain_handoff_scoped_adapter_runtime_scope_review(
        request,
        allowed_host="example-program.test",
        allowed_scheme="https",
        allowed_method="GET",
    ).to_dict()
    return export_case_intake_brain_handoff_scoped_adapter_safety_review(runtime_review).to_dict()


def test_final_execution_gate_records_approved_without_execution() -> None:
    gate = record_case_intake_brain_handoff_scoped_adapter_final_execution_gate(
        _safety_review(),
        decision="approved",
        decided_by="human-reviewer",
        reason="Approved for future adapter execution path only after separate explicit runtime confirmation.",
    )

    assert gate.final_gate_id == "FEG-ASR-RSR-SAER-AFC-ADP-RSM-EG-CP-AD-AP-001"
    assert gate.safety_review_id == "ASR-RSR-SAER-AFC-ADP-RSM-EG-CP-AD-AP-001"
    assert gate.final_execution_gate_decision == "approved"
    assert gate.final_execution_gate_status == "approved-for-future-adapter-path-no-execution"
    assert gate.decided_by == "human-reviewer"
    assert gate.human_final_execution_gate_recorded is True
    assert gate.final_go_no_go == "go-recorded-for-future-adapter-path-only"
    assert gate.adapter_execution_state == "not_executed"
    assert gate.blocked is False
    assert gate.dry_run_only is True
    assert gate.can_execute_now is False
    assert gate.final_execution_gate_allows_execution is False
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


def test_final_execution_gate_records_denied_without_execution() -> None:
    gate = record_case_intake_brain_handoff_scoped_adapter_final_execution_gate(
        _safety_review(),
        decision="denied",
        decided_by="human-reviewer",
        reason="Human reviewer denied the final gate.",
    )

    assert gate.final_execution_gate_decision == "denied"
    assert gate.final_execution_gate_status == "denied-by-human-no-execution"
    assert gate.final_go_no_go == "no-go-denied-by-human"
    assert gate.human_final_execution_gate_recorded is True
    assert gate.blocked is True
    assert gate.can_execute_now is False


def test_final_execution_gate_records_blocked_without_execution() -> None:
    gate = record_case_intake_brain_handoff_scoped_adapter_final_execution_gate(
        _safety_review(),
        decision="blocked",
        decided_by="human-reviewer",
        reason="Human reviewer blocked the final gate.",
    )

    assert gate.final_execution_gate_decision == "blocked"
    assert gate.final_execution_gate_status == "blocked-by-human-no-execution"
    assert gate.final_go_no_go == "no-go-blocked-by-human"
    assert gate.human_final_execution_gate_recorded is True
    assert gate.blocked is True
    assert gate.can_execute_now is False


def test_final_execution_gate_blocks_invalid_decision() -> None:
    gate = record_case_intake_brain_handoff_scoped_adapter_final_execution_gate(
        _safety_review(),
        decision="maybe",
        decided_by="human-reviewer",
        reason="Invalid decision.",
    )

    assert gate.blocked is True
    assert "Invalid final execution gate decision" in gate.block_reason
    assert gate.human_final_execution_gate_recorded is False
    assert gate.can_execute_now is False


def test_final_execution_gate_blocks_invalid_input() -> None:
    gate = record_case_intake_brain_handoff_scoped_adapter_final_execution_gate(
        {"kind": "wrong"},
        decision="approved",
        decided_by="human-reviewer",
        reason="Approved.",
    )

    assert gate.blocked is True
    assert "not a case_intake_brain_handoff_scoped_adapter_safety_review" in gate.block_reason
    assert gate.can_execute_now is False


def test_final_execution_gate_serializes_safety_metadata() -> None:
    data = record_case_intake_brain_handoff_scoped_adapter_final_execution_gate(
        _safety_review(),
        decision="approved",
        decided_by="human-reviewer",
        reason="Approved for future adapter execution path only after separate explicit runtime confirmation.",
    ).to_dict()

    assert data["kind"] == "case_intake_brain_handoff_scoped_adapter_final_execution_gate"
    assert data["dry_run_only"] is True
    assert data["can_execute_now"] is False
    assert data["final_execution_gate_allows_execution"] is False
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


def test_final_execution_gate_markdown_contains_decision_and_safety() -> None:
    markdown = record_case_intake_brain_handoff_scoped_adapter_final_execution_gate(
        _safety_review(),
        decision="approved",
        decided_by="human-reviewer",
        reason="Approved for future adapter execution path only after separate explicit runtime confirmation.",
    ).to_markdown()

    assert "# Case Intake Brain Scoped Adapter Final Execution Gate" in markdown
    assert "Final execution gate allows execution" in markdown
    assert "No command execution" in markdown
    assert "Decision Reason" in markdown
