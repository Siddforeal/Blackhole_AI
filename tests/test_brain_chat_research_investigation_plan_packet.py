from __future__ import annotations

import json

from bugintel.core.brain_chat_research_investigation_plan_packet import (
    build_packet_from_file,
    build_research_investigation_plan_packet,
    render_research_investigation_plan_packet_markdown,
)


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


def test_builds_research_investigation_plan_packet_from_selected_hypotheses() -> None:
    packet = build_research_investigation_plan_packet(_selection_packet())

    assert packet["kind"] == "brain_chat_research_investigation_plan_packet"
    assert packet["target_name"] == "demo-self-hosted-product"
    assert packet["packet_status"] == "ready-for-human-review"
    assert packet["selection_status"] == "ready-for-local-investigation-planning"
    assert packet["investigation_plan_status"] == "ready-for-human-review"
    assert packet["selected_count"] == 3
    assert packet["plan_count"] == 3
    assert packet["primary_hypothesis_id"] == "HYP-005"
    assert packet["hypothesis_plan_ids"] == ["HYP-005", "HYP-003", "HYP-006"]

    assert packet["plans"][0]["hypothesis_type"] == "worker-execution-trust-boundary"
    assert packet["plans"][1]["hypothesis_type"] == "input-to-filesystem-trust-boundary"
    assert packet["plans"][2]["hypothesis_type"] == "authorization-admin-boundary"

    for plan in packet["plans"]:
        assert plan["plan_status"] == "ready-for-human-review"
        assert plan["investigation_allowed"] is True
        assert plan["validation_allowed"] is False
        assert plan["evidence_collection_allowed"] is False
        assert plan["vulnerability_confirmation_allowed"] is False
        assert plan["investigation_phases"]
        assert plan["review_questions"]
        assert plan["evidence_requirements"]
        assert "command generation" in plan["blocked_until_later_gate"]
        assert "target interaction" in plan["blocked_until_later_gate"]


def test_safety_flags_remain_false_and_rejected_actions_are_present() -> None:
    packet = build_research_investigation_plan_packet(_selection_packet())

    for name in (
        "web_browsing",
        "network_interaction",
        "command_generation",
        "tool_execution",
        "browser_execution",
        "curl_execution",
        "kali_execution",
        "burp_execution",
        "target_interaction",
        "evidence_collection",
        "validation_execution",
        "report_submission",
        "vulnerability_confirmation",
    ):
        assert packet["safety_flags"][name] is False

    assert packet["rejected_actions_count"] == 6
    assert len(packet["rejected_actions"]) == 6
    assert any("target" in item["action"].lower() for item in packet["rejected_actions"])


def test_blocks_when_no_selected_hypotheses_are_available() -> None:
    packet = build_research_investigation_plan_packet(
        {
            "kind": "brain_chat_research_hypothesis_selection_packet",
            "target_name": "demo-self-hosted-product",
            "selection_status": "blocked-no-selection",
            "selected_hypotheses": [],
        }
    )

    assert packet["packet_status"] == "blocked-no-selected-hypotheses"
    assert packet["investigation_plan_status"] == "blocked-no-selected-hypotheses"
    assert packet["selected_count"] == 0
    assert packet["plan_count"] == 0
    assert packet["plans"] == []
    assert packet["allowed_local_next_steps_count"] == 0


def test_renders_markdown_packet() -> None:
    packet = build_research_investigation_plan_packet(_selection_packet())
    markdown = render_research_investigation_plan_packet_markdown(packet)

    assert "# Research Investigation Plan Packet" in markdown
    assert "brain_chat_research_investigation_plan_packet" in markdown
    assert "HYP-005 - worker-execution-trust-boundary" in markdown
    assert "HYP-003 - input-to-filesystem-trust-boundary" in markdown
    assert "HYP-006 - authorization-admin-boundary" in markdown
    assert "validation_allowed: `false`" in markdown
    assert "evidence_collection_allowed: `false`" in markdown
    assert "vulnerability_confirmation_allowed: `false`" in markdown


def test_build_packet_from_file_writes_markdown_and_json(tmp_path) -> None:
    selection_file = tmp_path / "research-hypothesis-selection-packet.json"
    output_file = tmp_path / "research-investigation-plan-packet.md"
    json_output = tmp_path / "research-investigation-plan-packet.json"

    selection_file.write_text(json.dumps(_selection_packet()), encoding="utf-8")

    packet = build_packet_from_file(
        selection_file,
        output_file=output_file,
        json_output=json_output,
    )

    assert packet["kind"] == "brain_chat_research_investigation_plan_packet"
    assert output_file.exists()
    assert json_output.exists()

    written = json.loads(json_output.read_text(encoding="utf-8"))
    assert written["kind"] == "brain_chat_research_investigation_plan_packet"
    assert written["selected_count"] == 3
    assert "Research Investigation Plan Packet" in output_file.read_text(encoding="utf-8")
