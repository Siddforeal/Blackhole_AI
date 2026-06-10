from __future__ import annotations

import json

import re
from typer.testing import CliRunner

from bugintel.cli import app
from bugintel.core.brain_chat_research_action_proposal_packet import (
    build_research_action_proposal_packet,
)
from bugintel.core.brain_chat_research_investigation_plan_packet import (
    build_research_investigation_plan_packet,
)
from bugintel.core.brain_chat_research_investigation_plan_review_gate import (
    build_research_investigation_plan_review_gate,
)


runner = CliRunner()


def _selection_packet() -> dict:
    return {
        "kind": (
            "brain_chat_research_hypothesis_selection_packet"
        ),
        "target_name": "demo-self-hosted-product",
        "selection_status": (
            "ready-for-local-investigation-planning"
        ),
        "primary_hypothesis_id": "HYP-005",
        "selected_hypotheses": [
            {
                "hypothesis_id": "HYP-005",
                "hypothesis_type": (
                    "worker-execution-trust-boundary"
                ),
                "title": (
                    "Agent, runner, worker, or deployment "
                    "trust boundary"
                ),
                "priority": "high",
                "confidence": "high",
                "score": 386,
                "tags": [
                    "worker",
                    "runner",
                    "deployment",
                ],
            },
            {
                "hypothesis_id": "HYP-006",
                "hypothesis_type": (
                    "authorization-admin-boundary"
                ),
                "title": (
                    "Authorization and administrative "
                    "access control"
                ),
                "priority": "high",
                "confidence": "high",
                "score": 376,
                "tags": [
                    "authorization",
                    "admin",
                    "rbac",
                    "tenant",
                ],
            },
        ],
    }


def _action_packet() -> dict:
    plan = build_research_investigation_plan_packet(
        _selection_packet()
    )
    plan_review = build_research_investigation_plan_review_gate(
        plan
    )

    return build_research_action_proposal_packet(
        plan,
        plan_review,
    ).to_dict()


def _write_proposal(tmp_path, packet: dict | None = None):
    proposal_file = tmp_path / "research-action-proposal.json"
    proposal_data = _action_packet() if packet is None else packet
    proposal_file.write_text(
        json.dumps(proposal_data),
        encoding="utf-8",
    )
    return proposal_file


def test_cli_writes_markdown_and_json(tmp_path) -> None:
    proposal_file = _write_proposal(tmp_path)
    markdown_file = tmp_path / "review-gate.md"
    json_file = tmp_path / "review-gate.json"

    result = runner.invoke(
        app,
        [
            "brain-chat-research-action-proposal-review-gate",
            "--proposal-file",
            str(proposal_file),
            "--output-file",
            str(markdown_file),
            "--json-output",
            str(json_file),
        ],
    )

    assert result.exit_code == 0, result.output

    assert (
        "Brain Chat Research Action Proposal Review Gate"
        in result.output
    )
    assert "needs-human-review" in result.output
    assert "Review ready" in result.output
    assert "True" in result.output
    assert "Proposal count" in result.output
    assert "16" in result.output
    assert "Schema findings" in result.output
    assert "Safety findings" in result.output
    assert "Proposal findings" in result.output
    assert "Command generation allowed" in result.output
    assert "Package installation allowed" in result.output
    assert "Runtime execution allowed" in result.output
    assert "false" in result.output

    assert markdown_file.exists()
    assert json_file.exists()

    data = json.loads(
        json_file.read_text(encoding="utf-8")
    )

    assert data["kind"] == (
        "brain_chat_research_action_proposal_review_gate"
    )
    assert data["target_name"] == "demo-self-hosted-product"
    assert data["review_status"] == "needs-human-review"
    assert data["review_ready"] is True
    assert data["proposal_count"] == 16

    assert data["schema_findings"] == []
    assert data["safety_findings"] == []
    assert data["proposal_findings"] == []

    assert data["command_generation_allowed"] is False
    assert data["package_installation_allowed"] is False
    assert data["execution_allowed"] is False
    assert data["runtime_execution_allowed"] is False
    assert data["target_interaction_allowed"] is False
    assert data["evidence_collection_allowed"] is False
    assert data["validation_allowed"] is False
    assert data["report_submission_allowed"] is False
    assert data["vulnerability_confirmation_allowed"] is False

    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["browser_execution"] is False
    assert data["safety"]["kali_execution"] is False
    assert data["safety"]["burp_execution"] is False
    assert data["safety"]["package_installation"] is False
    assert data["safety"]["runtime_execution_allowed"] is False

    markdown = markdown_file.read_text(encoding="utf-8")

    assert "# Research Action Proposal Review Gate" in markdown
    assert "review_status: `needs-human-review`" in markdown
    assert "review_ready: `true`" in markdown
    assert "command_generation_allowed: `false`" in markdown
    assert "package_installation_allowed: `false`" in markdown
    assert "runtime_execution_allowed: `false`" in markdown


