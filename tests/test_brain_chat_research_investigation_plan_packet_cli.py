from __future__ import annotations

import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def _selection_packet() -> dict:
    return {
        "kind": "brain_chat_research_hypothesis_selection_packet",
        "target_name": "demo-self-hosted-product",
        "selection_status": "ready-for-local-investigation-planning",
        "primary_hypothesis_id": "HYP-005",
        "selected_hypotheses": [
            {
                "hypothesis_id": "HYP-005",
                "hypothesis_type": "worker-execution-trust-boundary",
                "title": "Agent, runner, worker, or deployment trust boundary",
                "priority": "high",
                "confidence": "high",
                "score": 386,
                "tags": ["worker", "runner", "deployment"],
            },
            {
                "hypothesis_id": "HYP-003",
                "hypothesis_type": "input-to-filesystem-trust-boundary",
                "title": "Import/export/archive/package handling",
                "priority": "high",
                "confidence": "high",
                "score": 381,
                "tags": ["import", "archive", "filesystem"],
            },
            {
                "hypothesis_id": "HYP-006",
                "hypothesis_type": "authorization-admin-boundary",
                "title": "Authorization and administrative access control",
                "priority": "high",
                "confidence": "high",
                "score": 376,
                "tags": ["authorization", "admin", "rbac", "tenant"],
            },
        ],
    }


def test_research_investigation_plan_packet_cli_writes_outputs(tmp_path) -> None:
    selection_file = tmp_path / "research-hypothesis-selection-packet.json"
    output_file = tmp_path / "research-investigation-plan-packet.md"
    json_output = tmp_path / "research-investigation-plan-packet.json"

    selection_file.write_text(json.dumps(_selection_packet()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-investigation-plan-packet",
            "--selection-file",
            str(selection_file),
            "--output-file",
            str(output_file),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Brain Chat Research Investigation Plan Packet" in result.output
    assert "Investigation plan status" in result.output
    assert "ready-for-human-review" in result.output
    assert "HYP-005" in result.output
    assert "worker-execution-trust-boundary" in result.output
    assert "Target interaction" in result.output
    assert "false" in result.output

    assert output_file.exists()
    assert json_output.exists()

    packet = json.loads(json_output.read_text(encoding="utf-8"))
    assert packet["kind"] == "brain_chat_research_investigation_plan_packet"
    assert packet["target_name"] == "demo-self-hosted-product"
    assert packet["packet_status"] == "ready-for-human-review"
    assert packet["selected_count"] == 3
    assert packet["plan_count"] == 3
    assert packet["primary_hypothesis_id"] == "HYP-005"

    for safety_value in packet["safety_flags"].values():
        assert safety_value is False

    markdown = output_file.read_text(encoding="utf-8")
    assert "# Research Investigation Plan Packet" in markdown
    assert "HYP-003 - input-to-filesystem-trust-boundary" in markdown


def test_research_investigation_plan_packet_cli_rejects_missing_selection_file(tmp_path) -> None:
    missing_file = tmp_path / "missing-selection.json"

    result = runner.invoke(
        app,
        [
            "brain-chat-research-investigation-plan-packet",
            "--selection-file",
            str(missing_file),
        ],
    )

    assert result.exit_code == 1
    assert "Research hypothesis selection JSON not found" in result.output


def test_research_investigation_plan_packet_cli_rejects_invalid_json(tmp_path) -> None:
    selection_file = tmp_path / "bad-selection.json"
    selection_file.write_text("{not-json", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-investigation-plan-packet",
            "--selection-file",
            str(selection_file),
        ],
    )

    assert result.exit_code == 1
    assert "Invalid JSON" in result.output
