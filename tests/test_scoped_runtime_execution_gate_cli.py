import json

from typer.testing import CliRunner

from bugintel.cli import app
from bugintel.adapters.scoped_runtime.contracts import (
    SAFE_BLUEPRINT_STATE,
    SAFE_BLUEPRINT_STATUS,
)

runner = CliRunner()


def _blueprint() -> dict:
    return {
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
        "blueprint_note": "Execution gate CLI only.",
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


def test_scoped_runtime_execution_gate_cli_writes_blocked_json(tmp_path) -> None:
    input_file = tmp_path / "request.json"
    output_file = tmp_path / "gate.json"
    input_file.write_text(json.dumps(_blueprint()))

    result = runner.invoke(
        app,
        [
            "scoped-runtime-execution-gate",
            str(input_file),
            "--json-output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0
    assert output_file.exists()
    data = json.loads(output_file.read_text())
    assert data["kind"] == "scoped_runtime_execution_gate_artifact"
    assert data["gate_status"] == "blocked-runtime-execution-not-authorized"
    assert data["future_authorization_requested"] is False
    assert data["adapter_execution_state"] == "not_executed"
    assert data["can_execute_now"] is False
    assert data["execution_allowed"] is False
    assert data["runtime_execution_allowed"] is False
    assert data["tool_execution_allowed"] is False
    assert data["network_requests_allowed"] is False
    assert data["evidence_collection_allowed"] is False
    assert data["target_mutation_allowed"] is False
    assert data["report_submission_allowed"] is False
    assert data["vulnerability_confirmation_allowed"] is False
    assert data["safety"]["network_requests"] is False
    assert data["safety"]["tool_execution"] is False
    assert "does not execute curl" in result.stdout


def test_scoped_runtime_execution_gate_cli_records_future_authorization_without_execution(tmp_path) -> None:
    input_file = tmp_path / "request.json"
    output_file = tmp_path / "gate.json"
    input_file.write_text(json.dumps(_blueprint()))

    result = runner.invoke(
        app,
        [
            "scoped-runtime-execution-gate",
            str(input_file),
            "--future-authorization-requested",
            "--human-authorization-recorded",
            "--controlled-account-recorded",
            "--scope-review-recorded",
            "--json-output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0
    data = json.loads(output_file.read_text())
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


def test_scoped_runtime_execution_gate_cli_blocks_partial_authorization(tmp_path) -> None:
    input_file = tmp_path / "request.json"
    output_file = tmp_path / "gate.json"
    input_file.write_text(json.dumps(_blueprint()))

    result = runner.invoke(
        app,
        [
            "scoped-runtime-execution-gate",
            str(input_file),
            "--future-authorization-requested",
            "--human-authorization-recorded",
            "--scope-review-recorded",
            "--json-output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0
    data = json.loads(output_file.read_text())
    assert data["gate_status"] == "blocked-runtime-execution-not-authorized"
    assert any("Controlled account" in item for item in data["blocking_findings"])
    assert data["can_execute_now"] is False
    assert data["network_requests_allowed"] is False


def test_scoped_runtime_execution_gate_cli_rejects_missing_file(tmp_path) -> None:
    missing = tmp_path / "missing.json"

    result = runner.invoke(app, ["scoped-runtime-execution-gate", str(missing)])

    combined_output = result.stdout + getattr(result, "stderr", "") + str(result.exception or "")
    assert result.exit_code != 0
    assert "request file does not exist" in combined_output


def test_scoped_runtime_execution_gate_cli_writes_markdown_output(tmp_path) -> None:
    input_file = tmp_path / "request.json"
    output_file = tmp_path / "gate.md"
    input_file.write_text(json.dumps(_blueprint()))

    result = runner.invoke(
        app,
        [
            "scoped-runtime-execution-gate",
            str(input_file),
            "--future-authorization-requested",
            "--human-authorization-recorded",
            "--controlled-account-recorded",
            "--scope-review-recorded",
            "--output-file",
            str(output_file),
        ],
    )

    assert result.exit_code == 0
    assert output_file.exists()
    markdown = output_file.read_text()
    assert "# Scoped Runtime Execution Gate" in markdown
    assert "Gate status: `future-runtime-authorization-recorded-no-execution`" in markdown
    assert "Can execute now: `false`" in markdown
    assert "Network requests allowed: `false`" in markdown
    assert "Tool execution allowed: `false`" in markdown
    assert "REDACTED_CONTROLLED_TOKEN" in markdown
    assert "CONTROLLED_TOKEN_ONLY" not in markdown
    assert "Saved scoped runtime execution gate Markdown" in result.stdout
