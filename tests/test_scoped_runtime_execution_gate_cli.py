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


def test_scoped_runtime_execution_gate_cli_writes_bundle_output_dir(tmp_path) -> None:
    input_file = tmp_path / "request.json"
    bundle_dir = tmp_path / "bundle"
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
            "--bundle-output-dir",
            str(bundle_dir),
        ],
    )

    assert result.exit_code == 0
    gate_json = bundle_dir / "gate.json"
    gate_markdown = bundle_dir / "gate.md"
    manifest_json = bundle_dir / "manifest.json"
    assert gate_json.exists()
    assert gate_markdown.exists()
    assert manifest_json.exists()

    data = json.loads(gate_json.read_text())
    markdown = gate_markdown.read_text()
    manifest = json.loads(manifest_json.read_text())

    assert data["kind"] == "scoped_runtime_execution_gate_artifact"
    assert data["gate_status"] == "future-runtime-authorization-recorded-no-execution"
    assert data["can_execute_now"] is False
    assert data["network_requests_allowed"] is False
    assert manifest["kind"] == "scoped_runtime_execution_gate_bundle_manifest"
    assert manifest["bundle_mode"] == "local_files_only_no_execution"
    assert [item["filename"] for item in manifest["artifact_files"]] == [
        "gate.json",
        "gate.md",
        "manifest.json",
    ]
    assert manifest["can_execute_now"] is False
    assert manifest["network_requests_allowed"] is False
    assert manifest["tool_execution_allowed"] is False
    assert "# Scoped Runtime Execution Gate" in markdown
    assert "REDACTED_CONTROLLED_TOKEN" in markdown
    assert "CONTROLLED_TOKEN_ONLY" not in markdown
    assert "Saved scoped runtime execution gate bundle" in result.stdout


def test_scoped_runtime_execution_gate_bundle_verify_cli_writes_json_and_markdown(tmp_path) -> None:
    input_file = tmp_path / "request.json"
    bundle_dir = tmp_path / "bundle"
    verification_json = tmp_path / "verification.json"
    verification_markdown = tmp_path / "verification.md"
    input_file.write_text(json.dumps(_blueprint()))

    bundle_result = runner.invoke(
        app,
        [
            "scoped-runtime-execution-gate",
            str(input_file),
            "--future-authorization-requested",
            "--human-authorization-recorded",
            "--controlled-account-recorded",
            "--scope-review-recorded",
            "--bundle-output-dir",
            str(bundle_dir),
        ],
    )
    assert bundle_result.exit_code == 0

    verify_result = runner.invoke(
        app,
        [
            "scoped-runtime-execution-gate-bundle-verify",
            str(bundle_dir),
            "--json-output",
            str(verification_json),
            "--output-file",
            str(verification_markdown),
        ],
    )

    assert verify_result.exit_code == 0
    assert verification_json.exists()
    assert verification_markdown.exists()

    data = json.loads(verification_json.read_text())
    markdown = verification_markdown.read_text()

    assert data["kind"] == "scoped_runtime_execution_gate_bundle_verification_artifact"
    assert data["verification_status"] == "verified-local-bundle-no-execution"
    assert data["bundle_mode"] == "local_files_only_no_execution"
    assert data["missing_files"] == []
    assert data["unexpected_files"] == []
    assert data["markdown_has_unredacted_secret"] is False
    assert data["can_execute_now"] is False
    assert data["network_requests_allowed"] is False
    assert data["tool_execution_allowed"] is False
    assert "# Scoped Runtime Execution Gate Bundle Verification" in markdown
    assert "Saved scoped runtime execution gate bundle verification JSON" in verify_result.stdout
    assert "Saved scoped runtime execution gate bundle verification Markdown" in verify_result.stdout


