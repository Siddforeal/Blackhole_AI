from __future__ import annotations

import json
import re

from typer.testing import CliRunner

from bugintel.cli import app
from bugintel.core.brain_chat_research_action_decision_packet import (
    build_research_action_decision_template,
)
from bugintel.core.brain_chat_research_action_proposal_packet import (
    build_research_action_proposal_packet,
)
from bugintel.core.brain_chat_research_action_proposal_review_gate import (
    build_research_action_proposal_review_gate,
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
                "title": "Worker trust boundary",
                "priority": "high",
                "confidence": "high",
                "score": 386,
                "tags": ["worker"],
            },
        ],
    }


def _proposal_and_review() -> tuple[dict, dict]:
    plan = build_research_investigation_plan_packet(
        _selection_packet()
    )
    plan_review = build_research_investigation_plan_review_gate(
        plan
    )

    proposal = build_research_action_proposal_packet(
        plan,
        plan_review,
    ).to_dict()

    review = build_research_action_proposal_review_gate(
        proposal
    )

    return proposal, review


def _decision_input(
    proposal: dict,
    decision: str = "approved",
) -> dict:
    value = build_research_action_decision_template(
        proposal
    )
    value["reviewer"] = "authorized-human-reviewer"
    value["overall_reason"] = (
        "Reviewed for the next planning stage."
    )

    for item in value["decisions"]:
        item["decision"] = decision
        item["reason"] = (
            f"Human decision recorded as {decision}."
        )

    return value


def _write_json(tmp_path, name: str, value) -> object:
    path = tmp_path / name
    path.write_text(
        json.dumps(value),
        encoding="utf-8",
    )
    return path


def _write_pipeline(
    tmp_path,
    decision: str = "approved",
) -> tuple[object, object, object]:
    proposal, review = _proposal_and_review()
    decision_input = _decision_input(
        proposal,
        decision=decision,
    )

    return (
        _write_json(
            tmp_path,
            "proposal.json",
            proposal,
        ),
        _write_json(
            tmp_path,
            "review.json",
            review,
        ),
        _write_json(
            tmp_path,
            "decision.json",
            decision_input,
        ),
    )


