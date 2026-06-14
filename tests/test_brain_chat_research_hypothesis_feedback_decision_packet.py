import copy
import json

from bugintel.core.brain_chat_research_hypothesis_feedback_decision_packet import (
    EXPECTED_DECISION_INPUT_KIND,
    EXPECTED_FEEDBACK_KIND,
    EXPECTED_FEEDBACK_STATUS,
    VALID_DECISIONS,
    build_decision_packet_from_files,
    build_research_hypothesis_feedback_decision_packet,
    load_json_object,
    write_json,
)
from bugintel.core.brain_chat_research_hypothesis_feedback_decision_template import (
    build_research_hypothesis_feedback_decision_template,
)


def _proposal(
    feedback_id="HFB-001",
    hypothesis_id="HYP-001",
    current="medium",
    proposed="high",
    delta=3,
):
    return {
        "feedback_id": feedback_id,
        "hypothesis_id": hypothesis_id,
        "title": "Admin boundary hypothesis",
        "current_confidence": current,
        "proposed_confidence": proposed,
        "proposed_disposition": "propose-confidence-promotion",
        "categorical_confidence_change": current != proposed,
        "net_confidence_delta": delta,
        "evidence_direction": "strengthens",
        "observation_ids": ["OBS-001"],
        "proposal_digest": "a" * 64,
        "confidence_mutation_allowed": False,
        "state_mutation_allowed": False,
        "human_review_required": True,
        "required_review": "human-hypothesis-feedback-review",
        "planning_only": True,
        "execution_allowed": False,
        "runtime_execution_allowed": False,
    }


def _feedback_packet():
    return {
        "kind": EXPECTED_FEEDBACK_KIND,
        "target_name": "demo-target",
        "packet_status": EXPECTED_FEEDBACK_STATUS,
        "packet_ready": True,
        "hypothesis_feedback_review_ready": True,
        "feedback_digest": "b" * 64,
        "feedback_proposal_count": 2,
        "feedback_proposals": [
            _proposal("HFB-001", "HYP-001", "medium", "high", 3),
            _proposal("HFB-002", "HYP-002", "high", "high", 1),
        ],
        "confidence_update_ready": False,
        "research_state_transition_ready": False,
        "planning_only": True,
        "execution_allowed": False,
    }


def _decision_input(decision="accepted", confirmed=True):
    value = build_research_hypothesis_feedback_decision_template(
        _feedback_packet()
    )
    value["reviewer"] = "Sidd"
    value["overall_reason"] = "Human feedback decision recorded."
    for item in value["decisions"]:
        item["decision"] = decision
        item["accepted_proposed_confidence"] = (
            confirmed if decision == "accepted" else False
        )
        item["reason"] = f"Human decision recorded as {decision}."
    return value


def _build(decision="accepted", confirmed=True):
    feedback = _feedback_packet()
    decision_input = _decision_input(decision, confirmed)
    packet = build_research_hypothesis_feedback_decision_packet(
        feedback,
        decision_input,
    )
    return feedback, decision_input, packet


def _categories(packet, key="decision_findings"):
    return {item["category"] for item in packet[key]}


def test_constants():
    assert EXPECTED_FEEDBACK_KIND == "brain_chat_research_hypothesis_feedback_packet"
    assert EXPECTED_FEEDBACK_STATUS == "ready-for-hypothesis-feedback-review"
    assert EXPECTED_DECISION_INPUT_KIND == "brain_chat_research_hypothesis_feedback_decision_input"
    assert VALID_DECISIONS == (
        "accepted",
        "rejected",
        "changes-requested",
        "deferred",
    )


def test_accepted_feedback_is_ready_for_update_packet():
    _, _, packet = _build("accepted", confirmed=True)

    assert packet["kind"] == "brain_chat_research_hypothesis_feedback_decision_packet"
    assert packet["decision_status"] == "ready-for-hypothesis-confidence-update-packet"
    assert packet["decision_ready"] is True
    assert packet["hypothesis_confidence_update_packet_ready"] is True
    assert packet["effective_acceptance_granted"] is True
    assert packet["accepted_feedback_count"] == 2
    assert packet["rejected_feedback_count"] == 0
    assert packet["deferred_feedback_count"] == 0
    assert packet["missing_decision_count"] == 0
    assert len(packet["accepted_feedback"]) == 2
    assert packet["source_findings"] == []
    assert packet["decision_findings"] == []


def test_accepted_records_are_fail_closed():
    _, _, packet = _build("accepted", confirmed=True)

    assert packet["confidence_update_ready"] is False
    assert packet["research_state_transition_ready"] is False
    assert packet["hypothesis_mutation_allowed"] is False
    assert packet["research_state_mutation_allowed"] is False
    assert packet["execution_allowed"] is False

    record = packet["accepted_feedback"][0]
    assert record["effective_confidence_update_granted"] is True
    assert record["confidence_update_packet_required"] is True
    assert record["confidence_update_allowed"] is False
    assert record["hypothesis_mutation_allowed"] is False
    assert record["research_state_mutation_allowed"] is False
    assert record["execution_allowed"] is False


def test_rejected_feedback_status():
    _, _, packet = _build("rejected")

    assert packet["decision_status"] == "rejected"
    assert packet["hypothesis_confidence_update_packet_ready"] is False
    assert packet["accepted_feedback_count"] == 0
    assert packet["rejected_feedback_count"] == 2
    assert len(packet["rejected_feedback"]) == 2


def test_deferred_feedback_status():
    _, _, packet = _build("deferred")

    assert packet["decision_status"] == "deferred"
    assert packet["hypothesis_confidence_update_packet_ready"] is False
    assert packet["deferred_feedback_count"] == 2
    assert len(packet["deferred_feedback"]) == 2


