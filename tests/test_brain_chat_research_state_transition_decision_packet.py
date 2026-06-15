import copy
import json

from bugintel.core.brain_chat_research_state_transition_decision_packet import (
    EXPECTED_PACKET_KIND,
    build_decision_packet_from_files,
    build_research_state_transition_decision_packet,
    load_json_object,
)


def _candidate(index=1, hypothesis_id="HYP-001"):
    return {
        "transition_id": f"RST-{index:03d}",
        "source_update_id": f"HCU-{index:03d}",
        "source_feedback_id": f"HFB-{index:03d}",
        "hypothesis_id": hypothesis_id,
        "title": "Admin boundary hypothesis",
        "proposed_state_change": "update-hypothesis-confidence",
        "current_confidence": "medium",
        "proposed_confidence": "high",
        "categorical_confidence_change": True,
        "net_confidence_delta": 3,
        "observation_ids": ["OBS-001"],
        "source_update_digest": "u" * 64,
        "review_decision": "pending-human-transition-decision",
        "human_review_required": True,
        "transition_packet_required_after_approval": True,
        "research_state_transition_allowed": False,
        "confidence_update_allowed": False,
        "hypothesis_mutation_allowed": False,
        "selection_mutation_allowed": False,
        "investigation_plan_mutation_allowed": False,
        "research_state_mutation_allowed": False,
        "execution_allowed": False,
        "runtime_execution_allowed": False,
        "planning_only": True,
        "execution_state": "not_executed",
        "transition_candidate_digest": f"{index}" * 64,
    }


def _gate():
    candidates = [_candidate(1, "HYP-001"), _candidate(2, "HYP-002")]
    return {
        "kind": "brain_chat_research_state_transition_review_gate",
        "target_name": "demo-target",
        "gate_status": "ready-for-human-transition-decision",
        "source_update_digest": "u" * 64,
        "source_hypothesis_digest": "h" * 64,
        "source_decision_digest": "d" * 64,
        "source_feedback_digest": "f" * 64,
        "transition_candidate_count": 2,
        "transition_review_ready": True,
        "human_transition_decision_required": True,
        "research_state_transition_packet_ready": False,
        "research_state_transition_ready": False,
        "transition_candidates": candidates,
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
        "gate_digest": "g" * 64,
    }


def _decision(index=1, decision="approve-transition-packet", reason="Approved for later local state-transition packet."):
    approved = decision == "approve-transition-packet"
    requested_changes = ["Add missing evidence note."] if decision == "request-changes" else []
    return {
        "decision_id": f"RSTD-{index:03d}",
        "transition_id": f"RST-{index:03d}",
        "source_update_id": f"HCU-{index:03d}",
        "hypothesis_id": f"HYP-{index:03d}",
        "title": "Admin boundary hypothesis",
        "proposed_state_change": "update-hypothesis-confidence",
        "current_confidence": "medium",
        "proposed_confidence": "high",
        "source_update_digest": "u" * 64,
        "source_transition_candidate_digest": f"{index}" * 64,
        "decision": decision,
        "decision_reason": reason,
        "requested_changes": requested_changes,
        "human_operator": "tester",
        "human_reviewed_at": "2026-06-14T00:00:00Z",
        "approved_for_state_transition_packet": approved,
        "state_transition_packet_required": approved,
        "human_review_required": True,
        "research_state_transition_allowed": False,
        "confidence_update_allowed": False,
        "hypothesis_mutation_allowed": False,
        "selection_mutation_allowed": False,
        "investigation_plan_mutation_allowed": False,
        "research_state_mutation_allowed": False,
        "execution_allowed": False,
        "runtime_execution_allowed": False,
        "planning_only": True,
        "execution_state": "not_executed",
        "decision_template_digest": f"t{index}" * 32,
    }


def _template(decision1="approve-transition-packet", decision2="reject-transition"):
    return {
        "kind": "brain_chat_research_state_transition_decision_template",
        "target_name": "demo-target",
        "template_status": "ready-for-human-transition-decision",
        "source_gate_digest": "g" * 64,
        "source_update_digest": "u" * 64,
        "source_hypothesis_digest": "h" * 64,
        "source_decision_digest": "d" * 64,
        "source_feedback_digest": "f" * 64,
        "transition_candidate_count": 2,
        "transition_decision_count": 2,
        "human_transition_decision_required": True,
        "human_transition_decision_complete": False,
        "research_state_transition_packet_ready": False,
        "research_state_transition_ready": False,
        "transition_decisions": [_decision(1, decision1), _decision(2, decision2, "Rejected for now.")],
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
        "template_digest": "T" * 64,
    }


def _build():
    return build_research_state_transition_decision_packet(_gate(), _template())


def _categories(packet, key):
    return {item["category"] for item in packet[key]}


def test_approval_decision_packet_is_ready_for_later_transition_packet():
    packet = _build()

    assert packet["kind"] == EXPECTED_PACKET_KIND
    assert packet["decision_status"] == "ready-for-research-state-transition-packet"
    assert packet["human_transition_decision_complete"] is True
    assert packet["research_state_transition_packet_required"] is True
    assert packet["research_state_transition_packet_ready"] is True
    assert packet["research_state_transition_ready"] is False
    assert packet["approved_transition_count"] == 1
    assert len(packet["approved_transition_candidates"]) == 1
    assert packet["gate_findings"] == []
    assert packet["template_findings"] == []
    assert packet["decision_findings"] == []


