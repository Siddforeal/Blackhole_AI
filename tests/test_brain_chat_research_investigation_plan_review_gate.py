from __future__ import annotations

import json

from bugintel.core.brain_chat_research_investigation_plan_packet import (
    build_research_investigation_plan_packet,
)
from bugintel.core.brain_chat_research_investigation_plan_review_gate import (
    build_research_investigation_plan_review_gate,
    build_review_gate_from_file,
    render_research_investigation_plan_review_gate_markdown,
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


def _plan_packet() -> dict:
    return build_research_investigation_plan_packet(_selection_packet())


def test_review_gate_accepts_valid_investigation_plan_for_human_review() -> None:
    review = build_research_investigation_plan_review_gate(_plan_packet())

    assert review["kind"] == "brain_chat_research_investigation_plan_review_gate"
    assert review["target_name"] == "demo-self-hosted-product"
    assert review["review_status"] == "needs-human-review"
    assert review["review_ready"] is True
    assert review["packet_status"] == "ready-for-human-review"
    assert review["investigation_plan_status"] == "ready-for-human-review"
    assert review["plan_count"] == 3
    assert review["validation_allowed"] is False
    assert review["runtime_execution_allowed"] is False
    assert review["evidence_collection_allowed"] is False
    assert review["report_submission_allowed"] is False
    assert review["vulnerability_confirmation_allowed"] is False
    assert review["schema_findings"] == []
    assert review["safety_findings"] == []
    assert review["plan_findings"] == []
    assert review["planning_only"] is True
    assert review["execution_state"] == "not_executed"
    assert review["gate_state"] == "reviewed_not_used"

    assert review["safety"]["local_only"] is True
    assert review["safety"]["planning_only"] is True
    assert review["safety"]["human_approval_required"] is True
    assert review["safety"]["tool_execution"] is False
    assert review["safety"]["browser_execution"] is False
    assert review["safety"]["curl_execution"] is False
    assert review["safety"]["kali_execution"] is False
    assert review["safety"]["burp_execution"] is False
    assert review["safety"]["evidence_collection"] is False
    assert review["safety"]["validation_execution"] is False
    assert review["safety"]["runtime_execution_allowed"] is False
    assert review["safety"]["report_submission"] is False
    assert review["safety"]["vulnerability_confirmation"] is False


def test_review_gate_blocks_invalid_packet_kind() -> None:
    review = build_research_investigation_plan_review_gate({"kind": "wrong"})

    assert review["review_status"] == "blocked-invalid-packet"
    assert review["review_ready"] is False
    assert review["counts"]["schema_findings"] >= 1
    assert any(item["subject"] == "kind" for item in review["schema_findings"])
    assert review["runtime_execution_allowed"] is False


def test_review_gate_blocks_when_no_investigation_plans() -> None:
    packet = build_research_investigation_plan_packet(
        {
            "kind": "brain_chat_research_hypothesis_selection_packet",
            "target_name": "demo-self-hosted-product",
            "selection_status": "blocked-no-selection",
            "selected_hypotheses": [],
        }
    )

    review = build_research_investigation_plan_review_gate(packet)

    assert review["review_status"] == "blocked-no-investigation-plans"
    assert review["review_ready"] is False
    assert review["plan_count"] == 0
    assert review["validation_allowed"] is False
    assert review["evidence_collection_allowed"] is False


def test_review_gate_blocks_unsafe_top_level_safety_flag() -> None:
    packet = _plan_packet()
    packet["safety_flags"]["tool_execution"] = True

    review = build_research_investigation_plan_review_gate(packet)

    assert review["review_status"] == "blocked-unsafe-plan"
    assert review["review_ready"] is False
    assert any(
        item["subject"] == "safety_flags.tool_execution"
        and item["severity"] == "high"
        for item in review["safety_findings"]
    )


def test_review_gate_blocks_unsafe_per_plan_flags() -> None:
    packet = _plan_packet()
    packet["plans"][0]["validation_allowed"] = True
    packet["plans"][1]["evidence_collection_allowed"] = True
    packet["plans"][2]["vulnerability_confirmation_allowed"] = True

    review = build_research_investigation_plan_review_gate(packet)

    assert review["review_status"] == "blocked-unsafe-plan"
    assert review["review_ready"] is False
    messages = [item["message"] for item in review["plan_findings"]]
    assert "validation_allowed must be false." in messages
    assert "evidence_collection_allowed must be false." in messages
    assert "vulnerability_confirmation_allowed must be false." in messages


def test_review_gate_flags_missing_blocked_until_later_gate_items() -> None:
    packet = _plan_packet()
    packet["plans"][0]["blocked_until_later_gate"] = ["runtime validation"]

    review = build_research_investigation_plan_review_gate(packet)

    assert review["review_status"] == "needs-human-review"
    assert review["review_ready"] is True
    assert any(
        "blocked_until_later_gate is missing" in item["message"]
        for item in review["plan_findings"]
    )


def test_review_gate_markdown_is_readable() -> None:
    review = build_research_investigation_plan_review_gate(_plan_packet())
    markdown = render_research_investigation_plan_review_gate_markdown(review)

    assert "# Research Investigation Plan Review Gate" in markdown
    assert "Review Status" in markdown
    assert "Schema Findings" in markdown
    assert "Safety Findings" in markdown
    assert "Plan Findings" in markdown
    assert "Human Review Items" in markdown
    assert "Rejected Actions" in markdown
    assert "Safety" in markdown
    assert "validation_allowed: `false`" in markdown
    assert "\\n" not in markdown


def test_build_review_gate_from_file_writes_markdown_and_json(tmp_path) -> None:
    plan_file = tmp_path / "research-investigation-plan-packet.json"
    output_file = tmp_path / "research-investigation-plan-review-gate.md"
    json_output = tmp_path / "research-investigation-plan-review-gate.json"

    plan_file.write_text(json.dumps(_plan_packet()), encoding="utf-8")

    review = build_review_gate_from_file(
        plan_file,
        output_file=output_file,
        json_output=json_output,
    )

    assert review["kind"] == "brain_chat_research_investigation_plan_review_gate"
    assert output_file.exists()
    assert json_output.exists()

    written = json.loads(json_output.read_text(encoding="utf-8"))
    assert written["kind"] == "brain_chat_research_investigation_plan_review_gate"
    assert written["review_status"] == "needs-human-review"
    assert "Research Investigation Plan Review Gate" in output_file.read_text(encoding="utf-8")
