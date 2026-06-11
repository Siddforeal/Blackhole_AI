from __future__ import annotations

import copy
import json
import re

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


def _decision_packet(
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
        "Approved for normalized planning records."
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

    return build_research_action_decision_packet(
        proposal,
        proposal_review,
        decision_input,
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


def test_cli_writes_markdown_and_json(tmp_path) -> None:
    decision_file = _write_json(
        tmp_path,
        "decision.json",
        _decision_packet(),
    )
    markdown_file = (
        tmp_path
        / "output"
        / "approved-actions.md"
    )
    json_file = (
        tmp_path
        / "output"
        / "approved-actions.json"
    )

    result = runner.invoke(
        app,
        [
            "brain-chat-research-approved-action-packet",
            "--decision-file",
            str(decision_file),
            "--output-file",
            str(markdown_file),
            "--json-output",
            str(json_file),
        ],
    )

    assert result.exit_code == 0, result.output

    output = _normalize_output(result.output)

    assert "Research Approved Action Packet" in output
    assert (
        "ready-for-typed-tool-request-manifest"
        in output
    )
    assert "Normalized Approved Actions" in output
    assert "Tool family counts" in output
    assert "Adapter family counts" in output
    assert "Risk level counts" in output
    assert "Runtime execution allowed" in output
    assert "false" in output

    assert markdown_file.exists()
    assert json_file.exists()

    data = json.loads(
        json_file.read_text(encoding="utf-8")
    )

    assert data["kind"] == (
        "brain_chat_research_approved_action_packet"
    )
    assert data["packet_status"] == (
        "ready-for-typed-tool-request-manifest"
    )
    assert data["packet_ready"] is True
    assert (
        data["typed_tool_request_manifest_ready"]
        is True
    )
    assert data["approved_action_count"] == 8
    assert data["runtime_gated_action_count"] == 4
    assert data["runtime_execution_allowed"] is False
    assert data["risk_level_counts"] == {
        "high": 1,
        "low": 3,
        "medium": 4,
    }

    markdown = markdown_file.read_text(
        encoding="utf-8"
    )

    assert "# Research Approved Action Packet" in markdown
    assert (
        "typed_tool_request_manifest_ready: `true`"
        in markdown
    )
    assert (
        "runtime_execution_allowed: `false`"
        in markdown
    )


def test_cli_supports_aliases(tmp_path) -> None:
    decision_file = _write_json(
        tmp_path,
        "decision.json",
        _decision_packet(),
    )
    markdown_file = tmp_path / "alias.md"

    result = runner.invoke(
        app,
        [
            "brain-chat-research-approved-action-packet",
            "--decision",
            str(decision_file),
            "--output",
            str(markdown_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert markdown_file.exists()


def test_cli_mixed_decisions_include_only_approved(
    tmp_path,
) -> None:
    decision_packet = _decision_packet(
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
    decision_file = _write_json(
        tmp_path,
        "decision.json",
        decision_packet,
    )
    json_file = tmp_path / "mixed.json"

    result = runner.invoke(
        app,
        [
            "brain-chat-research-approved-action-packet",
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

    assert data["packet_status"] == (
        "ready-for-typed-tool-request-manifest"
    )
    assert data["approved_action_count"] == 4
    assert {
        item["manual_order"]
        for item in data["approved_actions"]
    } == {1, 3, 5, 7}


def test_cli_blocks_non_ready_decision_packet(
    tmp_path,
) -> None:
    decision_packet = _decision_packet()
    decision_packet["decision_status"] = "rejected"

    decision_file = _write_json(
        tmp_path,
        "decision.json",
        decision_packet,
    )
    json_file = tmp_path / "blocked.json"

    result = runner.invoke(
        app,
        [
            "brain-chat-research-approved-action-packet",
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

    assert data["packet_status"] == (
        "blocked-decision-not-ready"
    )
    assert data["packet_ready"] is False
    assert (
        data["typed_tool_request_manifest_ready"]
        is False
    )


def test_cli_blocks_unsafe_decision_packet(
    tmp_path,
) -> None:
    decision_packet = _decision_packet()
    decision_packet["runtime_execution_allowed"] = True

    decision_file = _write_json(
        tmp_path,
        "decision.json",
        decision_packet,
    )
    json_file = tmp_path / "unsafe.json"

    result = runner.invoke(
        app,
        [
            "brain-chat-research-approved-action-packet",
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

    assert data["packet_status"] == (
        "blocked-unsafe-decision-packet"
    )
    assert data["runtime_execution_allowed"] is False
    assert data["counts"]["high_findings"] >= 1


def test_cli_blocks_inconsistent_approved_action(
    tmp_path,
) -> None:
    decision_packet = _decision_packet()
    decision_packet["approved_actions"][0][
        "proposed_tool_family"
    ] = "browser"

    decision_file = _write_json(
        tmp_path,
        "decision.json",
        decision_packet,
    )
    json_file = tmp_path / "inconsistent.json"

    result = runner.invoke(
        app,
        [
            "brain-chat-research-approved-action-packet",
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

    assert data["packet_status"] == (
        "blocked-inconsistent-approved-actions"
    )
    assert data["packet_ready"] is False
    assert data["counts"]["high_findings"] >= 1


def test_cli_synthetic_no_approved_actions(
    tmp_path,
) -> None:
    decision_packet = _decision_packet()
    decision_packet["approved_actions"] = []
    decision_packet["approved_action_count"] = 0

    decision_file = _write_json(
        tmp_path,
        "decision.json",
        decision_packet,
    )
    json_file = tmp_path / "empty.json"

    result = runner.invoke(
        app,
        [
            "brain-chat-research-approved-action-packet",
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

    assert data["packet_status"] == (
        "blocked-no-approved-actions"
    )
    assert data["approved_action_count"] == 0
    assert data["packet_ready"] is False


def test_cli_medium_findings_remain_ready(
    tmp_path,
) -> None:
    decision_packet = _decision_packet()
    decision_packet["approved_actions"][0][
        "expected_artifact"
    ] = ""

    decision_file = _write_json(
        tmp_path,
        "decision.json",
        decision_packet,
    )
    json_file = tmp_path / "medium.json"

    result = runner.invoke(
        app,
        [
            "brain-chat-research-approved-action-packet",
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

    assert data["packet_status"] == (
        "ready-for-typed-tool-request-manifest"
    )
    assert data["packet_ready"] is True
    assert data["counts"]["high_findings"] == 0
    assert data["counts"]["medium_findings"] == 1


def test_cli_missing_file_errors(tmp_path) -> None:
    result = runner.invoke(
        app,
        [
            "brain-chat-research-approved-action-packet",
            "--decision-file",
            str(tmp_path / "missing.json"),
        ],
    )

    assert result.exit_code == 1
    assert (
        "Research action decision JSON not found"
        in result.output
    )


def test_cli_invalid_json_errors(tmp_path) -> None:
    decision_file = tmp_path / "invalid.json"
    decision_file.write_text(
        "{not-json",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "brain-chat-research-approved-action-packet",
            "--decision-file",
            str(decision_file),
        ],
    )

    assert result.exit_code == 2
    assert (
        "Invalid research action decision JSON"
        in result.output
    )


def test_cli_non_object_json_errors(tmp_path) -> None:
    decision_file = _write_json(
        tmp_path,
        "list.json",
        ["not", "object"],
    )

    result = runner.invoke(
        app,
        [
            "brain-chat-research-approved-action-packet",
            "--decision-file",
            str(decision_file),
        ],
    )

    assert result.exit_code == 2
    assert (
        "Invalid approved-action packet input"
        in result.output
    )


def test_cli_creates_nested_output_directories(
    tmp_path,
) -> None:
    decision_file = _write_json(
        tmp_path,
        "decision.json",
        _decision_packet(),
    )
    markdown_file = (
        tmp_path
        / "nested"
        / "markdown"
        / "approved.md"
    )
    json_file = (
        tmp_path
        / "nested"
        / "json"
        / "approved.json"
    )

    result = runner.invoke(
        app,
        [
            "brain-chat-research-approved-action-packet",
            "--decision-file",
            str(decision_file),
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
            "brain-chat-research-approved-action-packet",
            "--help",
        ],
    )

    assert result.exit_code == 0, result.output

    output = _normalize_output(result.output)

    assert "--decision-file" in output
    assert "--decision" in output
    assert "--output-file" in output
    assert "--output" in output
    assert "--json-output" in output


def test_cli_safety_message_is_explicit(
    tmp_path,
) -> None:
    decision_file = _write_json(
        tmp_path,
        "decision.json",
        _decision_packet(),
    )

    result = runner.invoke(
        app,
        [
            "brain-chat-research-approved-action-packet",
            "--decision-file",
            str(decision_file),
        ],
    )

    assert result.exit_code == 0, result.output

    output = _normalize_output(result.output)

    assert "Safety:" in output
    assert "does not generate commands" in output
    assert "install software" in output
    assert "execute tools" in output
    assert "launch browsers" in output
    assert "interact with Burp Suite" in output
    assert "use Kali tools" in output
    assert "send requests" in output
    assert "collect evidence" in output
    assert "validate findings" in output
    assert "mutate state" in output
    assert "submit reports" in output
    assert "confirm vulnerabilities" in output
    assert "typed tool-request manifest" in output
    assert "separate execution gate" in output


def test_cli_does_not_mutate_input_file(
    tmp_path,
) -> None:
    decision_packet = _decision_packet()
    before = copy.deepcopy(decision_packet)

    decision_file = _write_json(
        tmp_path,
        "decision.json",
        decision_packet,
    )

    result = runner.invoke(
        app,
        [
            "brain-chat-research-approved-action-packet",
            "--decision-file",
            str(decision_file),
        ],
    )

    assert result.exit_code == 0, result.output

    after = json.loads(
        decision_file.read_text(encoding="utf-8")
    )

    assert after == before
