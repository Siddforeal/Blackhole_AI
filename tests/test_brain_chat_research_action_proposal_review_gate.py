from __future__ import annotations

import copy
import json

from bugintel.core.brain_chat_research_action_proposal_packet import (
    build_research_action_proposal_packet,
)
from bugintel.core.brain_chat_research_action_proposal_review_gate import (
    EXPECTED_KIND,
    EXPECTED_TOOL_FAMILIES,
    build_research_action_proposal_review_gate,
    build_review_gate_from_file,
    render_research_action_proposal_review_gate_markdown,
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


def _action_packet() -> dict:
    plan = build_research_investigation_plan_packet(_selection_packet())
    plan_review = build_research_investigation_plan_review_gate(plan)
    return build_research_action_proposal_packet(
        plan,
        plan_review,
    ).to_dict()


def _finding_subjects(review: dict, section: str) -> list[str]:
    return [
        item["subject"]
        for item in review[section]
        if isinstance(item, dict)
    ]


def _finding_messages(review: dict, section: str) -> list[str]:
    return [
        item["message"]
        for item in review[section]
        if isinstance(item, dict)
    ]


def test_valid_packet_is_ready_for_human_review() -> None:
    packet = _action_packet()
    review = build_research_action_proposal_review_gate(packet)

    assert review["kind"] == (
        "brain_chat_research_action_proposal_review_gate"
    )
    assert review["packet_kind"] == EXPECTED_KIND
    assert review["target_name"] == "demo-self-hosted-product"
    assert review["review_status"] == "needs-human-review"
    assert review["review_ready"] is True

    assert review["proposal_status"] == (
        "ready-for-action-proposal-review"
    )
    assert review["source_review_status"] == "needs-human-review"
    assert review["source_review_ready"] is True
    assert review["source_action_proposal_ready"] is True

    assert review["plan_count"] == 2
    assert review["declared_proposal_count"] == 16
    assert review["proposal_count"] == 16

    assert review["schema_findings"] == []
    assert review["safety_findings"] == []
    assert review["proposal_findings"] == []

    assert review["counts"]["schema_findings"] == 0
    assert review["counts"]["safety_findings"] == 0
    assert review["counts"]["proposal_findings"] == 0
    assert review["counts"]["high_findings"] == 0
    assert review["counts"]["medium_findings"] == 0

    assert review["command_generation_allowed"] is False
    assert review["package_installation_allowed"] is False
    assert review["execution_allowed"] is False
    assert review["runtime_execution_allowed"] is False
    assert review["target_interaction_allowed"] is False
    assert review["evidence_collection_allowed"] is False
    assert review["validation_allowed"] is False
    assert review["report_submission_allowed"] is False
    assert review["vulnerability_confirmation_allowed"] is False

    assert review["planning_only"] is True
    assert review["execution_state"] == "not_executed"
    assert review["gate_state"] == "reviewed_not_used"

    assert review["safety"]["local_only"] is True
    assert review["safety"]["planning_only"] is True
    assert review["safety"]["human_approval_required"] is True
    assert review["safety"]["command_generation"] is False
    assert review["safety"]["tool_execution"] is False
    assert review["safety"]["browser_execution"] is False
    assert review["safety"]["curl_execution"] is False
    assert review["safety"]["kali_execution"] is False
    assert review["safety"]["burp_execution"] is False
    assert review["safety"]["package_installation"] is False
    assert review["safety"]["target_interaction"] is False
    assert review["safety"]["evidence_collection"] is False
    assert review["safety"]["validation_execution"] is False
    assert review["safety"]["runtime_execution_allowed"] is False
    assert review["safety"]["state_mutation"] is False
    assert review["safety"]["report_submission"] is False
    assert review["safety"]["vulnerability_confirmation"] is False

    assert len(review["human_review_items"]) >= 9
    assert len(review["rejected_actions"]) >= 9


def test_empty_packet_is_blocked_invalid() -> None:
    review = build_research_action_proposal_review_gate({})

    assert review["review_status"] == "blocked-invalid-packet"
    assert review["review_ready"] is False
    assert review["proposal_count"] == 0
    assert review["counts"]["high_findings"] > 0
    assert "kind" in _finding_subjects(review, "schema_findings")


def test_wrong_packet_kind_is_blocked() -> None:
    packet = _action_packet()
    packet["kind"] = "wrong-kind"

    review = build_research_action_proposal_review_gate(packet)

    assert review["review_status"] == "blocked-invalid-packet"
    assert review["review_ready"] is False
    assert any(
        "Packet kind must be" in message
        for message in _finding_messages(review, "schema_findings")
    )


def test_missing_required_packet_field_is_blocked() -> None:
    packet = _action_packet()
    del packet["target_name"]

    review = build_research_action_proposal_review_gate(packet)

    assert review["review_status"] == "blocked-invalid-packet"
    assert "target_name" in _finding_subjects(
        review,
        "schema_findings",
    )


def test_non_list_proposals_is_blocked() -> None:
    packet = _action_packet()
    packet["proposals"] = {"wrong": True}

    review = build_research_action_proposal_review_gate(packet)

    assert review["review_status"] == "blocked-invalid-packet"
    assert any(
        item["subject"] == "proposals"
        and item["severity"] == "high"
        for item in review["schema_findings"]
    )


def test_empty_proposal_list_is_blocked() -> None:
    packet = _action_packet()
    packet["proposals"] = []
    packet["proposal_count"] = 0

    review = build_research_action_proposal_review_gate(packet)

    assert review["review_status"] == (
        "blocked-no-action-proposals"
    )
    assert review["review_ready"] is False
    assert review["proposal_count"] == 0


def test_declared_proposal_count_mismatch_is_reviewable() -> None:
    packet = _action_packet()
    packet["proposal_count"] = 999

    review = build_research_action_proposal_review_gate(packet)

    assert review["review_status"] == "needs-human-review"
    assert review["review_ready"] is True
    assert review["counts"]["medium_findings"] >= 1
    assert any(
        item["subject"] == "proposal_count"
        for item in review["schema_findings"]
    )


def test_planning_only_false_is_blocked() -> None:
    packet = _action_packet()
    packet["planning_only"] = False

    review = build_research_action_proposal_review_gate(packet)

    assert review["review_status"] == "blocked-invalid-packet"
    assert any(
        item["subject"] == "planning_only"
        and item["severity"] == "high"
        for item in review["schema_findings"]
    )


def test_execution_state_must_be_not_executed() -> None:
    packet = _action_packet()
    packet["execution_state"] = "executed"

    review = build_research_action_proposal_review_gate(packet)

    assert review["review_status"] == "blocked-invalid-packet"
    assert any(
        item["subject"] == "execution_state"
        for item in review["schema_findings"]
    )


def test_packet_execution_flag_true_is_blocked() -> None:
    packet = _action_packet()
    packet["runtime_execution_allowed"] = True

    review = build_research_action_proposal_review_gate(packet)

    assert review["review_status"] == (
        "blocked-unsafe-action-proposals"
    )
    assert review["review_ready"] is False
    assert any(
        item["subject"] == "runtime_execution_allowed"
        for item in review["safety_findings"]
    )


def test_all_packet_level_unsafe_flags_are_detected() -> None:
    unsafe_fields = (
        "execution_allowed",
        "runtime_execution_allowed",
        "command_generation_allowed",
        "target_interaction_allowed",
        "evidence_collection_allowed",
        "validation_allowed",
        "report_submission_allowed",
        "vulnerability_confirmation_allowed",
    )

    for field in unsafe_fields:
        packet = _action_packet()
        packet[field] = True

        review = build_research_action_proposal_review_gate(packet)

        assert review["review_status"] == (
            "blocked-unsafe-action-proposals"
        )
        assert any(
            item["subject"] == field
            and item["severity"] == "high"
            for item in review["safety_findings"]
        )


def test_missing_safety_object_is_blocked() -> None:
    packet = _action_packet()
    del packet["safety"]

    review = build_research_action_proposal_review_gate(packet)

    assert review["review_status"] == "blocked-invalid-packet"
    assert any(
        item["subject"] == "safety"
        for item in review["schema_findings"]
    )
    assert any(
        item["subject"] == "safety"
        for item in review["safety_findings"]
    )


def test_true_safety_guardrail_must_remain_true() -> None:
    for field in (
        "local_only",
        "planning_only",
        "human_approval_required",
    ):
        packet = _action_packet()
        packet["safety"][field] = False

        review = build_research_action_proposal_review_gate(packet)

        assert review["review_status"] == (
            "blocked-unsafe-action-proposals"
        )
        assert any(
            item["subject"] == f"safety.{field}"
            and item["severity"] == "high"
            for item in review["safety_findings"]
        )


def test_false_safety_flags_must_remain_false() -> None:
    unsafe_fields = (
        "network_interaction",
        "target_mutation",
        "command_generation",
        "tool_execution",
        "browser_execution",
        "curl_execution",
        "kali_execution",
        "burp_execution",
        "provider_execution",
        "package_installation",
        "target_interaction",
        "evidence_collection",
        "validation_execution",
        "runtime_execution_allowed",
        "state_mutation",
        "report_submission",
        "vulnerability_confirmation",
    )

    for field in unsafe_fields:
        packet = _action_packet()
        packet["safety"][field] = True

        review = build_research_action_proposal_review_gate(packet)

        assert review["review_status"] == (
            "blocked-unsafe-action-proposals"
        )
        assert any(
            item["subject"] == f"safety.{field}"
            and item["severity"] == "high"
            for item in review["safety_findings"]
        )


def test_missing_required_proposal_field_is_blocked() -> None:
    packet = _action_packet()
    del packet["proposals"][0]["purpose"]

    review = build_research_action_proposal_review_gate(packet)

    assert review["review_status"] == (
        "blocked-unsafe-action-proposals"
    )
    assert any(
        "Required proposal field is missing: purpose."
        == item["message"]
        for item in review["proposal_findings"]
    )


def test_non_object_proposal_is_blocked() -> None:
    packet = _action_packet()
    packet["proposals"][0] = "wrong"

    review = build_research_action_proposal_review_gate(packet)

    assert review["review_status"] == (
        "blocked-unsafe-action-proposals"
    )
    assert any(
        item["subject"] == "proposals[0]"
        and item["severity"] == "high"
        for item in review["proposal_findings"]
    )


def test_duplicate_action_id_is_blocked() -> None:
    packet = _action_packet()
    packet["proposals"][1]["action_id"] = (
        packet["proposals"][0]["action_id"]
    )

    review = build_research_action_proposal_review_gate(packet)

    assert review["review_status"] == (
        "blocked-unsafe-action-proposals"
    )
    assert any(
        "Duplicate action_id detected" in item["message"]
        for item in review["proposal_findings"]
    )


def test_invalid_action_type_is_blocked() -> None:
    packet = _action_packet()
    packet["proposals"][0]["action_type"] = (
        "execute-arbitrary-command"
    )

    review = build_research_action_proposal_review_gate(packet)

    assert review["review_status"] == (
        "blocked-unsafe-action-proposals"
    )
    assert any(
        "Unsupported action_type" in item["message"]
        and item["severity"] == "high"
        for item in review["proposal_findings"]
    )


def test_tool_family_mismatch_is_medium_finding() -> None:
    packet = _action_packet()
    packet["proposals"][0]["proposed_tool_family"] = "browser"

    review = build_research_action_proposal_review_gate(packet)

    assert review["review_status"] == "needs-human-review"
    assert review["review_ready"] is True
    assert any(
        "Tool family mismatch" in item["message"]
        and item["severity"] == "medium"
        for item in review["proposal_findings"]
    )


def test_expected_tool_family_map_covers_every_action_type() -> None:
    packet = _action_packet()

    for proposal in packet["proposals"]:
        action_type = proposal["action_type"]
        assert action_type in EXPECTED_TOOL_FAMILIES
        assert (
            proposal["proposed_tool_family"]
            == EXPECTED_TOOL_FAMILIES[action_type]
        )


def test_empty_hypothesis_id_is_blocked() -> None:
    packet = _action_packet()
    packet["proposals"][0]["hypothesis_id"] = ""

    review = build_research_action_proposal_review_gate(packet)

    assert review["review_status"] == (
        "blocked-unsafe-action-proposals"
    )
    assert any(
        "hypothesis_id must not be empty" in item["message"]
        for item in review["proposal_findings"]
    )


def test_empty_human_readable_fields_are_medium_findings() -> None:
    for field in ("title", "purpose", "expected_artifact"):
        packet = _action_packet()
        packet["proposals"][0][field] = ""

        review = build_research_action_proposal_review_gate(packet)

        assert review["review_status"] == "needs-human-review"
        assert any(
            item["message"] == f"{field} should not be empty."
            for item in review["proposal_findings"]
        )


def test_human_approval_is_required_for_every_proposal() -> None:
    packet = _action_packet()
    packet["proposals"][0]["requires_human_approval"] = False

    review = build_research_action_proposal_review_gate(packet)

    assert review["review_status"] == (
        "blocked-unsafe-action-proposals"
    )
    assert any(
        "requires_human_approval must be true"
        in item["message"]
        for item in review["proposal_findings"]
    )


def test_scope_confirmation_required_for_active_preparation() -> None:
    packet = _action_packet()
    browser = next(
        proposal
        for proposal in packet["proposals"]
        if proposal["action_type"] == (
            "browser-observation-proposal"
        )
    )
    browser["requires_scope_confirmation"] = False

    review = build_research_action_proposal_review_gate(packet)

    assert review["review_status"] == (
        "blocked-unsafe-action-proposals"
    )
    assert any(
        "requires_scope_confirmation must be true"
        in item["message"]
        for item in review["proposal_findings"]
    )


def test_local_review_does_not_require_scope_confirmation() -> None:
    packet = _action_packet()
    local = next(
        proposal
        for proposal in packet["proposals"]
        if proposal["action_type"] == "local-source-review"
    )

    assert local["requires_scope_confirmation"] is False

    review = build_research_action_proposal_review_gate(packet)

    assert review["review_status"] == "needs-human-review"
    assert review["review_ready"] is True


def test_proposal_execution_flags_must_remain_false() -> None:
    unsafe_fields = (
        "execution_allowed",
        "runtime_execution_allowed",
        "command_generated",
        "target_interaction_allowed",
        "evidence_collection_allowed",
        "validation_allowed",
    )

    for field in unsafe_fields:
        packet = _action_packet()
        packet["proposals"][0][field] = True

        review = build_research_action_proposal_review_gate(packet)

        assert review["review_status"] == (
            "blocked-unsafe-action-proposals"
        )
        assert any(
            f"Proposal flag must remain false: {field}."
            == item["message"]
            for item in review["proposal_findings"]
        )


def test_empty_blocked_by_is_blocked() -> None:
    packet = _action_packet()
    packet["proposals"][0]["blocked_by"] = []

    review = build_research_action_proposal_review_gate(packet)

    assert review["review_status"] == (
        "blocked-unsafe-action-proposals"
    )
    assert any(
        "blocked_by must contain explicit review gates"
        in item["message"]
        for item in review["proposal_findings"]
    )


def test_missing_action_specific_blocker_is_medium() -> None:
    packet = _action_packet()
    browser = next(
        proposal
        for proposal in packet["proposals"]
        if proposal["action_type"] == (
            "browser-observation-proposal"
        )
    )
    browser["blocked_by"].remove("browser-execution-gate")

    review = build_research_action_proposal_review_gate(packet)

    assert review["review_status"] == "needs-human-review"
    assert review["review_ready"] is True
    assert any(
        item["message"] == (
            "Required blocker is missing: "
            "browser-execution-gate."
        )
        for item in review["proposal_findings"]
    )


def test_duplicate_manual_order_is_medium() -> None:
    packet = _action_packet()
    packet["proposals"][1]["manual_order"] = 1

    review = build_research_action_proposal_review_gate(packet)

    assert review["review_status"] == "needs-human-review"
    assert any(
        "Duplicate manual_order detected" in item["message"]
        for item in review["proposal_findings"]
    )


def test_non_contiguous_manual_order_is_medium() -> None:
    packet = _action_packet()
    packet["proposals"][-1]["manual_order"] = 99

    review = build_research_action_proposal_review_gate(packet)

    assert review["review_status"] == "needs-human-review"
    assert any(
        "manual_order values should form a continuous sequence"
        in item["message"]
        for item in review["proposal_findings"]
    )


def test_zero_manual_order_is_medium() -> None:
    packet = _action_packet()
    packet["proposals"][0]["manual_order"] = 0

    review = build_research_action_proposal_review_gate(packet)

    assert review["review_status"] == "needs-human-review"
    assert any(
        "manual_order must be a positive integer"
        in item["message"]
        for item in review["proposal_findings"]
    )


def test_input_packet_is_not_mutated() -> None:
    packet = _action_packet()
    before = copy.deepcopy(packet)

    build_research_action_proposal_review_gate(packet)

    assert packet == before


def test_markdown_contains_all_review_sections() -> None:
    review = build_research_action_proposal_review_gate(
        _action_packet()
    )
    markdown = (
        render_research_action_proposal_review_gate_markdown(
            review
        )
    )

    assert "# Research Action Proposal Review Gate" in markdown
    assert "## Review Status" in markdown
    assert "## Schema Findings" in markdown
    assert "## Safety Findings" in markdown
    assert "## Proposal Findings" in markdown
    assert "## Human Review Items" in markdown
    assert "## Rejected Actions" in markdown
    assert "## Safety" in markdown

    assert "review_status: `needs-human-review`" in markdown
    assert "review_ready: `true`" in markdown
    assert "command_generation_allowed: `false`" in markdown
    assert "package_installation_allowed: `false`" in markdown
    assert "runtime_execution_allowed: `false`" in markdown
    assert "target_interaction_allowed: `false`" in markdown
    assert "validation_allowed: `false`" in markdown
    assert "\\n" not in markdown


def test_file_builder_writes_markdown_and_json(tmp_path) -> None:
    proposal_file = tmp_path / "action-proposals.json"
    markdown_file = tmp_path / "action-proposal-review.md"
    json_file = tmp_path / "action-proposal-review.json"

    proposal_file.write_text(
        json.dumps(_action_packet()),
        encoding="utf-8",
    )

    review = build_review_gate_from_file(
        proposal_file,
        output_file=markdown_file,
        json_output=json_file,
    )

    assert review["review_status"] == "needs-human-review"
    assert markdown_file.exists()
    assert json_file.exists()

    written = json.loads(json_file.read_text(encoding="utf-8"))
    assert written["kind"] == (
        "brain_chat_research_action_proposal_review_gate"
    )
    assert written["proposal_count"] == 16
    assert written["runtime_execution_allowed"] is False

    markdown = markdown_file.read_text(encoding="utf-8")
    assert "# Research Action Proposal Review Gate" in markdown


def test_file_builder_creates_parent_directories(tmp_path) -> None:
    proposal_file = tmp_path / "input" / "packet.json"
    proposal_file.parent.mkdir()
    proposal_file.write_text(
        json.dumps(_action_packet()),
        encoding="utf-8",
    )

    markdown_file = tmp_path / "nested" / "review" / "review.md"
    json_file = tmp_path / "nested" / "review" / "review.json"

    build_review_gate_from_file(
        proposal_file,
        output_file=markdown_file,
        json_output=json_file,
    )

    assert markdown_file.exists()
    assert json_file.exists()


def test_rejected_actions_keep_execution_disabled() -> None:
    review = build_research_action_proposal_review_gate(
        _action_packet()
    )

    rejected = "\n".join(review["rejected_actions"])

    assert "Do not execute action proposals" in rejected
    assert "Do not generate shell" in rejected
    assert "Do not install packages" in rejected
    assert "Do not browse" in rejected
    assert "Do not collect evidence" in rejected
    assert "Do not validate exploitability" in rejected
    assert "Do not confirm vulnerabilities" in rejected
    assert "Do not submit" in rejected
    assert "Do not mutate case memory" in rejected