def test_cli_supports_short_option_aliases(tmp_path) -> None:
    proposal_file = _write_proposal(tmp_path)
    markdown_file = tmp_path / "alias-review.md"

    result = runner.invoke(
        app,
        [
            "brain-chat-research-action-proposal-review-gate",
            "--proposal",
            str(proposal_file),
            "--output",
            str(markdown_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert markdown_file.exists()
    assert "needs-human-review" in result.output


def test_cli_blocked_invalid_packet_exits_zero(tmp_path) -> None:
    proposal_file = _write_proposal(tmp_path, {})
    json_file = tmp_path / "blocked-invalid.json"

    result = runner.invoke(
        app,
        [
            "brain-chat-research-action-proposal-review-gate",
            "--proposal-file",
            str(proposal_file),
            "--json-output",
            str(json_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "blocked-invalid-packet" in result.output
    assert "Schema findings" in result.output

    data = json.loads(
        json_file.read_text(encoding="utf-8")
    )

    assert data["review_status"] == "blocked-invalid-packet"
    assert data["review_ready"] is False
    assert data["counts"]["high_findings"] > 0
    assert data["runtime_execution_allowed"] is False


def test_cli_blocked_unsafe_packet_exits_zero(tmp_path) -> None:
    packet = _action_packet()
    packet["runtime_execution_allowed"] = True
    packet["safety"]["tool_execution"] = True
    packet["proposals"][0]["execution_allowed"] = True

    proposal_file = _write_proposal(tmp_path, packet)
    json_file = tmp_path / "blocked-unsafe.json"

    result = runner.invoke(
        app,
        [
            "brain-chat-research-action-proposal-review-gate",
            "--proposal-file",
            str(proposal_file),
            "--json-output",
            str(json_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "blocked-unsafe-action-proposals" in result.output
    assert "Safety findings" in result.output
    assert "Proposal findings" in result.output

    data = json.loads(
        json_file.read_text(encoding="utf-8")
    )

    assert data["review_ready"] is False
    assert data["counts"]["high_findings"] >= 3
    assert data["runtime_execution_allowed"] is False


def test_cli_empty_proposals_exits_zero(tmp_path) -> None:
    packet = _action_packet()
    packet["proposals"] = []
    packet["proposal_count"] = 0

    proposal_file = _write_proposal(tmp_path, packet)
    json_file = tmp_path / "empty.json"

    result = runner.invoke(
        app,
        [
            "brain-chat-research-action-proposal-review-gate",
            "--proposal-file",
            str(proposal_file),
            "--json-output",
            str(json_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "blocked-no-action-proposals" in result.output

    data = json.loads(
        json_file.read_text(encoding="utf-8")
    )

    assert data["proposal_count"] == 0
    assert data["review_ready"] is False


def test_cli_medium_findings_remain_reviewable(tmp_path) -> None:
    packet = _action_packet()
    packet["proposal_count"] = 999
    packet["proposals"][0]["proposed_tool_family"] = "browser"

    proposal_file = _write_proposal(tmp_path, packet)
    json_file = tmp_path / "medium-findings.json"

    result = runner.invoke(
        app,
        [
            "brain-chat-research-action-proposal-review-gate",
            "--proposal-file",
            str(proposal_file),
            "--json-output",
            str(json_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "needs-human-review" in result.output
    assert "Schema findings" in result.output
    assert "Proposal findings" in result.output

    data = json.loads(
        json_file.read_text(encoding="utf-8")
    )

    assert data["review_ready"] is True
    assert data["counts"]["high_findings"] == 0
    assert data["counts"]["medium_findings"] >= 2


def test_cli_missing_file_errors(tmp_path) -> None:
    result = runner.invoke(
        app,
        [
            "brain-chat-research-action-proposal-review-gate",
            "--proposal-file",
            str(tmp_path / "missing.json"),
        ],
    )

    assert result.exit_code == 1
    assert (
        "Research action proposal JSON not found"
        in result.output
    )


def test_cli_invalid_json_errors(tmp_path) -> None:
    proposal_file = tmp_path / "invalid.json"
    proposal_file.write_text("{not-json", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-action-proposal-review-gate",
            "--proposal-file",
            str(proposal_file),
        ],
    )

    assert result.exit_code == 2
    assert (
        "Invalid research action proposal JSON"
        in result.output
    )


def test_cli_non_object_json_errors(tmp_path) -> None:
    proposal_file = tmp_path / "list.json"
    proposal_file.write_text(
        json.dumps(["not", "an", "object"]),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "brain-chat-research-action-proposal-review-gate",
            "--proposal-file",
            str(proposal_file),
        ],
    )

    assert result.exit_code == 2
    assert (
        "Invalid research action proposal review-gate input"
        in result.output
    )


def test_cli_creates_nested_output_directories(tmp_path) -> None:
    proposal_file = _write_proposal(tmp_path)
    markdown_file = tmp_path / "nested" / "md" / "review.md"
    json_file = tmp_path / "nested" / "json" / "review.json"

    result = runner.invoke(
        app,
        [
            "brain-chat-research-action-proposal-review-gate",
            "--proposal-file",
            str(proposal_file),
            "--output-file",
            str(markdown_file),
            "--json-output",
            str(json_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert markdown_file.exists()
    assert json_file.exists()


def test_cli_help_lists_required_input() -> None:
    result = runner.invoke(
        app,
        [
            "brain-chat-research-action-proposal-review-gate",
            "--help",
        ],
    )

    assert result.exit_code == 0, result.output
    output = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", result.output)
    assert "--proposal-file" in output
    assert "--proposal" in output
    assert "--output-file" in output
    assert "--json-output" in output


def test_cli_safety_message_is_explicit(tmp_path) -> None:
    proposal_file = _write_proposal(tmp_path)

    result = runner.invoke(
        app,
        [
            "brain-chat-research-action-proposal-review-gate",
            "--proposal-file",
            str(proposal_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Safety:" in result.output
    assert "does not generate commands" in result.output
    assert "install software" in result.output
    assert "execute tools" in result.output
    assert "interact with Burp Suite" in result.output
    assert "use Kali tools" in result.output
    assert "send requests" in result.output
    assert "collect evidence" in result.output
    assert "validate findings" in result.output
    assert "confirm vulnerabilities" in result.output
