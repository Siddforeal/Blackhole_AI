from __future__ import annotations

import copy
import json
import re

from typer.testing import CliRunner

from bugintel.cli import app
from bugintel.core.brain_chat_research_observation_packet import (
    build_research_observation_packet,
)


runner = CliRunner()

COMMAND = "brain-chat-research-observation-review-gate"
FOCUS_ENDPOINT = "/api/projects/123/workers/456"


def _base_observation(**overrides) -> dict:
    observation = {
        "request_id": "RTR-001",
        "action_id": "ACT-001",
        "hypothesis_id": "HYP-005",
        "source_type": "manual-note",
        "outcome": "supports-hypothesis",
        "evidence_strength": "moderate",
        "summary": (
            "Local source review shows worker configuration "
            "reaches job planning."
        ),
        "details": [
            "Reviewed local controller data flow.",
            "No live target interaction was performed.",
        ],
        "artifact_refs": [
            "notes/worker-dataflow.md",
        ],
        "signals": [
            "worker trust boundary",
        ],
        "errors": [],
        "scope_status": "not-applicable",
        "controlled_assets_status": "not-required",
        "redaction_status": "not-required",
        "human_reviewed": True,
    }
    observation.update(overrides)
    return observation


def _packet(
    observations: list | None = None,
    **overrides,
) -> dict:
    payload = {
        "target_name": "demo-self-hosted-product",
        "focus_endpoint": FOCUS_ENDPOINT,
        "source_manifest_digest": "a" * 64,
        "source_review_digest": "b" * 64,
        "observations": (
            observations
            if observations is not None
            else [_base_observation()]
        ),
    }
    payload.update(overrides)

    return build_research_observation_packet(
        payload
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
    packet_file = _write_json(
        tmp_path,
        "observation-packet.json",
        _packet(),
    )
    markdown_file = (
        tmp_path
        / "output"
        / "observation-review.md"
    )
    json_file = (
        tmp_path
        / "output"
        / "observation-review.json"
    )

    result = runner.invoke(
        app,
        [
            COMMAND,
            "--packet-file",
            str(packet_file),
            "--output-file",
            str(markdown_file),
            "--json-output",
            str(json_file),
        ],
    )

    assert result.exit_code == 0, result.output

    output = _normalize_output(result.output)

    assert "Research Observation Review Gate" in output
    assert (
        "ready-for-hypothesis-feedback-review"
        in output
    )
    assert "Observation Reviews" in output
    assert (
        "Verified Preliminary Hypothesis Impacts"
        in output
    )
    assert "Source packet digest:" in output
    assert "Review digest:" in output

    assert markdown_file.exists()
    assert json_file.exists()

    data = json.loads(
        json_file.read_text(encoding="utf-8")
    )

    assert data["kind"] == (
        "brain_chat_research_observation_review_gate"
    )
    assert data["review_status"] == (
        "ready-for-hypothesis-feedback-review"
    )
    assert data["review_ready"] is True
    assert (
        data["hypothesis_feedback_packet_ready"]
        is True
    )
    assert (
        data["research_state_transition_ready"]
        is False
    )
    assert data["runtime_execution_allowed"] is False
    assert data["observation_count"] == 1

    assert data["counts"]["observations"] == 1
    assert data["counts"]["ready_observations"] == 1
    assert data["counts"]["blocked_observations"] == 0
    assert data["counts"]["high_findings"] == 0

    observation_review = data[
        "observation_reviews"
    ][0]

    assert observation_review[
        "observation_id"
    ] == "OBS-001"
    assert observation_review[
        "request_id"
    ] == "RTR-001"
    assert observation_review[
        "action_id"
    ] == "ACT-001"
    assert observation_review[
        "hypothesis_id"
    ] == "HYP-005"
    assert observation_review[
        "expected_confidence_delta"
    ] == 2
    assert observation_review[
        "expected_hypothesis_effect"
    ] == "slightly-strengthen"
    assert observation_review[
        "review_ready"
    ] is True
    assert observation_review[
        "automatic_hypothesis_update_allowed"
    ] is False

    assert len(data["source_packet_digest"]) == 64
    assert len(data["review_digest"]) == 64

    markdown = markdown_file.read_text(
        encoding="utf-8"
    )

    assert (
        "# Research Observation Review Gate"
        in markdown
    )
    assert (
        "review_status: "
        "`ready-for-hypothesis-feedback-review`"
        in markdown
    )
    assert "review_ready: `true`" in markdown
    assert (
        "research_state_transition_ready: `false`"
        in markdown
    )
    assert (
        "runtime_execution_allowed: `false`"
        in markdown
    )


def test_cli_tampered_packet_is_blocked(
    tmp_path,
) -> None:
    packet = _packet()
    packet["observations"][0]["summary"] = (
        "Tampered observation summary."
    )

    packet_file = _write_json(
        tmp_path,
        "tampered-packet.json",
        packet,
    )
    json_file = tmp_path / "tampered-review.json"

    result = runner.invoke(
        app,
        [
            COMMAND,
            "--packet-file",
            str(packet_file),
            "--json-output",
            str(json_file),
        ],
    )

    assert result.exit_code == 0, result.output

    output = _normalize_output(result.output)

    assert (
        "blocked-observation-integrity-failure"
        in output
    )

    data = json.loads(
        json_file.read_text(encoding="utf-8")
    )

    assert data["review_status"] == (
        "blocked-observation-integrity-failure"
    )
    assert data["review_ready"] is False
    assert (
        data["hypothesis_feedback_packet_ready"]
        is False
    )
    assert data["runtime_execution_allowed"] is False

    categories = {
        item["category"]
        for item in (
            data["packet_findings"]
            + data["observation_findings"]
        )
    }

    assert "packet-integrity" in categories
    assert "observation-integrity" in categories


def test_cli_source_packet_not_ready_is_blocked(
    tmp_path,
) -> None:
    packet = _packet(
        observations=[
            _base_observation(
                human_reviewed=False,
            )
        ]
    )

    assert packet["packet_status"] == (
        "review-needed-observation-gaps"
    )

    packet_file = _write_json(
        tmp_path,
        "not-ready-packet.json",
        packet,
    )
    json_file = tmp_path / "not-ready-review.json"

    result = runner.invoke(
        app,
        [
            COMMAND,
            "--packet-file",
            str(packet_file),
            "--json-output",
            str(json_file),
        ],
    )

    assert result.exit_code == 0, result.output

    data = json.loads(
        json_file.read_text(encoding="utf-8")
    )

    assert data["review_status"] == (
        "blocked-observation-packet-not-ready"
    )
    assert data["review_ready"] is False
    assert data["runtime_execution_allowed"] is False

    categories = {
        item["category"]
        for item in data["packet_findings"]
    }

    assert "packet-readiness" in categories


def test_cli_unsafe_packet_is_blocked(
    tmp_path,
) -> None:
    packet = _packet()
    packet["execution_allowed"] = True

    packet_file = _write_json(
        tmp_path,
        "unsafe-packet.json",
        packet,
    )
    json_file = tmp_path / "unsafe-review.json"

    result = runner.invoke(
        app,
        [
            COMMAND,
            "--packet-file",
            str(packet_file),
            "--json-output",
            str(json_file),
        ],
    )

    assert result.exit_code == 0, result.output

    data = json.loads(
        json_file.read_text(encoding="utf-8")
    )

    assert data["review_status"] == (
        "blocked-unsafe-observations"
    )
    assert data["review_ready"] is False
    assert data["execution_allowed"] is False
    assert data["runtime_execution_allowed"] is False

    categories = {
        item["category"]
        for item in data["packet_findings"]
    }

    assert "packet-safety" in categories


def test_cli_action_only_linkage_is_ready(
    tmp_path,
) -> None:
    packet = _packet(
        observations=[
            _base_observation(
                request_id=None,
                hypothesis_id=None,
                action_id="ACT-123",
            )
        ]
    )

    packet_file = _write_json(
        tmp_path,
        "action-only.json",
        packet,
    )
    json_file = tmp_path / "action-only-review.json"

    result = runner.invoke(
        app,
        [
            COMMAND,
            "--packet-file",
            str(packet_file),
            "--json-output",
            str(json_file),
        ],
    )

    assert result.exit_code == 0, result.output

    data = json.loads(
        json_file.read_text(encoding="utf-8")
    )

    assert data["review_status"] == (
        "ready-for-hypothesis-feedback-review"
    )
    assert data["review_ready"] is True
    assert data[
        "expected_preliminary_hypothesis_impacts"
    ] == []

    observation_review = data[
        "observation_reviews"
    ][0]

    assert observation_review[
        "action_id"
    ] == "ACT-123"
    assert observation_review[
        "hypothesis_id"
    ] is None
    assert observation_review[
        "hypothesis_feedback_ready"
    ] is False


def test_cli_aliases_work(tmp_path) -> None:
    packet_file = _write_json(
        tmp_path,
        "observation-packet.json",
        _packet(),
    )
    markdown_file = tmp_path / "alias-review.md"

    result = runner.invoke(
        app,
        [
            COMMAND,
            "--observation-packet",
            str(packet_file),
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
        "# Research Observation Review Gate"
        in markdown
    )


def test_cli_creates_nested_output_directories(
    tmp_path,
) -> None:
    packet_file = _write_json(
        tmp_path,
        "observation-packet.json",
        _packet(),
    )
    markdown_file = (
        tmp_path
        / "nested"
        / "markdown"
        / "observation-review.md"
    )
    json_file = (
        tmp_path
        / "nested"
        / "json"
        / "observation-review.json"
    )

    result = runner.invoke(
        app,
        [
            COMMAND,
            "--packet-file",
            str(packet_file),
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
    packet_file = _write_json(
        tmp_path,
        "observation-packet.json",
        _packet(),
    )
    first_file = tmp_path / "first-review.json"
    second_file = tmp_path / "second-review.json"

    for output_file in (
        first_file,
        second_file,
    ):
        result = runner.invoke(
            app,
            [
                COMMAND,
                "--packet-file",
                str(packet_file),
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
        first["review_digest"]
        == second["review_digest"]
    )


def test_cli_does_not_mutate_input_file(
    tmp_path,
) -> None:
    packet = _packet()
    before = copy.deepcopy(packet)

    packet_file = _write_json(
        tmp_path,
        "observation-packet.json",
        packet,
    )

    result = runner.invoke(
        app,
        [
            COMMAND,
            "--packet-file",
            str(packet_file),
        ],
    )

    assert result.exit_code == 0, result.output

    after = json.loads(
        packet_file.read_text(encoding="utf-8")
    )

    assert after == before


def test_cli_missing_file_errors(
    tmp_path,
) -> None:
    result = runner.invoke(
        app,
        [
            COMMAND,
            "--packet-file",
            str(tmp_path / "missing.json"),
        ],
    )

    assert result.exit_code == 1
    assert (
        "Research observation packet not found"
        in result.output
    )


def test_cli_invalid_json_errors(
    tmp_path,
) -> None:
    packet_file = tmp_path / "invalid.json"
    packet_file.write_text(
        "{not-valid-json",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            COMMAND,
            "--packet-file",
            str(packet_file),
        ],
    )

    assert result.exit_code == 2
    assert (
        "Invalid research observation packet JSON"
        in result.output
    )


def test_cli_non_object_json_errors(
    tmp_path,
) -> None:
    packet_file = _write_json(
        tmp_path,
        "list.json",
        ["not", "an", "object"],
    )

    result = runner.invoke(
        app,
        [
            COMMAND,
            "--packet-file",
            str(packet_file),
        ],
    )

    assert result.exit_code == 2
    assert (
        "Invalid research observation review input"
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

    assert "--packet-file" in output
    assert "--output-file" in output
    assert "--json-output" in output


def test_cli_safety_message_is_explicit(
    tmp_path,
) -> None:
    packet_file = _write_json(
        tmp_path,
        "observation-packet.json",
        _packet(),
    )

    result = runner.invoke(
        app,
        [
            COMMAND,
            "--packet-file",
            str(packet_file),
        ],
    )

    assert result.exit_code == 0, result.output

    output = _normalize_output(result.output)

    assert "Safety:" in output
    assert "local integrity" in output
    assert "linkage" in output
    assert "authorization" in output
    assert "redaction" in output
    assert "hypothesis-impact consistency" in output
    assert "does not execute commands" in output
    assert "launch browsers" in output
    assert "replay Burp requests" in output
    assert "run Kali tools" in output
    assert "send network requests" in output
    assert "interact with targets" in output
    assert "collect evidence" in output
    assert "validate findings" in output
    assert "change hypothesis confidence" in output
    assert "mutate research state" in output
    assert "submit reports" in output
    assert "confirm vulnerabilities" in output
