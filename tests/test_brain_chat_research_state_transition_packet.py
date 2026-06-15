import copy
import json

from bugintel.core.brain_chat_research_state_transition_packet import (
    EXPECTED_DECISION_KIND,
    EXPECTED_DECISION_STATUS,
    EXPECTED_PACKET_KIND,
    build_research_state_transition_packet,
    build_transition_packet_from_file,
    load_json_object,
)


def _approved(index=1, hypothesis_id="HYP-001"):
    item = {
        "decision_id": f"RSTD-{index:03d}",
        "transition_id": f"RST-{index:03d}",
        "source_update_id": f"HCU-{index:03d}",
        "hypothesis_id": hypothesis_id,
        "title": "Admin boundary hypothesis",
        "proposed_state_change": "update-hypothesis-confidence",
        "current_confidence": "medium",
        "proposed_confidence": "high",
        "decision": "approve-transition-packet",
        "decision_reason": "Approved for later local state-transition packet.",
        "source_update_digest": "u" * 64,
        "source_transition_candidate_digest": f"c{index}" * 32,
        "state_transition_packet_required": True,
        "research_state_transition_allowed": False,
        "confidence_update_allowed": False,
        "research_state_mutation_allowed": False,
        "execution_allowed": False,
        "runtime_execution_allowed": False,
        "planning_only": True,
        "execution_state": "not_executed",
    }
    item["approved_transition_digest"] = f"a{index}" * 32
    return item


def _decision_packet():
    approved = [
        _approved(1, "HYP-001"),
        _approved(2, "HYP-002"),
    ]
    return {
        "kind": EXPECTED_DECISION_KIND,
        "source": "brain-chat-research-state-transition-decision-packet",
        "target_name": "demo-target",
        "decision_status": EXPECTED_DECISION_STATUS,
        "summary": "2 approved transitions.",
        "source_gate_digest": "g" * 64,
        "source_template_digest": "t" * 64,
        "source_update_digest": "u" * 64,
        "source_hypothesis_digest": "h" * 64,
        "source_feedback_digest": "f" * 64,
        "transition_candidate_count": 2,
        "transition_decision_count": 2,
        "approved_transition_count": 2,
        "human_transition_decision_complete": True,
        "human_transition_decision_required": False,
        "research_state_transition_packet_required": True,
        "research_state_transition_packet_ready": True,
        "research_state_transition_ready": False,
        "transition_decisions": [],
        "approved_transition_candidates": approved,
        "gate_findings": [],
        "template_findings": [],
        "safety_findings": [],
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
        "confidence_update_allowed": False,
        "hypothesis_mutation_allowed": False,
        "selection_mutation_allowed": False,
        "investigation_plan_mutation_allowed": False,
        "research_state_mutation_allowed": False,
        "report_submission_allowed": False,
        "vulnerability_confirmation_allowed": False,
        "planning_only": True,
        "execution_state": "not_executed",
        "decision_digest": "d" * 64,
    }


def _build():
    return build_research_state_transition_packet(_decision_packet())


def _categories(packet, key):
    return {item["category"] for item in packet[key]}


def test_constants():
    assert EXPECTED_DECISION_KIND == "brain_chat_research_state_transition_decision_packet"
    assert EXPECTED_DECISION_STATUS == "ready-for-research-state-transition-packet"
    assert EXPECTED_PACKET_KIND == "brain_chat_research_state_transition_packet"


def test_ready_decision_packet_builds_local_transition_packet():
    packet = _build()

    assert packet["kind"] == EXPECTED_PACKET_KIND
    assert packet["packet_status"] == "ready-for-research-state-transition-apply-review"
    assert packet["local_transition_packet_ready"] is True
    assert packet["research_state_transition_apply_review_required"] is True
    assert packet["persistent_research_state_write_ready"] is False
    assert packet["persistent_research_state_write_allowed"] is False
    assert packet["research_state_transition_ready"] is False
    assert packet["transition_operation_count"] == 2
    assert len(packet["transition_operations"]) == 2
    assert packet["source_findings"] == []
    assert packet["safety_findings"] == []
    assert packet["operation_findings"] == []


def test_transition_packet_is_fail_closed():
    packet = _build()

    assert packet["confidence_update_allowed"] is False
    assert packet["hypothesis_mutation_allowed"] is False
    assert packet["selection_mutation_allowed"] is False
    assert packet["investigation_plan_mutation_allowed"] is False
    assert packet["research_state_mutation_allowed"] is False
    assert packet["persistent_research_state_write_allowed"] is False
    assert packet["execution_allowed"] is False
    assert packet["runtime_execution_allowed"] is False
    assert packet["target_interaction_allowed"] is False
    assert packet["evidence_collection_allowed"] is False
    assert packet["report_submission_allowed"] is False
    assert packet["vulnerability_confirmation_allowed"] is False


