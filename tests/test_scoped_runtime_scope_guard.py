from dataclasses import replace

from bugintel.adapters.scoped_runtime.contracts import (
    SAFE_BLUEPRINT_STATE,
    SAFE_BLUEPRINT_STATUS,
    ScopedAdapterRequest,
)
from bugintel.adapters.scoped_runtime.scope_guard import validate_scoped_adapter_request


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
            "reviewed_command": "curl --request GET --url 'https://example-program.test/api/admin/users/SYNTHETIC_USER_ID/permissions'",
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


def test_scope_guard_allows_safe_contract_for_future_implementation_only() -> None:
    result = validate_scoped_adapter_request(_request())
    data = result.to_dict()

    assert result.allowed is True
    assert result.status == "valid-for-future-implementation-contract-only-no-execution"
    assert result.blocking_findings == ()
    assert data["adapter_execution_state"] == "not_executed"
    assert data["can_execute_now"] is False
    assert data["execution_allowed"] is False
    assert data["tool_execution_allowed"] is False
    assert data["network_requests_allowed"] is False
    assert data["evidence_collection_allowed"] is False
    assert data["target_mutation_allowed"] is False
    assert data["report_submission_allowed"] is False
    assert data["vulnerability_confirmation_allowed"] is False
    assert data["safety"]["network_requests"] is False
    assert data["safety"]["tool_execution"] is False


def test_scope_guard_blocks_network_flag() -> None:
    result = validate_scoped_adapter_request(replace(_request(), network_requests_allowed=True))

    assert result.allowed is False
    assert result.status == "blocked"
    assert any("unsafe execution" in item for item in result.blocking_findings)


def test_scope_guard_blocks_mutation_method() -> None:
    result = validate_scoped_adapter_request(replace(_request(), reviewed_method="POST"))

    assert result.allowed is False
    assert any("read-only" in item for item in result.blocking_findings)


def test_scope_guard_blocks_unresolved_placeholders() -> None:
    result = validate_scoped_adapter_request(replace(_request(), unresolved_placeholders=("id",)))

    assert result.allowed is False
    assert any("Unresolved placeholders" in item for item in result.blocking_findings)


def test_scope_guard_blocks_wrong_source_kind() -> None:
    result = validate_scoped_adapter_request(replace(_request(), blueprint_artifact_kind="wrong"))

    assert result.allowed is False
    assert any("implementation blueprint artifact" in item for item in result.blocking_findings)
