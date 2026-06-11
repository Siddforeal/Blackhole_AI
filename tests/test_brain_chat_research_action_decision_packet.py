from __future__ import annotations

import copy
import json

from bugintel.core.brain_chat_research_action_decision_packet import (
    EXPECTED_DECISION_INPUT_KIND,
    VALID_DECISIONS,
    build_decision_packet_from_files,
    build_research_action_decision_packet,
    build_research_action_decision_template,
    render_research_action_decision_packet_markdown,
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
                "title": (
                    "Agent, runner, worker, or deployment "
                    "trust boundary"
                ),
                "priority": "high",
                "confidence": "high",
                "score": 386,
                "tags": [
                    "worker",
                    "runner",
                    "deployment",
                ],
            },
        ],
    }


def _proposal_and_review() -> tuple[dict, dict]:
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

    return proposal, proposal_review


def _decision_input(
    proposal: dict,
    decision: str = "approved",
) -> dict:
    value = build_research_action_decision_template(
        proposal
    )
    value["reviewer"] = "authorized-human-reviewer"
    value["overall_reason"] = (
        "Reviewed for the next local planning stage."
    )

    for item in value["decisions"]:
        item["decision"] = decision
        item["reason"] = (
            f"Human decision recorded as {decision}."
        )

    return value


def _build(
    decision: str = "approved",
) -> tuple[dict, dict, dict, dict]:
    proposal, review = _proposal_and_review()
    decision_input = _decision_input(
        proposal,
        decision=decision,
    )
    packet = build_research_action_decision_packet(
        proposal,
        review,
        decision_input,
    )
    return proposal, review, decision_input, packet


def _messages(
    packet: dict,
    section: str,
) -> list[str]:
    return [
        item["message"]
        for item in packet[section]
        if isinstance(item, dict)
    ]


def _subjects(
    packet: dict,
    section: str,
) -> list[str]:
    return [
        item["subject"]
        for item in packet[section]
        if isinstance(item, dict)
    ]


def test_decision_template_covers_every_action() -> None:
    proposal, _ = _proposal_and_review()

    template = build_research_action_decision_template(
        proposal
    )

    assert template["kind"] == EXPECTED_DECISION_INPUT_KIND
    assert (
        template["target_name"]
        == "demo-self-hosted-product"
    )
    assert template["reviewer"] == ""
    assert template["overall_reason"] == ""
    assert template["planning_only"] is True
    assert template["execution_state"] == "not_executed"
    assert len(template["decisions"]) == 8

    assert [
        item["action_id"]
        for item in template["decisions"]
    ] == [
        proposal_item["action_id"]
        for proposal_item in proposal["proposals"]
    ]

    assert all(
        item["decision"] == "deferred"
        for item in template["decisions"]
    )


def test_template_does_not_mutate_proposal() -> None:
    proposal, _ = _proposal_and_review()
    before = copy.deepcopy(proposal)

    build_research_action_decision_template(proposal)

    assert proposal == before


def test_all_approved_actions_are_ready() -> None:
    _, _, _, packet = _build("approved")

    assert packet["kind"] == (
        "brain_chat_research_action_decision_packet"
    )
    assert packet["target_name"] == (
        "demo-self-hosted-product"
    )
    assert packet["decision_status"] == (
        "ready-for-approved-action-packet"
    )
    assert packet["decision_ready"] is True
    assert packet["effective_approval_granted"] is True
    assert packet["approved_action_packet_ready"] is True

    assert packet["proposal_count"] == 8
    assert packet["decision_count"] == 8
    assert packet["approved_action_count"] == 8
    assert packet["rejected_action_count"] == 0
    assert packet["changes_requested_count"] == 0
    assert packet["deferred_action_count"] == 0
    assert packet["missing_decision_count"] == 0
    assert packet["unresolved_action_ids"] == []

    assert len(packet["approved_actions"]) == 8
    assert packet["rejected_actions"] == []
    assert packet["changes_requested_actions"] == []
    assert packet["deferred_actions"] == []

    assert all(
        item["effective_approval_granted"] is True
        for item in packet["approved_actions"]
    )

    assert packet["source_findings"] == []
    assert packet["decision_findings"] == []
    assert packet["counts"]["high_findings"] == 0
    assert packet["counts"]["medium_findings"] == 0


