from __future__ import annotations

import copy
import json
import re

from typer.testing import CliRunner

from bugintel.cli import app
from bugintel.core.brain_chat_research_observation_packet import (
    build_research_observation_packet,
)
from bugintel.core.brain_chat_research_observation_review_gate import (
    build_research_observation_review_gate,
)


runner = CliRunner()

COMMAND = (
    "brain-chat-research-hypothesis-feedback-packet"
)
TARGET = "demo-self-hosted-product"


def _hypothesis(
    hypothesis_id: str = "HYP-005",
    **overrides,
) -> dict:
    value = {
        "hypothesis_id": hypothesis_id,
        "title": "Worker trust-boundary weakness",
        "attack_surface": "worker execution",
        "hypothesis_type": (
            "worker-execution-trust-boundary"
        ),
        "priority": "high",
        "confidence": "medium",
    }
    value.update(overrides)
    return value


def _hypothesis_packet(
    hypotheses: list[dict] | None = None,
    **overrides,
) -> dict:
    items = (
        hypotheses
        if hypotheses is not None
        else [_hypothesis()]
    )

    value = {
        "kind": (
            "brain_chat_research_hypothesis_packet"
        ),
        "source": (
            "brain-chat-research-hypothesis-packet"
        ),
        "target_name": TARGET,
        "packet_status": (
            "ready-for-hypothesis-review"
        ),
        "hypothesis_count": len(items),
        "hypotheses": items,
        "planning_only": True,
        "execution_state": "not_executed",
    }
    value.update(overrides)
    return value


def _observation(
    hypothesis_id: str | None = "HYP-005",
    **overrides,
) -> dict:
    value = {
        "request_id": "RTR-001",
        "action_id": "ACT-001",
        "hypothesis_id": hypothesis_id,
        "source_type": "manual-note",
        "outcome": "supports-hypothesis",
        "evidence_strength": "strong",
        "summary": (
            "Local review supports the worker "
            "trust-boundary hypothesis."
        ),
        "details": [
            "Reviewed local controller-to-worker flow.",
        ],
        "artifact_refs": [
            "notes/worker-flow.md",
        ],
        "signals": [
            "privileged worker boundary",
        ],
        "errors": [],
        "scope_status": "not-applicable",
        "controlled_assets_status": "not-required",
        "redaction_status": "not-required",
        "human_reviewed": True,
    }
    value.update(overrides)
    return value


def _artifacts(
    hypotheses: list[dict] | None = None,
    observations: list[dict] | None = None,
):
    hypothesis_packet = _hypothesis_packet(
        hypotheses=hypotheses,
    )

    observation_packet = (
        build_research_observation_packet(
            {
                "target_name": TARGET,
                "observations": (
                    observations
                    if observations is not None
                    else [_observation()]
                ),
            }
        )
    )

    observation_review = (
        build_research_observation_review_gate(
            observation_packet
        )
    )

    return (
        hypothesis_packet,
        observation_packet,
        observation_review,
    )


def _write_json(
    tmp_path,
    name: str,
    value,
):
    path = tmp_path / name
    path.write_text(
        json.dumps(value),
        encoding="utf-8",
    )
    return path


def _write_artifacts(
    tmp_path,
    hypotheses: list[dict] | None = None,
    observations: list[dict] | None = None,
):
    hypothesis_packet, observation_packet, review = (
        _artifacts(
            hypotheses=hypotheses,
            observations=observations,
        )
    )

    hypothesis_file = _write_json(
        tmp_path,
        "hypotheses.json",
        hypothesis_packet,
    )
    observation_file = _write_json(
        tmp_path,
        "observations.json",
        observation_packet,
    )
    review_file = _write_json(
        tmp_path,
        "observation-review.json",
        review,
    )

    return (
        hypothesis_file,
        observation_file,
        review_file,
    )


def _command_args(
    hypothesis_file,
    observation_file,
    review_file,
) -> list[str]:
    return [
        COMMAND,
        "--hypothesis-file",
        str(hypothesis_file),
        "--observation-file",
        str(observation_file),
        "--review-file",
        str(review_file),
    ]


def _normalize_output(value: str) -> str:
    value = re.sub(
        r"\x1b\[[0-?]*[ -/]*[@-~]",
        "",
        value,
    )
    return re.sub(r"\s+", " ", value)