def test_operation_records_preserve_decision_fields():
    operation = _build()["transition_operations"][0]

    assert operation["operation_id"] == "RSTO-001"
    assert operation["transition_id"] == "RST-001"
    assert operation["decision_id"] == "RSTD-001"
    assert operation["source_update_id"] == "HCU-001"
    assert operation["hypothesis_id"] == "HYP-001"
    assert operation["operation_type"] == "local-proposed-hypothesis-confidence-update"
    assert operation["field_path"] == "hypotheses.HYP-001.confidence"
    assert operation["current_value"] == "medium"
    assert operation["proposed_value"] == "high"
    assert operation["apply_review_required"] is True
    assert operation["persistent_write_allowed"] is False
    assert operation["research_state_mutation_allowed"] is False
    assert len(operation["operation_digest"]) == 64


def test_invalid_decision_status_is_blocked():
    decision = _decision_packet()
    decision["decision_status"] = "blocked-invalid-transition-decisions"

    packet = build_research_state_transition_packet(decision)

    assert packet["packet_status"] == "blocked-invalid-transition-decision-packet"
    assert packet["local_transition_packet_ready"] is False
    assert "source-status" in _categories(packet, "source_findings")


def test_missing_human_completion_is_blocked():
    decision = _decision_packet()
    decision["human_transition_decision_complete"] = False

    packet = build_research_state_transition_packet(decision)

    assert packet["packet_status"] == "blocked-invalid-transition-decision-packet"
    assert "source-readiness" in _categories(packet, "source_findings")


def test_unsafe_source_is_blocked():
    decision = _decision_packet()
    decision["research_state_mutation_allowed"] = True

    packet = build_research_state_transition_packet(decision)

    assert packet["packet_status"] == "blocked-unsafe-transition-decision-packet"
    assert "unsafe-flag" in _categories(packet, "safety_findings")


def test_no_approved_transitions_is_blocked():
    decision = _decision_packet()
    decision["approved_transition_candidates"] = []
    decision["approved_transition_count"] = 0

    packet = build_research_state_transition_packet(decision)

    assert packet["packet_status"] == "blocked-invalid-transition-decision-packet"
    assert "source-content" in _categories(packet, "source_findings")


def test_duplicate_hypothesis_operations_are_blocked():
    decision = _decision_packet()
    decision["approved_transition_candidates"][1]["hypothesis_id"] = "HYP-001"

    packet = build_research_state_transition_packet(decision)

    assert packet["packet_status"] == "blocked-invalid-transition-operations"
    assert "operation-coverage" in _categories(packet, "operation_findings")


def test_non_approval_transition_is_blocked():
    decision = _decision_packet()
    decision["approved_transition_candidates"][0]["decision"] = "reject-transition"

    packet = build_research_state_transition_packet(decision)

    assert packet["packet_status"] == "blocked-invalid-transition-operations"
    assert "operation-decision" in _categories(packet, "operation_findings")


def test_unsupported_operation_type_is_blocked():
    decision = _decision_packet()
    decision["approved_transition_candidates"][0]["proposed_state_change"] = "replace-investigation-plan"

    packet = build_research_state_transition_packet(decision)

    assert packet["packet_status"] == "blocked-invalid-transition-operations"
    assert "operation-type" in _categories(packet, "operation_findings")


def test_operation_unsafe_flag_is_blocked():
    decision = _decision_packet()
    decision["approved_transition_candidates"][0]["research_state_mutation_allowed"] = True

    packet = build_research_state_transition_packet(decision)

    assert packet["packet_status"] == "blocked-invalid-transition-operations"
    assert "operation-unsafe-flag" in _categories(packet, "operation_findings")


def test_packet_is_deterministic():
    first = _build()
    second = _build()

    assert first == second
    assert len(first["transition_packet_digest"]) == 64


def test_builder_does_not_mutate_input():
    decision = _decision_packet()
    original = copy.deepcopy(decision)

    build_research_state_transition_packet(decision)

    assert decision == original


def test_build_from_file_round_trip(tmp_path):
    decision_file = tmp_path / "decision.json"
    output_file = tmp_path / "transition.json"
    decision_file.write_text(json.dumps(_decision_packet()), encoding="utf-8")

    packet = build_transition_packet_from_file(decision_file, output_file)

    assert packet["packet_status"] == "ready-for-research-state-transition-apply-review"
    assert load_json_object(output_file) == packet
