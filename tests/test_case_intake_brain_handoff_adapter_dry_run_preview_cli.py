import json

from typer.testing import CliRunner

from bugintel.cli import app
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


def test_adapter_dry_run_preview_cli_writes_json_and_markdown(tmp_path) -> None:
    manifest_file = tmp_path / "runtime-safety-manifest.json"
    json_output = tmp_path / "adapter-dry-run-preview.json"
    markdown_output = tmp_path / "adapter-dry-run-preview.md"

    manifest_file.write_text(json.dumps(_runtime_manifest()))

    result = CliRunner().invoke(
        app,
        [
            "case-intake-brain-adapter-dry-run-preview",
            str(manifest_file),
            "--target-base-url",
            "https://example-program.test",
            "--controlled-account-token-placeholder",
            "CONTROLLED_TOKEN_ONLY",
            "--path-parameter",
            "id=SYNTHETIC_USER_ID",
            "--json-output",
            str(json_output),
            "--output-file",
            str(markdown_output),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Case Intake Brain Adapter Dry-Run Preview" in result.output
    assert "Saved case intake brain adapter dry-run preview JSON" in result.output
    assert "Saved case intake brain adapter dry-run preview Markdown" in result.output

    data = json.loads(json_output.read_text())
    assert data["kind"] == "case_intake_brain_handoff_adapter_dry_run_preview"
    assert data["preview_id"] == "ADP-RSM-EG-CP-AD-AP-001"
    assert data["resolved_target_url"] == "https://example-program.test/api/admin/users/SYNTHETIC_USER_ID/permissions"
    assert "CONTROLLED_TOKEN_ONLY" in data["resolved_command_preview"]
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

    markdown = markdown_output.read_text()
    assert "# Case Intake Brain Adapter Dry-Run Preview" in markdown
    assert "## Resolved Dry-Run Command Preview" in markdown
    assert "No command execution" in markdown


def test_adapter_dry_run_preview_cli_rejects_missing_manifest_file(tmp_path) -> None:
    missing = tmp_path / "missing.json"

    result = CliRunner().invoke(
        app,
        [
            "case-intake-brain-adapter-dry-run-preview",
            str(missing),
            "--target-base-url",
            "https://example-program.test",
            "--controlled-account-token-placeholder",
            "CONTROLLED_TOKEN_ONLY",
            "--path-parameter",
            "id=SYNTHETIC_USER_ID",
        ],
    )

    assert result.exit_code != 0
    assert "runtime safety manifest file does not exist" in result.output


def test_adapter_dry_run_preview_cli_blocks_missing_path_parameter(tmp_path) -> None:
    manifest_file = tmp_path / "runtime-safety-manifest.json"
    json_output = tmp_path / "adapter-dry-run-preview.json"

    manifest_file.write_text(json.dumps(_runtime_manifest()))

    result = CliRunner().invoke(
        app,
        [
            "case-intake-brain-adapter-dry-run-preview",
            str(manifest_file),
            "--target-base-url",
            "https://example-program.test",
            "--controlled-account-token-placeholder",
            "CONTROLLED_TOKEN_ONLY",
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0, result.output
    data = json.loads(json_output.read_text())
    assert data["blocked"] is True
    assert "Missing path parameter replacement" in data["block_reason"]
    assert data["can_execute_now"] is False
