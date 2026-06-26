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
from tests.test_case_intake_brain_handoff_answerer import _handoff


def _final_gate() -> dict:
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
    safety_review = export_case_intake_brain_handoff_scoped_adapter_safety_review(
        runtime_review,
    ).to_dict()
    return record_case_intake_brain_handoff_scoped_adapter_final_execution_gate(
        safety_review,
        decision="approved",
        decided_by="human-reviewer",
        reason="Approved for future adapter execution path only after separate explicit runtime confirmation.",
    ).to_dict()


def test_runtime_confirmation_packet_records_exact_context_without_execution() -> None:
    packet = record_case_intake_brain_handoff_scoped_adapter_runtime_confirmation_packet(
        _final_gate(),
        confirmed_by="human-reviewer",
        confirmation_text="I confirm the exact scoped adapter context was reviewed for a future runtime path only.",
    )

    assert packet.runtime_confirmation_id == "RCP-FEG-ASR-RSR-SAER-AFC-ADP-RSM-EG-CP-AD-AP-001"
    assert packet.final_gate_id == "FEG-ASR-RSR-SAER-AFC-ADP-RSM-EG-CP-AD-AP-001"
    assert packet.runtime_confirmation_status == "confirmed-runtime-context-for-future-adapter-path-no-execution"
    assert packet.runtime_confirmation_state == "confirmed_local_only"
    assert packet.confirmed_by == "human-reviewer"
    assert packet.human_runtime_confirmation_recorded is True
    assert packet.exact_context_confirmed is True
    assert packet.final_execution_gate_decision == "approved"
    assert packet.final_go_no_go == "go-recorded-for-future-adapter-path-only"
    assert packet.adapter_execution_state == "not_executed"
    assert packet.blocked is False
    assert packet.dry_run_only is True
    assert packet.can_execute_now is False
    assert packet.runtime_confirmation_allows_execution is False
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


def test_runtime_confirmation_packet_blocks_missing_confirmation_text() -> None:
    packet = record_case_intake_brain_handoff_scoped_adapter_runtime_confirmation_packet(
        _final_gate(),
        confirmed_by="human-reviewer",
        confirmation_text="",
    )

    assert packet.blocked is True
    assert "Runtime confirmation text is required" in packet.block_reason
    assert packet.human_runtime_confirmation_recorded is False
    assert packet.can_execute_now is False


def test_runtime_confirmation_packet_blocks_invalid_input() -> None:
    packet = record_case_intake_brain_handoff_scoped_adapter_runtime_confirmation_packet(
        {"kind": "wrong"},
        confirmed_by="human-reviewer",
        confirmation_text="Confirmed.",
    )

    assert packet.blocked is True
    assert "not a case_intake_brain_handoff_scoped_adapter_final_execution_gate" in packet.block_reason
    assert packet.can_execute_now is False


def test_runtime_confirmation_packet_blocks_denied_gate() -> None:
    gate = _final_gate()
    gate["final_execution_gate_decision"] = "denied"
    gate["final_go_no_go"] = "no-go-denied-by-human"

    packet = record_case_intake_brain_handoff_scoped_adapter_runtime_confirmation_packet(
        gate,
        confirmed_by="human-reviewer",
        confirmation_text="Confirmed.",
    )

    assert packet.blocked is True
    assert "decision must be approved" in packet.block_reason
    assert packet.can_execute_now is False


def test_runtime_confirmation_packet_blocks_unsafe_gate_flags() -> None:
    gate = _final_gate()
    gate["network_requests_allowed"] = True

    packet = record_case_intake_brain_handoff_scoped_adapter_runtime_confirmation_packet(
        gate,
        confirmed_by="human-reviewer",
        confirmation_text="Confirmed.",
    )

    assert packet.blocked is True
    assert "reports execution" in packet.block_reason
    assert packet.can_execute_now is False


def test_runtime_confirmation_packet_serializes_safety_metadata() -> None:
    data = record_case_intake_brain_handoff_scoped_adapter_runtime_confirmation_packet(
        _final_gate(),
        confirmed_by="human-reviewer",
        confirmation_text="I confirm the exact scoped adapter context was reviewed for a future runtime path only.",
    ).to_dict()

    assert data["kind"] == "case_intake_brain_handoff_scoped_adapter_runtime_confirmation_packet"
    assert data["dry_run_only"] is True
    assert data["can_execute_now"] is False
    assert data["runtime_confirmation_allows_execution"] is False
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


def test_runtime_confirmation_packet_markdown_contains_confirmation_and_safety() -> None:
    markdown = record_case_intake_brain_handoff_scoped_adapter_runtime_confirmation_packet(
        _final_gate(),
        confirmed_by="human-reviewer",
        confirmation_text="I confirm the exact scoped adapter context was reviewed for a future runtime path only.",
    ).to_markdown()

    assert "# Case Intake Brain Scoped Adapter Runtime Confirmation Packet" in markdown
    assert "Runtime confirmation allows execution" in markdown
    assert "No command execution" in markdown
    assert "Confirmation Text" in markdown
