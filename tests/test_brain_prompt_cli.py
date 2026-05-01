import json

from typer.testing import CliRunner

from bugintel.cli import app
from bugintel.core.ai_brain import build_ai_brain_plan
from bugintel.core.orchestrator import create_orchestration_plan
from bugintel.core.research_state import build_research_state_from_orchestration


runner = CliRunner()


def _write_ai_brain_plan(tmp_path, endpoints):
    orchestration = create_orchestration_plan(target_name="demo", endpoints=endpoints)
    research_state = build_research_state_from_orchestration(orchestration.to_dict())
    ai_brain = build_ai_brain_plan(research_state.to_dict())

    path = tmp_path / "ai-brain.json"
    path.write_text(json.dumps(ai_brain.to_dict()))
    return path


def test_brain_prompt_cli_writes_markdown_and_json(tmp_path):
    ai_brain_file = _write_ai_brain_plan(
        tmp_path,
        ["/api/accounts/123/users/{id}/permissions"],
    )
    output_file = tmp_path / "brain-prompt.md"
    json_output = tmp_path / "brain-prompt.json"

    result = runner.invoke(
        app,
        [
            "brain-prompt",
            str(ai_brain_file),
            "--output-file",
            str(output_file),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0
    assert "LLM Brain Prompt Package" in result.output
    assert "Prompt Messages" in result.output
    assert "Provider execution" in result.output
    assert "Saved brain prompt Markdown" in result.output
    assert "Saved brain prompt JSON" in result.output

    markdown = output_file.read_text()
    data = json.loads(json_output.read_text())

    assert "# Blackhole LLM Brain Prompt Package: demo" in markdown
    assert "Provider execution is disabled" in markdown
    assert "authorization-boundary-hypothesis" in markdown
    assert data["planning_only"] is True
    assert data["provider_execution_enabled"] is False
    assert data["messages"]


def test_brain_prompt_cli_prints_markdown_without_outputs(tmp_path):
    ai_brain_file = _write_ai_brain_plan(
        tmp_path,
        ["/api/files/{id}/download"],
    )

    result = runner.invoke(app, ["brain-prompt", str(ai_brain_file)])

    assert result.exit_code == 0
    assert "# Blackhole LLM Brain Prompt Package: demo" in result.output
    assert "file-access-boundary-hypothesis" in result.output
    assert "Safety:" in result.output


def test_brain_prompt_cli_missing_file_exits_nonzero(tmp_path):
    missing = tmp_path / "missing.json"

    result = runner.invoke(app, ["brain-prompt", str(missing)])

    assert result.exit_code == 1
    assert "AI brain JSON not found" in result.output


def test_brain_prompt_cli_invalid_json_exits_nonzero(tmp_path):
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{not json")

    result = runner.invoke(app, ["brain-prompt", str(bad_file)])

    assert result.exit_code == 2
    assert "Invalid AI brain JSON" in result.output
