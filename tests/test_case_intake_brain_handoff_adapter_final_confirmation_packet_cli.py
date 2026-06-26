import json

from typer.testing import CliRunner

from bugintel.cli import app
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


def _dry_run_preview() -> dict:
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
    return export_case_intake_brain_handoff_adapter_dry_run_preview(
        runtime_manifest,
        target_base_url="https://example-program.test",
        controlled_account_token_placeholder="CONTROLLED_TOKEN_ONLY",
        path_parameters=["id=SYNTHETIC_USER_ID"],
    ).to_dict()


def test_adapter_final_confirmation_cli_writes_json_and_markdown(tmp_path) -> None:
    preview_file = tmp_path / "adapter-dry-run-preview.json"
    json_output = tmp_path / "adapter-final-confirmation.json"
    markdown_output = tmp_path / "adapter-final-confirmation.md"

    preview_file.write_text(json.dumps(_dry_run_preview()))

    result = CliRunner().invoke(
        app,
        [
            "case-intake-brain-adapter-final-confirmation",
            str(preview_file),
            "--decision",
            "confirmed",
            "--confirmed-by",
            "human-reviewer",
            "--reason",
            "Final human review confirms dry-run preview is ready for future scoped adapter only.",
            "--json-output",
            str(json_output),
            "--output-file",
            str(markdown_output),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Case Intake Brain Adapter Final Confirmation Packet" in result.output
    assert "Saved case intake brain adapter final confirmation JSON" in result.output
    assert "Saved case intake brain adapter final confirmation Markdown" in result.output

    data = json.loads(json_output.read_text())
    assert data["kind"] == "case_intake_brain_handoff_adapter_final_confirmation_packet"
    assert data["confirmation_id"] == "AFC-ADP-RSM-EG-CP-AD-AP-001"
    assert data["final_confirmation_decision"] == "confirmed"
    assert data["final_confirmation_status"] == "confirmed-no-execution-authorized"
    assert data["confirmed"] is True
    assert data["human_final_confirmation_recorded"] is True
    assert data["dry_run_only"] is True
    assert data["can_execute_now"] is False
    assert data["final_confirmation_allows_execution"] is False
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
    assert "# Case Intake Brain Adapter Final Confirmation Packet" in markdown
    assert "## Resolved Dry-Run Command Reviewed" in markdown
    assert "No command execution" in markdown


def test_adapter_final_confirmation_cli_rejects_missing_preview_file(tmp_path) -> None:
    missing = tmp_path / "missing.json"

    result = CliRunner().invoke(
        app,
        [
            "case-intake-brain-adapter-final-confirmation",
            str(missing),
            "--decision",
            "confirmed",
            "--confirmed-by",
            "human-reviewer",
        ],
    )

    assert result.exit_code != 0
    assert "adapter dry-run preview file does not exist" in result.output


def test_adapter_final_confirmation_cli_blocks_invalid_decision(tmp_path) -> None:
    preview_file = tmp_path / "adapter-dry-run-preview.json"
    json_output = tmp_path / "adapter-final-confirmation.json"

    preview_file.write_text(json.dumps(_dry_run_preview()))

    result = CliRunner().invoke(
        app,
        [
            "case-intake-brain-adapter-final-confirmation",
            str(preview_file),
            "--decision",
            "maybe",
            "--confirmed-by",
            "human-reviewer",
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0, result.output
    data = json.loads(json_output.read_text())
    assert data["blocked"] is True
    assert data["final_confirmation_decision"] == "maybe"
    assert "Final confirmation decision must be one of" in data["source_preview_block_reason"]
    assert data["can_execute_now"] is False
