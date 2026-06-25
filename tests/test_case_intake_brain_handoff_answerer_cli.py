import json

from typer.testing import CliRunner

from bugintel.cli import app
from bugintel.core.bug_bounty_case_intake import build_bug_bounty_case_intake_workflow
from bugintel.core.bug_bounty_case_intake_brain_handoff import build_case_intake_brain_handoff


runner = CliRunner()


def _write_handoff(tmp_path):
    intake = build_bug_bounty_case_intake_workflow(
        """
        GET /api/status
        GET /api/admin/users/{id}/permissions
        GET /api/files/{id}/download
        """,
        target_name="demo-program",
        top_n=3,
    ).to_dict()
    handoff = build_case_intake_brain_handoff(intake).to_dict()

    handoff_file = tmp_path / "brain-handoff.json"
    handoff_file.write_text(json.dumps(handoff, indent=2), encoding="utf-8")
    return handoff_file


def test_case_intake_brain_answer_cli_writes_json_and_markdown(tmp_path):
    handoff_file = _write_handoff(tmp_path)
    json_output = tmp_path / "answer.json"
    markdown_output = tmp_path / "answer.md"

    result = runner.invoke(
        app,
        [
            "case-intake-brain-answer",
            str(handoff_file),
            "What evidence is missing?",
            "--json-output",
            str(json_output),
            "--output-file",
            str(markdown_output),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Case Intake Brain Handoff Answer" in result.output
    assert "Saved case intake brain answer JSON" in result.output
    assert "Safety:" in result.output

    data = json.loads(json_output.read_text(encoding="utf-8"))
    assert data["kind"] == "case_intake_brain_handoff_answer"
    assert data["route"] == "missing-evidence"
    assert data["target_name"] == "demo-program"
    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["report_submission"] is False

    markdown = markdown_output.read_text(encoding="utf-8")
    assert "# Case Intake Brain Handoff Answer" in markdown
    assert "## Safety" in markdown


def test_case_intake_brain_answer_cli_rejects_missing_file(tmp_path):
    result = runner.invoke(
        app,
        [
            "case-intake-brain-answer",
            str(tmp_path / "missing.json"),
            "What should I test first?",
        ],
    )

    assert result.exit_code == 1
    assert "Handoff file not found" in result.output