def test_scoped_runtime_execution_gate_bundle_review_packet_cli_writes_json_and_markdown(tmp_path) -> None:
    input_file = tmp_path / "request.json"
    bundle_dir = tmp_path / "bundle"
    verification_json = tmp_path / "verification.json"
    review_json = tmp_path / "review.json"
    review_markdown = tmp_path / "review.md"
    input_file.write_text(json.dumps(_blueprint()))

    bundle_result = runner.invoke(
        app,
        [
            "scoped-runtime-execution-gate",
            str(input_file),
            "--future-authorization-requested",
            "--human-authorization-recorded",
            "--controlled-account-recorded",
            "--scope-review-recorded",
            "--bundle-output-dir",
            str(bundle_dir),
        ],
    )
    assert bundle_result.exit_code == 0

    verify_result = runner.invoke(
        app,
        [
            "scoped-runtime-execution-gate-bundle-verify",
            str(bundle_dir),
            "--json-output",
            str(verification_json),
        ],
    )
    assert verify_result.exit_code == 0

    review_result = runner.invoke(
        app,
        [
            "scoped-runtime-execution-gate-bundle-review-packet",
            str(verification_json),
            "--reviewed-by",
            "human-reviewer",
            "--review-note",
            "Reviewed local bundle verification artifact only; no execution authorized.",
            "--json-output",
            str(review_json),
            "--output-file",
            str(review_markdown),
        ],
    )

    assert review_result.exit_code == 0
    assert review_json.exists()
    assert review_markdown.exists()

    data = json.loads(review_json.read_text())
    markdown = review_markdown.read_text()

    assert data["kind"] == "scoped_runtime_execution_gate_bundle_review_packet"
    assert data["review_status"] == "accepted-local-bundle-verification-no-execution"
    assert data["review_state"] == "reviewed_local_only"
    assert data["reviewed_by"] == "human-reviewer"
    assert data["can_execute_now"] is False
    assert data["network_requests_allowed"] is False
    assert data["tool_execution_allowed"] is False
    assert data["evidence_collection_allowed"] is False
    assert "# Scoped Runtime Execution Gate Bundle Review Packet" in markdown
    assert "Saved scoped runtime execution gate bundle review packet JSON" in review_result.stdout
    assert "Saved scoped runtime execution gate bundle review packet Markdown" in review_result.stdout


def test_scoped_runtime_execution_gate_bundle_handoff_packet_cli_writes_json_and_markdown(tmp_path) -> None:
    input_file = tmp_path / "request.json"
    bundle_dir = tmp_path / "bundle"
    verification_json = tmp_path / "verification.json"
    review_json = tmp_path / "review.json"
    handoff_json = tmp_path / "handoff.json"
    handoff_markdown = tmp_path / "handoff.md"
    input_file.write_text(json.dumps(_blueprint()))

    bundle_result = runner.invoke(
        app,
        [
            "scoped-runtime-execution-gate",
            str(input_file),
            "--future-authorization-requested",
            "--human-authorization-recorded",
            "--controlled-account-recorded",
            "--scope-review-recorded",
            "--bundle-output-dir",
            str(bundle_dir),
        ],
    )
    assert bundle_result.exit_code == 0

    verify_result = runner.invoke(
        app,
        [
            "scoped-runtime-execution-gate-bundle-verify",
            str(bundle_dir),
            "--json-output",
            str(verification_json),
        ],
    )
    assert verify_result.exit_code == 0

    review_result = runner.invoke(
        app,
        [
            "scoped-runtime-execution-gate-bundle-review-packet",
            str(verification_json),
            "--reviewed-by",
            "human-reviewer",
            "--review-note",
            "Reviewed local bundle verification artifact only; no execution authorized.",
            "--json-output",
            str(review_json),
        ],
    )
    assert review_result.exit_code == 0

    handoff_result = runner.invoke(
        app,
        [
            "scoped-runtime-execution-gate-bundle-handoff-packet",
            str(review_json),
            "--handoff-to",
            "future-reviewer",
            "--handoff-note",
            "Handoff for future local review only; no execution authorized.",
            "--json-output",
            str(handoff_json),
            "--output-file",
            str(handoff_markdown),
        ],
    )

    assert handoff_result.exit_code == 0
    assert handoff_json.exists()
    assert handoff_markdown.exists()

    data = json.loads(handoff_json.read_text())
    markdown = handoff_markdown.read_text()

    assert data["kind"] == "scoped_runtime_execution_gate_bundle_handoff_packet"
    assert data["handoff_status"] == "ready-local-bundle-handoff-no-execution"
    assert data["handoff_state"] == "handoff_local_only"
    assert data["handoff_to"] == "future-reviewer"
    assert data["can_execute_now"] is False
    assert data["network_requests_allowed"] is False
    assert data["tool_execution_allowed"] is False
    assert data["evidence_collection_allowed"] is False
    assert "# Scoped Runtime Execution Gate Bundle Handoff Packet" in markdown
    assert "Saved scoped runtime execution gate bundle handoff packet JSON" in handoff_result.stdout
    assert "Saved scoped runtime execution gate bundle handoff packet Markdown" in handoff_result.stdout


