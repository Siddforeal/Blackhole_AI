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
from tests.test_case_intake_brain_handoff_answerer import _handoff


def _approval_decision() -> dict:
    plan = export_case_intake_brain_handoff_manual_validation_plan(_handoff()).to_dict()
    packet = export_case_intake_brain_handoff_approval_packet(
        plan,
        endpoint="/api/admin/users/{id}/permissions",
    ).to_dict()
    return record_case_intake_brain_handoff_approval_decision(
        packet,
        decision="approved",
        decided_by="sidd",
        reason="Approved read-only planning only with controlled accounts.",
    ).to_dict()


def test_read_only_command_proposal_cli_writes_json_and_markdown(tmp_path) -> None:
    decision_file = tmp_path / "approval-decision.json"
    json_output = tmp_path / "command-proposal.json"
    markdown_output = tmp_path / "command-proposal.md"

    decision_file.write_text(json.dumps(_approval_decision()))

    result = CliRunner().invoke(
        app,
        [
            "case-intake-brain-read-only-command-proposal",
            str(decision_file),
            "--command-family",
            "curl",
            "--json-output",
            str(json_output),
            "--output-file",
            str(markdown_output),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Case Intake Brain Read-Only Command Proposal" in result.output
    assert "Saved case intake brain read-only command proposal JSON" in result.output
    assert "Saved case intake brain read-only command proposal Markdown" in result.output

    data = json.loads(json_output.read_text())
    assert data["kind"] == "case_intake_brain_handoff_read_only_command_proposal"
    assert data["proposal_id"] == "CP-AD-AP-001"
    assert data["command_family"] == "curl"
    assert "{{TARGET_BASE_URL}}" in data["proposed_command"]
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
    assert "# Case Intake Brain Read-Only Command Proposal" in markdown
    assert "## Proposed Command" in markdown
    assert "No command execution" in markdown


def test_read_only_command_proposal_cli_rejects_missing_decision_file(tmp_path) -> None:
    missing = tmp_path / "missing.json"

    result = CliRunner().invoke(
        app,
        [
            "case-intake-brain-read-only-command-proposal",
            str(missing),
            "--command-family",
            "curl",
        ],
    )

    assert result.exit_code != 0
    assert "approval decision file does not exist" in result.output


def test_read_only_command_proposal_cli_blocks_unsupported_family(tmp_path) -> None:
    decision_file = tmp_path / "approval-decision.json"
    json_output = tmp_path / "command-proposal.json"

    decision_file.write_text(json.dumps(_approval_decision()))

    result = CliRunner().invoke(
        app,
        [
            "case-intake-brain-read-only-command-proposal",
            str(decision_file),
            "--command-family",
            "bash",
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0, result.output
    data = json.loads(json_output.read_text())
    assert data["blocked"] is True
    assert "Unsupported command family" in data["block_reason"]
    assert data["execution_allowed"] is False
