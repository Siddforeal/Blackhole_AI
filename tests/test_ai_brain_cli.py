import json

from typer.testing import CliRunner

from bugintel.cli import app
from bugintel.core.orchestrator import create_orchestration_plan
from bugintel.core.research_state import build_research_state_from_orchestration


runner = CliRunner()


def _write_research_state(tmp_path, endpoints):
    plan = create_orchestration_plan(target_name="demo", endpoints=endpoints)
    state = build_research_state_from_orchestration(plan.to_dict())

    path = tmp_path / "research-state.json"
    path.write_text(json.dumps(state.to_dict()))
    return path


def test_ai_brain_cli_writes_markdown_and_json(tmp_path):
    research_state_file = _write_research_state(
        tmp_path,
        ["/api/accounts/123/users/{id}/permissions", "/api/status"],
    )
    output_file = tmp_path / "ai-brain-plan.md"
    json_output = tmp_path / "ai-brain-plan.json"

    result = runner.invoke(
        app,
        [
            "ai-brain",
            str(research_state_file),
            "--output-file",
            str(output_file),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0
    assert "AI Brain Plan" in result.output
    assert "AI Brain Focus Queue" in result.output
    assert "AI Brain Safety Gates" in result.output
    assert "Provider execution" in result.output
    assert "Saved AI brain plan Markdown" in result.output
    assert "Saved AI brain plan JSON" in result.output

    markdown = output_file.read_text()
    data = json.loads(json_output.read_text())

    assert "# Blackhole AI Brain Plan: demo" in markdown
    assert "Planning-only AI brain interface" in markdown
    assert "Prepare approval-gated evidence collection" in markdown
    assert data["planning_only"] is True
    assert data["execution_state"] == "not_executed"
    assert data["provider_execution_enabled"] is False
    assert data["focus_queue"]


def test_ai_brain_cli_prints_markdown_without_outputs(tmp_path):
    research_state_file = _write_research_state(
        tmp_path,
        ["/api/files/{id}/download"],
    )

    result = runner.invoke(app, ["ai-brain", str(research_state_file)])

    assert result.exit_code == 0
    assert "# Blackhole AI Brain Plan: demo" in result.output
    assert "file-access-boundary-hypothesis" in result.output
    assert "Safety:" in result.output


def test_ai_brain_cli_missing_file_exits_nonzero(tmp_path):
    missing = tmp_path / "missing.json"

    result = runner.invoke(app, ["ai-brain", str(missing)])

    assert result.exit_code == 1
    assert "Research-state JSON not found" in result.output


def test_ai_brain_cli_invalid_json_exits_nonzero(tmp_path):
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{not json")

    result = runner.invoke(app, ["ai-brain", str(bad_file)])

    assert result.exit_code == 2
    assert "Invalid research-state JSON" in result.output