def test_cli_writes_ready_markdown_and_json(
    tmp_path,
) -> None:
    (
        hypothesis_file,
        observation_file,
        review_file,
    ) = _write_artifacts(tmp_path)

    markdown_file = (
        tmp_path
        / "output"
        / "hypothesis-feedback.md"
    )
    json_file = (
        tmp_path
        / "output"
        / "hypothesis-feedback.json"
    )

    result = runner.invoke(
        app,
        _command_args(
            hypothesis_file,
            observation_file,
            review_file,
        )
        + [
            "--output-file",
            str(markdown_file),
            "--json-output",
            str(json_file),
        ],
    )

    assert result.exit_code == 0, result.output

    output = _normalize_output(result.output)

    assert (
        "Research Hypothesis Feedback Packet"
        in output
    )
    assert (
        "ready-for-hypothesis-feedback-review"
        in output
    )
    assert (
        "Hypothesis Feedback Proposals"
        in output
    )
    assert "Hypothesis packet digest:" in output
    assert "Observation packet digest:" in output
    assert "Observation review digest:" in output
    assert "Feedback digest:" in output

    assert markdown_file.exists()
    assert json_file.exists()

    data = json.loads(
        json_file.read_text(encoding="utf-8")
    )

    assert data["kind"] == (
        "brain_chat_research_hypothesis_feedback_packet"
    )
    assert data["packet_status"] == (
        "ready-for-hypothesis-feedback-review"
    )
    assert data["packet_ready"] is True
    assert (
        data["hypothesis_feedback_review_ready"]
        is True
    )
    assert data["confidence_update_ready"] is False
    assert data["selection_update_ready"] is False
    assert (
        data["research_state_transition_ready"]
        is False
    )
    assert data["runtime_execution_allowed"] is False
    assert data["feedback_proposal_count"] == 1

    assert data["counts"]["source_hypotheses"] == 1
    assert (
        data["counts"][
            "verified_hypothesis_impacts"
        ]
        == 1
    )
    assert data["counts"]["feedback_proposals"] == 1
    assert (
        data["counts"][
            "categorical_confidence_changes"
        ]
        == 1
    )
    assert data["counts"]["high_findings"] == 0

    proposal = data["feedback_proposals"][0]

    assert proposal["feedback_id"] == "HFB-001"
    assert proposal["hypothesis_id"] == "HYP-005"
    assert proposal["current_confidence"] == (
        "medium"
    )
    assert proposal["proposed_confidence"] == "high"
    assert proposal[
        "categorical_confidence_change"
    ] is True
    assert proposal["net_confidence_delta"] == 3
    assert proposal["evidence_direction"] == (
        "strengthen"
    )
    assert proposal["confidence_mutation_allowed"] is False
    assert proposal["state_mutation_allowed"] is False
    assert proposal["runtime_execution_allowed"] is False

    for field in (
        "hypothesis_packet_digest",
        "observation_packet_digest",
        "observation_review_digest",
        "feedback_digest",
    ):
        assert len(data[field]) == 64

    markdown = markdown_file.read_text(
        encoding="utf-8"
    )

    assert (
        "# Research Hypothesis Feedback Packet"
        in markdown
    )
    assert (
        "packet_status: "
        "`ready-for-hypothesis-feedback-review`"
        in markdown
    )
    assert "packet_ready: `true`" in markdown
    assert (
        "confidence_update_ready: `false`"
        in markdown
    )
    assert (
        "research_state_transition_ready: `false`"
        in markdown
    )
    assert (
        "runtime_execution_allowed: `false`"
        in markdown
    )


def test_cli_unknown_hypothesis_is_blocked(
    tmp_path,
) -> None:
    (
        hypothesis_file,
        observation_file,
        review_file,
    ) = _write_artifacts(
        tmp_path,
        observations=[
            _observation(
                hypothesis_id="HYP-999",
            )
        ],
    )
    json_file = tmp_path / "unknown.json"

    result = runner.invoke(
        app,
        _command_args(
            hypothesis_file,
            observation_file,
            review_file,
        )
        + [
            "--json-output",
            str(json_file),
        ],
    )

    assert result.exit_code == 0, result.output

    data = json.loads(
        json_file.read_text(encoding="utf-8")
    )

    assert data["packet_status"] == (
        "blocked-unknown-hypothesis"
    )
    assert data["packet_ready"] is False
    assert data["runtime_execution_allowed"] is False

    categories = {
        item["category"]
        for item in data["findings"]
    }

    assert "hypothesis-linkage" in categories


