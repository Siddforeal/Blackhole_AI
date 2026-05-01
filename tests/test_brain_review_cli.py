import json

from typer.testing import CliRunner

from bugintel.cli import app
from bugintel.core.ai_brain import build_ai_brain_plan
from bugintel.core.brain_prompt import build_brain_prompt_package
from bugintel.core.orchestrator import create_orchestration_plan
from bugintel.core.research_state import build_research_state_from_orchestration


runner = CliRunner()


def _write_brain_prompt(tmp_path, endpoints):
    orchestration = create_orchestration_plan(target_name="demo", endpoints=endpoints)
    research_state = build_research_state_from_orchestration(orchestration.to_dict())
    ai_brain = build_ai_brain_plan(research_state.to_dict())
    prompt = build_brain_prompt_package(ai_brain.to_dict())

    path = tmp_path / "brain-prompt.json"
    path.write_text(json.dumps(prompt.to_dict()))
    return path


def test_brain_review_cli_writes_markdown_and_json(tmp_path):
    prompt_file = _write_brain_prompt(
        tmp_path,
        ["/api/accounts/123/users/{id}/permissions"],
    )
    output_file = tmp_path / "brain-review.md"
    json_output = tmp_path / "brain-review.json"

    result = runner.invoke(
        app,
        [
            "brain-review",
            str(prompt_file),
            "--output-file",
            str(output_file),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0
    assert "Brain Review" in result.output
    assert "Brain Review Sections" in result.output
    assert "Saved brain review Markdown" in result.output
    assert "Saved brain review JSON" in result.output

    markdown = output_file.read_text()
    data = json.loads(json_output.read_text())

    assert "# Blackhole Brain Review: demo" in markdown
    assert "Recommended Focus Endpoint" in markdown
    assert "authorization-boundary-hypothesis" in markdown
    assert data["planning_only"] is True
    assert data["provider_execution_enabled"] is False
    assert data["sections"]


def test_brain_review_cli_prints_markdown_without_outputs(tmp_path):
    prompt_file = _write_brain_prompt(
        tmp_path,
        ["/api/files/{id}/download"],
    )

    result = runner.invoke(app, ["brain-review", str(prompt_file)])

    assert result.exit_code == 0
    assert "# Blackhole Brain Review: demo" in result.output
    assert "file-access-boundary-hypothesis" in result.output
    assert "Safety:" in result.output


def test_brain_review_cli_missing_file_exits_nonzero(tmp_path):
    missing = tmp_path / "missing.json"

    result = runner.invoke(app, ["brain-review", str(missing)])

    assert result.exit_code == 1
    assert "Brain prompt JSON not found" in result.output


def test_brain_review_cli_invalid_json_exits_nonzero(tmp_path):
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{not json")

    result = runner.invoke(app, ["brain-review", str(bad_file)])

    assert result.exit_code == 2
    assert "Invalid brain prompt JSON" in result.output
