import json

from typer.testing import CliRunner

from bugintel.cli import app
from tests.test_case_intake_brain_handoff_answerer import _handoff


def test_question_set_cli_writes_json_and_markdown(tmp_path) -> None:
    handoff_file = tmp_path / "handoff.json"
    json_output = tmp_path / "question-set.json"
    markdown_output = tmp_path / "question-set.md"

    handoff_file.write_text(json.dumps(_handoff()))

    result = CliRunner().invoke(
        app,
        [
            "case-intake-brain-question-set",
            str(handoff_file),
            "--json-output",
            str(json_output),
            "--output-file",
            str(markdown_output),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Case Intake Brain Handoff Question Set" in result.output
    assert "Saved case intake brain question-set JSON" in result.output
    assert "Saved case intake brain question-set Markdown" in result.output

    data = json.loads(json_output.read_text())
    assert data["kind"] == "case_intake_brain_handoff_question_set"
    assert data["answer_count"] == 5
    assert data["validation_allowed"] is False
    assert data["runtime_execution_allowed"] is False
    assert data["report_submission_allowed"] is False
    assert data["vulnerability_confirmation_allowed"] is False

    markdown = markdown_output.read_text()
    assert "What should I test first?" in markdown
    assert "No tool execution" in markdown


def test_question_set_cli_rejects_missing_handoff_file(tmp_path) -> None:
    missing = tmp_path / "missing.json"

    result = CliRunner().invoke(
        app,
        [
            "case-intake-brain-question-set",
            str(missing),
        ],
    )

    assert result.exit_code != 0
    assert "handoff file does not exist" in result.output
