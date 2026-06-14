import copy
import json

from bugintel.core.brain_chat_research_state_transition_review_gate import (
    EXPECTED_GATE_KIND,
    EXPECTED_UPDATE_KIND,
    EXPECTED_UPDATE_STATUS,
    build_research_state_transition_review_gate,
    build_review_gate_from_file,
    load_json_object,
    write_json,
)


def _update_record(update_id="HCU-001", hypothesis_id="HYP-001", current="medium", proposed="high"):
    item = {
        "update_id": update_id,
        "feedback_id": "HFB-001",
        "hypothesis_id": hypothesis_id,
        "title": "Admin boundary hypothesis",
        "current_confidence": current,
        "proposed_confidence": proposed,
        "decision_current_confidence": current,
        "categorical_confidence_change": current != proposed,
        "net_confidence_delta": 3,
        "proposed_disposition": "propose-confidence-promotion",
        "observation_ids": ["OBS-001"],
        "source_feedback_id": "HFB-001",
        "source_proposal_digest": "a" * 64,
        "source_decision_digest": "c" * 64,
        "effective_confidence_update_ready": True,
        "research_state_transition_review_required": True,
        "confidence_update_allowed": False,
        "hypothesis_mutation_allowed": False,
        "selection_mutation_allowed": False,
        "investigation_plan_mutation_allowed": False,
        "research_state_mutation_allowed": False,
        "execution_allowed": False,
        "runtime_execution_allowed": False,
        "planning_only": True,
        "execution_state": "not_executed",
        "update_digest": "d" * 64,
    }
    return item


def _update_packet():
    updates = [
        _update_record("HCU-001", "HYP-001", "medium", "high"),
        _update_record("HCU-002", "HYP-002", "high", "confirmed"),
    ]
    return {
        "kind": EXPECTED_UPDATE_KIND,
        "source": "brain-chat-research-hypothesis-confidence-update-packet",
        "target_name": "demo-target",
        "update_status": EXPECTED_UPDATE_STATUS,
        "summary": "2 proposed confidence updates.",
        "source_hypothesis_digest": "h" * 64,
        "source_decision_digest": "d" * 64,
        "source_feedback_digest": "f" * 64,
        "hypothesis_count": 2,
        "accepted_feedback_count": 2,
        "confidence_update_count": 2,
        "confidence_update_packet_ready": True,
        "research_state_transition_review_required": True,
        "research_state_transition_ready": False,
        "confidence_updates": updates,
        "hypothesis_findings": [],
        "decision_findings": [],
        "safety_findings": [],
        "consistency_findings": [],
        "command_generation_allowed": False,
        "payload_generation_allowed": False,
        "package_installation_allowed": False,
        "execution_allowed": False,
        "runtime_execution_allowed": False,
        "network_interaction_allowed": False,
        "target_interaction_allowed": False,
        "evidence_collection_allowed": False,
        "validation_allowed": False,
        "confidence_update_allowed": False,
        "hypothesis_mutation_allowed": False,
        "selection_mutation_allowed": False,
        "investigation_plan_mutation_allowed": False,
        "research_state_mutation_allowed": False,
        "report_submission_allowed": False,
        "vulnerability_confirmation_allowed": False,
        "planning_only": True,
        "execution_state": "not_executed",
        "update_digest": "u" * 64,
    }


def _build():
    return build_research_state_transition_review_gate(_update_packet())


def _categories(packet, key):
    return {item["category"] for item in packet[key]}


def test_constants():
    assert EXPECTED_UPDATE_KIND == "brain_chat_research_hypothesis_confidence_update_packet"
    assert EXPECTED_UPDATE_STATUS == "ready-for-research-state-transition-review"
    assert EXPECTED_GATE_KIND == "brain_chat_research_state_transition_review_gate"


def test_ready_update_packet_creates_human_transition_gate():
    gate = _build()

    assert gate["kind"] == EXPECTED_GATE_KIND
    assert gate["gate_status"] == "ready-for-human-transition-decision"
    assert gate["transition_review_ready"] is True
    assert gate["human_transition_decision_required"] is True
    assert gate["research_state_transition_packet_ready"] is False
    assert gate["research_state_transition_ready"] is False
    assert gate["transition_candidate_count"] == 2
    assert len(gate["transition_candidates"]) == 2
    assert gate["source_findings"] == []
    assert gate["safety_findings"] == []
    assert gate["candidate_findings"] == []


