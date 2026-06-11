from __future__ import annotations

import copy
import json

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
    ACTION_PROFILES,
    EXPECTED_DECISION_KIND,
    EXPECTED_DECISION_STATUS,
    build_approved_action_packet_from_file,
    build_research_approved_action_packet,
    render_research_approved_action_packet_markdown,
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
                "title": "Worker execution trust boundary",
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


def _proposal_packet() -> dict:
    plan = build_research_investigation_plan_packet(
        _selection_packet()
    )
    plan_review = build_research_investigation_plan_review_gate(
        plan
    )

    return build_research_action_proposal_packet(
        plan,
        plan_review,
    ).to_dict()


def _decision_packet(
    decisions: list[str] | None = None,
) -> dict:
    proposal = _proposal_packet()
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
        "Reviewed for typed planning."
    )

    decision_values = decisions or [
        "approved"
        for _ in decision_input["decisions"]
    ]

    assert len(decision_values) == len(
        decision_input["decisions"]
    )

    for item, decision in zip(
        decision_input["decisions"],
        decision_values,
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


def _approved_packet(
    decisions: list[str] | None = None,
) -> dict:
    return build_research_approved_action_packet(
        _decision_packet(decisions)
    )


def _subjects(
    packet: dict,
    section: str,
) -> list[str]:
    return [
        item["subject"]
        for item in packet[section]
        if isinstance(item, dict)
    ]


def _messages(
    packet: dict,
    section: str,
) -> list[str]:
    return [
        item["message"]
        for item in packet[section]
        if isinstance(item, dict)
    ]


def _action(
    packet: dict,
    action_type: str,
) -> dict:
    return next(
        item
        for item in packet["approved_actions"]
        if item["action_type"] == action_type
    )


def test_expected_source_constants() -> None:
    assert EXPECTED_DECISION_KIND == (
        "brain_chat_research_action_decision_packet"
    )
    assert EXPECTED_DECISION_STATUS == (
        "ready-for-approved-action-packet"
    )


def test_all_action_profiles_are_defined() -> None:
    assert set(ACTION_PROFILES) == {
        "local-source-review",
        "local-artifact-review",
        "scope-confirmation-preparation",
        "controlled-account-preparation",
        "browser-observation-proposal",
        "burp-request-review-proposal",
        "command-proposal-preparation",
        "evidence-plan-preparation",
    }

    for action_type, profile in ACTION_PROFILES.items():
        assert action_type
        assert profile["tool_family"]
        assert profile["adapter_family"]
        assert profile["request_kind"]
        assert profile["risk_level"] in {
            "low",
            "medium",
            "high",
        }
        assert isinstance(
            profile["requires_scope_confirmation"],
            bool,
        )
        assert isinstance(
            profile["requires_controlled_assets"],
            bool,
        )
        assert isinstance(
            profile["requires_runtime_gate"],
            bool,
        )


def test_all_approved_actions_are_normalized() -> None:
    packet = _approved_packet()

    assert packet["kind"] == (
        "brain_chat_research_approved_action_packet"
    )
    assert packet["target_name"] == (
        "demo-self-hosted-product"
    )
    assert packet["packet_status"] == (
        "ready-for-typed-tool-request-manifest"
    )
    assert packet["packet_ready"] is True
    assert (
        packet["typed_tool_request_manifest_ready"]
        is True
    )
    assert packet["execution_gate_ready"] is False
    assert packet["runtime_execution_allowed"] is False

    assert packet["source_decision_status"] == (
        "ready-for-approved-action-packet"
    )
    assert packet["source_decision_ready"] is True
    assert (
        packet["source_effective_approval_granted"]
        is True
    )
    assert (
        packet["source_approved_action_packet_ready"]
        is True
    )

    assert packet["source_proposal_count"] == 8
    assert packet["source_decision_count"] == 8
    assert packet["declared_approved_action_count"] == 8
    assert packet["approved_action_count"] == 8

    assert len(packet["approved_actions"]) == 8
    assert packet["source_findings"] == []
    assert packet["action_findings"] == []
    assert packet["counts"]["high_findings"] == 0
    assert packet["counts"]["medium_findings"] == 0


def test_normalized_actions_follow_manual_order() -> None:
    packet = _approved_packet()

    orders = [
        item["manual_order"]
        for item in packet["approved_actions"]
    ]

    assert orders == sorted(orders)
    assert orders == list(range(1, 9))


def test_profile_mapping_matches_every_action() -> None:
    packet = _approved_packet()

    for action in packet["approved_actions"]:
        profile = ACTION_PROFILES[
            action["action_type"]
        ]

        assert (
            action["tool_family"]
            == profile["tool_family"]
        )
        assert (
            action["adapter_family"]
            == profile["adapter_family"]
        )
        assert (
            action["request_kind"]
            == profile["request_kind"]
        )
        assert (
            action["risk_level"]
            == profile["risk_level"]
        )
        assert (
            action["requires_scope_confirmation"]
            == profile[
                "requires_scope_confirmation"
            ]
        )
        assert (
            action["requires_controlled_assets"]
            == profile[
                "requires_controlled_assets"
            ]
        )
        assert (
            action["requires_runtime_gate"]
            == profile["requires_runtime_gate"]
        )


def test_risk_distribution_is_deterministic() -> None:
    packet = _approved_packet()

    assert packet["risk_level_counts"] == {
        "high": 1,
        "low": 3,
        "medium": 4,
    }
    assert packet["counts"]["risk_levels"] == 3


def test_tool_family_counts_are_deterministic() -> None:
    packet = _approved_packet()

    assert packet["tool_family_counts"] == {
        "browser": 1,
        "burp": 1,
        "evidence-planning": 1,
        "local-artifact-analysis": 1,
        "local-file-analysis": 1,
        "scope": 1,
        "shell-review": 1,
        "test-controls": 1,
    }
    assert packet["counts"]["tool_families"] == 8


def test_adapter_family_counts_are_deterministic() -> None:
    packet = _approved_packet()

    assert packet["adapter_family_counts"] == {
        "browser": 1,
        "burp": 1,
        "controlled-assets": 1,
        "evidence": 1,
        "local-artifact": 1,
        "local-file": 1,
        "scope-review": 1,
        "shell-review": 1,
    }
    assert packet["counts"]["adapter_families"] == 8


def test_runtime_gate_counts_are_deterministic() -> None:
    packet = _approved_packet()

    assert packet["runtime_gated_action_count"] == 4
    assert packet["scope_confirmation_action_count"] == 6
    assert packet["controlled_assets_action_count"] == 5

    assert packet["counts"]["runtime_gated_actions"] == 4
    assert (
        packet["counts"]["scope_confirmation_actions"]
        == 6
    )
    assert (
        packet["counts"]["controlled_assets_actions"]
        == 5
    )


def test_local_source_review_is_low_risk_local_only() -> None:
    packet = _approved_packet()
    action = _action(
        packet,
        "local-source-review",
    )

    assert action["risk_level"] == "low"
    assert action["tool_family"] == (
        "local-file-analysis"
    )
    assert action["adapter_family"] == "local-file"
    assert (
        action["requires_scope_confirmation"]
        is False
    )
    assert action["requires_controlled_assets"] is False
    assert action["requires_runtime_gate"] is False
    assert action["requires_observation_capture"] is False


def test_local_artifact_review_is_low_risk_local_only() -> None:
    packet = _approved_packet()
    action = _action(
        packet,
        "local-artifact-review",
    )

    assert action["risk_level"] == "low"
    assert action["tool_family"] == (
        "local-artifact-analysis"
    )
    assert action["adapter_family"] == (
        "local-artifact"
    )
    assert (
        action["requires_scope_confirmation"]
        is False
    )
    assert action["requires_controlled_assets"] is False
    assert action["requires_runtime_gate"] is False


def test_scope_preparation_is_low_risk_but_scope_bound() -> None:
    packet = _approved_packet()
    action = _action(
        packet,
        "scope-confirmation-preparation",
    )

    assert action["risk_level"] == "low"
    assert action["tool_family"] == "scope"
    assert action["adapter_family"] == "scope-review"
    assert (
        action["requires_scope_confirmation"]
        is True
    )
    assert action["requires_controlled_assets"] is False
    assert action["requires_runtime_gate"] is False


def test_browser_action_requires_runtime_guards() -> None:
    packet = _approved_packet()
    action = _action(
        packet,
        "browser-observation-proposal",
    )

    assert action["risk_level"] == "medium"
    assert action["tool_family"] == "browser"
    assert action["adapter_family"] == "browser"
    assert (
        action["requires_scope_confirmation"]
        is True
    )
    assert action["requires_controlled_assets"] is True
    assert action["requires_runtime_gate"] is True
    assert action["requires_observation_capture"] is True

    assert "runtime-human-approval-required" in (
        action["blocked_by"]
    )
    assert (
        "non-destructive-runtime-guard-required"
        in action["blocked_by"]
    )
    assert (
        "observation-capture-plan-required"
        in action["blocked_by"]
    )


def test_burp_action_requires_runtime_guards() -> None:
    packet = _approved_packet()
    action = _action(
        packet,
        "burp-request-review-proposal",
    )

    assert action["risk_level"] == "medium"
    assert action["tool_family"] == "burp"
    assert action["adapter_family"] == "burp"
    assert action["requires_runtime_gate"] is True
    assert action["requires_controlled_assets"] is True


def test_command_action_is_high_risk() -> None:
    packet = _approved_packet()
    action = _action(
        packet,
        "command-proposal-preparation",
    )

    assert action["risk_level"] == "high"
    assert action["tool_family"] == "shell-review"
    assert action["adapter_family"] == "shell-review"
    assert action["requires_runtime_gate"] is True

    assert any(
        "high risk classification" in reason
        for reason in action["risk_reasons"]
    )


def test_every_action_has_common_manifest_blockers() -> None:
    packet = _approved_packet()

    for action in packet["approved_actions"]:
        assert (
            "typed-tool-request-manifest-required"
            in action["blocked_by"]
        )
        assert (
            "human-tool-request-review-required"
            in action["blocked_by"]
        )
        assert (
            "tool-execution-gate-required"
            in action["blocked_by"]
        )


def test_scope_actions_receive_scope_blocker() -> None:
    packet = _approved_packet()

    for action in packet["approved_actions"]:
        if action["requires_scope_confirmation"]:
            assert "scope-confirmation-required" in (
                action["blocked_by"]
            )
        else:
            assert "scope-confirmation-required" not in (
                action["blocked_by"]
            )


def test_controlled_asset_actions_receive_blocker() -> None:
    packet = _approved_packet()

    for action in packet["approved_actions"]:
        if action["requires_controlled_assets"]:
            assert "controlled-assets-required" in (
                action["blocked_by"]
            )


def test_all_actions_remain_execution_disabled() -> None:
    packet = _approved_packet()

    for action in packet["approved_actions"]:
        assert action["manifest_eligible"] is True
        assert action["requires_human_approval"] is True
        assert action["requires_redaction_review"] is True
        assert action["command_generated"] is False
        assert (
            action["package_installation_allowed"]
            is False
        )
        assert action["execution_allowed"] is False
        assert (
            action["runtime_execution_allowed"]
            is False
        )
        assert (
            action["target_interaction_allowed"]
            is False
        )
        assert (
            action["evidence_collection_allowed"]
            is False
        )
        assert action["validation_allowed"] is False
        assert action["state_mutation_allowed"] is False


def test_mixed_decisions_include_only_approved_actions() -> None:
    packet = _approved_packet(
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

    assert packet["packet_status"] == (
        "ready-for-typed-tool-request-manifest"
    )
    assert packet["approved_action_count"] == 4
    assert len(packet["approved_actions"]) == 4

    assert {
        item["manual_order"]
        for item in packet["approved_actions"]
    } == {1, 3, 5, 7}


def test_builder_does_not_mutate_decision_packet() -> None:
    decision_packet = _decision_packet()
    before = copy.deepcopy(decision_packet)

    build_research_approved_action_packet(
        decision_packet
    )

    assert decision_packet == before


def test_wrong_decision_kind_is_blocked() -> None:
    decision_packet = _decision_packet()
    decision_packet["kind"] = "wrong-kind"

    packet = build_research_approved_action_packet(
        decision_packet
    )

    assert packet["packet_status"] == (
        "blocked-invalid-decision-packet"
    )
    assert packet["packet_ready"] is False
    assert "kind" in _subjects(
        packet,
        "source_findings",
    )


def test_missing_target_is_blocked() -> None:
    decision_packet = _decision_packet()
    decision_packet["target_name"] = ""

    packet = build_research_approved_action_packet(
        decision_packet
    )

    assert packet["packet_status"] == (
        "blocked-invalid-decision-packet"
    )
    assert "target_name" in _subjects(
        packet,
        "source_findings",
    )


def test_missing_reviewer_is_blocked() -> None:
    decision_packet = _decision_packet()
    decision_packet["reviewer"] = ""

    packet = build_research_approved_action_packet(
        decision_packet
    )

    assert packet["packet_status"] == (
        "blocked-invalid-decision-packet"
    )
    assert "reviewer" in _subjects(
        packet,
        "source_findings",
    )


def test_non_ready_decision_status_is_blocked() -> None:
    decision_packet = _decision_packet()
    decision_packet["decision_status"] = "rejected"

    packet = build_research_approved_action_packet(
        decision_packet
    )

    assert packet["packet_status"] == (
        "blocked-decision-not-ready"
    )
    assert packet["packet_ready"] is False


def test_decision_ready_false_is_blocked() -> None:
    decision_packet = _decision_packet()
    decision_packet["decision_ready"] = False

    packet = build_research_approved_action_packet(
        decision_packet
    )

    assert packet["packet_status"] == (
        "blocked-decision-not-ready"
    )


def test_effective_approval_false_is_blocked() -> None:
    decision_packet = _decision_packet()
    decision_packet["effective_approval_granted"] = False

    packet = build_research_approved_action_packet(
        decision_packet
    )

    assert packet["packet_status"] == (
        "blocked-decision-not-ready"
    )


def test_approved_packet_ready_false_is_blocked() -> None:
    decision_packet = _decision_packet()
    decision_packet["approved_action_packet_ready"] = False

    packet = build_research_approved_action_packet(
        decision_packet
    )

    assert packet["packet_status"] == (
        "blocked-decision-not-ready"
    )


def test_non_list_approved_actions_are_blocked() -> None:
    decision_packet = _decision_packet()
    decision_packet["approved_actions"] = {
        "wrong": True
    }

    packet = build_research_approved_action_packet(
        decision_packet
    )

    assert packet["packet_status"] == (
        "blocked-invalid-decision-packet"
    )
    assert "approved_actions" in _subjects(
        packet,
        "source_findings",
    )


def test_approved_action_count_mismatch_is_blocked() -> None:
    decision_packet = _decision_packet()
    decision_packet["approved_action_count"] = 999

    packet = build_research_approved_action_packet(
        decision_packet
    )

    assert packet["packet_status"] == (
        "blocked-invalid-decision-packet"
    )
    assert "approved_action_count" in _subjects(
        packet,
        "source_findings",
    )


def test_top_level_unsafe_flag_is_blocked() -> None:
    decision_packet = _decision_packet()
    decision_packet["runtime_execution_allowed"] = True

    packet = build_research_approved_action_packet(
        decision_packet
    )

    assert packet["packet_status"] == (
        "blocked-unsafe-decision-packet"
    )
    assert packet["runtime_execution_allowed"] is False


def test_source_must_remain_planning_only() -> None:
    decision_packet = _decision_packet()
    decision_packet["planning_only"] = False

    packet = build_research_approved_action_packet(
        decision_packet
    )

    assert packet["packet_status"] == (
        "blocked-unsafe-decision-packet"
    )


def test_source_must_remain_not_executed() -> None:
    decision_packet = _decision_packet()
    decision_packet["execution_state"] = "executed"

    packet = build_research_approved_action_packet(
        decision_packet
    )

    assert packet["packet_status"] == (
        "blocked-unsafe-decision-packet"
    )


def test_missing_safety_object_is_blocked() -> None:
    decision_packet = _decision_packet()
    del decision_packet["safety"]

    packet = build_research_approved_action_packet(
        decision_packet
    )

    assert packet["packet_status"] == (
        "blocked-unsafe-decision-packet"
    )
    assert "safety" in _subjects(
        packet,
        "source_findings",
    )


def test_required_true_safety_flag_is_enforced() -> None:
    for field in (
        "local_only",
        "planning_only",
        "human_decision_required",
    ):
        decision_packet = _decision_packet()
        decision_packet["safety"][field] = False

        packet = build_research_approved_action_packet(
            decision_packet
        )

        assert packet["packet_status"] == (
            "blocked-unsafe-decision-packet"
        )
        assert f"safety.{field}" in _subjects(
            packet,
            "source_findings",
        )


def test_required_false_safety_flags_are_enforced() -> None:
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
        decision_packet = _decision_packet()
        decision_packet["safety"][field] = True

        packet = build_research_approved_action_packet(
            decision_packet
        )

        assert packet["packet_status"] == (
            "blocked-unsafe-decision-packet"
        )
        assert f"safety.{field}" in _subjects(
            packet,
            "source_findings",
        )


def test_missing_action_field_is_blocked() -> None:
    decision_packet = _decision_packet()
    del decision_packet["approved_actions"][0]["purpose"]

    packet = build_research_approved_action_packet(
        decision_packet
    )

    assert packet["packet_status"] == (
        "blocked-inconsistent-approved-actions"
    )
    assert any(
        "Required action field is missing: purpose."
        == message
        for message in _messages(
            packet,
            "action_findings",
        )
    )


def test_duplicate_action_id_is_blocked() -> None:
    decision_packet = _decision_packet()
    decision_packet["approved_actions"][1]["action_id"] = (
        decision_packet["approved_actions"][0]["action_id"]
    )

    packet = build_research_approved_action_packet(
        decision_packet
    )

    assert packet["packet_status"] == (
        "blocked-inconsistent-approved-actions"
    )
    assert any(
        "Duplicate action_id" in message
        for message in _messages(
            packet,
            "action_findings",
        )
    )


def test_unsupported_action_type_is_blocked() -> None:
    decision_packet = _decision_packet()
    decision_packet["approved_actions"][0][
        "action_type"
    ] = "arbitrary-runtime-execution"

    packet = build_research_approved_action_packet(
        decision_packet
    )

    assert packet["packet_status"] == (
        "blocked-inconsistent-approved-actions"
    )
    assert any(
        "Unsupported approved action type" in message
        for message in _messages(
            packet,
            "action_findings",
        )
    )


def test_tool_family_mismatch_is_blocked() -> None:
    decision_packet = _decision_packet()
    decision_packet["approved_actions"][0][
        "proposed_tool_family"
    ] = "browser"

    packet = build_research_approved_action_packet(
        decision_packet
    )

    assert packet["packet_status"] == (
        "blocked-inconsistent-approved-actions"
    )
    assert any(
        "Tool-family mismatch" in message
        for message in _messages(
            packet,
            "action_findings",
        )
    )


def test_non_approved_action_is_blocked() -> None:
    decision_packet = _decision_packet()
    decision_packet["approved_actions"][0][
        "decision"
    ] = "rejected"

    packet = build_research_approved_action_packet(
        decision_packet
    )

    assert packet["packet_status"] == (
        "blocked-inconsistent-approved-actions"
    )
    assert any(
        "decision must be approved" in message
        for message in _messages(
            packet,
            "action_findings",
        )
    )


def test_ineffective_action_approval_is_blocked() -> None:
    decision_packet = _decision_packet()
    decision_packet["approved_actions"][0][
        "effective_approval_granted"
    ] = False

    packet = build_research_approved_action_packet(
        decision_packet
    )

    assert packet["packet_status"] == (
        "blocked-inconsistent-approved-actions"
    )
    assert any(
        "effective_approval_granted must be true"
        in message
        for message in _messages(
            packet,
            "action_findings",
        )
    )


def test_action_execution_flag_is_blocked() -> None:
    decision_packet = _decision_packet()
    decision_packet["approved_actions"][0][
        "execution_allowed"
    ] = True

    packet = build_research_approved_action_packet(
        decision_packet
    )

    assert packet["packet_status"] == (
        "blocked-inconsistent-approved-actions"
    )
    assert any(
        "Action safety field must remain false"
        in message
        for message in _messages(
            packet,
            "action_findings",
        )
    )


def test_empty_action_blockers_are_blocked() -> None:
    decision_packet = _decision_packet()
    decision_packet["approved_actions"][0][
        "blocked_by"
    ] = []

    packet = build_research_approved_action_packet(
        decision_packet
    )

    assert packet["packet_status"] == (
        "blocked-inconsistent-approved-actions"
    )
    assert any(
        "blocked_by must not be empty" in message
        for message in _messages(
            packet,
            "action_findings",
        )
    )


def test_empty_expected_artifact_is_medium_only() -> None:
    decision_packet = _decision_packet()
    decision_packet["approved_actions"][0][
        "expected_artifact"
    ] = ""

    packet = build_research_approved_action_packet(
        decision_packet
    )

    assert packet["packet_status"] == (
        "ready-for-typed-tool-request-manifest"
    )
    assert packet["packet_ready"] is True
    assert packet["counts"]["high_findings"] == 0
    assert packet["counts"]["medium_findings"] == 1


def test_invalid_manual_order_is_medium_only() -> None:
    decision_packet = _decision_packet()
    decision_packet["approved_actions"][0][
        "manual_order"
    ] = 0

    packet = build_research_approved_action_packet(
        decision_packet
    )

    assert packet["packet_status"] == (
        "ready-for-typed-tool-request-manifest"
    )
    assert packet["counts"]["medium_findings"] >= 1


def test_duplicate_manual_order_is_medium_only() -> None:
    decision_packet = _decision_packet()
    decision_packet["approved_actions"][1][
        "manual_order"
    ] = decision_packet["approved_actions"][0][
        "manual_order"
    ]

    packet = build_research_approved_action_packet(
        decision_packet
    )

    assert packet["packet_status"] == (
        "ready-for-typed-tool-request-manifest"
    )
    assert any(
        "Duplicate manual_order" in message
        for message in _messages(
            packet,
            "action_findings",
        )
    )


def test_synthetic_ready_packet_without_actions_is_blocked() -> None:
    decision_packet = _decision_packet()
    decision_packet["approved_actions"] = []
    decision_packet["approved_action_count"] = 0

    packet = build_research_approved_action_packet(
        decision_packet
    )

    assert packet["packet_status"] == (
        "blocked-no-approved-actions"
    )
    assert packet["approved_action_count"] == 0
    assert packet["packet_ready"] is False


def test_packet_remains_fail_closed() -> None:
    packet = _approved_packet()

    assert packet["execution_gate_ready"] is False
    assert packet["runtime_execution_allowed"] is False
    assert packet["command_generation_allowed"] is False
    assert packet["package_installation_allowed"] is False
    assert packet["execution_allowed"] is False
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
    assert (
        packet["safety"]["human_approval_recorded"]
        is True
    )
    assert (
        packet["safety"]["typed_normalization_only"]
        is True
    )
    assert packet["safety"]["command_generation"] is False
    assert packet["safety"]["tool_execution"] is False
    assert packet["safety"]["browser_execution"] is False
    assert packet["safety"]["burp_execution"] is False
    assert packet["safety"]["kali_execution"] is False
    assert (
        packet["safety"]["package_installation"]
        is False
    )
    assert (
        packet["safety"]["runtime_execution_allowed"]
        is False
    )


def test_allowed_next_steps_reference_typed_manifest() -> None:
    packet = _approved_packet()
    text = "\n".join(packet["allowed_next_steps"])

    assert "typed planning-only tool-request manifest" in text
    assert "tool family" in text
    assert "adapter family" in text
    assert "tool execution gate" in text


def test_markdown_contains_required_sections() -> None:
    packet = _approved_packet()

    markdown = (
        render_research_approved_action_packet_markdown(
            packet
        )
    )

    assert "# Research Approved Action Packet" in markdown
    assert "## Packet Status" in markdown
    assert "## Source Decision" in markdown
    assert "## Approved Actions" in markdown
    assert "## Source Findings" in markdown
    assert "## Action Findings" in markdown
    assert "## Allowed Next Steps" in markdown
    assert "## Rejected Next Steps" in markdown
    assert "## Safety" in markdown

    assert (
        "packet_status: "
        "`ready-for-typed-tool-request-manifest`"
        in markdown
    )
    assert "packet_ready: `true`" in markdown
    assert (
        "typed_tool_request_manifest_ready: `true`"
        in markdown
    )
    assert "runtime_execution_allowed: `false`" in markdown
    assert "Command generation allowed: `false`" in markdown
    assert "Package installation allowed: `false`" in markdown
    assert "\\n" not in markdown


def test_file_builder_writes_markdown_and_json(
    tmp_path,
) -> None:
    decision_packet = _decision_packet()

    decision_file = tmp_path / "decision.json"
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

    decision_file.write_text(
        json.dumps(decision_packet),
        encoding="utf-8",
    )

    packet = build_approved_action_packet_from_file(
        decision_file,
        output_file=markdown_file,
        json_output=json_file,
    )

    assert packet["packet_status"] == (
        "ready-for-typed-tool-request-manifest"
    )
    assert markdown_file.exists()
    assert json_file.exists()

    written = json.loads(
        json_file.read_text(encoding="utf-8")
    )

    assert written["kind"] == (
        "brain_chat_research_approved_action_packet"
    )
    assert written["approved_action_count"] == 8
    assert (
        written["typed_tool_request_manifest_ready"]
        is True
    )
    assert written["runtime_execution_allowed"] is False

    markdown = markdown_file.read_text(
        encoding="utf-8"
    )

    assert "# Research Approved Action Packet" in markdown
