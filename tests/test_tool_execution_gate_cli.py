import json

from typer.testing import CliRunner

from bugintel.cli import app
from bugintel.core.ai_brain import build_ai_brain_plan
from bugintel.core.brain_approval import build_brain_approval_packet
from bugintel.core.brain_decision import build_brain_decision_gate
from bugintel.core.brain_prompt import build_brain_prompt_package
from bugintel.core.brain_review import build_brain_review
from bugintel.core.orchestrator import create_orchestration_plan
from bugintel.core.research_state import build_research_state_from_orchestration
from bugintel.core.tool_request_manifest import build_tool_request_manifest


runner = CliRunner()


def _write_manifest(tmp_path, endpoints):
    orchestration = create_orchestration_plan(target_name="demo", endpoints=endpoints)
    research_state = build_research_state_from_orchestration(orchestration.to_dict())
    ai_brain = build_ai_brain_plan(research_state.to_dict())
    prompt = build_brain_prompt_package(ai_brain.to_dict())
    review = build_brain_review(prompt.to_dict())
    decision = build_brain_decision_gate(review.to_dict())
    approval = build_brain_approval_packet(decision.to_dict())
    manifest = build_tool_request_manifest(approval.to_dict())

    path = tmp_path / "tool-request-manifest.json"
    path.write_text(json.dumps(manifest.to_dict()))
    return path


def test_tool_execution_gate_cli_writes_markdown_and_json(tmp_path):
    manifest_file = _write_manifest(tmp_path, ["/api/accounts/123/users/{id}/permissions"])
    output_file = tmp_path / "tool-execution-gate.md"
    json_output = tmp_path / "tool-execution-gate.json"

    result = runner.invoke(
        app,
        [
            "tool-execution-gate",
            str(manifest_file),
            "--output-file",
            str(output_file),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0
    assert "Tool Execution Gate" in result.output
    assert "Execution Gate Items" in result.output
    assert "Saved tool execution gate Markdown" in result.output
    assert "Saved tool execution gate JSON" in result.output

    markdown = output_file.read_text()
    data = json.loads(json_output.read_text())

    assert "# Blackhole Tool Execution Gate: demo" in markdown
    assert "execution disabled" in markdown
    assert data["planning_only"] is True
    assert data["execution_allowed"] is False
    assert data["gate_decision"] == "blocked-manifest-execution-disabled"


def test_tool_execution_gate_cli_prints_markdown_without_outputs(tmp_path):
    manifest_file = _write_manifest(tmp_path, ["/api/files/{id}/download"])

    result = runner.invoke(app, ["tool-execution-gate", str(manifest_file)])

    assert result.exit_code == 0
    assert "# Blackhole Tool Execution Gate: demo" in result.output
    assert "Safety:" in result.output


def test_tool_execution_gate_cli_missing_file_exits_nonzero(tmp_path):
    result = runner.invoke(app, ["tool-execution-gate", str(tmp_path / "missing.json")])

    assert result.exit_code == 1
    assert "Tool request manifest JSON not found" in result.output


def test_tool_execution_gate_cli_invalid_json_exits_nonzero(tmp_path):
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{not json")

    result = runner.invoke(app, ["tool-execution-gate", str(bad_file)])

    assert result.exit_code == 2
    assert "Invalid tool request manifest JSON" in result.output