def test_all_rejected_actions_produce_rejected_status() -> None:
    _, _, _, packet = _build("rejected")

    assert packet["decision_status"] == "rejected"
    assert packet["decision_ready"] is True
    assert packet["effective_approval_granted"] is False
    assert packet["approved_action_packet_ready"] is False
    assert packet["approved_action_count"] == 0
    assert packet["rejected_action_count"] == 8
    assert len(packet["rejected_actions"]) == 8


def test_all_deferred_actions_produce_deferred_status() -> None:
    _, _, _, packet = _build("deferred")

    assert packet["decision_status"] == "deferred"
    assert packet["decision_ready"] is True
    assert packet["effective_approval_granted"] is False
    assert packet["approved_action_packet_ready"] is False
    assert packet["deferred_action_count"] == 8
    assert len(packet["deferred_actions"]) == 8


def test_changes_requested_blocks_approved_packet() -> None:
    _, _, _, packet = _build("changes-requested")

    assert packet["decision_status"] == "changes-requested"
    assert packet["decision_ready"] is True
    assert packet["effective_approval_granted"] is False
    assert packet["approved_action_packet_ready"] is False
    assert packet["changes_requested_count"] == 8
    assert len(packet["changes_requested_actions"]) == 8


def test_mixed_decisions_preserve_each_outcome() -> None:
    proposal, review = _proposal_and_review()
    decision_input = _decision_input(proposal)

    values = [
        "approved",
        "approved",
        "rejected",
        "rejected",
        "deferred",
        "deferred",
        "approved",
        "rejected",
    ]

    for item, decision in zip(
        decision_input["decisions"],
        values,
        strict=True,
    ):
        item["decision"] = decision
        item["reason"] = f"Selected {decision}."

    packet = build_research_action_decision_packet(
        proposal,
        review,
        decision_input,
    )

    assert packet["decision_status"] == (
        "ready-for-approved-action-packet"
    )
    assert packet["approved_action_count"] == 3
    assert packet["rejected_action_count"] == 3
    assert packet["deferred_action_count"] == 2
    assert packet["effective_approval_granted"] is True


def test_changes_requested_takes_precedence_over_approval() -> None:
    proposal, review = _proposal_and_review()
    decision_input = _decision_input(proposal)

    decision_input["decisions"][0]["decision"] = (
        "changes-requested"
    )
    decision_input["decisions"][0]["reason"] = (
        "Revise this action."
    )

    packet = build_research_action_decision_packet(
        proposal,
        review,
        decision_input,
    )

    assert packet["decision_status"] == "changes-requested"
    assert packet["approved_action_packet_ready"] is False
    assert packet["effective_approval_granted"] is False
    assert packet["approved_action_count"] == 7
    assert packet["changes_requested_count"] == 1
    assert all(
        item["effective_approval_granted"] is False
        for item in packet["approved_actions"]
    )


def test_approved_records_add_downstream_blockers() -> None:
    _, _, _, packet = _build("approved")

    for item in packet["approved_actions"]:
        assert "approved-action-packet-required" in (
            item["blocked_by"]
        )
        assert "typed-tool-request-manifest-required" in (
            item["blocked_by"]
        )
        assert "execution-gate-required" in (
            item["blocked_by"]
        )


def test_valid_decision_spellings_are_supported() -> None:
    assert VALID_DECISIONS == (
        "approved",
        "rejected",
        "changes-requested",
        "deferred",
    )

    proposal, review = _proposal_and_review()
    decision_input = _decision_input(proposal)

    decision_input["decisions"][0]["decision"] = (
        "changes_requested"
    )
    decision_input["decisions"][1]["decision"] = (
        "changes requested"
    )

    packet = build_research_action_decision_packet(
        proposal,
        review,
        decision_input,
    )

    assert packet["changes_requested_count"] == 2
    assert packet["decision_status"] == "changes-requested"


