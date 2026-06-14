import copy
import json

from bugintel.core.brain_chat_research_hypothesis_confidence_update_packet import (
    EXPECTED_DECISION_KIND,
    EXPECTED_DECISION_STATUS,
    EXPECTED_HYPOTHESIS_KIND,
    EXPECTED_HYPOTHESIS_STATUS,
    EXPECTED_UPDATE_KIND,
    build_confidence_update_packet_from_files,
    build_research_hypothesis_confidence_update_packet,
    load_json_object,
    write_json,
)


def _hypothesis(
    hypothesis_id="HYP-001",
    title="Admin boundary hypothesis",
    confidence="medium",
):
    return {
        "hypothesis_id": hypothesis_id,
        "title": title,
        "attack_surface": "admin",
        "hypothesis_type": "authorization-boundary",
        "rationale": "Local planning hypothesis.",
        "local_review_questions": ["What local evidence exists?"],
        "evidence_needed": ["Reviewed observation packet."],
        "allowed_local_checks": ["Review local artifacts only."],
        "rejected_actions": ["Do not execute tools."],
        "priority": "high",
        "confidence": confidence,
        "tags": ["authz"],
    }


def _hypothesis_packet():
    return {
        "kind": EXPECTED_HYPOTHESIS_KIND,
        "source": "brain-chat-research-hypothesis-packet",
        "target_name": "demo-target",
        "packet_status": EXPECTED_HYPOTHESIS_STATUS,
        "source_packet_status": "ready-for-hypothesis-generation",
        "hypothesis_count": 2,
        "hypotheses": [
            _hypothesis("HYP-001", "Admin boundary hypothesis", "medium"),
            _hypothesis("HYP-002", "Worker boundary hypothesis", "high"),
        ],
        "source_gaps": [],
        "hypothesis_gaps": [],
        "allowed_local_next_steps": ["Review hypotheses."],
        "rejected_actions": ["Do not execute tools."],
        "planning_only": True,
        "execution_state": "not_executed",
    }


def _accepted_feedback(
    feedback_id="HFB-001",
    hypothesis_id="HYP-001",
    current="medium",
    proposed="high",
    delta=3,
):
    item = {
        "feedback_id": feedback_id,
        "hypothesis_id": hypothesis_id,
        "title": "Admin boundary hypothesis",
        "current_confidence": current,
        "proposed_confidence": proposed,
        "categorical_confidence_change": current != proposed,
        "net_confidence_delta": delta,
        "proposed_disposition": "propose-confidence-promotion",
        "observation_ids": ["OBS-001"],
        "proposal_digest": "a" * 64,
        "decision": "accepted",
        "decision_reason": "Human accepted confidence update.",
        "accepted_proposed_confidence": True,
        "effective_confidence_update_granted": True,
        "confidence_update_packet_required": True,
        "confidence_update_allowed": False,
        "hypothesis_mutation_allowed": False,
        "research_state_mutation_allowed": False,
        "planning_only": True,
        "execution_allowed": False,
        "runtime_execution_allowed": False,
    }
    item["decision_digest"] = "c" * 64
    return item


