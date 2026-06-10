from __future__ import annotations

import json

from bugintel.core.brain_chat_research_action_proposal_packet import (
    build_packet_from_files,
    build_research_action_proposal_packet,
)
from bugintel.core.brain_chat_research_investigation_plan_packet import (
    build_research_investigation_plan_packet,
)
from bugintel.core.brain_chat_research_investigation_plan_review_gate import (
    build_research_investigation_plan_review_gate,
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


def _review_gate(plan_packet: dict | None = None) -> dict:
    return build_research_investigation_plan_review_gate(
        plan_packet or _plan_packet()
    )


def test_action_proposal_packet_builds_deterministic_proposals() -> None:
    plan = _plan_packet()
    review = _review_gate(plan)

    packet = build_research_action_proposal_packet(plan, review)
    data = packet.to_dict()

    assert data["kind"] == "brain_chat_research_action_proposal_packet"
    assert data["target_name"] == "demo-self-hosted-product"
    assert data["proposal_status"] == "ready-for-action-proposal-review"
    assert data["review_status"] == "needs-human-review"
    assert data["review_ready"] is True
    assert data["action_proposal_ready"] is True
    assert data["plan_count"] == 2
    assert data["proposal_count"] == 16
    assert data["blockers"] == []

    first = data["proposals"][0]
    assert first["action_id"] == "ACT-HYP-005-001"
    assert first["hypothesis_id"] == "HYP-005"
    assert first["action_type"] == "local-source-review"
    assert first["proposed_tool_family"] == "local-file-analysis"
    assert first["execution_allowed"] is False
    assert first["runtime_execution_allowed"] is False
    assert first["command_generated"] is False
    assert first["target_interaction_allowed"] is False
    assert first["evidence_collection_allowed"] is False
    assert first["validation_allowed"] is False

    action_types = {item["action_type"] for item in data["proposals"]}
    assert action_types == {
        "local-source-review",
        "local-artifact-review",
        "scope-confirmation-preparation",
        "controlled-account-preparation",
        "browser-observation-proposal",
        "burp-request-review-proposal",
        "command-proposal-preparation",
        "evidence-plan-preparation",
    }

    assert data["execution_allowed"] is False
    assert data["runtime_execution_allowed"] is False
    assert data["command_generation_allowed"] is False
    assert data["target_interaction_allowed"] is False
    assert data["evidence_collection_allowed"] is False
    assert data["validation_allowed"] is False
    assert data["report_submission_allowed"] is False
    assert data["vulnerability_confirmation_allowed"] is False

    assert data["safety"]["local_only"] is True
    assert data["safety"]["planning_only"] is True
    assert data["safety"]["human_approval_required"] is True
    assert data["safety"]["command_generation"] is False
    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["browser_execution"] is False
    assert data["safety"]["curl_execution"] is False
    assert data["safety"]["kali_execution"] is False
    assert data["safety"]["burp_execution"] is False
    assert data["safety"]["package_installation"] is False
    assert data["safety"]["target_interaction"] is False
    assert data["safety"]["evidence_collection"] is False
    assert data["safety"]["validation_execution"] is False
    assert data["safety"]["runtime_execution_allowed"] is False
    assert data["safety"]["state_mutation"] is False
    assert data["safety"]["report_submission"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_action_proposal_packet_blocks_invalid_plan_kind() -> None:
    plan = _plan_packet()
    plan["kind"] = "wrong"

    packet = build_research_action_proposal_packet(plan, _review_gate())
    data = packet.to_dict()

    assert data["proposal_status"] == "blocked-invalid-investigation-plan"
    assert data["action_proposal_ready"] is False
    assert data["proposal_count"] == 0
    assert "invalid-investigation-plan-kind" in data["blockers"]


def test_action_proposal_packet_blocks_invalid_review_kind() -> None:
    plan = _plan_packet()
    review = _review_gate(plan)
    review["kind"] = "wrong"

    packet = build_research_action_proposal_packet(plan, review)
    data = packet.to_dict()

    assert data["proposal_status"] == "blocked-invalid-review-gate"
    assert data["action_proposal_ready"] is False
    assert data["proposal_count"] == 0
    assert "invalid-review-gate-kind" in data["blockers"]


def test_action_proposal_packet_blocks_target_mismatch() -> None:
    plan = _plan_packet()
    review = _review_gate(plan)
    review["target_name"] = "different-target"

    packet = build_research_action_proposal_packet(plan, review)
    data = packet.to_dict()

    assert data["proposal_status"] == "blocked-plan-review-mismatch"
    assert data["action_proposal_ready"] is False
    assert "plan-review-target-mismatch" in data["blockers"]


def test_action_proposal_packet_blocks_plan_count_mismatch() -> None:
    plan = _plan_packet()
    review = _review_gate(plan)
    review["plan_count"] = 99

    packet = build_research_action_proposal_packet(plan, review)
    data = packet.to_dict()

    assert data["proposal_status"] == "blocked-plan-review-mismatch"
    assert data["proposal_count"] == 0
    assert "plan-review-count-mismatch" in data["blockers"]


def test_action_proposal_packet_blocks_review_not_ready() -> None:
    plan = _plan_packet()
    review = _review_gate(plan)
    review["review_status"] = "blocked-unsafe-plan"
    review["review_ready"] = False

    packet = build_research_action_proposal_packet(plan, review)
    data = packet.to_dict()

    assert data["proposal_status"] == "blocked-pending-review-ready-plan"
    assert data["action_proposal_ready"] is False
    assert data["proposal_count"] == 0
    assert "review-status-not-human-reviewable" in data["blockers"]
    assert "review-gate-not-ready" in data["blockers"]


def test_action_proposal_packet_blocks_unsafe_review_flags() -> None:
    plan = _plan_packet()
    review = _review_gate(plan)
    review["runtime_execution_allowed"] = True
    review["validation_allowed"] = True
    review["evidence_collection_allowed"] = True

    packet = build_research_action_proposal_packet(plan, review)
    data = packet.to_dict()

    assert data["proposal_status"] == "blocked-pending-review-ready-plan"
    assert data["proposal_count"] == 0
    assert "review-gate-runtime-execution-enabled" in data["blockers"]
    assert "review-gate-validation-enabled" in data["blockers"]
    assert "review-gate-evidence-collection-enabled" in data["blockers"]


def test_action_proposal_packet_blocks_empty_plan_set() -> None:
    plan = build_research_investigation_plan_packet(
        {
            "kind": "brain_chat_research_hypothesis_selection_packet",
            "target_name": "demo-self-hosted-product",
            "selection_status": "blocked-no-selection",
            "selected_hypotheses": [],
        }
    )
    review = build_research_investigation_plan_review_gate(plan)

    packet = build_research_action_proposal_packet(plan, review)
    data = packet.to_dict()

    assert data["proposal_status"] == "blocked-pending-review-ready-plan"
    assert data["action_proposal_ready"] is False
    assert data["proposal_count"] == 0


def test_action_proposal_packet_markdown_is_readable() -> None:
    plan = _plan_packet()
    review = _review_gate(plan)

    packet = build_research_action_proposal_packet(plan, review)
    markdown = packet.to_markdown()

    assert "# Research Action Proposal Packet" in markdown
    assert "Proposal Status" in markdown
    assert "Proposed Actions" in markdown
    assert "Human Review Items" in markdown
    assert "Rejected Actions" in markdown
    assert "Command generation allowed: `false`" in markdown
    assert "It does not generate executable commands or install software." in markdown
    assert "\\n" not in markdown


def test_build_packet_from_files_writes_markdown_and_json(tmp_path) -> None:
    plan = _plan_packet()
    review = _review_gate(plan)

    plan_file = tmp_path / "investigation-plan.json"
    review_file = tmp_path / "investigation-plan-review.json"
    markdown_file = tmp_path / "action-proposal.md"
    json_file = tmp_path / "action-proposal.json"

    plan_file.write_text(json.dumps(plan), encoding="utf-8")
    review_file.write_text(json.dumps(review), encoding="utf-8")

    packet = build_packet_from_files(
        plan_file,
        review_file,
        output_file=markdown_file,
        json_output=json_file,
    )

    assert packet.proposal_status == "ready-for-action-proposal-review"
    assert markdown_file.exists()
    assert json_file.exists()

    data = json.loads(json_file.read_text(encoding="utf-8"))
    assert data["kind"] == "brain_chat_research_action_proposal_packet"
    assert data["proposal_count"] == 16
    assert data["runtime_execution_allowed"] is False

    markdown = markdown_file.read_text(encoding="utf-8")
    assert "# Research Action Proposal Packet" in markdown