def test_wrong_proposal_kind_is_blocked() -> None:
    proposal, review = _proposal_and_review()
    proposal["kind"] = "wrong-kind"

    packet = build_research_action_decision_packet(
        proposal,
        review,
        _decision_input(proposal),
    )

    assert packet["decision_status"] == (
        "blocked-invalid-source"
    )
    assert packet["decision_ready"] is False
    assert "proposal.kind" in _subjects(
        packet,
        "source_findings",
    )


def test_wrong_review_kind_is_blocked() -> None:
    proposal, review = _proposal_and_review()
    review["kind"] = "wrong-kind"

    packet = build_research_action_decision_packet(
        proposal,
        review,
        _decision_input(proposal),
    )

    assert packet["decision_status"] == (
        "blocked-invalid-source"
    )
    assert "review.kind" in _subjects(
        packet,
        "source_findings",
    )


def test_source_target_mismatch_is_blocked() -> None:
    proposal, review = _proposal_and_review()
    review["target_name"] = "another-target"

    packet = build_research_action_decision_packet(
        proposal,
        review,
        _decision_input(proposal),
    )

    assert packet["decision_status"] == (
        "blocked-invalid-source"
    )
    assert "target_name" in _subjects(
        packet,
        "source_findings",
    )


def test_proposal_not_ready_is_blocked() -> None:
    proposal, review = _proposal_and_review()
    proposal["proposal_status"] = (
        "blocked-invalid-investigation-plan"
    )

    packet = build_research_action_decision_packet(
        proposal,
        review,
        _decision_input(proposal),
    )

    assert packet["decision_status"] == (
        "blocked-review-not-ready"
    )
    assert packet["approved_action_packet_ready"] is False


def test_action_proposal_ready_false_is_blocked() -> None:
    proposal, review = _proposal_and_review()
    proposal["action_proposal_ready"] = False

    packet = build_research_action_decision_packet(
        proposal,
        review,
        _decision_input(proposal),
    )

    assert packet["decision_status"] == (
        "blocked-review-not-ready"
    )


def test_review_not_ready_is_blocked() -> None:
    proposal, review = _proposal_and_review()
    review["review_ready"] = False

    packet = build_research_action_decision_packet(
        proposal,
        review,
        _decision_input(proposal),
    )

    assert packet["decision_status"] == (
        "blocked-review-not-ready"
    )


def test_wrong_review_status_is_blocked() -> None:
    proposal, review = _proposal_and_review()
    review["review_status"] = (
        "blocked-unsafe-action-proposals"
    )

    packet = build_research_action_decision_packet(
        proposal,
        review,
        _decision_input(proposal),
    )

    assert packet["decision_status"] == (
        "blocked-review-not-ready"
    )


def test_proposal_count_mismatch_is_blocked() -> None:
    proposal, review = _proposal_and_review()
    proposal["proposal_count"] = 999

    packet = build_research_action_decision_packet(
        proposal,
        review,
        _decision_input(proposal),
    )

    assert packet["decision_status"] == (
        "blocked-invalid-source"
    )
    assert "proposal.proposal_count" in _subjects(
        packet,
        "source_findings",
    )


def test_review_count_mismatch_is_blocked() -> None:
    proposal, review = _proposal_and_review()
    review["proposal_count"] = 999

    packet = build_research_action_decision_packet(
        proposal,
        review,
        _decision_input(proposal),
    )

    assert packet["decision_status"] == (
        "blocked-invalid-source"
    )
    assert "review.proposal_count" in _subjects(
        packet,
        "source_findings",
    )


def test_duplicate_proposal_action_ids_are_blocked() -> None:
    proposal, review = _proposal_and_review()
    proposal["proposals"][1]["action_id"] = (
        proposal["proposals"][0]["action_id"]
    )

    packet = build_research_action_decision_packet(
        proposal,
        review,
        _decision_input(proposal),
    )

    assert packet["decision_status"] == (
        "blocked-invalid-source"
    )
    assert any(
        "action IDs must be unique" in message
        for message in _messages(
            packet,
            "source_findings",
        )
    )