def test_cli_non_ready_review_is_blocked(
    tmp_path,
) -> None:
    (
        hypothesis_packet,
        observation_packet,
        review,
    ) = _artifacts()

    review["review_status"] = (
        "blocked-invalid-observations"
    )
    review["review_ready"] = False
    review[
        "hypothesis_feedback_packet_ready"
    ] = False

    hypothesis_file = _write_json(
        tmp_path,
        "hypotheses.json",
        hypothesis_packet,
    )
    observation_file = _write_json(
        tmp_path,
        "observations.json",
        observation_packet,
    )
    review_file = _write_json(
        tmp_path,
        "blocked-review.json",
        review,
    )
    json_file = tmp_path / "feedback.json"

    result = runner.invoke(
        app,
        _command_args(
            hypothesis_file,
            observation_file,
            review_file,
        )
        + [
            "--json-output",
            str(json_file),
        ],
    )

    assert result.exit_code == 0, result.output

    data = json.loads(
        json_file.read_text(encoding="utf-8")
    )

    assert data["packet_status"] == (
        "blocked-observation-review-not-ready"
    )
    assert data["packet_ready"] is False
    assert data["confidence_update_ready"] is False
    assert data["runtime_execution_allowed"] is False


def test_cli_unsafe_observation_packet_is_blocked(
    tmp_path,
) -> None:
    (
        hypothesis_packet,
        observation_packet,
        review,
    ) = _artifacts()

    observation_packet["execution_allowed"] = True

    hypothesis_file = _write_json(
        tmp_path,
        "hypotheses.json",
        hypothesis_packet,
    )
    observation_file = _write_json(
        tmp_path,
        "unsafe-observations.json",
        observation_packet,
    )
    review_file = _write_json(
        tmp_path,
        "observation-review.json",
        review,
    )
    json_file = tmp_path / "unsafe-feedback.json"

    result = runner.invoke(
        app,
        _command_args(
            hypothesis_file,
            observation_file,
            review_file,
        )
        + [
            "--json-output",
            str(json_file),
        ],
    )

    assert result.exit_code == 0, result.output

    data = json.loads(
        json_file.read_text(encoding="utf-8")
    )

    assert data["packet_status"] == (
        "blocked-unsafe-feedback-input"
    )
    assert data["packet_ready"] is False
    assert data["execution_allowed"] is False
    assert data["runtime_execution_allowed"] is False

    categories = {
        item["category"]
        for item in data["findings"]
    }

    assert "observation-safety" in categories


def test_cli_no_hypothesis_impacts_needs_review(
    tmp_path,
) -> None:
    (
        hypothesis_file,
        observation_file,
        review_file,
    ) = _write_artifacts(
        tmp_path,
        observations=[
            _observation(
                hypothesis_id=None,
                action_id="ACT-100",
            )
        ],
    )
    json_file = tmp_path / "no-impacts.json"

    result = runner.invoke(
        app,
        _command_args(
            hypothesis_file,
            observation_file,
            review_file,
        )
        + [
            "--json-output",
            str(json_file),
        ],
    )

    assert result.exit_code == 0, result.output

    data = json.loads(
        json_file.read_text(encoding="utf-8")
    )

    assert data["packet_status"] == (
        "review-needed-no-hypothesis-impacts"
    )
    assert data["packet_ready"] is False
    assert data["feedback_proposal_count"] == 0
    assert data["feedback_proposals"] == []
    assert data["allowed_next_steps"] == []
    assert data["runtime_execution_allowed"] is False


