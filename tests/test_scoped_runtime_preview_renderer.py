from dataclasses import replace

from bugintel.adapters.scoped_runtime.contracts import (
    SAFE_BLUEPRINT_STATE,
    SAFE_BLUEPRINT_STATUS,
    ScopedAdapterRequest,
)
from bugintel.adapters.scoped_runtime.preview_renderer import render_scoped_runtime_preview


def _request() -> ScopedAdapterRequest:
    return ScopedAdapterRequest.from_blueprint_artifact(
        {
            "kind": "case_intake_brain_handoff_scoped_adapter_implementation_blueprint",
            "implementation_blueprint_id": "SIB-ERR-SEP-RCP-FEG-ASR-RSR-SAER-AFC-ADP-RSM-EG-CP-AD-AP-001",
            "readiness_review_id": "ERR-SEP-RCP-FEG-ASR-RSR-SAER-AFC-ADP-RSM-EG-CP-AD-AP-001",
            "execution_plan_id": "SEP-RCP-FEG-ASR-RSR-SAER-AFC-ADP-RSM-EG-CP-AD-AP-001",
            "request_id": "SAER-AFC-ADP-RSM-EG-CP-AD-AP-001",
            "target_name": "demo-program",
            "endpoint": "/api/admin/users/{id}/permissions",
            "adapter_family": "curl",
            "command_family": "curl",
            "resolved_target_url": "https://example-program.test/api/admin/users/SYNTHETIC_USER_ID/permissions",
            "reviewed_command": "curl --request GET --url 'https://example-program.test/api/admin/users/SYNTHETIC_USER_ID/permissions' --header 'Authorization: Bearer CONTROLLED_TOKEN_ONLY'",
            "reviewed_method": "GET",
            "reviewed_scheme": "https",
            "reviewed_host": "example-program.test",
            "reviewed_path": "/api/admin/users/SYNTHETIC_USER_ID/permissions",
            "implementation_blueprint_status": SAFE_BLUEPRINT_STATUS,
            "implementation_blueprint_state": SAFE_BLUEPRINT_STATE,
            "adapter_execution_state": "not_executed",
            "blueprint_note": "Contracts only.",
            "proposed_validation_guards": ["Reject execution without later explicit runtime execution confirmation."],
            "required_preconditions": ["Controlled account only."],
            "scope_check_requirements": ["Host must match."],
            "placeholder_check_requirements": ["No unresolved placeholders."],
            "redaction_requirements": ["Redact token."],
            "stop_conditions": ["Stop on scope mismatch."],
            "unresolved_placeholders": [],
            "missing_safe_flags": [],
            "blocked_flags_seen": [],
            "shell_control_patterns_seen": [],
        }
    )


def test_preview_renderer_renders_local_preview_without_execution() -> None:
    artifact = render_scoped_runtime_preview(_request())
    data = artifact.to_dict()

    assert data["kind"] == "scoped_runtime_preview_artifact"
    assert data["preview_id"] == "SRP-SIB-ERR-SEP-RCP-FEG-ASR-RSR-SAER-AFC-ADP-RSM-EG-CP-AD-AP-001"
    assert data["render_status"] == "rendered-local-preview-only-no-execution"
    assert data["render_mode"] == "preview_only"
    assert data["scope_guard"]["allowed"] is True
    assert data["prepared_command"]["render_mode"] == "preview_only"
    assert data["adapter_execution_state"] == "not_executed"
    assert data["can_execute_now"] is False
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


def test_preview_renderer_redacts_controlled_token_placeholder() -> None:
    artifact = render_scoped_runtime_preview(_request())

    assert "CONTROLLED_TOKEN_ONLY" in artifact.preview_command
    assert "CONTROLLED_TOKEN_ONLY" not in artifact.redacted_preview_command
    assert "REDACTED_CONTROLLED_TOKEN" in artifact.redacted_preview_command


def test_preview_renderer_blocks_unsafe_request_without_rendering_command() -> None:
    artifact = render_scoped_runtime_preview(replace(_request(), network_requests_allowed=True))
    data = artifact.to_dict()

    assert data["render_status"] == "blocked"
    assert data["scope_guard"]["allowed"] is False
    assert data["preview_command"] == ""
    assert data["redacted_preview_command"] == ""
    assert data["can_execute_now"] is False
    assert data["network_requests_allowed"] is False
    assert data["tool_execution_allowed"] is False
    assert data["evidence_collection_allowed"] is False


def test_preview_renderer_blocks_mutation_method() -> None:
    artifact = render_scoped_runtime_preview(replace(_request(), reviewed_method="POST"))

    assert artifact.render_status == "blocked"
    assert artifact.preview_command == ""
    assert any("read-only" in item for item in artifact.blocking_findings)


def test_preview_renderer_is_serializable_and_preview_only() -> None:
    data = render_scoped_runtime_preview(_request()).to_dict()

    assert data["prepared_command"]["can_execute_now"] is False
    assert data["prepared_command"]["execution_allowed"] is False
    assert data["prepared_command"]["tool_execution_allowed"] is False
    assert data["prepared_command"]["network_requests_allowed"] is False
    assert data["planning_only"] is True
    assert data["dry_run_only"] is True
