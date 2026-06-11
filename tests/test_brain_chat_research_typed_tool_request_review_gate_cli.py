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
from bugintel.core.brain_chat_research_approved_action_packet import (
    build_research_approved_action_packet,
)
from bugintel.core.brain_chat_research_investigation_plan_packet import (
    build_research_investigation_plan_packet,
)
from bugintel.core.brain_chat_research_investigation_plan_review_gate import (
    build_research_investigation_plan_review_gate,
)
from bugintel.core.brain_chat_research_typed_tool_request_manifest import (
    build_research_typed_tool_request_manifest,
)


runner = CliRunner()

COMMAND = (
    "brain-chat-research-typed-tool-request-review-gate"
)
FOCUS_ENDPOINT = "/api/projects/123/workers/456"


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


def _approved_action_packet() -> dict:
    plan = build_research_investigation_plan_packet(
        _selection_packet()
    )
    plan_review = (
        build_research_investigation_plan_review_gate(
            plan
        )
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
        "Approved for typed request review."
    )

    for item in decision_input["decisions"]:
        item["decision"] = "approved"
        item["reason"] = (
            "Approved for typed request review."
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


def _manifest(
    focus_endpoint: str | None = FOCUS_ENDPOINT,
) -> dict:
    approved = _approved_action_packet()

    if focus_endpoint is not None:
        approved["focus_endpoint"] = focus_endpoint

    return build_research_typed_tool_request_manifest(
        approved
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
    manifest_file = _write_json(
        tmp_path,
        "typed-manifest.json",
        _manifest(),
    )
    markdown_file = (
        tmp_path
        / "output"
        / "typed-request-review.md"
    )
    json_file = (
        tmp_path
        / "output"
        / "typed-request-review.json"
    )

    result = runner.invoke(
        app,
        [
            COMMAND,
            "--manifest-file",
            str(manifest_file),
            "--output-file",
            str(markdown_file),
            "--json-output",
            str(json_file),
        ],
    )

    assert result.exit_code == 0, result.output

    output = _normalize_output(result.output)

    assert (
        "Research Typed Tool Request Review Gate"
        in output
    )
    assert (
        "ready-for-runtime-approval-template"
        in output
    )
    assert "Typed Request Reviews" in output
    assert "Runtime approval template ready" in output
    assert "Runtime execution allowed" in output

    assert markdown_file.exists()
    assert json_file.exists()

    data = json.loads(
        json_file.read_text(encoding="utf-8")
    )

    assert data["kind"] == (
        "brain_chat_research_typed_tool_request_review_gate"
    )
    assert data["review_status"] == (
        "ready-for-runtime-approval-template"
    )
    assert data["review_ready"] is True
    assert (
        data["runtime_approval_template_ready"]
        is True
    )
    assert data["runtime_execution_allowed"] is False
    assert data["typed_request_count"] == 8
    assert data["counts"]["ready_requests"] == 8
    assert data["counts"]["blocked_requests"] == 0
    assert data["counts"]["high_findings"] == 0

    markdown = markdown_file.read_text(
        encoding="utf-8"
    )

    assert (
        "# Research Typed Tool Request Review Gate"
        in markdown
    )
    assert (
        "review_status: "
        "`ready-for-runtime-approval-template`"
        in markdown
    )
    assert (
        "runtime_execution_allowed: `false`"
        in markdown
    )


def test_cli_missing_focus_endpoint_is_blocked(
    tmp_path,
) -> None:
    manifest_file = _write_json(
        tmp_path,
        "no-focus.json",
        _manifest(focus_endpoint=None),
    )
    json_file = tmp_path / "blocked.json"

    result = runner.invoke(
        app,
        [
            COMMAND,
            "--manifest-file",
            str(manifest_file),
            "--json-output",
            str(json_file),
        ],
    )

    assert result.exit_code == 0, result.output

    output = _normalize_output(result.output)

    assert "blocked-missing-focus-endpoint" in output
    assert "Focus endpoint" in output

    data = json.loads(
        json_file.read_text(encoding="utf-8")
    )

    assert data["focus_endpoint"] is None
    assert data["review_status"] == (
        "blocked-missing-focus-endpoint"
    )
    assert data["review_ready"] is False
    assert (
        data["runtime_approval_template_ready"]
        is False
    )
    assert data["runtime_execution_allowed"] is False
    assert data["counts"]["high_findings"] >= 1


def test_cli_detects_tampered_request(
    tmp_path,
) -> None:
    manifest = _manifest()
    manifest["typed_requests"][0]["purpose"] = (
        "tampered purpose"
    )

    manifest_file = _write_json(
        tmp_path,
        "tampered.json",
        manifest,
    )
    json_file = tmp_path / "tampered-review.json"

    result = runner.invoke(
        app,
        [
            COMMAND,
            "--manifest-file",
            str(manifest_file),
            "--json-output",
            str(json_file),
        ],
    )

    assert result.exit_code == 0, result.output

    data = json.loads(
        json_file.read_text(encoding="utf-8")
    )

    assert data["review_status"] == (
        "blocked-invalid-typed-tool-requests"
    )
    assert data["review_ready"] is False
    assert data["counts"]["high_findings"] >= 2

    categories = {
        item["category"]
        for item in (
            data["manifest_findings"]
            + data["request_findings"]
        )
    }

    assert "manifest-integrity" in categories
    assert "request-integrity" in categories


def test_cli_detects_unsafe_manifest(
    tmp_path,
) -> None:
    manifest = _manifest()
    manifest["execution_allowed"] = True

    manifest_file = _write_json(
        tmp_path,
        "unsafe.json",
        manifest,
    )
    json_file = tmp_path / "unsafe-review.json"

    result = runner.invoke(
        app,
        [
            COMMAND,
            "--manifest-file",
            str(manifest_file),
            "--json-output",
            str(json_file),
        ],
    )

    assert result.exit_code == 0, result.output

    data = json.loads(
        json_file.read_text(encoding="utf-8")
    )

    assert data["review_status"] == (
        "blocked-unsafe-manifest"
    )
    assert data["review_ready"] is False
    assert data["runtime_execution_allowed"] is False
    assert data["counts"]["high_findings"] >= 1


def test_cli_detects_gate_preview_tampering(
    tmp_path,
) -> None:
    manifest = _manifest()
    manifest["execution_gate_preview"][
        "gate_decision"
    ] = "eligible-for-execution"

    manifest_file = _write_json(
        tmp_path,
        "gate-tampering.json",
        manifest,
    )
    json_file = tmp_path / "gate-review.json"

    result = runner.invoke(
        app,
        [
            COMMAND,
            "--manifest-file",
            str(manifest_file),
            "--json-output",
            str(json_file),
        ],
    )

    assert result.exit_code == 0, result.output

    data = json.loads(
        json_file.read_text(encoding="utf-8")
    )

    assert data["review_status"] == (
        "blocked-invalid-typed-tool-requests"
    )
    assert data["review_ready"] is False

    categories = {
        item["category"]
        for item in data["gate_findings"]
    }

    assert "gate-consistency" in categories


def test_cli_aliases_work(tmp_path) -> None:
    manifest_file = _write_json(
        tmp_path,
        "typed-manifest.json",
        _manifest(),
    )
    markdown_file = tmp_path / "alias-output.md"

    result = runner.invoke(
        app,
        [
            COMMAND,
            "--typed-manifest",
            str(manifest_file),
            "--output",
            str(markdown_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert markdown_file.exists()


def test_cli_creates_nested_directories(
    tmp_path,
) -> None:
    manifest_file = _write_json(
        tmp_path,
        "typed-manifest.json",
        _manifest(),
    )
    markdown_file = (
        tmp_path
        / "nested"
        / "markdown"
        / "review.md"
    )
    json_file = (
        tmp_path
        / "nested"
        / "json"
        / "review.json"
    )

    result = runner.invoke(
        app,
        [
            COMMAND,
            "--manifest-file",
            str(manifest_file),
            "--output-file",
            str(markdown_file),
            "--json-output",
            str(json_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert markdown_file.exists()
    assert json_file.exists()


def test_cli_is_deterministic(tmp_path) -> None:
    manifest_file = _write_json(
        tmp_path,
        "typed-manifest.json",
        _manifest(),
    )
    first_file = tmp_path / "first.json"
    second_file = tmp_path / "second.json"

    for output_file in (first_file, second_file):
        result = runner.invoke(
            app,
            [
                COMMAND,
                "--manifest-file",
                str(manifest_file),
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


def test_cli_does_not_mutate_input_file(
    tmp_path,
) -> None:
    manifest = _manifest()
    before = copy.deepcopy(manifest)

    manifest_file = _write_json(
        tmp_path,
        "typed-manifest.json",
        manifest,
    )

    result = runner.invoke(
        app,
        [
            COMMAND,
            "--manifest-file",
            str(manifest_file),
        ],
    )

    assert result.exit_code == 0, result.output

    after = json.loads(
        manifest_file.read_text(encoding="utf-8")
    )

    assert after == before


def test_cli_missing_file_errors(tmp_path) -> None:
    result = runner.invoke(
        app,
        [
            COMMAND,
            "--manifest-file",
            str(tmp_path / "missing.json"),
        ],
    )

    assert result.exit_code == 1
    assert (
        "Research typed tool-request manifest not found"
        in result.output
    )


def test_cli_invalid_json_errors(tmp_path) -> None:
    manifest_file = tmp_path / "invalid.json"
    manifest_file.write_text(
        "{not-json",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            COMMAND,
            "--manifest-file",
            str(manifest_file),
        ],
    )

    assert result.exit_code == 2
    assert (
        "Invalid typed tool-request manifest JSON"
        in result.output
    )


def test_cli_non_object_json_errors(tmp_path) -> None:
    manifest_file = _write_json(
        tmp_path,
        "list.json",
        ["not", "an", "object"],
    )

    result = runner.invoke(
        app,
        [
            COMMAND,
            "--manifest-file",
            str(manifest_file),
        ],
    )

    assert result.exit_code == 2
    assert (
        "Invalid typed tool-request review-gate input"
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

    assert "--manifest-file" in output
    assert "--output-file" in output
    assert "--json-output" in output


def test_cli_safety_message_is_explicit(
    tmp_path,
) -> None:
    manifest_file = _write_json(
        tmp_path,
        "typed-manifest.json",
        _manifest(),
    )

    result = runner.invoke(
        app,
        [
            COMMAND,
            "--manifest-file",
            str(manifest_file),
        ],
    )

    assert result.exit_code == 0, result.output

    output = _normalize_output(result.output)

    assert "Safety:" in output
    assert "does not generate commands or payloads" in output
    assert "install software" in output
    assert "execute tools" in output
    assert "launch browsers" in output
    assert "replay Burp requests" in output
    assert "use Kali tools" in output
    assert "send network requests" in output
    assert "interact with targets" in output
    assert "collect evidence" in output
    assert "validate findings" in output
    assert "mutate state" in output
    assert "submit reports" in output
    assert "confirm vulnerabilities" in output
