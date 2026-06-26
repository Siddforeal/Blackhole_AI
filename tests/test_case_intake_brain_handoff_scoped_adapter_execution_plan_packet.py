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
from bugintel.core.case_intake_brain_handoff_scoped_adapter_runtime_confirmation_packet import (
    record_case_intake_brain_handoff_scoped_adapter_runtime_confirmation_packet,
)
from bugintel.core.case_intake_brain_handoff_scoped_adapter_execution_plan_packet import (
    export_case_intake_brain_handoff_scoped_adapter_execution_plan_packet,
)
from tests.test_case_intake_brain_handoff_answerer import _handoff


def _runtime_confirmation() -> dict:
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
    safety_review = export_case_intake_brain_handoff_scoped_adapter_safety_review(runtime_review).to_dict()
    final_gate = record_case_intake_brain_handoff_scoped_adapter_final_execution_gate(
        safety_review,
        decision="approved",
        decided_by="human-reviewer",
        reason="Approved for future adapter execution path only after separate explicit runtime confirmation.",
    ).to_dict()
    return record_case_intake_brain_handoff_scoped_adapter_runtime_confirmation_packet(
        final_gate,
        confirmed_by="human-reviewer",
        confirmation_text="I confirm the exact scoped adapter context was reviewed for a future runtime path only.",
    ).to_dict()


def test_execution_plan_packet_records_plan_without_execution() -> None:
    plan = export_case_intake_brain_handoff_scoped_adapter_execution_plan_packet(
        _runtime_confirmation(),
        planned_by="human-reviewer",
        plan_purpose="Prepare a future scoped adapter execution plan without executing anything.",
    )

    assert plan.execution_plan_id == "SEP-RCP-FEG-ASR-RSR-SAER-AFC-ADP-RSM-EG-CP-AD-AP-001"
    assert plan.runtime_confirmation_id == "RCP-FEG-ASR-RSR-SAER-AFC-ADP-RSM-EG-CP-AD-AP-001"
    assert plan.execution_plan_status == "planned-for-future-scoped-adapter-execution-no-execution"
    assert plan.execution_plan_state == "planned_local_only"
    assert plan.planned_by == "human-reviewer"
    assert plan.execution_plan_steps
    assert plan.execution_preflight_checks
    assert plan.execution_stop_conditions
    assert plan.adapter_execution_state == "not_executed"
    assert plan.blocked is False
    assert plan.dry_run_only is True
    assert plan.can_execute_now is False
    assert plan.execution_plan_allows_execution is False
    assert plan.execution_allowed is False
    assert plan.validation_allowed is False
    assert plan.runtime_execution_allowed is False
    assert plan.tool_execution_allowed is False
    assert plan.browser_execution_allowed is False
    assert plan.network_requests_allowed is False
    assert plan.evidence_collection_allowed is False
    assert plan.target_mutation_allowed is False
    assert plan.report_submission_allowed is False
    assert plan.vulnerability_confirmation_allowed is False


def test_execution_plan_packet_blocks_missing_plan_purpose() -> None:
    plan = export_case_intake_brain_handoff_scoped_adapter_execution_plan_packet(
        _runtime_confirmation(),
        planned_by="human-reviewer",
        plan_purpose="",
    )

    assert plan.blocked is True
    assert "Execution plan purpose is required" in plan.block_reason
    assert plan.can_execute_now is False


def test_execution_plan_packet_blocks_invalid_input() -> None:
    plan = export_case_intake_brain_handoff_scoped_adapter_execution_plan_packet(
        {"kind": "wrong"},
        planned_by="human-reviewer",
        plan_purpose="Prepare plan.",
    )

    assert plan.blocked is True
    assert "not a case_intake_brain_handoff_scoped_adapter_runtime_confirmation_packet" in plan.block_reason
    assert plan.can_execute_now is False


def test_execution_plan_packet_blocks_unconfirmed_packet() -> None:
    packet = _runtime_confirmation()
    packet["runtime_confirmation_status"] = "blocked"

    plan = export_case_intake_brain_handoff_scoped_adapter_execution_plan_packet(
        packet,
        planned_by="human-reviewer",
        plan_purpose="Prepare plan.",
    )

    assert plan.blocked is True
    assert "runtime confirmation status has not passed" in plan.block_reason
    assert plan.can_execute_now is False


def test_execution_plan_packet_blocks_unsafe_packet_flags() -> None:
    packet = _runtime_confirmation()
    packet["network_requests_allowed"] = True

    plan = export_case_intake_brain_handoff_scoped_adapter_execution_plan_packet(
        packet,
        planned_by="human-reviewer",
        plan_purpose="Prepare plan.",
    )

    assert plan.blocked is True
    assert "reports execution" in plan.block_reason
    assert plan.can_execute_now is False


def test_execution_plan_packet_serializes_safety_metadata() -> None:
    data = export_case_intake_brain_handoff_scoped_adapter_execution_plan_packet(
        _runtime_confirmation(),
        planned_by="human-reviewer",
        plan_purpose="Prepare a future scoped adapter execution plan without executing anything.",
    ).to_dict()

    assert data["kind"] == "case_intake_brain_handoff_scoped_adapter_execution_plan_packet"
    assert data["dry_run_only"] is True
    assert data["can_execute_now"] is False
    assert data["execution_plan_allows_execution"] is False
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


def test_execution_plan_packet_markdown_contains_plan_and_safety() -> None:
    markdown = export_case_intake_brain_handoff_scoped_adapter_execution_plan_packet(
        _runtime_confirmation(),
        planned_by="human-reviewer",
        plan_purpose="Prepare a future scoped adapter execution plan without executing anything.",
    ).to_markdown()

    assert "# Case Intake Brain Scoped Adapter Execution Plan Packet" in markdown
    assert "Execution plan allows execution" in markdown
    assert "No command execution" in markdown
    assert "Execution Plan Steps" in markdown
