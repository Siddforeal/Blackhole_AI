from dataclasses import replace

from bugintel.adapters.scoped_runtime.contracts import (
    SAFE_BLUEPRINT_STATE,
    SAFE_BLUEPRINT_STATUS,
    ScopedAdapterRequest,
)
from bugintel.adapters.scoped_runtime.execution_gate import (
    ScopedRuntimeExecutionGate,
    evaluate_scoped_runtime_execution_gate,
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
            "blueprint_note": "Execution gate only.",
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


def test_execution_gate_blocks_by_default_without_execution() -> None:
    artifact = ScopedRuntimeExecutionGate().evaluate(_request())
    data = artifact.to_dict()

    assert data["kind"] == "scoped_runtime_execution_gate_artifact"
    assert data["gate_id"] == "SREG-SIB-ERR-SEP-RCP-FEG-ASR-RSR-SAER-AFC-ADP-RSM-EG-CP-AD-AP-001"
    assert data["gate_status"] == "blocked-runtime-execution-not-authorized"
    assert data["gate_mode"] == "record_only_no_execution"
    assert data["future_authorization_requested"] is False
    assert data["adapter_preview"]["kind"] == "scoped_curl_adapter_preview"
    assert data["adapter_preview"]["render_status"] == "adapter-preview-rendered-local-only-no-execution"
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


def test_execution_gate_records_future_authorization_without_execution() -> None:
    artifact = ScopedRuntimeExecutionGate().evaluate(
        _request(),
        future_authorization_requested=True,
        human_authorization_recorded=True,
        controlled_account_recorded=True,
        scope_review_recorded=True,
    )
    data = artifact.to_dict()

    assert data["gate_status"] == "future-runtime-authorization-recorded-no-execution"
    assert data["blocking_findings"] == []
    assert data["future_authorization_requested"] is True
    assert data["human_authorization_recorded"] is True
    assert data["controlled_account_recorded"] is True
    assert data["scope_review_recorded"] is True
    assert data["can_execute_now"] is False
    assert data["execution_allowed"] is False
    assert data["runtime_execution_allowed"] is False
    assert data["tool_execution_allowed"] is False
    assert data["network_requests_allowed"] is False
    assert data["evidence_collection_allowed"] is False
    assert data["target_mutation_allowed"] is False
    assert data["report_submission_allowed"] is False
    assert data["vulnerability_confirmation_allowed"] is False


def test_execution_gate_blocks_partial_authorization() -> None:
    data = ScopedRuntimeExecutionGate().evaluate(
        _request(),
        future_authorization_requested=True,
        human_authorization_recorded=True,
        controlled_account_recorded=False,
        scope_review_recorded=True,
    ).to_dict()

    assert data["gate_status"] == "blocked-runtime-execution-not-authorized"
    assert any("Controlled account" in item for item in data["blocking_findings"])
    assert data["can_execute_now"] is False
    assert data["network_requests_allowed"] is False


def test_execution_gate_blocks_unsafe_adapter_preview() -> None:
    unsafe = replace(_request(), network_requests_allowed=True)
    data = ScopedRuntimeExecutionGate().evaluate(
        unsafe,
        future_authorization_requested=True,
        human_authorization_recorded=True,
        controlled_account_recorded=True,
        scope_review_recorded=True,
    ).to_dict()

    assert data["gate_status"] == "blocked-runtime-execution-not-authorized"
    assert data["adapter_preview"]["render_status"] == "blocked"
    assert any("runtime execution remains blocked" in item for item in data["blocking_findings"])
    assert data["can_execute_now"] is False
    assert data["network_requests_allowed"] is False


def test_execution_gate_redacts_preview_command() -> None:
    artifact = evaluate_scoped_runtime_execution_gate(
        _request(),
        future_authorization_requested=True,
        human_authorization_recorded=True,
        controlled_account_recorded=True,
        scope_review_recorded=True,
    )

    assert "CONTROLLED_TOKEN_ONLY" not in artifact.redacted_preview_command
    assert "REDACTED_CONTROLLED_TOKEN" in artifact.redacted_preview_command


def test_execution_gate_function_wrapper() -> None:
    data = evaluate_scoped_runtime_execution_gate(_request()).to_dict()

    assert data["kind"] == "scoped_runtime_execution_gate_artifact"
    assert data["gate_status"] == "blocked-runtime-execution-not-authorized"
    assert data["adapter_execution_state"] == "not_executed"
    assert data["can_execute_now"] is False
    assert data["network_requests_allowed"] is False
