import json

from typer.testing import CliRunner

from bugintel.cli import app
from bugintel.core.orchestrator import create_orchestration_plan
from bugintel.core.research_state import build_research_state_from_orchestration


runner = CliRunner()


def _write_research_state(tmp_path):
    orchestration = create_orchestration_plan(
        target_name="demo",
        endpoints=["/api/accounts/123/users/{id}/permissions"],
    )
    state = build_research_state_from_orchestration(orchestration.to_dict())

    path = tmp_path / "research-state.json"
    path.write_text(json.dumps(state.to_dict()))
    return path


def test_research_state_update_cli_writes_markdown_and_json(tmp_path):
    state_file = _write_research_state(tmp_path)
    output_file = tmp_path / "update.md"
    json_output = tmp_path / "update.json"

    result = runner.invoke(
        app,
        [
            "research-state-update",
            str(state_file),
            "--endpoint",
            "/api/accounts/123/users/{id}/permissions",
            "--validation-result",
            "supported",
            "--note",
            "Validated with controlled accounts.",
            "--output-file",
            str(output_file),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0
    assert "Research State Update Plan" in result.output
    assert "Proposed State Updates" in result.output
    assert output_file.exists()
    assert json_output.exists()

    data = json.loads(json_output.read_text())

    assert data["target_name"] == "demo"
    assert data["validation_result"] == "supported"
    assert data["planning_only"] is True
    assert any(action["new_value"] == "report-candidate" for action in data["actions"])
    assert any(action["new_value"] == "Validated with controlled accounts." for action in data["actions"])


def test_research_state_update_cli_invalid_result_exits_nonzero(tmp_path):
    state_file = _write_research_state(tmp_path)

    result = runner.invoke(
        app,
        [
            "research-state-update",
            str(state_file),
            "--endpoint",
            "/api/accounts/123/users/{id}/permissions",
            "--validation-result",
            "confirmed",
        ],
    )

    assert result.exit_code == 2
    assert "Invalid validation result" in result.output


def test_research_state_update_cli_missing_file_exits_nonzero(tmp_path):
    result = runner.invoke(
        app,
        [
            "research-state-update",
            str(tmp_path / "missing.json"),
            "--endpoint",
            "/api/x",
            "--validation-result",
            "supported",
        ],
    )

    assert result.exit_code == 1
    assert "Research-state JSON not found" in result.output
