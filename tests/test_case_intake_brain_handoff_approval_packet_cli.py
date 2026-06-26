import json

from typer.testing import CliRunner

from bugintel.cli import app
from bugintel.core.case_intake_brain_handoff_manual_validation_plan_exporter import (
    export_case_intake_brain_handoff_manual_validation_plan,
)
from tests.test_case_intake_brain_handoff_answerer import _handoff


def _manual_plan() -> dict:
    return export_case_intake_brain_handoff_manual_validation_plan(_handoff()).to_dict()


def test_approval_packet_cli_writes_json_and_markdown(tmp_path) -> None:
    plan_file = tmp_path / "manual-validation-plan.json"
    json_output = tmp_path / "approval-packet.json"
    markdown_output = tmp_path / "approval-packet.md"

    plan_file.write_text(json.dumps(_manual_plan()))

    result = CliRunner().invoke(
        app,
        [
            "case-intake-brain-approval-packet",
            str(plan_file),
            "--endpoint",
            "/api/admin/users/{id}/permissions",
            "--json-output",
            str(json_output),
            "--output-file",
            str(markdown_output),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Case Intake Brain Approval Packet" in result.output
    assert "Saved case intake brain approval packet JSON" in result.output
    assert "Saved case intake brain approval packet Markdown" in result.output

    data = json.loads(json_output.read_text())
    assert data["kind"] == "case_intake_brain_handoff_approval_packet"
    assert data["endpoint"] == "/api/admin/users/{id}/permissions"
    assert data["approved"] is False
    assert data["approval_status"] == "pending-human-approval"
    assert data["validation_allowed"] is False
    assert data["runtime_execution_allowed"] is False
    assert data["tool_execution_allowed"] is False
    assert data["browser_execution_allowed"] is False
    assert data["evidence_collection_allowed"] is False
    assert data["target_mutation_allowed"] is False
    assert data["report_submission_allowed"] is False
    assert data["vulnerability_confirmation_allowed"] is False

    markdown = markdown_output.read_text()
    assert "# Case Intake Brain Approval Packet" in markdown
    assert "## Approval Checkbox" in markdown
    assert "No tool execution" in markdown


def test_approval_packet_cli_defaults_to_first_endpoint(tmp_path) -> None:
    plan_file = tmp_path / "manual-validation-plan.json"
    json_output = tmp_path / "approval-packet.json"

    plan_file.write_text(json.dumps(_manual_plan()))

    result = CliRunner().invoke(
        app,
        [
            "case-intake-brain-approval-packet",
            str(plan_file),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0, result.output
    data = json.loads(json_output.read_text())
    assert data["approval_id"] == "AP-001"
    assert data["endpoint"] == "/api/admin/users/{id}/permissions"


def test_approval_packet_cli_rejects_missing_plan_file(tmp_path) -> None:
    missing = tmp_path / "missing.json"

    result = CliRunner().invoke(
        app,
        [
            "case-intake-brain-approval-packet",
            str(missing),
        ],
    )

    assert result.exit_code != 0
    assert "manual validation plan file does not exist" in result.output
