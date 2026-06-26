import json

from typer.testing import CliRunner

from bugintel.cli import app
from bugintel.core.case_intake_brain_handoff_approval_decision_recorder import (
    record_case_intake_brain_handoff_approval_decision,
)
from bugintel.core.case_intake_brain_handoff_approval_packet_exporter import (
    export_case_intake_brain_handoff_approval_packet,
)
from bugintel.core.case_intake_brain_handoff_manual_validation_plan_exporter import (
    export_case_intake_brain_handoff_manual_validation_plan,
)
from bugintel.core.case_intake_brain_handoff_read_only_command_proposal_exporter import (
    export_case_intake_brain_handoff_read_only_command_proposal,
)
from tests.test_case_intake_brain_handoff_answerer import _handoff


def _command_proposal() -> dict:
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
    return export_case_intake_brain_handoff_read_only_command_proposal(
        approval_decision,
        command_family="curl",
    ).to_dict()


def test_execution_approval_gate_cli_writes_json_and_markdown(tmp_path) -> None:
    proposal_file = tmp_path / "command-proposal.json"
    json_output = tmp_path / "execution-approval.json"
    markdown_output = tmp_path / "execution-approval.md"

    proposal_file.write_text(json.dumps(_command_proposal()))

    result = CliRunner().invoke(
        app,
        [
            "case-intake-brain-execution-approval-gate",
            str(proposal_file),
            "--decision",
            "approved",
            "--decided-by",
            "sidd",
            "--reason",
            "Approved only for future controlled read-only execution adapter preview.",
            "--json-output",
            str(json_output),
            "--output-file",
            str(markdown_output),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Case Intake Brain Execution Approval Gate" in result.output
    assert "Saved case intake brain execution approval gate JSON" in result.output
    assert "Saved case intake brain execution approval gate Markdown" in result.output

    data = json.loads(json_output.read_text())
    assert data["kind"] == "case_intake_brain_handoff_execution_approval_gate"
    assert data["gate_id"] == "EG-CP-AD-AP-001"
    assert data["execution_decision"] == "approved"
    assert data["approved"] is True
    assert data["human_execution_approval_recorded"] is True
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

    markdown = markdown_output.read_text()
    assert "# Case Intake Brain Execution Approval Gate" in markdown
    assert "## Proposed Command Under Review" in markdown
    assert "No command execution" in markdown


def test_execution_approval_gate_cli_rejects_missing_proposal_file(tmp_path) -> None:
    missing = tmp_path / "missing.json"

    result = CliRunner().invoke(
        app,
        [
            "case-intake-brain-execution-approval-gate",
            str(missing),
            "--decision",
            "approved",
            "--decided-by",
            "sidd",
        ],
    )

    assert result.exit_code != 0
    assert "command proposal file does not exist" in result.output


def test_execution_approval_gate_cli_blocks_invalid_decision(tmp_path) -> None:
    proposal_file = tmp_path / "command-proposal.json"
    json_output = tmp_path / "execution-approval.json"

    proposal_file.write_text(json.dumps(_command_proposal()))

    result = CliRunner().invoke(
        app,
        [
            "case-intake-brain-execution-approval-gate",
            str(proposal_file),
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
    assert data["execution_decision"] == "maybe"
    assert "Execution approval decision must be one of" in data["original_proposal_block_reason"]
    assert data["can_execute_now"] is False