def test_decision_packet_is_fail_closed():
    packet = _build()

    assert packet["confidence_update_allowed"] is False
    assert packet["hypothesis_mutation_allowed"] is False
    assert packet["selection_mutation_allowed"] is False
    assert packet["investigation_plan_mutation_allowed"] is False
    assert packet["research_state_mutation_allowed"] is False
    assert packet["execution_allowed"] is False
    assert packet["runtime_execution_allowed"] is False
    assert packet["target_interaction_allowed"] is False
    assert packet["report_submission_allowed"] is False
    assert packet["vulnerability_confirmation_allowed"] is False


def test_all_rejected_decisions_are_complete_without_transition_packet():
    packet = build_research_state_transition_decision_packet(
        _gate(),
        _template("reject-transition", "defer-transition"),
    )

    assert packet["decision_status"] == "ready-no-research-state-transition-packet"
    assert packet["human_transition_decision_complete"] is True
    assert packet["research_state_transition_packet_required"] is False
    assert packet["research_state_transition_packet_ready"] is False
    assert packet["approved_transition_count"] == 0


def test_missing_reason_blocks_decision_packet():
    template = _template()
    template["transition_decisions"][0]["decision_reason"] = ""

    packet = build_research_state_transition_decision_packet(_gate(), template)

    assert packet["decision_status"] == "blocked-invalid-transition-decisions"
    assert "decision-reason" in _categories(packet, "decision_findings")


def test_pending_decision_blocks_decision_packet():
    template = _template()
    template["transition_decisions"][0]["decision"] = "pending-human-transition-decision"

    packet = build_research_state_transition_decision_packet(_gate(), template)

    assert packet["decision_status"] == "blocked-invalid-transition-decisions"
    assert "decision-value" in _categories(packet, "decision_findings")


def test_digest_mismatch_blocks_decision_packet():
    template = _template()
    template["source_gate_digest"] = "x" * 64

    packet = build_research_state_transition_decision_packet(_gate(), template)

    assert packet["decision_status"] == "blocked-invalid-transition-decision-template"
    assert "template-linkage" in _categories(packet, "template_findings")


def test_candidate_digest_mismatch_blocks_decision_packet():
    template = _template()
    template["transition_decisions"][0]["source_transition_candidate_digest"] = "x" * 64

    packet = build_research_state_transition_decision_packet(_gate(), template)

    assert packet["decision_status"] == "blocked-invalid-transition-decisions"
    assert "decision-linkage" in _categories(packet, "decision_findings")


def test_request_changes_requires_requested_changes():
    template = _template("request-changes", "reject-transition")
    template["transition_decisions"][0]["requested_changes"] = []

    packet = build_research_state_transition_decision_packet(_gate(), template)

    assert packet["decision_status"] == "blocked-invalid-transition-decisions"
    assert "decision-changes" in _categories(packet, "decision_findings")


def test_unsafe_decision_flag_blocks_packet():
    template = _template()
    template["transition_decisions"][0]["research_state_mutation_allowed"] = True

    packet = build_research_state_transition_decision_packet(_gate(), template)

    assert packet["decision_status"] == "blocked-invalid-transition-decisions"
    assert "decision-unsafe-flag" in _categories(packet, "decision_findings")


def test_unsafe_template_blocks_packet():
    template = _template()
    template["execution_allowed"] = True

    packet = build_research_state_transition_decision_packet(_gate(), template)

    assert packet["decision_status"] == "blocked-unsafe-transition-decision-source"
    assert "unsafe-flag" in _categories(packet, "safety_findings")


def test_missing_decision_blocks_packet():
    template = _template()
    template["transition_decisions"] = template["transition_decisions"][:1]
    template["transition_decision_count"] = 1

    packet = build_research_state_transition_decision_packet(_gate(), template)

    assert packet["decision_status"] == "blocked-invalid-transition-decisions"
    assert "decision-coverage" in _categories(packet, "decision_findings")


def test_packet_is_deterministic():
    first = _build()
    second = _build()

    assert first == second
    assert len(first["decision_digest"]) == 64


def test_builder_does_not_mutate_inputs():
    gate = _gate()
    template = _template()
    original_gate = copy.deepcopy(gate)
    original_template = copy.deepcopy(template)

    build_research_state_transition_decision_packet(gate, template)

    assert gate == original_gate
    assert template == original_template


def test_build_decision_packet_from_files_round_trip(tmp_path):
    gate_file = tmp_path / "gate.json"
    template_file = tmp_path / "template.json"
    output_file = tmp_path / "decision.json"
    gate_file.write_text(json.dumps(_gate()), encoding="utf-8")
    template_file.write_text(json.dumps(_template()), encoding="utf-8")

    packet = build_decision_packet_from_files(gate_file, template_file, output_file)

    assert packet["decision_status"] == "ready-for-research-state-transition-packet"
    assert load_json_object(output_file) == packet