def test_changes_requested_takes_precedence():
    feedback = _feedback_packet()
    decision_input = _decision_input("accepted", confirmed=True)
    decision_input["decisions"][0]["decision"] = "changes-requested"
    decision_input["decisions"][0]["accepted_proposed_confidence"] = False
    decision_input["decisions"][0]["reason"] = "Need better observation linkage."

    packet = build_research_hypothesis_feedback_decision_packet(
        feedback,
        decision_input,
    )

    assert packet["decision_status"] == "changes-requested"
    assert packet["hypothesis_confidence_update_packet_ready"] is False
    assert packet["accepted_feedback_count"] == 1
    assert packet["changes_requested_feedback_count"] == 1


def test_accepted_requires_explicit_confidence_confirmation():
    _, _, packet = _build("accepted", confirmed=False)

    assert packet["decision_status"] == "blocked-invalid-decisions"
    assert packet["hypothesis_confidence_update_packet_ready"] is False
    assert "decision-confirmation" in _categories(packet)


def test_missing_reviewer_is_blocked():
    feedback = _feedback_packet()
    decision_input = _decision_input("accepted", confirmed=True)
    decision_input["reviewer"] = ""

    packet = build_research_hypothesis_feedback_decision_packet(
        feedback,
        decision_input,
    )

    assert packet["decision_status"] == "blocked-invalid-decisions"
    assert "decision-schema" in _categories(packet)


def test_missing_decision_is_blocked():
    feedback = _feedback_packet()
    decision_input = _decision_input("accepted", confirmed=True)
    decision_input["decisions"] = decision_input["decisions"][:1]

    packet = build_research_hypothesis_feedback_decision_packet(
        feedback,
        decision_input,
    )

    assert packet["decision_status"] == "blocked-invalid-decisions"
    assert packet["missing_decision_count"] == 1
    assert "decision-coverage" in _categories(packet)


def test_unknown_feedback_id_is_blocked():
    feedback = _feedback_packet()
    decision_input = _decision_input("accepted", confirmed=True)
    decision_input["decisions"][0]["feedback_id"] = "HFB-999"

    packet = build_research_hypothesis_feedback_decision_packet(
        feedback,
        decision_input,
    )

    assert packet["decision_status"] == "blocked-invalid-decisions"
    assert "decision-consistency" in _categories(packet)


def test_wrong_feedback_kind_is_blocked():
    feedback = _feedback_packet()
    feedback["kind"] = "wrong-kind"

    packet = build_research_hypothesis_feedback_decision_packet(
        feedback,
        _decision_input("accepted", confirmed=True),
    )

    assert packet["decision_status"] == "blocked-invalid-source"
    assert packet["decision_ready"] is False


def test_feedback_not_ready_is_blocked():
    feedback = _feedback_packet()
    feedback["packet_status"] = "blocked-invalid-feedback-input"

    packet = build_research_hypothesis_feedback_decision_packet(
        feedback,
        _decision_input("accepted", confirmed=True),
    )

    assert packet["decision_status"] == "blocked-invalid-source"
    assert "source-readiness" in _categories(packet, "source_findings")


def test_unsafe_feedback_is_blocked():
    feedback = _feedback_packet()
    feedback["hypothesis_mutation_allowed"] = True

    packet = build_research_hypothesis_feedback_decision_packet(
        feedback,
        _decision_input("accepted", confirmed=True),
    )

    assert packet["decision_status"] == "blocked-unsafe-source"
    assert "source-safety" in _categories(packet, "source_findings")


def test_unsafe_decision_input_is_blocked():
    feedback = _feedback_packet()
    decision_input = _decision_input("accepted", confirmed=True)
    decision_input["research_state_mutation_allowed"] = True

    packet = build_research_hypothesis_feedback_decision_packet(
        feedback,
        decision_input,
    )

    assert packet["decision_status"] == "blocked-unsafe-decisions"
    assert "decision-safety" in _categories(packet)


def test_packet_is_deterministic():
    feedback = _feedback_packet()
    decision_input = _decision_input("accepted", confirmed=True)

    one = build_research_hypothesis_feedback_decision_packet(
        feedback,
        decision_input,
    )
    two = build_research_hypothesis_feedback_decision_packet(
        feedback,
        decision_input,
    )

    assert one == two
    assert len(one["decision_digest"]) == 64


def test_builder_does_not_mutate_inputs():
    feedback = _feedback_packet()
    decision_input = _decision_input("accepted", confirmed=True)
    feedback_before = copy.deepcopy(feedback)
    decision_before = copy.deepcopy(decision_input)

    build_research_hypothesis_feedback_decision_packet(
        feedback,
        decision_input,
    )

    assert feedback == feedback_before
    assert decision_input == decision_before


def test_build_from_files_round_trip(tmp_path):
    feedback_file = tmp_path / "feedback.json"
    decision_file = tmp_path / "decision.json"
    output_file = tmp_path / "packet.json"

    write_json(feedback_file, _feedback_packet())
    write_json(decision_file, _decision_input("accepted", confirmed=True))

    packet = build_decision_packet_from_files(
        feedback_file,
        decision_file,
        output_file,
    )

    loaded = load_json_object(output_file)
    assert loaded == packet
    assert packet["decision_status"] == "ready-for-hypothesis-confidence-update-packet"
    assert json.loads(output_file.read_text(encoding="utf-8")) == packet


def test_non_object_json_is_rejected(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("[]", encoding="utf-8")

    try:
        load_json_object(path)
    except ValueError as exc:
        assert "Expected JSON object" in str(exc)
    else:
        raise AssertionError("non-object JSON was accepted")
