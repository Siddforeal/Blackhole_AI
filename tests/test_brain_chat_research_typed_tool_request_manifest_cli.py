from __future__ import annotations

import copy
import json
import re
import string

from typer.testing import CliRunner

from bugintel.cli import app
from bugintel.core.brain_chat_research_action_decision_packet import (
    build_research_action_decision_packet,
    build_research_action_decision_template,
)
from bugintel.core.brain_chat_research_action_proposal_packet import (
    build_research_action_proposal_packet,
)
from bugintel.core.brain_chat_research_action_proposal_review_gate import (
    build_research_action_proposal_review_gate,
)
from bugintel.core.brain_chat_research_approved_action_packet import (
    build_research_approved_action_packet,
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


def _approved_action_packet(
    decisions: list[str] | None = None,
) -> dict:
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

    proposal_review = (
        build_research_action_proposal_review_gate(
            proposal
        )
    )

    decision_input = (
        build_research_action_decision_template(
            proposal
        )
    )
    decision_input["reviewer"] = (
        "authorized-human-reviewer"
    )
    decision_input["overall_reason"] = (
        "Approved for typed request planning."
    )

    values = decisions or [
        "approved"
        for _ in decision_input["decisions"]
    ]

    assert len(values) == len(
        decision_input["decisions"]
    )

    for item, decision in zip(
        decision_input["decisions"],
        values,
        strict=True,
    ):
        item["decision"] = decision
        item["reason"] = (
            f"Human decision recorded as {decision}."
        )

    decision_packet = (
        build_research_action_decision_packet(
            proposal,
            proposal_review,
            decision_input,
        )
    )

    return build_research_approved_action_packet(
        decision_packet
    )


def _write_json(tmp_path, name: str, value):
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


def _is_sha256(value: str) -> bool:
    return (
        len(value) == 64
        and all(
            character in string.hexdigits
            for character in value
        )
    )


def test_cli_writes_markdown_and_json(tmp_path) -> None:
    approved_file = _write_json(
        tmp_path,
        "approved-actions.json",
        _approved_action_packet(),
    )
    markdown_file = (
        tmp_path
        / "output"
        / "typed-manifest.md"
    )
    json_file = (
        tmp_path
        / "output"
        / "typed-manifest.json"
    )

    result = runner.invoke(
        app,
        [
            (
                "brain-chat-research-typed-"
                "tool-request-manifest"
            ),
            "--approved-action-file",
            str(approved_file),
            "--output-file",
            str(markdown_file),
            "--json-output",
            str(json_file),
        ],
    )

    assert result.exit_code == 0, result.output

    output = _normalize_output(result.output)

    assert (
        "Research Typed Tool Request Manifest"
        in output
    )
    assert (
        "ready-for-tool-execution-gate-review"
        in output
    )
    assert "Typed Planning Requests" in output
    assert "Execution-gate compatibility preview" in output
    assert "blocked-missing-focus-endpoint" in output
    assert "Digests:" in output

    assert markdown_file.exists()
    assert json_file.exists()

    data = json.loads(
        json_file.read_text(encoding="utf-8")
    )

    assert data["kind"] == (
        "brain_chat_research_typed_tool_request_manifest"
    )
    assert data["manifest_status"] == (
        "ready-for-tool-execution-gate-review"
    )
    assert data["manifest_ready"] is True
    assert data["typed_request_count"] == 8
    assert data["runtime_execution_allowed"] is False
    assert (
        data["execution_gate_preview_decision"]
        == "blocked-missing-focus-endpoint"
    )
    assert (
        data["execution_gate_preview_execution_allowed"]
        is False
    )
    assert _is_sha256(
        data["approved_action_packet_digest"]
    )
    assert _is_sha256(data["manifest_digest"])

    markdown = markdown_file.read_text(
        encoding="utf-8"
    )

    assert (
        "# Research Typed Tool Request Manifest"
        in markdown
    )
    assert "manifest_ready: `true`" in markdown
    assert (
        "runtime_execution_allowed: `false`"
        in markdown
    )


def test_cli_focus_endpoint_override(tmp_path) -> None:
    approved_file = _write_json(
        tmp_path,
        "approved-actions.json",
        _approved_action_packet(),
    )
    json_file = tmp_path / "focused.json"
    endpoint = "/api/projects/123/workers/456"

    result = runner.invoke(
        app,
        [
            (
                "brain-chat-research-typed-"
                "tool-request-manifest"
            ),
            "--approved-action-file",
            str(approved_file),
            "--focus-endpoint",
            endpoint,
            "--json-output",
            str(json_file),
        ],
    )

    assert result.exit_code == 0, result.output

    data = json.loads(
        json_file.read_text(encoding="utf-8")
    )

    assert data["focus_endpoint"] == endpoint
    assert (
        data[
            "requires_focus_endpoint_before_runtime_review"
        ]
        is False
    )
    assert (
        data["execution_gate_preview_decision"]
        == "blocked-manifest-execution-disabled"
    )
    assert (
        data["execution_gate_input"][
            "focus_endpoint"
        ]
        == endpoint
    )
    assert data["runtime_execution_allowed"] is False


def test_cli_aliases(tmp_path) -> None:
    approved_file = _write_json(
        tmp_path,
        "approved-actions.json",
        _approved_action_packet(),
    )
    markdown_file = tmp_path / "alias.md"

    result = runner.invoke(
        app,
        [
            (
                "brain-chat-research-typed-"
                "tool-request-manifest"
            ),
            "--approved-actions",
            str(approved_file),
            "--output",
            str(markdown_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert markdown_file.exists()


def test_cli_mixed_decisions_generate_subset(
    tmp_path,
) -> None:
    packet = _approved_action_packet(
        [
            "approved",
            "rejected",
            "approved",
            "deferred",
            "approved",
            "rejected",
            "approved",
            "rejected",
        ]
    )
    approved_file = _write_json(
        tmp_path,
        "approved-actions.json",
        packet,
    )
    json_file = tmp_path / "subset.json"

    result = runner.invoke(
        app,
        [
            (
                "brain-chat-research-typed-"
                "tool-request-manifest"
            ),
            "--approved-action-file",
            str(approved_file),
            "--json-output",
            str(json_file),
        ],
    )

    assert result.exit_code == 0, result.output

    data = json.loads(
        json_file.read_text(encoding="utf-8")
    )

    assert data["typed_request_count"] == 4
    assert {
        item["manual_order"]
        for item in data["typed_requests"]
    } == {1, 3, 5, 7}


def test_cli_blocks_non_ready_source(tmp_path) -> None:
    packet = _approved_action_packet()
    packet["packet_ready"] = False

    approved_file = _write_json(
        tmp_path,
        "approved-actions.json",
        packet,
    )
    json_file = tmp_path / "blocked.json"

    result = runner.invoke(
        app,
        [
            (
                "brain-chat-research-typed-"
                "tool-request-manifest"
            ),
            "--approved-action-file",
            str(approved_file),
            "--json-output",
            str(json_file),
        ],
    )

    assert result.exit_code == 0, result.output

    data = json.loads(
        json_file.read_text(encoding="utf-8")
    )

    assert data["manifest_status"] == (
        "blocked-approved-action-packet-not-ready"
    )
    assert data["manifest_ready"] is False
    assert data["runtime_execution_allowed"] is False


def test_cli_blocks_unsafe_source(tmp_path) -> None:
    packet = _approved_action_packet()
    packet["execution_allowed"] = True

    approved_file = _write_json(
        tmp_path,
        "approved-actions.json",
        packet,
    )
    json_file = tmp_path / "unsafe.json"

    result = runner.invoke(
        app,
        [
            (
                "brain-chat-research-typed-"
                "tool-request-manifest"
            ),
            "--approved-action-file",
            str(approved_file),
            "--json-output",
            str(json_file),
        ],
    )

    assert result.exit_code == 0, result.output

    data = json.loads(
        json_file.read_text(encoding="utf-8")
    )

    assert data["manifest_status"] == (
        "blocked-unsafe-approved-action-packet"
    )
    assert data["counts"]["high_findings"] >= 1
    assert data["runtime_execution_allowed"] is False


def test_cli_blocks_invalid_typed_request(
    tmp_path,
) -> None:
    packet = _approved_action_packet()
    packet["approved_actions"][0]["tool_family"] = (
        "browser"
    )

    approved_file = _write_json(
        tmp_path,
        "approved-actions.json",
        packet,
    )
    json_file = tmp_path / "invalid-request.json"

    result = runner.invoke(
        app,
        [
            (
                "brain-chat-research-typed-"
                "tool-request-manifest"
            ),
            "--approved-action-file",
            str(approved_file),
            "--json-output",
            str(json_file),
        ],
    )

    assert result.exit_code == 0, result.output

    data = json.loads(
        json_file.read_text(encoding="utf-8")
    )

    assert data["manifest_status"] == (
        "blocked-invalid-typed-requests"
    )
    assert data["counts"]["high_findings"] >= 1
    assert data["manifest_ready"] is False


def test_cli_medium_findings_remain_ready(
    tmp_path,
) -> None:
    packet = _approved_action_packet()
    packet["approved_actions"][0][
        "expected_artifact"
    ] = ""

    approved_file = _write_json(
        tmp_path,
        "approved-actions.json",
        packet,
    )
    json_file = tmp_path / "medium.json"

    result = runner.invoke(
        app,
        [
            (
                "brain-chat-research-typed-"
                "tool-request-manifest"
            ),
            "--approved-action-file",
            str(approved_file),
            "--json-output",
            str(json_file),
        ],
    )

    assert result.exit_code == 0, result.output

    data = json.loads(
        json_file.read_text(encoding="utf-8")
    )

    assert data["manifest_status"] == (
        "ready-for-tool-execution-gate-review"
    )
    assert data["manifest_ready"] is True
    assert data["counts"]["high_findings"] == 0
    assert data["counts"]["medium_findings"] == 1


def test_cli_is_deterministic(tmp_path) -> None:
    approved_file = _write_json(
        tmp_path,
        "approved-actions.json",
        _approved_action_packet(),
    )
    first_file = tmp_path / "first.json"
    second_file = tmp_path / "second.json"

    for output_file in (first_file, second_file):
        result = runner.invoke(
            app,
            [
                (
                    "brain-chat-research-typed-"
                    "tool-request-manifest"
                ),
                "--approved-action-file",
                str(approved_file),
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

    assert first["manifest_digest"] == (
        second["manifest_digest"]
    )
    assert first["typed_requests"] == (
        second["typed_requests"]
    )


def test_cli_missing_file_errors(tmp_path) -> None:
    result = runner.invoke(
        app,
        [
            (
                "brain-chat-research-typed-"
                "tool-request-manifest"
            ),
            "--approved-action-file",
            str(tmp_path / "missing.json"),
        ],
    )

    assert result.exit_code == 1
    assert (
        "Research approved-action JSON not found"
        in result.output
    )


def test_cli_invalid_json_errors(tmp_path) -> None:
    approved_file = tmp_path / "invalid.json"
    approved_file.write_text(
        "{not-json",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            (
                "brain-chat-research-typed-"
                "tool-request-manifest"
            ),
            "--approved-action-file",
            str(approved_file),
        ],
    )

    assert result.exit_code == 2
    assert (
        "Invalid research approved-action JSON"
        in result.output
    )


def test_cli_non_object_json_errors(tmp_path) -> None:
    approved_file = _write_json(
        tmp_path,
        "list.json",
        ["not", "object"],
    )

    result = runner.invoke(
        app,
        [
            (
                "brain-chat-research-typed-"
                "tool-request-manifest"
            ),
            "--approved-action-file",
            str(approved_file),
        ],
    )

    assert result.exit_code == 2
    assert (
        "Invalid typed tool-request manifest input"
        in result.output
    )


def test_cli_creates_nested_output_directories(
    tmp_path,
) -> None:
    approved_file = _write_json(
        tmp_path,
        "approved-actions.json",
        _approved_action_packet(),
    )
    markdown_file = (
        tmp_path
        / "nested"
        / "markdown"
        / "manifest.md"
    )
    json_file = (
        tmp_path
        / "nested"
        / "json"
        / "manifest.json"
    )

    result = runner.invoke(
        app,
        [
            (
                "brain-chat-research-typed-"
                "tool-request-manifest"
            ),
            "--approved-action-file",
            str(approved_file),
            "--output-file",
            str(markdown_file),
            "--json-output",
            str(json_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert markdown_file.exists()
    assert json_file.exists()


def test_cli_help_lists_options() -> None:
    result = runner.invoke(
        app,
        [
            (
                "brain-chat-research-typed-"
                "tool-request-manifest"
            ),
            "--help",
        ],
    )

    assert result.exit_code == 0, result.output

    output = _normalize_output(result.output)

    assert "--approved-action-file" in output
    assert "--focus-endpoint" in output
    assert "--output-file" in output
    assert "--output" in output
    assert "--json-output" in output


def test_cli_safety_message_is_explicit(
    tmp_path,
) -> None:
    approved_file = _write_json(
        tmp_path,
        "approved-actions.json",
        _approved_action_packet(),
    )

    result = runner.invoke(
        app,
        [
            (
                "brain-chat-research-typed-"
                "tool-request-manifest"
            ),
            "--approved-action-file",
            str(approved_file),
        ],
    )

    assert result.exit_code == 0, result.output

    output = _normalize_output(result.output)

    assert "Safety:" in output
    assert "does not generate commands or payloads" in (
        output
    )
    assert "install software" in output
    assert "execute tools" in output
    assert "launch browsers" in output
    assert "replay Burp requests" in output
    assert "use Kali tools" in output
    assert "send network requests" in output
    assert "collect evidence" in output
    assert "validate findings" in output
    assert "mutate state" in output
    assert "submit reports" in output
    assert "confirm vulnerabilities" in output


def test_cli_does_not_mutate_input_file(
    tmp_path,
) -> None:
    packet = _approved_action_packet()
    before = copy.deepcopy(packet)

    approved_file = _write_json(
        tmp_path,
        "approved-actions.json",
        packet,
    )

    result = runner.invoke(
        app,
        [
            (
                "brain-chat-research-typed-"
                "tool-request-manifest"
            ),
            "--approved-action-file",
            str(approved_file),
            "--focus-endpoint",
            "/api/projects/123/workers/456",
        ],
    )

    assert result.exit_code == 0, result.output

    after = json.loads(
        approved_file.read_text(encoding="utf-8")
    )

    assert after == before
