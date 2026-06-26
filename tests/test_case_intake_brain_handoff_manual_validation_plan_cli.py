import json

from typer.testing import CliRunner

from bugintel.cli import app
from tests.test_case_intake_brain_handoff_answerer import _handoff


def test_manual_validation_plan_cli_writes_json_and_markdown(tmp_path) -> None:
    handoff_file = tmp_path / "handoff.json"
    json_output = tmp_path / "manual-validation-plan.json"
    markdown_output = tmp_path / "manual-validation-plan.md"

    handoff_file.write_text(json.dumps(_handoff()))

    result = CliRunner().invoke(
        app,
        [
            "case-intake-brain-manual-validation-plan",
            str(handoff_file),
            "--json-output",
            str(json_output),
            "--output-file",
            str(markdown_output),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Case Intake Brain Manual Validation Plan" in result.output
    assert "Saved case intake brain manual validation plan JSON" in result.output
    assert "Saved case intake brain manual validation plan Markdown" in result.output

    data = json.loads(json_output.read_text())
    assert data["kind"] == "case_intake_brain_handoff_manual_validation_plan"
    assert data["validation_allowed"] is False
    assert data["runtime_execution_allowed"] is False
    assert data["report_submission_allowed"] is False
    assert data["vulnerability_confirmation_allowed"] is False
    assert data["approval_required"] is True
    assert data["read_only_required"] is True

    markdown = markdown_output.read_text()
    assert "# Case Intake Brain Manual Validation Plan" in markdown
    assert "No tool execution" in markdown


def test_manual_validation_plan_cli_rejects_missing_handoff_file(tmp_path) -> None:
    missing = tmp_path / "missing.json"

    result = CliRunner().invoke(
        app,
        [
            "case-intake-brain-manual-validation-plan",
            str(missing),
        ],
    )

    assert result.exit_code != 0
    assert "handoff file does not exist" in result.output
