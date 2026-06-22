import json

from typer.testing import CliRunner

from bugintel.cli import app
from bugintel.core.bug_bounty_case_intake import build_bug_bounty_case_intake_workflow


runner = CliRunner()


def test_case_intake_brain_handoff_cli_writes_json(tmp_path):
    intake_file = tmp_path / "intake.json"
    output_file = tmp_path / "handoff.json"

    intake = build_bug_bounty_case_intake_workflow(
        """
        GET /api/status
        GET /api/admin/users/{id}/permissions
        GET /api/files/{id}/download
        """,
        target_name="demo-program",
        top_n=3,
    ).to_dict()
    intake_file.write_text(json.dumps(intake), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "case-intake-brain-handoff",
            str(intake_file),
            "--json-output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0
    assert "Case Intake Brain Handoff" in result.output
    assert "Brain Focus Endpoints" in result.output
    assert "Brain questions" in result.output
    assert "planning-only" in result.output
    assert output_file.exists()

    data = json.loads(output_file.read_text())
    assert data["kind"] == "case_intake_brain_handoff"
    assert data["status"] == "ready-for-brain-case-context"
    assert data["focus_endpoint_count"] == 2
    assert data["brain_questions"]
    assert data["safety"]["network_requests"] is False
    assert data["safety"]["tool_execution"] is False


def test_case_intake_brain_handoff_cli_missing_file_exits_nonzero(tmp_path):
    missing = tmp_path / "missing.json"

    result = runner.invoke(app, ["case-intake-brain-handoff", str(missing)])

    assert result.exit_code == 1
    assert "Input file not found" in result.output