def test_unsafe_proposal_flag_is_blocked() -> None:
    proposal, review = _proposal_and_review()
    proposal["runtime_execution_allowed"] = True

    packet = build_research_action_decision_packet(
        proposal,
        review,
        _decision_input(proposal),
    )

    assert packet["decision_status"] == (
        "blocked-unsafe-source"
    )
    assert packet["runtime_execution_allowed"] is False


def test_unsafe_review_flag_is_blocked() -> None:
    proposal, review = _proposal_and_review()
    review["package_installation_allowed"] = True

    packet = build_research_action_decision_packet(
        proposal,
        review,
        _decision_input(proposal),
    )

    assert packet["decision_status"] == (
        "blocked-unsafe-source"
    )


def test_nested_unsafe_proposal_flag_is_blocked() -> None:
    proposal, review = _proposal_and_review()
    proposal["safety"]["tool_execution"] = True

    packet = build_research_action_decision_packet(
        proposal,
        review,
        _decision_input(proposal),
    )

    assert packet["decision_status"] == (
        "blocked-unsafe-source"
    )
    assert any(
        item["subject"]
        == "proposal.safety.tool_execution"
        for item in packet["source_findings"]
    )


def test_nested_unsafe_review_flag_is_blocked() -> None:
    proposal, review = _proposal_and_review()
    review["safety"]["browser_execution"] = True

    packet = build_research_action_decision_packet(
        proposal,
        review,
        _decision_input(proposal),
    )

    assert packet["decision_status"] == (
        "blocked-unsafe-source"
    )


def test_missing_source_safety_object_is_blocked() -> None:
    proposal, review = _proposal_and_review()
    del proposal["safety"]

    packet = build_research_action_decision_packet(
        proposal,
        review,
        _decision_input(proposal),
    )

    assert packet["decision_status"] == (
        "blocked-unsafe-source"
    )
    assert "proposal.safety" in _subjects(
        packet,
        "source_findings",
    )


def test_wrong_decision_input_kind_is_blocked() -> None:
    proposal, review = _proposal_and_review()
    decision_input = _decision_input(proposal)
    decision_input["kind"] = "wrong-kind"

    packet = build_research_action_decision_packet(
        proposal,
        review,
        decision_input,
    )

    assert packet["decision_status"] == (
        "blocked-invalid-decisions"
    )
    assert packet["decision_ready"] is False


def test_decision_target_mismatch_is_blocked() -> None:
    proposal, review = _proposal_and_review()
    decision_input = _decision_input(proposal)
    decision_input["target_name"] = "another-target"

    packet = build_research_action_decision_packet(
        proposal,
        review,
        decision_input,
    )

    assert packet["decision_status"] == (
        "blocked-invalid-decisions"
    )


def test_empty_reviewer_is_blocked() -> None:
    proposal, review = _proposal_and_review()
    decision_input = _decision_input(proposal)
    decision_input["reviewer"] = ""

    packet = build_research_action_decision_packet(
        proposal,
        review,
        decision_input,
    )

    assert packet["decision_status"] == (
        "blocked-invalid-decisions"
    )
    assert "decision.reviewer" in _subjects(
        packet,
        "decision_findings",
    )


def test_non_list_decisions_are_blocked_invalid() -> None:
    proposal, review = _proposal_and_review()
    decision_input = _decision_input(proposal)
    decision_input["decisions"] = {"wrong": True}

    packet = build_research_action_decision_packet(
        proposal,
        review,
        decision_input,
    )

    assert packet["decision_status"] == (
        "blocked-invalid-decisions"
    )
    assert packet["decision_ready"] is False


def test_missing_decision_is_blocked_incomplete() -> None:
    proposal, review = _proposal_and_review()
    decision_input = _decision_input(proposal)

    missing_action_id = (
        decision_input["decisions"][-1]["action_id"]
    )
    decision_input["decisions"].pop()

    packet = build_research_action_decision_packet(
        proposal,
        review,
        decision_input,
    )

    assert packet["decision_status"] == (
        "blocked-incomplete-decisions"
    )
    assert packet["missing_decision_count"] == 1
    assert packet["unresolved_action_ids"] == [
        missing_action_id
    ]