def test_scoped_runtime_execution_gate_bundle_handoff_checklist_cli_writes_json_and_markdown(tmp_path) -> None:
    input_file = tmp_path / "request.json"
    bundle_dir = tmp_path / "bundle"
    verification_json = tmp_path / "verification.json"
    review_json = tmp_path / "review.json"
    handoff_json = tmp_path / "handoff.json"
    checklist_json = tmp_path / "checklist.json"
    checklist_markdown = tmp_path / "checklist.md"
    input_file.write_text(json.dumps(_blueprint()))

    bundle_result = runner.invoke(
        app,
        [
            "scoped-runtime-execution-gate",
            str(input_file),
            "--future-authorization-requested",
            "--human-authorization-recorded",
            "--controlled-account-recorded",
            "--scope-review-recorded",
            "--bundle-output-dir",
            str(bundle_dir),
        ],
    )
    assert bundle_result.exit_code == 0

    verify_result = runner.invoke(
        app,
        [
            "scoped-runtime-execution-gate-bundle-verify",
            str(bundle_dir),
            "--json-output",
            str(verification_json),
        ],
    )
    assert verify_result.exit_code == 0

    review_result = runner.invoke(
        app,
        [
            "scoped-runtime-execution-gate-bundle-review-packet",
            str(verification_json),
            "--reviewed-by",
            "human-reviewer",
            "--review-note",
            "Reviewed local bundle verification artifact only; no execution authorized.",
            "--json-output",
            str(review_json),
        ],
    )
    assert review_result.exit_code == 0

    handoff_result = runner.invoke(
        app,
        [
            "scoped-runtime-execution-gate-bundle-handoff-packet",
            str(review_json),
            "--handoff-to",
            "future-reviewer",
            "--handoff-note",
            "Handoff for future local review only; no execution authorized.",
            "--json-output",
            str(handoff_json),
        ],
    )
    assert handoff_result.exit_code == 0

    checklist_result = runner.invoke(
        app,
        [
            "scoped-runtime-execution-gate-bundle-handoff-checklist",
            str(handoff_json),
            "--checked-by",
            "human-reviewer",
            "--checklist-note",
            "Checked local handoff packet only; no execution authorized.",
            "--json-output",
            str(checklist_json),
            "--output-file",
            str(checklist_markdown),
        ],
    )

    assert checklist_result.exit_code == 0
    assert checklist_json.exists()
    assert checklist_markdown.exists()

    data = json.loads(checklist_json.read_text())
    markdown = checklist_markdown.read_text()

    assert data["kind"] == "scoped_runtime_execution_gate_bundle_handoff_checklist"
    assert data["checklist_status"] == "passed-local-bundle-handoff-checklist-no-execution"
    assert data["checklist_state"] == "checked_local_only"
    assert data["checked_by"] == "human-reviewer"
    assert len(data["passed_checks"]) == len(data["required_checks"])
    assert data["failed_checks"] == []
    assert data["can_execute_now"] is False
    assert data["network_requests_allowed"] is False
    assert data["tool_execution_allowed"] is False
    assert data["evidence_collection_allowed"] is False
    assert "# Scoped Runtime Execution Gate Bundle Handoff Checklist" in markdown
    assert "Saved scoped runtime execution gate bundle handoff checklist JSON" in checklist_result.stdout
    assert "Saved scoped runtime execution gate bundle handoff checklist Markdown" in checklist_result.stdout


