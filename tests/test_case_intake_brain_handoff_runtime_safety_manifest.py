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


def _execution_gate(decision: str = "approved") -> dict:
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
    command_proposal = export_case_intake_brain_handoff_read_only_command_proposal(
        approval_decision,
        command_family="curl",
    ).to_dict()
    return record_case_intake_brain_handoff_execution_approval_gate(
        command_proposal,
        decision=decision,
        decided_by="sidd",
        reason="Approved only for future controlled read-only execution adapter preview.",
    ).to_dict()


def test_runtime_safety_manifest_exports_curl_manifest_without_execution() -> None:
    manifest = export_case_intake_brain_handoff_runtime_safety_manifest(
        _execution_gate(),
        adapter_family="curl",
    )

    assert manifest.manifest_id == "RSM-EG-CP-AD-AP-001"
    assert manifest.gate_id == "EG-CP-AD-AP-001"
    assert manifest.proposal_id == "CP-AD-AP-001"
    assert manifest.adapter_family == "curl"
    assert manifest.command_family == "curl"
    assert manifest.runtime_manifest_status == "ready-for-future-adapter-review-no-execution"
    assert "{{TARGET_BASE_URL}}" in manifest.proposed_command
    assert manifest.blocked is False
    assert manifest.can_execute_now is False
    assert manifest.manifest_allows_execution is False
    assert manifest.requires_runtime_scope_check is True
    assert manifest.requires_final_human_confirmation is True
    assert manifest.requires_adapter_safety_check is True
    assert manifest.execution_allowed is False
    assert manifest.validation_allowed is False
    assert manifest.runtime_execution_allowed is False
    assert manifest.tool_execution_allowed is False
    assert manifest.browser_execution_allowed is False
    assert manifest.network_requests_allowed is False
    assert manifest.evidence_collection_allowed is False
    assert manifest.target_mutation_allowed is False
    assert manifest.report_submission_allowed is False
    assert manifest.vulnerability_confirmation_allowed is False
    assert manifest.scope_check_requirements
    assert manifest.placeholder_check_requirements
    assert manifest.adapter_safety_requirements
    assert manifest.final_human_confirmation_requirements


def test_runtime_safety_manifest_blocks_denied_execution_gate() -> None:
    manifest = export_case_intake_brain_handoff_runtime_safety_manifest(
        _execution_gate(decision="denied"),
        adapter_family="curl",
    )

    assert manifest.blocked is True
    assert "must be approved" in manifest.block_reason
    assert manifest.can_execute_now is False
    assert manifest.manifest_allows_execution is False


def test_runtime_safety_manifest_blocks_invalid_input() -> None:
    manifest = export_case_intake_brain_handoff_runtime_safety_manifest(
        {"kind": "wrong"},
        adapter_family="curl",
    )

    assert manifest.blocked is True
    assert "not a case_intake_brain_handoff_execution_approval_gate" in manifest.block_reason
    assert manifest.can_execute_now is False


def test_runtime_safety_manifest_blocks_unsupported_adapter() -> None:
    manifest = export_case_intake_brain_handoff_runtime_safety_manifest(
        _execution_gate(),
        adapter_family="burp",
    )

    assert manifest.blocked is True
    assert "Unsupported adapter family" in manifest.block_reason
    assert manifest.adapter_family == "burp"
    assert manifest.can_execute_now is False


def test_runtime_safety_manifest_serializes_safety_metadata() -> None:
    data = export_case_intake_brain_handoff_runtime_safety_manifest(
        _execution_gate(),
        adapter_family="curl",
    ).to_dict()

    assert data["kind"] == "case_intake_brain_handoff_runtime_safety_manifest"
    assert data["can_execute_now"] is False
    assert data["manifest_allows_execution"] is False
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


def test_runtime_safety_manifest_markdown_contains_requirements_and_safety() -> None:
    markdown = export_case_intake_brain_handoff_runtime_safety_manifest(
        _execution_gate(),
        adapter_family="curl",
    ).to_markdown()

    assert "# Case Intake Brain Runtime Safety Manifest" in markdown
    assert "## Runtime Scope Check Requirements" in markdown
    assert "## Adapter Safety Requirements" in markdown
    assert "{{TARGET_BASE_URL}}" in markdown
    assert "Manifest allows execution" in markdown
    assert "No command execution" in markdown