def test_duplicate_decision_is_blocked_invalid() -> None:
    proposal, review = _proposal_and_review()
    decision_input = _decision_input(proposal)

    decision_input["decisions"].append(
        copy.deepcopy(decision_input["decisions"][0])
    )

    packet = build_research_action_decision_packet(
        proposal,
        review,
        decision_input,
    )

    assert packet["decision_status"] == (
        "blocked-invalid-decisions"
    )
    assert any(
        "Duplicate decision" in message
        for message in _messages(
            packet,
            "decision_findings",
        )
    )


def test_unknown_action_id_is_blocked_invalid() -> None:
    proposal, review = _proposal_and_review()
    decision_input = _decision_input(proposal)

    decision_input["decisions"][0]["action_id"] = (
        "ACT-UNKNOWN-999"
    )

    packet = build_research_action_decision_packet(
        proposal,
        review,
        decision_input,
    )

    assert packet["decision_status"] == (
        "blocked-invalid-decisions"
    )
    assert any(
        "Unknown action_id" in message
        for message in _messages(
            packet,
            "decision_findings",
        )
    )


def test_invalid_decision_value_is_blocked() -> None:
    proposal, review = _proposal_and_review()
    decision_input = _decision_input(proposal)

    decision_input["decisions"][0]["decision"] = (
        "execute-now"
    )

    packet = build_research_action_decision_packet(
        proposal,
        review,
        decision_input,
    )

    assert packet["decision_status"] == (
        "blocked-invalid-decisions"
    )
    assert any(
        "Invalid decision" in message
        for message in _messages(
            packet,
            "decision_findings",
        )
    )


def test_non_object_decision_item_is_blocked() -> None:
    proposal, review = _proposal_and_review()
    decision_input = _decision_input(proposal)

    decision_input["decisions"][0] = "wrong"

    packet = build_research_action_decision_packet(
        proposal,
        review,
        decision_input,
    )

    assert packet["decision_status"] == (
        "blocked-invalid-decisions"
    )
    assert any(
        "Decision item must be an object" in message
        for message in _messages(
            packet,
            "decision_findings",
        )
    )


def test_missing_reason_is_medium_finding() -> None:
    proposal, review = _proposal_and_review()
    decision_input = _decision_input(
        proposal,
        decision="rejected",
    )

    decision_input["decisions"][0]["reason"] = ""

    packet = build_research_action_decision_packet(
        proposal,
        review,
        decision_input,
    )

    assert packet["decision_status"] == "rejected"
    assert packet["decision_ready"] is True
    assert packet["counts"]["medium_findings"] == 1
    assert packet["counts"]["high_findings"] == 0


def test_decision_input_must_remain_planning_only() -> None:
    proposal, review = _proposal_and_review()
    decision_input = _decision_input(proposal)
    decision_input["planning_only"] = False

    packet = build_research_action_decision_packet(
        proposal,
        review,
        decision_input,
    )

    assert packet["decision_status"] == (
        "blocked-invalid-decisions"
    )


def test_decision_input_must_remain_not_executed() -> None:
    proposal, review = _proposal_and_review()
    decision_input = _decision_input(proposal)
    decision_input["execution_state"] = "executed"

    packet = build_research_action_decision_packet(
        proposal,
        review,
        decision_input,
    )

    assert packet["decision_status"] == (
        "blocked-invalid-decisions"
    )


def test_builder_does_not_mutate_inputs() -> None:
    proposal, review = _proposal_and_review()
    decision_input = _decision_input(proposal)

    proposal_before = copy.deepcopy(proposal)
    review_before = copy.deepcopy(review)
    decision_before = copy.deepcopy(decision_input)

    build_research_action_decision_packet(
        proposal,
        review,
        decision_input,
    )

    assert proposal == proposal_before
    assert review == review_before
    assert decision_input == decision_before