def test_cli_aliases_work(tmp_path) -> None:
    (
        hypothesis_file,
        observation_file,
        review_file,
    ) = _write_artifacts(tmp_path)

    markdown_file = (
        tmp_path
        / "alias-feedback.md"
    )

    result = runner.invoke(
        app,
        [
            COMMAND,
            "--hypothesis-packet",
            str(hypothesis_file),
            "--observation-packet",
            str(observation_file),
            "--observation-review",
            str(review_file),
            "--output",
            str(markdown_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert markdown_file.exists()

    markdown = markdown_file.read_text(
        encoding="utf-8"
    )

    assert (
        "# Research Hypothesis Feedback Packet"
        in markdown
    )


def test_cli_creates_nested_output_directories(
    tmp_path,
) -> None:
    (
        hypothesis_file,
        observation_file,
        review_file,
    ) = _write_artifacts(tmp_path)

    markdown_file = (
        tmp_path
        / "nested"
        / "markdown"
        / "feedback.md"
    )
    json_file = (
        tmp_path
        / "nested"
        / "json"
        / "feedback.json"
    )

    result = runner.invoke(
        app,
        _command_args(
            hypothesis_file,
            observation_file,
            review_file,
        )
        + [
            "--output-file",
            str(markdown_file),
            "--json-output",
            str(json_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert markdown_file.exists()
    assert json_file.exists()


def test_cli_output_is_deterministic(
    tmp_path,
) -> None:
    (
        hypothesis_file,
        observation_file,
        review_file,
    ) = _write_artifacts(tmp_path)

    first_file = tmp_path / "first.json"
    second_file = tmp_path / "second.json"

    for output_file in (
        first_file,
        second_file,
    ):
        result = runner.invoke(
            app,
            _command_args(
                hypothesis_file,
                observation_file,
                review_file,
            )
            + [
                "--json-output",
                str(output_file),
            ],
        )

        assert result.exit_code == 0, result.output

    first = json.loads(
        first_file.read_text(encoding="utf-8")
    )
    second = json.loads(
        second_file.read_text(encoding="utf-8")
    )

    assert first == second
    assert (
        first["feedback_digest"]
        == second["feedback_digest"]
    )
    assert (
        first["feedback_proposals"][0][
            "proposal_digest"
        ]
        == second["feedback_proposals"][0][
            "proposal_digest"
        ]
    )


def test_cli_does_not_mutate_input_files(
    tmp_path,
) -> None:
    (
        hypothesis_packet,
        observation_packet,
        review,
    ) = _artifacts()

    before = copy.deepcopy(
        (
            hypothesis_packet,
            observation_packet,
            review,
        )
    )

    hypothesis_file = _write_json(
        tmp_path,
        "hypotheses.json",
        hypothesis_packet,
    )
    observation_file = _write_json(
        tmp_path,
        "observations.json",
        observation_packet,
    )
    review_file = _write_json(
        tmp_path,
        "observation-review.json",
        review,
    )

    result = runner.invoke(
        app,
        _command_args(
            hypothesis_file,
            observation_file,
            review_file,
        ),
    )

    assert result.exit_code == 0, result.output

    after = (
        json.loads(
            hypothesis_file.read_text(
                encoding="utf-8"
            )
        ),
        json.loads(
            observation_file.read_text(
                encoding="utf-8"
            )
        ),
        json.loads(
            review_file.read_text(
                encoding="utf-8"
            )
        ),
    )

    assert after == before


def test_cli_missing_file_errors(
    tmp_path,
) -> None:
    result = runner.invoke(
        app,
        [
            COMMAND,
            "--hypothesis-file",
            str(tmp_path / "missing-hypotheses.json"),
            "--observation-file",
            str(tmp_path / "missing-observations.json"),
            "--review-file",
            str(tmp_path / "missing-review.json"),
        ],
    )

    assert result.exit_code == 1
    assert (
        "Research hypothesis packet not found"
        in result.output
    )


def test_cli_invalid_json_errors(
    tmp_path,
) -> None:
    (
        _,
        observation_file,
        review_file,
    ) = _write_artifacts(tmp_path)

    hypothesis_file = tmp_path / "invalid.json"
    hypothesis_file.write_text(
        "{not-valid-json",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        _command_args(
            hypothesis_file,
            observation_file,
            review_file,
        ),
    )

    assert result.exit_code == 2
    assert (
        "Invalid hypothesis feedback JSON input"
        in result.output
    )


def test_cli_non_object_json_errors(
    tmp_path,
) -> None:
    (
        _,
        observation_file,
        review_file,
    ) = _write_artifacts(tmp_path)

    hypothesis_file = _write_json(
        tmp_path,
        "list.json",
        ["not", "an", "object"],
    )

    result = runner.invoke(
        app,
        _command_args(
            hypothesis_file,
            observation_file,
            review_file,
        ),
    )

    assert result.exit_code == 2
    assert (
        "Invalid hypothesis feedback input"
        in result.output
    )


def test_cli_help_lists_primary_options() -> None:
    result = runner.invoke(
        app,
        [
            COMMAND,
            "--help",
        ],
    )

    assert result.exit_code == 0, result.output

    output = _normalize_output(result.output)

    assert "--hypothesis-file" in output
    assert "--observation-file" in output
    assert "--review-file" in output
    assert "--output-file" in output
    assert "--json-output" in output


def test_cli_safety_message_is_explicit(
    tmp_path,
) -> None:
    (
        hypothesis_file,
        observation_file,
        review_file,
    ) = _write_artifacts(tmp_path)

    result = runner.invoke(
        app,
        _command_args(
            hypothesis_file,
            observation_file,
            review_file,
        ),
    )

    assert result.exit_code == 0, result.output

    output = _normalize_output(result.output)

    assert "Safety:" in output
    assert (
        "proposed hypothesis-confidence feedback"
        in output
    )
    assert "does not change hypothesis confidence" in output
    assert "alter hypothesis selection" in output
    assert "modify investigation plans" in output
    assert "mutate research state" in output
    assert "generate commands or payloads" in output
    assert "execute tools" in output
    assert "launch browsers" in output
    assert "replay Burp requests" in output
    assert "run Kali tools" in output
    assert "send network requests" in output
    assert "interact with targets" in output
    assert "collect evidence" in output
    assert "validate findings" in output
    assert "submit reports" in output
    assert "confirm vulnerabilities" in output
