from __future__ import annotations

import json

from typer.testing import CliRunner

from bugintel.cli import app
from bugintel.core.brain_chat_research_investigation_plan_packet import (
    build_research_investigation_plan_packet,
)


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


def _plan_packet() -> dict:
    return build_research_investigation_plan_packet(_selection_packet())


def test_research_investigation_plan_review_gate_cli_writes_outputs(tmp_path) -> None:
    plan_file = tmp_path / "research-investigation-plan-packet.json"
    output_file = tmp_path / "research-investigation-plan-review-gate.md"
    json_output = tmp_path / "research-investigation-plan-review-gate.json"
    plan_file.write_text(json.dumps(_plan_packet()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-investigation-plan-review-gate",
            "--plan-file",
            str(plan_file),
            "--output-file",
            str(output_file),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Brain Chat Research Investigation Plan Review Gate" in result.output
    assert "needs-human-review" in result.output
    assert "Runtime execution allowed" in result.output
    assert "Validation allowed" in result.output
    assert "Evidence collection" in result.output
    assert "Vulnerability confirmation" in result.output
    assert "false" in result.output
    assert output_file.exists()
    assert json_output.exists()

    data = json.loads(json_output.read_text(encoding="utf-8"))
    assert data["kind"] == "brain_chat_research_investigation_plan_review_gate"
    assert data["target_name"] == "demo-self-hosted-product"
    assert data["review_status"] == "needs-human-review"
    assert data["review_ready"] is True
    assert data["plan_count"] == 3
    assert data["validation_allowed"] is False
    assert data["runtime_execution_allowed"] is False
    assert data["evidence_collection_allowed"] is False
    assert data["report_submission_allowed"] is False
    assert data["vulnerability_confirmation_allowed"] is False
    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["browser_execution"] is False
    assert data["safety"]["curl_execution"] is False
    assert data["safety"]["kali_execution"] is False
    assert data["safety"]["validation_execution"] is False
    assert data["safety"]["runtime_execution_allowed"] is False
    assert data["safety"]["report_submission"] is False
    assert data["safety"]["vulnerability_confirmation"] is False

    markdown = output_file.read_text(encoding="utf-8")
    assert "# Research Investigation Plan Review Gate" in markdown
    assert "Human Review Items" in markdown


def test_research_investigation_plan_review_gate_cli_blocks_unsafe_plan_but_exits_zero(tmp_path) -> None:
    plan = _plan_packet()
    plan["safety_flags"]["tool_execution"] = True
    plan_file = tmp_path / "unsafe-plan.json"
    json_output = tmp_path / "unsafe-review.json"
    plan_file.write_text(json.dumps(plan), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-investigation-plan-review-gate",
            "--plan-file",
            str(plan_file),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "blocked-unsafe-plan" in result.output
    assert "Safety findings" in result.output

    data = json.loads(json_output.read_text(encoding="utf-8"))
    assert data["review_status"] == "blocked-unsafe-plan"
    assert data["review_ready"] is False
    assert any(item["subject"] == "safety_flags.tool_execution" for item in data["safety_findings"])


def test_research_investigation_plan_review_gate_cli_missing_file_errors(tmp_path) -> None:
    result = runner.invoke(
        app,
        [
            "brain-chat-research-investigation-plan-review-gate",
            "--plan-file",
            str(tmp_path / "missing-plan.json"),
        ],
    )

    assert result.exit_code == 1
    assert "Research investigation plan JSON not found" in result.output


def test_research_investigation_plan_review_gate_cli_invalid_json_errors(tmp_path) -> None:
    plan_file = tmp_path / "bad-plan.json"
    plan_file.write_text("{not-json", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-investigation-plan-review-gate",
            "--plan-file",
            str(plan_file),
        ],
    )

    assert result.exit_code == 2
    assert "Invalid research investigation plan JSON" in result.output


def test_research_investigation_plan_review_gate_cli_rejects_non_object_json(tmp_path) -> None:
    plan_file = tmp_path / "bad-plan.json"
    plan_file.write_text(json.dumps(["not", "object"]), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-investigation-plan-review-gate",
            "--plan-file",
            str(plan_file),
        ],
    )

    assert result.exit_code == 2
    assert "Invalid investigation plan review gate input" in result.output
