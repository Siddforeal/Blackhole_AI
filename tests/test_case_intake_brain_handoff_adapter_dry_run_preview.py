from bugintel.core.case_intake_brain_handoff_adapter_dry_run_preview import (
    export_case_intake_brain_handoff_adapter_dry_run_preview,
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


def _runtime_manifest() -> dict:
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
    execution_gate = record_case_intake_brain_handoff_execution_approval_gate(
        command_proposal,
        decision="approved",
        decided_by="sidd",
        reason="Approved only for future controlled read-only execution adapter preview.",
    ).to_dict()
    return export_case_intake_brain_handoff_runtime_safety_manifest(
        execution_gate,
        adapter_family="curl",
    ).to_dict()


def test_adapter_dry_run_preview_resolves_placeholders_without_execution() -> None:
    preview = export_case_intake_brain_handoff_adapter_dry_run_preview(
        _runtime_manifest(),
        target_base_url="https://example-program.test",
        controlled_account_token_placeholder="CONTROLLED_TOKEN_ONLY",
        path_parameters=["id=SYNTHETIC_USER_ID"],
    )

    assert preview.preview_id == "ADP-RSM-EG-CP-AD-AP-001"
    assert preview.manifest_id == "RSM-EG-CP-AD-AP-001"
    assert preview.adapter_family == "curl"
    assert preview.command_family == "curl"
    assert preview.resolved_endpoint == "/api/admin/users/SYNTHETIC_USER_ID/permissions"
    assert preview.resolved_target_url == "https://example-program.test/api/admin/users/SYNTHETIC_USER_ID/permissions"
    assert "https://example-program.test/api/admin/users/SYNTHETIC_USER_ID/permissions" in preview.resolved_command_preview
    assert "CONTROLLED_TOKEN_ONLY" in preview.resolved_command_preview
    assert "{{TARGET_BASE_URL}}" not in preview.resolved_command_preview
    assert "{id}" not in preview.resolved_command_preview
    assert preview.unresolved_placeholders == ()
    assert preview.blocked is False
    assert preview.dry_run_only is True
    assert preview.preview_ready is True
    assert preview.can_execute_now is False
    assert preview.preview_allows_execution is False
    assert preview.execution_allowed is False
    assert preview.validation_allowed is False
    assert preview.runtime_execution_allowed is False
    assert preview.tool_execution_allowed is False
    assert preview.browser_execution_allowed is False
    assert preview.network_requests_allowed is False
    assert preview.evidence_collection_allowed is False
    assert preview.target_mutation_allowed is False
    assert preview.report_submission_allowed is False
    assert preview.vulnerability_confirmation_allowed is False


def test_adapter_dry_run_preview_blocks_missing_path_parameter() -> None:
    preview = export_case_intake_brain_handoff_adapter_dry_run_preview(
        _runtime_manifest(),
        target_base_url="https://example-program.test",
        controlled_account_token_placeholder="CONTROLLED_TOKEN_ONLY",
        path_parameters=[],
    )

    assert preview.blocked is True
    assert "Missing path parameter replacement" in preview.block_reason
    assert "{id}" in preview.block_reason
    assert preview.can_execute_now is False


def test_adapter_dry_run_preview_blocks_invalid_input() -> None:
    preview = export_case_intake_brain_handoff_adapter_dry_run_preview(
        {"kind": "wrong"},
        target_base_url="https://example-program.test",
        controlled_account_token_placeholder="CONTROLLED_TOKEN_ONLY",
        path_parameters=["id=SYNTHETIC_USER_ID"],
    )

    assert preview.blocked is True
    assert "not a case_intake_brain_handoff_runtime_safety_manifest" in preview.block_reason
    assert preview.can_execute_now is False


def test_adapter_dry_run_preview_blocks_unsupported_adapter() -> None:
    manifest = _runtime_manifest()
    manifest["adapter_family"] = "burp"

    preview = export_case_intake_brain_handoff_adapter_dry_run_preview(
        manifest,
        target_base_url="https://example-program.test",
        controlled_account_token_placeholder="CONTROLLED_TOKEN_ONLY",
        path_parameters=["id=SYNTHETIC_USER_ID"],
    )

    assert preview.blocked is True
    assert "Unsupported adapter family" in preview.block_reason
    assert preview.adapter_family == "burp"
    assert preview.can_execute_now is False


def test_adapter_dry_run_preview_blocks_unsafe_target_base_url() -> None:
    preview = export_case_intake_brain_handoff_adapter_dry_run_preview(
        _runtime_manifest(),
        target_base_url="http://localhost",
        controlled_account_token_placeholder="CONTROLLED_TOKEN_ONLY",
        path_parameters=["id=SYNTHETIC_USER_ID"],
    )

    assert preview.blocked is True
    assert "Target base URL must use https" in preview.block_reason
    assert "host is not allowed" in preview.block_reason
    assert preview.can_execute_now is False


def test_adapter_dry_run_preview_serializes_safety_metadata() -> None:
    data = export_case_intake_brain_handoff_adapter_dry_run_preview(
        _runtime_manifest(),
        target_base_url="https://example-program.test",
        controlled_account_token_placeholder="CONTROLLED_TOKEN_ONLY",
        path_parameters=["id=SYNTHETIC_USER_ID"],
    ).to_dict()

    assert data["kind"] == "case_intake_brain_handoff_adapter_dry_run_preview"
    assert data["dry_run_only"] is True
    assert data["preview_ready"] is True
    assert data["can_execute_now"] is False
    assert data["preview_allows_execution"] is False
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


def test_adapter_dry_run_preview_markdown_contains_preview_and_safety() -> None:
    markdown = export_case_intake_brain_handoff_adapter_dry_run_preview(
        _runtime_manifest(),
        target_base_url="https://example-program.test",
        controlled_account_token_placeholder="CONTROLLED_TOKEN_ONLY",
        path_parameters=["id=SYNTHETIC_USER_ID"],
    ).to_markdown()

    assert "# Case Intake Brain Adapter Dry-Run Preview" in markdown
    assert "## Resolved Dry-Run Command Preview" in markdown
    assert "https://example-program.test/api/admin/users/SYNTHETIC_USER_ID/permissions" in markdown
    assert "Preview allows execution" in markdown
    assert "No command execution" in markdown