def test_scoped_runtime_execution_gate_bundle_handoff_checklist_summary_cli_writes_json_and_markdown(tmp_path) -> None:
    input_file = tmp_path / "request.json"
    bundle_dir = tmp_path / "bundle"
    verification_json = tmp_path / "verification.json"
    review_json = tmp_path / "review.json"
    handoff_json = tmp_path / "handoff.json"
    checklist_json = tmp_path / "checklist.json"
    summary_json = tmp_path / "summary.json"
    summary_markdown = tmp_path / "summary.md"
    input_file.write_text(json.dumps(_blueprint()))

    bundle_result = runner.invoke(
        app,
        [
            "scoped-runtime-execution-gate",
            str(input_file),
            "--future-authorization-requested",
            "--human-authorization-recorded",
            "--controlled-account-recorded",
            "--scope-review-recorded",
            "--bundle-output-dir",
            str(bundle_dir),
        ],
    )
    assert bundle_result.exit_code == 0

    verify_result = runner.invoke(
        app,
        [
            "scoped-runtime-execution-gate-bundle-verify",
            str(bundle_dir),
            "--json-output",
            str(verification_json),
        ],
    )
    assert verify_result.exit_code == 0

    review_result = runner.invoke(
        app,
        [
            "scoped-runtime-execution-gate-bundle-review-packet",
            str(verification_json),
            "--reviewed-by",
            "human-reviewer",
            "--review-note",
            "Reviewed local bundle verification artifact only; no execution authorized.",
            "--json-output",
            str(review_json),
        ],
    )
    assert review_result.exit_code == 0

    handoff_result = runner.invoke(
        app,
        [
            "scoped-runtime-execution-gate-bundle-handoff-packet",
            str(review_json),
            "--handoff-to",
            "future-reviewer",
            "--handoff-note",
            "Handoff for future local review only; no execution authorized.",
            "--json-output",
            str(handoff_json),
        ],
    )
    assert handoff_result.exit_code == 0

    checklist_result = runner.invoke(
        app,
        [
            "scoped-runtime-execution-gate-bundle-handoff-checklist",
            str(handoff_json),
            "--checked-by",
            "human-reviewer",
            "--checklist-note",
            "Checked local handoff packet only; no execution authorized.",
            "--json-output",
            str(checklist_json),
        ],
    )
    assert checklist_result.exit_code == 0

    summary_result = runner.invoke(
        app,
        [
            "scoped-runtime-execution-gate-bundle-handoff-checklist-summary",
            str(checklist_json),
            "--summarized-by",
            "human-reviewer",
            "--summary-note",
            "Summarized local checklist only; no execution authorized.",
            "--json-output",
            str(summary_json),
            "--output-file",
            str(summary_markdown),
        ],
    )

    assert summary_result.exit_code == 0
    assert summary_json.exists()
    assert summary_markdown.exists()

    data = json.loads(summary_json.read_text())
    markdown = summary_markdown.read_text()

    assert data["kind"] == "scoped_runtime_execution_gate_bundle_handoff_checklist_summary"
    assert data["summary_status"] == "summarized-local-bundle-handoff-checklist-no-execution"
    assert data["summary_state"] == "summarized_local_only"
    assert data["summarized_by"] == "human-reviewer"
    assert data["required_check_count"] == 11
    assert data["passed_check_count"] == 11
    assert data["failed_check_count"] == 0
    assert data["can_execute_now"] is False
    assert data["network_requests_allowed"] is False
    assert data["tool_execution_allowed"] is False
    assert data["evidence_collection_allowed"] is False
    assert "# Scoped Runtime Execution Gate Bundle Handoff Checklist Summary" in markdown
    assert "Saved scoped runtime execution gate bundle handoff checklist summary JSON" in summary_result.stdout
    assert "Saved scoped runtime execution gate bundle handoff checklist summary Markdown" in summary_result.stdout
