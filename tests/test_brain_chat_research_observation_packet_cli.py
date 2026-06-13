from __future__ import annotations

import copy
import json
import re

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()

COMMAND = "brain-chat-research-observation-packet"
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
            "Local source review shows user-controlled worker "
            "configuration reaches job planning."
        ),
        "details": [
            "Reviewed the local controller-to-worker data flow.",
            "No live target interaction was performed.",
        ],
        "artifact_refs": [
            "notes/worker-dataflow.md",
        ],
        "signals": [
            "user-controlled worker configuration",
            "privileged worker boundary",
        ],
        "errors": [],
        "scope_status": "not-applicable",
        "controlled_assets_status": "not-required",
        "redaction_status": "not-required",
        "human_reviewed": True,
    }
    observation.update(overrides)
    return observation


def _ready_input(
    observations: list | None = None,
    **overrides,
) -> dict:
    value = {
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
    value.update(overrides)
    return value


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
    observation_file = _write_json(
        tmp_path,
        "observations.json",
        _ready_input(),
    )
    markdown_file = (
        tmp_path
        / "output"
        / "observation-packet.md"
    )
    json_file = (
        tmp_path
        / "output"
        / "observation-packet.json"
    )

    result = runner.invoke(
        app,
        [
            COMMAND,
            "--observation-file",
            str(observation_file),
            "--output-file",
            str(markdown_file),
            "--json-output",
            str(json_file),
        ],
    )

    assert result.exit_code == 0, result.output

    output = _normalize_output(result.output)

    assert "Research Observation Packet" in output
    assert "ready-for-observation-review" in output
    assert "Normalized Observations" in output
    assert "Preliminary Hypothesis Impacts" in output
    assert "Packet digest:" in output

    assert markdown_file.exists()
    assert json_file.exists()

    data = json.loads(
        json_file.read_text(encoding="utf-8")
    )

    assert data["kind"] == (
        "brain_chat_research_observation_packet"
    )
    assert data["packet_status"] == (
        "ready-for-observation-review"
    )
    assert data["packet_ready"] is True
    assert data["observation_review_ready"] is True
    assert (
        data["hypothesis_feedback_review_ready"]
        is True
    )
    assert (
        data["research_state_transition_ready"]
        is False
    )
    assert data["runtime_execution_allowed"] is False
    assert data["observation_count"] == 1

    observation = data["observations"][0]

    assert observation["observation_id"] == "OBS-001"
    assert observation["request_id"] == "RTR-001"
    assert observation["action_id"] == "ACT-001"
    assert observation["hypothesis_id"] == "HYP-005"
    assert observation["outcome"] == (
        "supports-hypothesis"
    )
    assert observation[
        "preliminary_hypothesis_effect"
    ] == "slightly-strengthen"

    assert data["counts"]["observations"] == 1
    assert data["counts"]["high_findings"] == 0
    assert len(data["packet_digest"]) == 64

    impact = data[
        "preliminary_hypothesis_impacts"
    ][0]

    assert impact["hypothesis_id"] == "HYP-005"
    assert impact["net_confidence_delta"] == 2
    assert impact["preliminary_direction"] == (
        "slightly-strengthen"
    )
    assert impact["automatic_update_allowed"] is False

    markdown = markdown_file.read_text(
        encoding="utf-8"
    )

    assert "# Research Observation Packet" in markdown
    assert (
        "packet_status: "
        "`ready-for-observation-review`"
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


def test_cli_empty_observations_are_blocked(
    tmp_path,
) -> None:
    observation_file = _write_json(
        tmp_path,
        "empty.json",
        {
            "target_name": "demo-self-hosted-product",
            "observations": [],
        },
    )
    json_file = tmp_path / "empty-result.json"

    result = runner.invoke(
        app,
        [
            COMMAND,
            "--observation-file",
            str(observation_file),
            "--json-output",
            str(json_file),
        ],
    )

    assert result.exit_code == 0, result.output

    output = _normalize_output(result.output)

    assert "blocked-no-observations" in output

    data = json.loads(
        json_file.read_text(encoding="utf-8")
    )

    assert data["packet_status"] == (
        "blocked-no-observations"
    )
    assert data["packet_ready"] is False
    assert data["observation_count"] == 0
    assert data["runtime_execution_allowed"] is False


def test_cli_pending_redaction_is_blocked(
    tmp_path,
) -> None:
    observation_file = _write_json(
        tmp_path,
        "redaction-pending.json",
        _ready_input(
            observations=[
                _base_observation(
                    redaction_status="pending",
                )
            ]
        ),
    )
    json_file = tmp_path / "redaction-review.json"

    result = runner.invoke(
        app,
        [
            COMMAND,
            "--observation-file",
            str(observation_file),
            "--json-output",
            str(json_file),
        ],
    )

    assert result.exit_code == 0, result.output

    data = json.loads(
        json_file.read_text(encoding="utf-8")
    )

    assert data["packet_status"] == (
        "blocked-redaction-required"
    )
    assert data["packet_ready"] is False
    assert data["counts"]["high_findings"] >= 1

    categories = {
        item["category"]
        for item in data["findings"]
    }

    assert "observation-redaction" in categories


def test_cli_live_observation_requires_scope(
    tmp_path,
) -> None:
    observation_file = _write_json(
        tmp_path,
        "scope-pending.json",
        _ready_input(
            observations=[
                _base_observation(
                    source_type="http-response",
                    scope_status="pending",
                    controlled_assets_status=(
                        "confirmed"
                    ),
                    redaction_status="reviewed",
                )
            ]
        ),
    )
    json_file = tmp_path / "scope-review.json"

    result = runner.invoke(
        app,
        [
            COMMAND,
            "--observation-file",
            str(observation_file),
            "--json-output",
            str(json_file),
        ],
    )

    assert result.exit_code == 0, result.output

    data = json.loads(
        json_file.read_text(encoding="utf-8")
    )

    assert data["packet_status"] == (
        "blocked-authorization-review-required"
    )
    assert data["packet_ready"] is False

    categories = {
        item["category"]
        for item in data["findings"]
    }

    assert "observation-scope" in categories


def test_cli_unsafe_authority_flag_is_blocked(
    tmp_path,
) -> None:
    observation_file = _write_json(
        tmp_path,
        "unsafe.json",
        _ready_input(
            observations=[
                _base_observation(
                    execution_allowed=True,
                )
            ]
        ),
    )
    json_file = tmp_path / "unsafe-result.json"

    result = runner.invoke(
        app,
        [
            COMMAND,
            "--observation-file",
            str(observation_file),
            "--json-output",
            str(json_file),
        ],
    )

    assert result.exit_code == 0, result.output

    data = json.loads(
        json_file.read_text(encoding="utf-8")
    )

    assert data["packet_status"] == (
        "blocked-unsafe-observations"
    )
    assert data["packet_ready"] is False
    assert data["execution_allowed"] is False
    assert data["runtime_execution_allowed"] is False

    categories = {
        item["category"]
        for item in data["findings"]
    }

    assert "observation-safety" in categories


def test_cli_aliases_work(tmp_path) -> None:
    observation_file = _write_json(
        tmp_path,
        "observations.json",
        _ready_input(),
    )
    markdown_file = tmp_path / "alias-output.md"

    result = runner.invoke(
        app,
        [
            COMMAND,
            "--observations",
            str(observation_file),
            "--output",
            str(markdown_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert markdown_file.exists()

    markdown = markdown_file.read_text(
        encoding="utf-8"
    )

    assert "# Research Observation Packet" in markdown


def test_cli_creates_nested_output_directories(
    tmp_path,
) -> None:
    observation_file = _write_json(
        tmp_path,
        "observations.json",
        _ready_input(),
    )
    markdown_file = (
        tmp_path
        / "nested"
        / "markdown"
        / "observation-packet.md"
    )
    json_file = (
        tmp_path
        / "nested"
        / "json"
        / "observation-packet.json"
    )

    result = runner.invoke(
        app,
        [
            COMMAND,
            "--observation-file",
            str(observation_file),
            "--output-file",
            str(markdown_file),
            "--json-output",
            str(json_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert markdown_file.exists()
    assert json_file.exists()


def test_cli_output_is_deterministic(tmp_path) -> None:
    observation_file = _write_json(
        tmp_path,
        "observations.json",
        _ready_input(),
    )
    first_file = tmp_path / "first.json"
    second_file = tmp_path / "second.json"

    for output_file in (
        first_file,
        second_file,
    ):
        result = runner.invoke(
            app,
            [
                COMMAND,
                "--observation-file",
                str(observation_file),
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
        first["packet_digest"]
        == second["packet_digest"]
    )
    assert (
        first["observations"][0][
            "observation_digest"
        ]
        == second["observations"][0][
            "observation_digest"
        ]
    )


def test_cli_does_not_mutate_input_file(
    tmp_path,
) -> None:
    payload = _ready_input()
    before = copy.deepcopy(payload)

    observation_file = _write_json(
        tmp_path,
        "observations.json",
        payload,
    )

    result = runner.invoke(
        app,
        [
            COMMAND,
            "--observation-file",
            str(observation_file),
        ],
    )

    assert result.exit_code == 0, result.output

    after = json.loads(
        observation_file.read_text(
            encoding="utf-8"
        )
    )

    assert after == before


def test_cli_missing_file_errors(tmp_path) -> None:
    result = runner.invoke(
        app,
        [
            COMMAND,
            "--observation-file",
            str(tmp_path / "missing.json"),
        ],
    )

    assert result.exit_code == 1
    assert (
        "Research observation input not found"
        in result.output
    )


def test_cli_invalid_json_errors(tmp_path) -> None:
    observation_file = tmp_path / "invalid.json"
    observation_file.write_text(
        "{not-valid-json",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            COMMAND,
            "--observation-file",
            str(observation_file),
        ],
    )

    assert result.exit_code == 2
    assert (
        "Invalid research observation JSON"
        in result.output
    )


def test_cli_non_object_json_errors(tmp_path) -> None:
    observation_file = _write_json(
        tmp_path,
        "list.json",
        ["not", "an", "object"],
    )

    result = runner.invoke(
        app,
        [
            COMMAND,
            "--observation-file",
            str(observation_file),
        ],
    )

    assert result.exit_code == 2
    assert (
        "Invalid research observation input"
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

    assert "--observation-file" in output
    assert "--output-file" in output
    assert "--json-output" in output


def test_cli_safety_message_is_explicit(
    tmp_path,
) -> None:
    observation_file = _write_json(
        tmp_path,
        "observations.json",
        _ready_input(),
    )

    result = runner.invoke(
        app,
        [
            COMMAND,
            "--observation-file",
            str(observation_file),
        ],
    )

    assert result.exit_code == 0, result.output

    output = _normalize_output(result.output)

    assert "Safety:" in output
    assert "imports and normalizes" in output
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
