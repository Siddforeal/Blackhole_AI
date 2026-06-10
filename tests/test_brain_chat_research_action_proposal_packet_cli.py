from __future__ import annotations

import json

from typer.testing import CliRunner

from bugintel.cli import app
from bugintel.core.brain_chat_research_investigation_plan_packet import (
    build_research_investigation_plan_packet,
)
from bugintel.core.brain_chat_research_investigation_plan_review_gate import (
    build_research_investigation_plan_review_gate,
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


def _review_gate(plan: dict) -> dict:
    return build_research_investigation_plan_review_gate(plan)


def _write_inputs(tmp_path):
    plan = _plan_packet()
    review = _review_gate(plan)

    plan_file = tmp_path / "investigation-plan.json"
    review_file = tmp_path / "investigation-plan-review.json"

    plan_file.write_text(json.dumps(plan), encoding="utf-8")
    review_file.write_text(json.dumps(review), encoding="utf-8")

    return plan_file, review_file


def test_research_action_proposal_packet_cli_writes_outputs(tmp_path) -> None:
    plan_file, review_file = _write_inputs(tmp_path)
    output_file = tmp_path / "research-action-proposal.md"
    json_output = tmp_path / "research-action-proposal.json"

    result = runner.invoke(
        app,
        [
            "brain-chat-research-action-proposal-packet",
            "--plan-file",
            str(plan_file),
            "--review-file",
            str(review_file),
            "--output-file",
            str(output_file),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Brain Chat Research Action Proposal Packet" in result.output
    assert "ready-for-action-proposal-review" in result.output
    assert "Proposal count" in result.output
    assert "16" in result.output
    assert "Execution allowed" in result.output
    assert "Runtime execution allowed" in result.output
    assert "Command generation allowed" in result.output
    assert "Package installation" in result.output
    assert "false" in result.output

    assert output_file.exists()
    assert json_output.exists()

    data = json.loads(json_output.read_text(encoding="utf-8"))
    assert data["kind"] == "brain_chat_research_action_proposal_packet"
    assert data["proposal_status"] == "ready-for-action-proposal-review"
    assert data["action_proposal_ready"] is True
    assert data["plan_count"] == 2
    assert data["proposal_count"] == 16
    assert data["execution_allowed"] is False
    assert data["runtime_execution_allowed"] is False
    assert data["command_generation_allowed"] is False
    assert data["target_interaction_allowed"] is False
    assert data["evidence_collection_allowed"] is False
    assert data["validation_allowed"] is False
    assert data["report_submission_allowed"] is False
    assert data["vulnerability_confirmation_allowed"] is False

    assert data["safety"]["command_generation"] is False
    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["browser_execution"] is False
    assert data["safety"]["curl_execution"] is False
    assert data["safety"]["kali_execution"] is False
    assert data["safety"]["burp_execution"] is False
    assert data["safety"]["package_installation"] is False
    assert data["safety"]["target_interaction"] is False
    assert data["safety"]["evidence_collection"] is False
    assert data["safety"]["validation_execution"] is False
    assert data["safety"]["runtime_execution_allowed"] is False
    assert data["safety"]["state_mutation"] is False
    assert data["safety"]["report_submission"] is False
    assert data["safety"]["vulnerability_confirmation"] is False

    markdown = output_file.read_text(encoding="utf-8")
    assert "# Research Action Proposal Packet" in markdown
    assert "Proposed Actions" in markdown
    assert "Command generation allowed: `false`" in markdown


def test_research_action_proposal_packet_cli_blocked_packet_exits_zero(tmp_path) -> None:
    plan = _plan_packet()
    review = _review_gate(plan)
    review["review_status"] = "blocked-unsafe-plan"
    review["review_ready"] = False

    plan_file = tmp_path / "investigation-plan.json"
    review_file = tmp_path / "investigation-plan-review.json"
    json_output = tmp_path / "blocked-action-proposal.json"

    plan_file.write_text(json.dumps(plan), encoding="utf-8")
    review_file.write_text(json.dumps(review), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-action-proposal-packet",
            "--plan-file",
            str(plan_file),
            "--review-file",
            str(review_file),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "blocked-pending-review-ready-plan" in result.output
    assert "Blockers" in result.output

    data = json.loads(json_output.read_text(encoding="utf-8"))
    assert data["proposal_status"] == "blocked-pending-review-ready-plan"
    assert data["action_proposal_ready"] is False
    assert data["proposal_count"] == 0
    assert "review-status-not-human-reviewable" in data["blockers"]
    assert "review-gate-not-ready" in data["blockers"]


def test_research_action_proposal_packet_cli_missing_plan_errors(tmp_path) -> None:
    review_file = tmp_path / "review.json"
    review_file.write_text(json.dumps({}), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-action-proposal-packet",
            "--plan-file",
            str(tmp_path / "missing-plan.json"),
            "--review-file",
            str(review_file),
        ],
    )

    assert result.exit_code == 1
    assert "Research investigation plan JSON not found" in result.output


def test_research_action_proposal_packet_cli_missing_review_errors(tmp_path) -> None:
    plan_file = tmp_path / "plan.json"
    plan_file.write_text(json.dumps({}), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-action-proposal-packet",
            "--plan-file",
            str(plan_file),
            "--review-file",
            str(tmp_path / "missing-review.json"),
        ],
    )

    assert result.exit_code == 1
    assert "Research investigation plan review JSON not found" in result.output


def test_research_action_proposal_packet_cli_invalid_json_errors(tmp_path) -> None:
    plan_file = tmp_path / "plan.json"
    review_file = tmp_path / "review.json"

    plan_file.write_text("{not-json", encoding="utf-8")
    review_file.write_text(json.dumps({}), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-action-proposal-packet",
            "--plan-file",
            str(plan_file),
            "--review-file",
            str(review_file),
        ],
    )

    assert result.exit_code == 2
    assert "Invalid research action proposal input JSON" in result.output


def test_research_action_proposal_packet_cli_non_object_json_errors(tmp_path) -> None:
    plan_file = tmp_path / "plan.json"
    review_file = tmp_path / "review.json"

    plan_file.write_text(json.dumps(["not", "object"]), encoding="utf-8")
    review_file.write_text(json.dumps({}), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-action-proposal-packet",
            "--plan-file",
            str(plan_file),
            "--review-file",
            str(review_file),
        ],
    )

    assert result.exit_code == 2
    assert "Invalid research action proposal input" in result.output
