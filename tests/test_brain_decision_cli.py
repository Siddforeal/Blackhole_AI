import json

from typer.testing import CliRunner

from bugintel.cli import app
from bugintel.core.ai_brain import build_ai_brain_plan
from bugintel.core.brain_prompt import build_brain_prompt_package
from bugintel.core.brain_review import build_brain_review
from bugintel.core.orchestrator import create_orchestration_plan
from bugintel.core.research_state import build_research_state_from_orchestration


runner = CliRunner()


def _write_brain_review(tmp_path, endpoints):
    orchestration = create_orchestration_plan(target_name="demo", endpoints=endpoints)
    research_state = build_research_state_from_orchestration(orchestration.to_dict())
    ai_brain = build_ai_brain_plan(research_state.to_dict())
    prompt = build_brain_prompt_package(ai_brain.to_dict())
    review = build_brain_review(prompt.to_dict())

    path = tmp_path / "brain-review.json"
    path.write_text(json.dumps(review.to_dict()))
    return path


def test_brain_decision_cli_writes_markdown_and_json(tmp_path):
    review_file = _write_brain_review(
        tmp_path,
        ["/api/accounts/123/users/{id}/permissions"],
    )
    output_file = tmp_path / "brain-decision.md"
    json_output = tmp_path / "brain-decision.json"

    result = runner.invoke(
        app,
        [
            "brain-decision",
            str(review_file),
            "--output-file",
            str(output_file),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0
    assert "Brain Decision Gate" in result.output
    assert "Decision Blockers" in result.output
    assert "Saved brain decision Markdown" in result.output
    assert "Saved brain decision JSON" in result.output

    markdown = output_file.read_text()
    data = json.loads(json_output.read_text())

    assert "# Blackhole Brain Decision Gate: demo" in markdown
    assert "scope-confirmation-required" in markdown
    assert data["planning_only"] is True
    assert data["reportable"] is False
    assert data["decision"] == "blocked-pending-scope-and-controls"


def test_brain_decision_cli_prints_markdown_without_outputs(tmp_path):
    review_file = _write_brain_review(
        tmp_path,
        ["/api/files/{id}/download"],
    )

    result = runner.invoke(app, ["brain-decision", str(review_file)])

    assert result.exit_code == 0
    assert "# Blackhole Brain Decision Gate: demo" in result.output
    assert "Safety:" in result.output


def test_brain_decision_cli_missing_file_exits_nonzero(tmp_path):
    missing = tmp_path / "missing.json"

    result = runner.invoke(app, ["brain-decision", str(missing)])

    assert result.exit_code == 1
    assert "Brain review JSON not found" in result.output


def test_brain_decision_cli_invalid_json_exits_nonzero(tmp_path):
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{not json")

    result = runner.invoke(app, ["brain-decision", str(bad_file)])

    assert result.exit_code == 2
    assert "Invalid brain review JSON" in result.output
