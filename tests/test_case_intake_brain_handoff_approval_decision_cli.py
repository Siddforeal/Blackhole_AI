import json

from typer.testing import CliRunner

from bugintel.cli import app
from bugintel.core.case_intake_brain_handoff_approval_packet_exporter import (
    export_case_intake_brain_handoff_approval_packet,
)
from bugintel.core.case_intake_brain_handoff_manual_validation_plan_exporter import (
    export_case_intake_brain_handoff_manual_validation_plan,
)
from tests.test_case_intake_brain_handoff_answerer import _handoff


def _approval_packet() -> dict:
    plan = export_case_intake_brain_handoff_manual_validation_plan(_handoff()).to_dict()
    return export_case_intake_brain_handoff_approval_packet(
        plan,
        endpoint="/api/admin/users/{id}/permissions",
    ).to_dict()


def test_approval_decision_cli_writes_json_and_markdown(tmp_path) -> None:
    packet_file = tmp_path / "approval-packet.json"
    json_output = tmp_path / "approval-decision.json"
    markdown_output = tmp_path / "approval-decision.md"

    packet_file.write_text(json.dumps(_approval_packet()))

    result = CliRunner().invoke(
        app,
        [
            "case-intake-brain-approval-decision",
            str(packet_file),
            "--decision",
            "approved",
            "--decided-by",
            "sidd",
            "--reason",
            "Approved read-only planning only with controlled accounts.",
            "--json-output",
            str(json_output),
            "--output-file",
            str(markdown_output),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Case Intake Brain Approval Decision" in result.output
    assert "Saved case intake brain approval decision JSON" in result.output
    assert "Saved case intake brain approval decision Markdown" in result.output

    data = json.loads(json_output.read_text())
    assert data["kind"] == "case_intake_brain_handoff_approval_decision"
    assert data["approval_id"] == "AP-001"
    assert data["decision"] == "approved"
    assert data["approved"] is True
    assert data["can_proceed_to_execution"] is False
    assert data["validation_allowed"] is False
    assert data["runtime_execution_allowed"] is False
    assert data["tool_execution_allowed"] is False
    assert data["browser_execution_allowed"] is False
    assert data["evidence_collection_allowed"] is False
    assert data["target_mutation_allowed"] is False
    assert data["report_submission_allowed"] is False
    assert data["vulnerability_confirmation_allowed"] is False

    markdown = markdown_output.read_text()
    assert "# Case Intake Brain Approval Decision" in markdown
    assert "## Reason" in markdown
    assert "No tool execution" in markdown


def test_approval_decision_cli_rejects_missing_packet_file(tmp_path) -> None:
    missing = tmp_path / "missing.json"

    result = CliRunner().invoke(
        app,
        [
            "case-intake-brain-approval-decision",
            str(missing),
            "--decision",
            "approved",
            "--decided-by",
            "sidd",
        ],
    )

    assert result.exit_code != 0
    assert "approval packet file does not exist" in result.output


def test_approval_decision_cli_blocks_invalid_decision(tmp_path) -> None:
    packet_file = tmp_path / "approval-packet.json"
    json_output = tmp_path / "approval-decision.json"

    packet_file.write_text(json.dumps(_approval_packet()))

    result = CliRunner().invoke(
        app,
        [
            "case-intake-brain-approval-decision",
            str(packet_file),
            "--decision",
            "maybe",
            "--decided-by",
            "sidd",
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0, result.output
    data = json.loads(json_output.read_text())
    assert data["blocked"] is True
    assert data["decision"] == "maybe"
    assert "Decision must be one of" in data["packet_block_reason"]
    assert data["can_proceed_to_execution"] is False