def test_packet_remains_fail_closed() -> None:
    _, _, _, packet = _build("approved")

    assert packet["tool_request_manifest_ready"] is False
    assert packet["execution_gate_ready"] is False
    assert packet["command_generation_allowed"] is False
    assert packet["package_installation_allowed"] is False
    assert packet["execution_allowed"] is False
    assert packet["runtime_execution_allowed"] is False
    assert packet["target_interaction_allowed"] is False
    assert packet["evidence_collection_allowed"] is False
    assert packet["validation_allowed"] is False
    assert packet["state_mutation_allowed"] is False
    assert packet["report_submission_allowed"] is False
    assert (
        packet["vulnerability_confirmation_allowed"]
        is False
    )

    assert packet["planning_only"] is True
    assert packet["execution_state"] == "not_executed"

    assert packet["safety"]["local_only"] is True
    assert packet["safety"]["planning_only"] is True
    assert packet["safety"]["human_decision_required"] is True
    assert packet["safety"]["command_generation"] is False
    assert packet["safety"]["package_installation"] is False
    assert packet["safety"]["tool_execution"] is False
    assert packet["safety"]["browser_execution"] is False
    assert packet["safety"]["burp_execution"] is False
    assert packet["safety"]["kali_execution"] is False
    assert packet["safety"]["target_interaction"] is False
    assert packet["safety"]["evidence_collection"] is False
    assert packet["safety"]["validation_execution"] is False
    assert (
        packet["safety"]["runtime_execution_allowed"]
        is False
    )


def test_allowed_next_steps_reference_bridge() -> None:
    _, _, _, packet = _build("approved")

    allowed = "\n".join(packet["allowed_next_steps"])

    assert "approved-action packet" in allowed
    assert "typed planning-only tool requests" in allowed
    assert "tool execution gate" in allowed


def test_markdown_contains_decision_and_safety_sections() -> None:
    _, _, _, packet = _build("approved")

    markdown = (
        render_research_action_decision_packet_markdown(
            packet
        )
    )

    assert "# Research Action Decision Packet" in markdown
    assert "## Decision Status" in markdown
    assert "## Counts" in markdown
    assert "## Action Decisions" in markdown
    assert "## Source Findings" in markdown
    assert "## Decision Findings" in markdown
    assert "## Allowed Next Steps" in markdown
    assert "## Rejected Next Steps" in markdown
    assert "## Safety" in markdown

    assert (
        "decision_status: "
        "`ready-for-approved-action-packet`"
        in markdown
    )
    assert "decision_ready: `true`" in markdown
    assert (
        "effective_approval_granted: `true`"
        in markdown
    )
    assert "Runtime execution allowed: `false`" in markdown
    assert "Command generation allowed: `false`" in markdown
    assert "\\n" not in markdown


def test_file_builder_writes_markdown_and_json(
    tmp_path,
) -> None:
    proposal, review = _proposal_and_review()
    decision_input = _decision_input(proposal)

    proposal_file = tmp_path / "proposal.json"
    review_file = tmp_path / "review.json"
    decision_file = tmp_path / "decision.json"
    markdown_file = tmp_path / "output" / "decision.md"
    json_file = tmp_path / "output" / "decision.json"

    proposal_file.write_text(
        json.dumps(proposal),
        encoding="utf-8",
    )
    review_file.write_text(
        json.dumps(review),
        encoding="utf-8",
    )
    decision_file.write_text(
        json.dumps(decision_input),
        encoding="utf-8",
    )

    packet = build_decision_packet_from_files(
        proposal_file,
        review_file,
        decision_file,
        output_file=markdown_file,
        json_output=json_file,
    )

    assert packet["decision_status"] == (
        "ready-for-approved-action-packet"
    )
    assert markdown_file.exists()
    assert json_file.exists()

    written = json.loads(
        json_file.read_text(encoding="utf-8")
    )

    assert written["kind"] == (
        "brain_chat_research_action_decision_packet"
    )
    assert written["approved_action_count"] == 8
    assert written["runtime_execution_allowed"] is False

    markdown = markdown_file.read_text(encoding="utf-8")
    assert "# Research Action Decision Packet" in markdown