def _decision_packet():
    accepted = [
        _accepted_feedback("HFB-001", "HYP-001", "medium", "high", 3),
        _accepted_feedback("HFB-002", "HYP-002", "high", "confirmed", 2),
    ]
    return {
        "kind": EXPECTED_DECISION_KIND,
        "source": "brain-chat-research-hypothesis-feedback-decision-packet",
        "target_name": "demo-target",
        "decision_status": EXPECTED_DECISION_STATUS,
        "summary": "2 accepted feedback decisions.",
        "reviewer": "Sidd",
        "overall_reason": "Accepted after human review.",
        "source_feedback_digest": "b" * 64,
        "decision_digest": "d" * 64,
        "feedback_proposal_count": 2,
        "decision_count": 2,
        "decision_ready": True,
        "hypothesis_confidence_update_packet_ready": True,
        "effective_acceptance_granted": True,
        "confidence_update_ready": False,
        "research_state_transition_ready": False,
        "accepted_feedback_count": 2,
        "accepted_feedback": accepted,
        "feedback_decisions": accepted,
        "rejected_feedback": [],
        "changes_requested_feedback": [],
        "deferred_feedback": [],
        "unresolved_feedback_ids": [],
        "source_findings": [],
        "decision_findings": [],
        "command_generation_allowed": False,
        "payload_generation_allowed": False,
        "package_installation_allowed": False,
        "execution_allowed": False,
        "runtime_execution_allowed": False,
        "network_interaction_allowed": False,
        "target_interaction_allowed": False,
        "evidence_collection_allowed": False,
        "validation_allowed": False,
        "hypothesis_mutation_allowed": False,
        "selection_mutation_allowed": False,
        "investigation_plan_mutation_allowed": False,
        "research_state_mutation_allowed": False,
        "report_submission_allowed": False,
        "vulnerability_confirmation_allowed": False,
        "planning_only": True,
        "execution_state": "not_executed",
    }


def _build():
    return build_research_hypothesis_confidence_update_packet(
        _hypothesis_packet(),
        _decision_packet(),
    )


def _categories(packet, key):
    return {item["category"] for item in packet[key]}


def test_constants():
    assert EXPECTED_HYPOTHESIS_KIND == "brain_chat_research_hypothesis_packet"
    assert EXPECTED_HYPOTHESIS_STATUS == "ready-for-hypothesis-review"
    assert EXPECTED_DECISION_KIND == "brain_chat_research_hypothesis_feedback_decision_packet"
    assert EXPECTED_DECISION_STATUS == "ready-for-hypothesis-confidence-update-packet"
    assert EXPECTED_UPDATE_KIND == "brain_chat_research_hypothesis_confidence_update_packet"


def test_accepted_decisions_create_ready_update_packet():
    packet = _build()

    assert packet["kind"] == EXPECTED_UPDATE_KIND
    assert packet["update_status"] == "ready-for-research-state-transition-review"
    assert packet["confidence_update_packet_ready"] is True
    assert packet["research_state_transition_review_required"] is True
    assert packet["research_state_transition_ready"] is False
    assert packet["confidence_update_count"] == 2
    assert len(packet["confidence_updates"]) == 2
    assert packet["hypothesis_findings"] == []
    assert packet["decision_findings"] == []
    assert packet["safety_findings"] == []
    assert packet["consistency_findings"] == []


def test_update_records_are_fail_closed():
    packet = _build()

    assert packet["confidence_update_allowed"] is False
    assert packet["hypothesis_mutation_allowed"] is False
    assert packet["research_state_mutation_allowed"] is False
    assert packet["execution_allowed"] is False
    assert packet["runtime_execution_allowed"] is False
    assert packet["validation_allowed"] is False
    assert packet["report_submission_allowed"] is False
    assert packet["vulnerability_confirmation_allowed"] is False

    record = packet["confidence_updates"][0]
    assert record["effective_confidence_update_ready"] is True
    assert record["research_state_transition_review_required"] is True
    assert record["confidence_update_allowed"] is False
    assert record["hypothesis_mutation_allowed"] is False
    assert record["research_state_mutation_allowed"] is False
    assert record["execution_allowed"] is False


def test_update_record_preserves_current_and_proposed_confidence():
    packet = _build()
    record = packet["confidence_updates"][0]

    assert record["update_id"] == "HCU-001"
    assert record["feedback_id"] == "HFB-001"
    assert record["hypothesis_id"] == "HYP-001"
    assert record["current_confidence"] == "medium"
    assert record["decision_current_confidence"] == "medium"
    assert record["proposed_confidence"] == "high"
    assert record["categorical_confidence_change"] is True
    assert record["net_confidence_delta"] == 3
    assert record["observation_ids"] == ["OBS-001"]
    assert len(record["update_digest"]) == 64


