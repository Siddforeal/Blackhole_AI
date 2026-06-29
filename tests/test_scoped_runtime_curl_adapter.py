from dataclasses import replace

from bugintel.adapters.scoped_runtime.contracts import (
    SAFE_BLUEPRINT_STATE,
    SAFE_BLUEPRINT_STATUS,
    ScopedAdapterRequest,
)
from bugintel.adapters.scoped_runtime.curl_adapter import (
    ScopedCurlAdapter,
    render_scoped_curl_adapter_preview,
)


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
            "blueprint_note": "Curl adapter skeleton only.",
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


def test_scoped_curl_adapter_prepare_request_is_preview_only() -> None:
    adapter = ScopedCurlAdapter()
    prepared = adapter.prepare_request(_request())
    data = prepared.to_dict()

    assert data["render_mode"] == "preview_only"
    assert data["adapter_execution_state"] == "not_executed"
    assert data["can_execute_now"] is False
    assert data["execution_allowed"] is False
    assert data["tool_execution_allowed"] is False
    assert data["network_requests_allowed"] is False
    assert data["evidence_collection_allowed"] is False
    assert data["target_mutation_allowed"] is False
    assert data["report_submission_allowed"] is False
    assert data["vulnerability_confirmation_allowed"] is False


def test_scoped_curl_adapter_renders_preview_without_execution() -> None:
    adapter = ScopedCurlAdapter()
    preview = adapter.render_preview(_request())
    data = preview.to_dict()

    assert data["kind"] == "scoped_curl_adapter_preview"
    assert data["adapter_name"] == "scoped-curl-adapter-skeleton"
    assert data["render_status"] == "adapter-preview-rendered-local-only-no-execution"
    assert data["render_mode"] == "preview_only"
    assert data["preview_artifact"]["kind"] == "scoped_runtime_preview_artifact"
    assert data["preview_artifact"]["render_status"] == "rendered-local-preview-only-no-execution"
    assert data["preview_artifact"]["scope_guard"]["allowed"] is True
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


def test_scoped_curl_adapter_redacts_preview_command() -> None:
    preview = ScopedCurlAdapter().render_preview(_request())

    assert "CONTROLLED_TOKEN_ONLY" not in preview.redacted_preview_command
    assert "REDACTED_CONTROLLED_TOKEN" in preview.redacted_preview_command


def test_scoped_curl_adapter_blocks_unsafe_request() -> None:
    preview = ScopedCurlAdapter().render_preview(replace(_request(), network_requests_allowed=True))
    data = preview.to_dict()

    assert data["render_status"] == "blocked"
    assert data["preview_artifact"]["render_status"] == "blocked"
    assert data["preview_artifact"]["preview_command"] == ""
    assert data["preview_artifact"]["redacted_preview_command"] == ""
    assert data["blocking_findings"]
    assert data["can_execute_now"] is False
    assert data["network_requests_allowed"] is False
    assert data["tool_execution_allowed"] is False
    assert data["evidence_collection_allowed"] is False


def test_scoped_curl_adapter_function_wrapper() -> None:
    data = render_scoped_curl_adapter_preview(_request()).to_dict()

    assert data["kind"] == "scoped_curl_adapter_preview"
    assert data["render_status"] == "adapter-preview-rendered-local-only-no-execution"
    assert data["adapter_execution_state"] == "not_executed"
    assert data["can_execute_now"] is False
    assert data["network_requests_allowed"] is False