def test_transition_candidates_are_fail_closed():
    gate = _build()

    assert gate["confidence_update_allowed"] is False
    assert gate["hypothesis_mutation_allowed"] is False
    assert gate["research_state_mutation_allowed"] is False
    assert gate["execution_allowed"] is False
    assert gate["runtime_execution_allowed"] is False
    assert gate["validation_allowed"] is False
    assert gate["report_submission_allowed"] is False
    assert gate["vulnerability_confirmation_allowed"] is False

    candidate = gate["transition_candidates"][0]
    assert candidate["review_decision"] == "pending-human-transition-decision"
    assert candidate["human_review_required"] is True
    assert candidate["transition_packet_required_after_approval"] is True
    assert candidate["research_state_transition_allowed"] is False
    assert candidate["confidence_update_allowed"] is False
    assert candidate["research_state_mutation_allowed"] is False
    assert candidate["execution_allowed"] is False


def test_candidate_preserves_update_fields():
    gate = _build()
    candidate = gate["transition_candidates"][0]

    assert candidate["transition_id"] == "RST-001"
    assert candidate["source_update_id"] == "HCU-001"
    assert candidate["source_feedback_id"] == "HFB-001"
    assert candidate["hypothesis_id"] == "HYP-001"
    assert candidate["current_confidence"] == "medium"
    assert candidate["proposed_confidence"] == "high"
    assert candidate["proposed_state_change"] == "update-hypothesis-confidence"
    assert candidate["observation_ids"] == ["OBS-001"]
    assert len(candidate["transition_candidate_digest"]) == 64


def test_invalid_update_status_is_blocked():
    packet = _update_packet()
    packet["update_status"] = "blocked-invalid-confidence-update"

    gate = build_research_state_transition_review_gate(packet)

    assert gate["gate_status"] == "blocked-invalid-confidence-update-packet"
    assert gate["transition_review_ready"] is False
    assert "source-status" in _categories(gate, "source_findings")


def test_unsafe_source_is_blocked():
    packet = _update_packet()
    packet["research_state_mutation_allowed"] = True

    gate = build_research_state_transition_review_gate(packet)

    assert gate["gate_status"] == "blocked-unsafe-source"
    assert gate["transition_review_ready"] is False
    assert "unsafe-flag" in _categories(gate, "safety_findings")


def test_empty_updates_are_blocked():
    packet = _update_packet()
    packet["confidence_updates"] = []
    packet["confidence_update_count"] = 0

    gate = build_research_state_transition_review_gate(packet)

    assert gate["gate_status"] == "blocked-invalid-confidence-update-packet"
    assert gate["transition_review_ready"] is False
    assert "source-content" in _categories(gate, "source_findings")


def test_duplicate_hypothesis_candidates_are_blocked():
    packet = _update_packet()
    packet["confidence_updates"][1]["hypothesis_id"] = "HYP-001"

    gate = build_research_state_transition_review_gate(packet)

    assert gate["gate_status"] == "blocked-invalid-transition-candidates"
    assert gate["transition_review_ready"] is False
    assert "candidate-coverage" in _categories(gate, "candidate_findings")


def test_not_effective_update_is_blocked():
    packet = _update_packet()
    packet["confidence_updates"][0]["effective_confidence_update_ready"] = False

    gate = build_research_state_transition_review_gate(packet)

    assert gate["gate_status"] == "blocked-invalid-transition-candidates"
    assert "candidate-readiness" in _categories(gate, "candidate_findings")


def test_candidate_unsafe_flag_is_blocked():
    packet = _update_packet()
    packet["confidence_updates"][0]["execution_allowed"] = True

    gate = build_research_state_transition_review_gate(packet)

    assert gate["gate_status"] == "blocked-invalid-transition-candidates"
    assert "candidate-unsafe-flag" in _categories(gate, "candidate_findings")


def test_packet_is_deterministic():
    first = _build()
    second = _build()

    assert first == second
    assert len(first["gate_digest"]) == 64


def test_builder_does_not_mutate_inputs():
    packet = _update_packet()
    original = copy.deepcopy(packet)

    build_research_state_transition_review_gate(packet)

    assert packet == original


def test_build_from_file_round_trip(tmp_path):
    update_file = tmp_path / "update.json"
    output_file = tmp_path / "gate.json"

    update_file.write_text(json.dumps(_update_packet()), encoding="utf-8")

    gate = build_review_gate_from_file(update_file, output_file)

    assert gate["gate_status"] == "ready-for-human-transition-decision"
    assert load_json_object(output_file) == gate


def test_write_json_rejects_non_object_json(tmp_path):
    output_file = tmp_path / "gate.json"
    write_json(output_file, _build())

    assert load_json_object(output_file)["kind"] == EXPECTED_GATE_KIND

    bad_file = tmp_path / "bad.json"
    bad_file.write_text("[]", encoding="utf-8")

    try:
        load_json_object(bad_file)
    except ValueError as exc:
        assert "Expected JSON object" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