def test_non_ready_decision_packet_is_blocked():
    decision = _decision_packet()
    decision["decision_status"] = "deferred"
    decision["hypothesis_confidence_update_packet_ready"] = False

    packet = build_research_hypothesis_confidence_update_packet(
        _hypothesis_packet(),
        decision,
    )

    assert packet["update_status"] == "blocked-invalid-decision-packet"
    assert packet["confidence_update_packet_ready"] is False
    assert "decision-status" in _categories(packet, "decision_findings")


def test_stale_current_confidence_is_blocked():
    decision = _decision_packet()
    decision["accepted_feedback"][0]["current_confidence"] = "low"

    packet = build_research_hypothesis_confidence_update_packet(
        _hypothesis_packet(),
        decision,
    )

    assert packet["update_status"] == "blocked-invalid-confidence-update"
    assert packet["confidence_update_packet_ready"] is False
    assert "confidence-consistency" in _categories(packet, "consistency_findings")


def test_missing_hypothesis_reference_is_blocked():
    decision = _decision_packet()
    decision["accepted_feedback"][0]["hypothesis_id"] = "HYP-999"

    packet = build_research_hypothesis_confidence_update_packet(
        _hypothesis_packet(),
        decision,
    )

    assert packet["update_status"] == "blocked-invalid-confidence-update"
    assert "update-coverage" in _categories(packet, "consistency_findings")


def test_unsafe_source_is_blocked():
    decision = _decision_packet()
    decision["research_state_mutation_allowed"] = True

    packet = build_research_hypothesis_confidence_update_packet(
        _hypothesis_packet(),
        decision,
    )

    assert packet["update_status"] == "blocked-unsafe-source"
    assert packet["confidence_update_packet_ready"] is False
    assert "unsafe-flag" in _categories(packet, "safety_findings")


def test_invalid_hypothesis_packet_is_blocked():
    hypothesis = _hypothesis_packet()
    hypothesis["packet_status"] = "review-needed-hypothesis-gaps"

    packet = build_research_hypothesis_confidence_update_packet(
        hypothesis,
        _decision_packet(),
    )

    assert packet["update_status"] == "blocked-invalid-hypothesis-packet"
    assert packet["confidence_update_packet_ready"] is False
    assert "hypothesis-status" in _categories(packet, "hypothesis_findings")


def test_target_mismatch_is_blocked():
    decision = _decision_packet()
    decision["target_name"] = "other-target"

    packet = build_research_hypothesis_confidence_update_packet(
        _hypothesis_packet(),
        decision,
    )

    assert packet["update_status"] == "blocked-invalid-confidence-update"
    assert "target-consistency" in _categories(packet, "consistency_findings")


def test_packet_is_deterministic():
    first = _build()
    second = _build()

    assert first == second
    assert len(first["update_digest"]) == 64


def test_builder_does_not_mutate_inputs():
    hypothesis = _hypothesis_packet()
    decision = _decision_packet()
    original_hypothesis = copy.deepcopy(hypothesis)
    original_decision = copy.deepcopy(decision)

    build_research_hypothesis_confidence_update_packet(hypothesis, decision)

    assert hypothesis == original_hypothesis
    assert decision == original_decision


def test_build_from_files_round_trip(tmp_path):
    hypothesis_file = tmp_path / "hypothesis.json"
    decision_file = tmp_path / "decision.json"
    output_file = tmp_path / "update.json"

    hypothesis_file.write_text(json.dumps(_hypothesis_packet()), encoding="utf-8")
    decision_file.write_text(json.dumps(_decision_packet()), encoding="utf-8")

    packet = build_confidence_update_packet_from_files(
        hypothesis_file,
        decision_file,
        output_file,
    )

    assert packet["update_status"] == "ready-for-research-state-transition-review"
    assert load_json_object(output_file) == packet


def test_write_json_rejects_non_object_json(tmp_path):
    output_file = tmp_path / "packet.json"
    write_json(output_file, _build())

    assert load_json_object(output_file)["kind"] == EXPECTED_UPDATE_KIND

    bad_file = tmp_path / "bad.json"
    bad_file.write_text("[]", encoding="utf-8")

    try:
        load_json_object(bad_file)
    except ValueError as exc:
        assert "Expected JSON object" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