def test_template_cli_writes_deferred_decisions(
    tmp_path,
) -> None:
    proposal, _ = _proposal_and_review()
    proposal_file = _write_json(
        tmp_path,
        "proposal.json",
        proposal,
    )
    output_file = tmp_path / "decision-template.json"

    result = runner.invoke(
        app,
        [
            "brain-chat-research-action-decision-template",
            "--proposal-file",
            str(proposal_file),
            "--output-file",
            str(output_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert output_file.exists()
    assert "Research Action Decision Template" in (
        result.output
    )
    assert "Default decision" in result.output
    assert "deferred" in result.output

    data = json.loads(
        output_file.read_text(encoding="utf-8")
    )

    assert data["kind"] == (
        "brain_chat_research_action_decision_input"
    )
    assert data["target_name"] == (
        "demo-self-hosted-product"
    )
    assert len(data["decisions"]) == 8
    assert all(
        item["decision"] == "deferred"
        for item in data["decisions"]
    )
    assert data["planning_only"] is True


def test_template_cli_supports_aliases(tmp_path) -> None:
    proposal, _ = _proposal_and_review()
    proposal_file = _write_json(
        tmp_path,
        "proposal.json",
        proposal,
    )
    output_file = tmp_path / "alias-template.json"

    result = runner.invoke(
        app,
        [
            "brain-chat-research-action-decision-template",
            "--proposal",
            str(proposal_file),
            "--output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert output_file.exists()


def test_template_cli_creates_parent_directories(
    tmp_path,
) -> None:
    proposal, _ = _proposal_and_review()
    proposal_file = _write_json(
        tmp_path,
        "proposal.json",
        proposal,
    )
    output_file = (
        tmp_path
        / "nested"
        / "templates"
        / "decision.json"
    )

    result = runner.invoke(
        app,
        [
            "brain-chat-research-action-decision-template",
            "--proposal-file",
            str(proposal_file),
            "--output-file",
            str(output_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert output_file.exists()


def test_template_cli_missing_proposal_errors(
    tmp_path,
) -> None:
    result = runner.invoke(
        app,
        [
            "brain-chat-research-action-decision-template",
            "--proposal-file",
            str(tmp_path / "missing.json"),
            "--output-file",
            str(tmp_path / "output.json"),
        ],
    )

    assert result.exit_code == 1
    assert (
        "Research action proposal JSON not found"
        in result.output
    )


def test_template_cli_invalid_json_errors(tmp_path) -> None:
    proposal_file = tmp_path / "invalid.json"
    proposal_file.write_text(
        "{not-json",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "brain-chat-research-action-decision-template",
            "--proposal-file",
            str(proposal_file),
            "--output-file",
            str(tmp_path / "output.json"),
        ],
    )

    assert result.exit_code == 2
    assert (
        "Invalid research action proposal JSON"
        in result.output
    )


def test_template_cli_non_object_json_errors(
    tmp_path,
) -> None:
    proposal_file = _write_json(
        tmp_path,
        "list.json",
        ["not", "object"],
    )

    result = runner.invoke(
        app,
        [
            "brain-chat-research-action-decision-template",
            "--proposal-file",
            str(proposal_file),
            "--output-file",
            str(tmp_path / "output.json"),
        ],
    )

    assert result.exit_code == 2
    assert (
        "Invalid research action proposal template input"
        in result.output
    )


def test_decision_packet_cli_writes_outputs(
    tmp_path,
) -> None:
    (
        proposal_file,
        review_file,
        decision_file,
    ) = _write_pipeline(tmp_path)

    markdown_file = (
        tmp_path / "output" / "decision.md"
    )
    json_file = (
        tmp_path / "output" / "decision.json"
    )

    result = runner.invoke(
        app,
        [
            "brain-chat-research-action-decision-packet",
            "--proposal-file",
            str(proposal_file),
            "--review-file",
            str(review_file),
            "--decision-file",
            str(decision_file),
            "--output-file",
            str(markdown_file),
            "--json-output",
            str(json_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Research Action Decision Packet" in result.output
    assert "ready-for-approved-action-packet" in (
        result.output
    )
    assert "Per-Action Human Decisions" in result.output

    assert markdown_file.exists()
    assert json_file.exists()

    data = json.loads(
        json_file.read_text(encoding="utf-8")
    )

    assert data["decision_status"] == (
        "ready-for-approved-action-packet"
    )
    assert data["decision_ready"] is True
    assert data["effective_approval_granted"] is True
    assert data["approved_action_count"] == 8
    assert data["runtime_execution_allowed"] is False
    assert data["tool_request_manifest_ready"] is False

    markdown = markdown_file.read_text(encoding="utf-8")
    assert "# Research Action Decision Packet" in markdown
    assert "Runtime execution allowed: `false`" in markdown


def test_decision_packet_cli_supports_aliases(
    tmp_path,
) -> None:
    (
        proposal_file,
        review_file,
        decision_file,
    ) = _write_pipeline(tmp_path)

    json_file = tmp_path / "aliases.json"

    result = runner.invoke(
        app,
        [
            "brain-chat-research-action-decision-packet",
            "--proposal",
            str(proposal_file),
            "--review",
            str(review_file),
            "--decision",
            str(decision_file),
            "--json-output",
            str(json_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert json_file.exists()


def test_decision_packet_cli_changes_requested(
    tmp_path,
) -> None:
    (
        proposal_file,
        review_file,
        decision_file,
    ) = _write_pipeline(
        tmp_path,
        decision="changes-requested",
    )

    json_file = tmp_path / "changes.json"

    result = runner.invoke(
        app,
        [
            "brain-chat-research-action-decision-packet",
            "--proposal-file",
            str(proposal_file),
            "--review-file",
            str(review_file),
            "--decision-file",
            str(decision_file),
            "--json-output",
            str(json_file),
        ],
    )

    assert result.exit_code == 0, result.output

    data = json.loads(
        json_file.read_text(encoding="utf-8")
    )

    assert data["decision_status"] == "changes-requested"
    assert data["approved_action_packet_ready"] is False
    assert data["effective_approval_granted"] is False
    assert data["changes_requested_count"] == 8


def test_decision_packet_cli_incomplete_decisions(
    tmp_path,
) -> None:
    proposal, review = _proposal_and_review()
    decision_input = _decision_input(proposal)
    decision_input["decisions"].pop()

    proposal_file = _write_json(
        tmp_path,
        "proposal.json",
        proposal,
    )
    review_file = _write_json(
        tmp_path,
        "review.json",
        review,
    )
    decision_file = _write_json(
        tmp_path,
        "decision.json",
        decision_input,
    )
    json_file = tmp_path / "incomplete.json"

    result = runner.invoke(
        app,
        [
            "brain-chat-research-action-decision-packet",
            "--proposal-file",
            str(proposal_file),
            "--review-file",
            str(review_file),
            "--decision-file",
            str(decision_file),
            "--json-output",
            str(json_file),
        ],
    )

    assert result.exit_code == 0, result.output

    data = json.loads(
        json_file.read_text(encoding="utf-8")
    )

    assert data["decision_status"] == (
        "blocked-incomplete-decisions"
    )
    assert data["decision_ready"] is False
    assert data["missing_decision_count"] == 1


def test_decision_packet_cli_blocks_unsafe_source(
    tmp_path,
) -> None:
    proposal, review = _proposal_and_review()
    proposal["runtime_execution_allowed"] = True
    decision_input = _decision_input(proposal)

    proposal_file = _write_json(
        tmp_path,
        "proposal.json",
        proposal,
    )
    review_file = _write_json(
        tmp_path,
        "review.json",
        review,
    )
    decision_file = _write_json(
        tmp_path,
        "decision.json",
        decision_input,
    )
    json_file = tmp_path / "unsafe.json"

    result = runner.invoke(
        app,
        [
            "brain-chat-research-action-decision-packet",
            "--proposal-file",
            str(proposal_file),
            "--review-file",
            str(review_file),
            "--decision-file",
            str(decision_file),
            "--json-output",
            str(json_file),
        ],
    )

    assert result.exit_code == 0, result.output

    data = json.loads(
        json_file.read_text(encoding="utf-8")
    )

    assert data["decision_status"] == (
        "blocked-unsafe-source"
    )
    assert data["runtime_execution_allowed"] is False
    assert data["counts"]["high_findings"] >= 1


def test_decision_packet_cli_missing_inputs_error(
    tmp_path,
) -> None:
    proposal, review = _proposal_and_review()
    decision_input = _decision_input(proposal)

    valid_proposal = _write_json(
        tmp_path,
        "proposal.json",
        proposal,
    )
    valid_review = _write_json(
        tmp_path,
        "review.json",
        review,
    )
    valid_decision = _write_json(
        tmp_path,
        "decision.json",
        decision_input,
    )

    cases = (
        (
            tmp_path / "missing-proposal.json",
            valid_review,
            valid_decision,
            "Research action proposal JSON not found",
        ),
        (
            valid_proposal,
            tmp_path / "missing-review.json",
            valid_decision,
            (
                "Research action proposal review "
                "JSON not found"
            ),
        ),
        (
            valid_proposal,
            valid_review,
            tmp_path / "missing-decision.json",
            "Research action decision JSON not found",
        ),
    )

    for (
        proposal_file,
        review_file,
        decision_file,
        message,
    ) in cases:
        result = runner.invoke(
            app,
            [
                (
                    "brain-chat-research-action-"
                    "decision-packet"
                ),
                "--proposal-file",
                str(proposal_file),
                "--review-file",
                str(review_file),
                "--decision-file",
                str(decision_file),
            ],
        )

        assert result.exit_code == 1
        assert message in result.output


def test_decision_packet_cli_invalid_json_errors(
    tmp_path,
) -> None:
    proposal, review = _proposal_and_review()

    proposal_file = _write_json(
        tmp_path,
        "proposal.json",
        proposal,
    )
    review_file = _write_json(
        tmp_path,
        "review.json",
        review,
    )
    decision_file = tmp_path / "invalid.json"
    decision_file.write_text(
        "{not-json",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "brain-chat-research-action-decision-packet",
            "--proposal-file",
            str(proposal_file),
            "--review-file",
            str(review_file),
            "--decision-file",
            str(decision_file),
        ],
    )

    assert result.exit_code == 2
    assert (
        "Invalid research action decision pipeline JSON"
        in result.output
    )


def test_decision_packet_cli_non_object_errors(
    tmp_path,
) -> None:
    proposal, review = _proposal_and_review()

    proposal_file = _write_json(
        tmp_path,
        "proposal.json",
        proposal,
    )
    review_file = _write_json(
        tmp_path,
        "review.json",
        review,
    )
    decision_file = _write_json(
        tmp_path,
        "list.json",
        ["wrong"],
    )

    result = runner.invoke(
        app,
        [
            "brain-chat-research-action-decision-packet",
            "--proposal-file",
            str(proposal_file),
            "--review-file",
            str(review_file),
            "--decision-file",
            str(decision_file),
        ],
    )

    assert result.exit_code == 2
    assert (
        "Invalid research action decision pipeline input"
        in result.output
    )


def test_decision_commands_help() -> None:
    command_options = (
        (
            "brain-chat-research-action-decision-template",
            (
                "--proposal-file",
                "--proposal",
                "--output-file",
                "--output",
            ),
        ),
        (
            "brain-chat-research-action-decision-packet",
            (
                "--proposal-file",
                "--review-file",
                "--decision-file",
                "--output-file",
                "--json-output",
            ),
        ),
    )

    for command, options in command_options:
        result = runner.invoke(
            app,
            [command, "--help"],
        )

        assert result.exit_code == 0, result.output

        output = re.sub(
            r"\x1b\[[0-?]*[ -/]*[@-~]",
            "",
            result.output,
        )

        for option in options:
            assert option in output


def test_decision_packet_cli_safety_message(
    tmp_path,
) -> None:
    (
        proposal_file,
        review_file,
        decision_file,
    ) = _write_pipeline(tmp_path)

    result = runner.invoke(
        app,
        [
            "brain-chat-research-action-decision-packet",
            "--proposal-file",
            str(proposal_file),
            "--review-file",
            str(review_file),
            "--decision-file",
            str(decision_file),
        ],
    )

    assert result.exit_code == 0, result.output

    output = re.sub(
        r"\x1b\[[0-?]*[ -/]*[@-~]",
        "",
        result.output,
    )
    output = re.sub(r"\s+", " ", output)

    assert "Safety:" in output
    assert "does not generate commands" in output
    assert "install software" in output
    assert "execute tools" in output
    assert "interact with Burp Suite" in output
    assert "use Kali tools" in output
    assert "send requests" in output
    assert "collect evidence" in output
    assert "confirm vulnerabilities" in output
