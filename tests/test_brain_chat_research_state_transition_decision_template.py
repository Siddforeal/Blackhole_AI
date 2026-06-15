import copy
import json

from bugintel.core.brain_chat_research_state_transition_decision_template import (
    EXPECTED_GATE_KIND,
    EXPECTED_GATE_STATUS,
    EXPECTED_TEMPLATE_KIND,
    build_decision_template_from_file,
    build_research_state_transition_decision_template,
    load_json_object,
)


def _candidate(index=1, hypothesis_id="HYP-001"):
    record = {
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
    }
    record["transition_candidate_digest"] = f"{index}" * 64
    return record


def _gate():
    candidates = [
        _candidate(1, "HYP-001"),
        _candidate(2, "HYP-002"),
    ]
    return {
        "kind": EXPECTED_GATE_KIND,
        "source": "brain-chat-research-state-transition-review-gate",
        "target_name": "demo-target",
        "gate_status": EXPECTED_GATE_STATUS,
        "summary": "2 candidates ready.",
        "source_update_kind": "brain_chat_research_hypothesis_confidence_update_packet",
        "source_update_status": "ready-for-research-state-transition-review",
        "source_update_digest": "u" * 64,
        "source_hypothesis_digest": "h" * 64,
        "source_decision_digest": "d" * 64,
        "source_feedback_digest": "f" * 64,
        "confidence_update_count": 2,
        "transition_candidate_count": 2,
        "transition_review_ready": True,
        "human_transition_decision_required": True,
        "research_state_transition_packet_ready": False,
        "research_state_transition_ready": False,
        "transition_candidates": candidates,
        "source_findings": [],
        "safety_findings": [],
        "candidate_findings": [],
        "allowed_decisions": [
            "approve-transition-packet",
            "reject-transition",
            "request-changes",
            "defer-transition",
        ],
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


def _build():
    return build_research_state_transition_decision_template(_gate())


def _categories(packet, key):
    return {item["category"] for item in packet[key]}


def test_constants():
    assert EXPECTED_GATE_KIND == "brain_chat_research_state_transition_review_gate"
    assert EXPECTED_GATE_STATUS == "ready-for-human-transition-decision"
    assert EXPECTED_TEMPLATE_KIND == "brain_chat_research_state_transition_decision_template"


def test_ready_gate_creates_pending_human_decision_template():
    template = _build()

    assert template["kind"] == EXPECTED_TEMPLATE_KIND
    assert template["template_status"] == "ready-for-human-transition-decision"
    assert template["human_transition_decision_required"] is True
    assert template["human_transition_decision_complete"] is False
    assert template["research_state_transition_packet_ready"] is False
    assert template["research_state_transition_ready"] is False
    assert template["transition_decision_count"] == 2
    assert len(template["transition_decisions"]) == 2
    assert template["gate_findings"] == []
    assert template["safety_findings"] == []


def test_decision_records_are_pending_and_fail_closed():
    decision = _build()["transition_decisions"][0]

    assert decision["decision_id"] == "RSTD-001"
    assert decision["transition_id"] == "RST-001"
    assert decision["decision"] == "pending-human-transition-decision"
    assert decision["decision_reason"] == ""
    assert decision["approved_for_state_transition_packet"] is False
    assert decision["state_transition_packet_required"] is False
    assert decision["research_state_transition_allowed"] is False
    assert decision["confidence_update_allowed"] is False
    assert decision["research_state_mutation_allowed"] is False
    assert decision["execution_allowed"] is False
    assert decision["runtime_execution_allowed"] is False


def test_template_preserves_source_linkage():
    template = _build()

    assert template["source_gate_digest"] == "g" * 64
    assert template["source_update_digest"] == "u" * 64
    assert template["source_hypothesis_digest"] == "h" * 64
    assert template["transition_decisions"][0]["source_transition_candidate_digest"] == "1" * 64
    assert len(template["template_digest"]) == 64


def test_invalid_gate_status_is_blocked():
    gate = _gate()
    gate["gate_status"] = "blocked-invalid-transition-candidates"

    template = build_research_state_transition_decision_template(gate)

    assert template["template_status"] == "blocked-invalid-transition-review-gate"
    assert template["human_transition_decision_required"] is False
    assert "gate-status" in _categories(template, "gate_findings")


def test_unsafe_gate_is_blocked():
    gate = _gate()
    gate["research_state_mutation_allowed"] = True

    template = build_research_state_transition_decision_template(gate)

    assert template["template_status"] == "blocked-unsafe-review-gate"
    assert "unsafe-flag" in _categories(template, "safety_findings")


def test_no_candidates_is_blocked():
    gate = _gate()
    gate["transition_candidates"] = []
    gate["transition_candidate_count"] = 0

    template = build_research_state_transition_decision_template(gate)

    assert template["template_status"] == "blocked-invalid-transition-review-gate"
    assert "gate-content" in _categories(template, "gate_findings")


def test_template_is_deterministic():
    first = _build()
    second = _build()

    assert first == second


def test_builder_does_not_mutate_input():
    gate = _gate()
    original = copy.deepcopy(gate)

    build_research_state_transition_decision_template(gate)

    assert gate == original


def test_build_template_from_file_round_trip(tmp_path):
    gate_file = tmp_path / "gate.json"
    output_file = tmp_path / "template.json"
    gate_file.write_text(json.dumps(_gate()), encoding="utf-8")

    template = build_decision_template_from_file(gate_file, output_file)

    assert template["template_status"] == "ready-for-human-transition-decision"
    assert load_json_object(output_file) == template
