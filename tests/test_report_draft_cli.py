import json

from typer.testing import CliRunner

from bugintel.cli import app
from bugintel.core.orchestrator import create_orchestration_plan


runner = CliRunner()


def test_report_draft_cli_writes_markdown_and_json(tmp_path):
    plan = create_orchestration_plan(
        target_name="demo",
        endpoints=["/api/accounts/123/users/{id}/permissions"],
    )

    orchestration_file = tmp_path / "orchestration.json"
    output_file = tmp_path / "report-draft.md"
    json_output = tmp_path / "report-draft.json"

    orchestration_file.write_text(json.dumps(plan.to_dict()))

    result = runner.invoke(
        app,
        [
            "report-draft",
            str(orchestration_file),
            "--output-file",
            str(output_file),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0
    assert "Report Draft" in result.output
    assert "Report Draft Sections" in result.output
    assert "Saved report draft Markdown" in result.output
    assert "Saved report draft JSON" in result.output

    markdown = output_file.read_text()
    data = json.loads(json_output.read_text())

    assert "# Blackhole Report Draft: demo" in markdown
    assert "## Scope and Authorization" in markdown
    assert "## Evidence Requirements" in markdown
    assert "controlled-account-role-matrix" in markdown
    assert data["planning_only"] is True
    assert data["execution_state"] == "not_executed"
    assert data["sections"]


def test_report_draft_cli_prints_markdown_without_outputs(tmp_path):
    plan = create_orchestration_plan(
        target_name="demo",
        endpoints=["/api/files/{id}/download"],
    )

    orchestration_file = tmp_path / "orchestration.json"
    orchestration_file.write_text(json.dumps(plan.to_dict()))

    result = runner.invoke(app, ["report-draft", str(orchestration_file)])

    assert result.exit_code == 0
    assert "# Blackhole Report Draft: demo" in result.output
    assert "file-access-control-evidence" in result.output
    assert "Safety:" in result.output


def test_report_draft_cli_missing_file_exits_nonzero(tmp_path):
    missing = tmp_path / "missing.json"

    result = runner.invoke(app, ["report-draft", str(missing)])

    assert result.exit_code == 1
    assert "Orchestration JSON not found" in result.output


def test_report_draft_cli_invalid_json_exits_nonzero(tmp_path):
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{not json")

    result = runner.invoke(app, ["report-draft", str(bad_file)])

    assert result.exit_code == 2
    assert "Invalid orchestration JSON" in result.output
