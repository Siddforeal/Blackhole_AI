import copy
import json

from bugintel.core.brain_chat_research_state_transition_apply_decision_packet import (
    ALLOWED_DECISIONS,
    EXPECTED_GATE_KIND,
    EXPECTED_GATE_STATUS,
    EXPECTED_PACKET_KIND,
    build_apply_decision_packet_from_files,
    build_research_state_transition_apply_decision_packet,
    load_json_object,
)


def _review_item(index=1, hypothesis_id="HYP-001"):
    return {
        "review_item_id": f"RSTAR-{index:03d}",
        "operation_id": f"RSTO-{index:03d}",
        "transition_id": f"RST-{index:03d}",
        "decision_id": f"RSTD-{index:03d}",
        "hypothesis_id": hypothesis_id,
        "field_path": f"hypotheses.{hypothesis_id}.confidence",
        "operation_type": "local-proposed-hypothesis-confidence-update",
        "current_value": "medium",
        "proposed_value": "high",
        "decision_reason": "Approved for later apply review.",
        "source_operation_digest": f"o{index}" * 32,
        "human_apply_decision_required": True,
        "allowed_decisions": list(ALLOWED_DECISIONS),
        "persistent_write_ready": False,
        "persistent_write_allowed": False,
        "research_state_transition_ready": False,
        "research_state_transition_allowed": False,
        "confidence_update_allowed": False,
        "hypothesis_mutation_allowed": False,
        "research_state_mutation_allowed": False,
        "execution_allowed": False,
        "runtime_execution_allowed": False,
        "planning_only": True,
        "execution_state": "not_executed",
        "review_item_digest": f"r{index}" * 32,
    }


def _gate():
    review_items = [_review_item(1, "HYP-001"), _review_item(2, "HYP-002")]
    return {
        "kind": EXPECTED_GATE_KIND,
        "source": "brain-chat-research-state-transition-apply-review-gate",
        "target_name": "demo-target",
        "gate_status": EXPECTED_GATE_STATUS,
        "summary": "2 items ready for human apply review.",
        "source_transition_packet_digest": "p" * 64,
        "source_decision_digest": "d" * 64,
        "source_gate_digest": "g" * 64,
        "source_template_digest": "t" * 64,
        "source_update_digest": "u" * 64,
        "source_hypothesis_digest": "h" * 64,
        "source_feedback_digest": "f" * 64,
        "transition_operation_count": 2,
        "apply_review_item_count": 2,
        "apply_review_ready": True,
        "human_apply_decision_required": True,
        "human_apply_decision_complete": False,
        "research_state_transition_apply_packet_ready": False,
        "persistent_research_state_write_ready": False,
        "persistent_research_state_write_allowed": False,
        "research_state_transition_ready": False,
        "apply_review_items": review_items,
        "source_findings": [],
        "safety_findings": [],
        "operation_findings": [],
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
        "persistent_research_state_write_allowed": False,
        "report_submission_allowed": False,
        "vulnerability_confirmation_allowed": False,
        "planning_only": True,
        "execution_state": "not_executed",
        "apply_review_gate_digest": "a" * 64,
    }


def _decisions():
    return [
        {
            "review_item_id": "RSTAR-001",
            "decision": "approve-apply-packet",
            "decision_reason": "Approved for local apply preview.",
            "persistent_write_allowed": False,
            "execution_allowed": False,
            "runtime_execution_allowed": False,
            "planning_only": True,
            "execution_state": "not_executed",
        },
        {
            "review_item_id": "RSTAR-002",
            "decision": "defer-apply",
            "decision_reason": "Defer until more review.",
            "persistent_write_allowed": False,
            "execution_allowed": False,
            "runtime_execution_allowed": False,
            "planning_only": True,
            "execution_state": "not_executed",
        },
    ]


def _build():
    return build_research_state_transition_apply_decision_packet(_gate(), _decisions())


def _categories(packet, key):
    return {item["category"] for item in packet[key]}


def test_constants():
    assert EXPECTED_GATE_KIND == "brain_chat_research_state_transition_apply_review_gate"
    assert EXPECTED_GATE_STATUS == "ready-for-human-apply-review"
    assert EXPECTED_PACKET_KIND == "brain_chat_research_state_transition_apply_decision_packet"
    assert "approve-apply-packet" in ALLOWED_DECISIONS


def test_ready_apply_decisions_build_packet():
    packet = _build()

    assert packet["kind"] == EXPECTED_PACKET_KIND
    assert packet["decision_status"] == "ready-for-research-state-transition-apply-preview"
    assert packet["human_apply_decision_complete"] is True
    assert packet["human_apply_decision_required"] is False
    assert packet["research_state_transition_apply_preview_required"] is True
    assert packet["research_state_transition_apply_preview_ready"] is True
    assert packet["persistent_research_state_write_ready"] is False
    assert packet["persistent_research_state_write_allowed"] is False
    assert packet["research_state_transition_ready"] is False
    assert packet["apply_decision_count"] == 2
    assert packet["approved_apply_decision_count"] == 1
    assert len(packet["approved_apply_items"]) == 1


def test_apply_decision_packet_is_fail_closed():
    packet = _build()

    assert packet["persistent_research_state_write_allowed"] is False
    assert packet["confidence_update_allowed"] is False
    assert packet["hypothesis_mutation_allowed"] is False
    assert packet["selection_mutation_allowed"] is False
    assert packet["investigation_plan_mutation_allowed"] is False
    assert packet["research_state_mutation_allowed"] is False
    assert packet["execution_allowed"] is False
    assert packet["runtime_execution_allowed"] is False
    assert packet["target_interaction_allowed"] is False
    assert packet["evidence_collection_allowed"] is False
    assert packet["report_submission_allowed"] is False
    assert packet["vulnerability_confirmation_allowed"] is False


def test_apply_decision_records_preserve_review_fields():
    decision = _build()["apply_decisions"][0]

    assert decision["apply_decision_id"] == "RSTAD-001"
    assert decision["review_item_id"] == "RSTAR-001"
    assert decision["operation_id"] == "RSTO-001"
    assert decision["hypothesis_id"] == "HYP-001"
    assert decision["field_path"] == "hypotheses.HYP-001.confidence"
    assert decision["current_value"] == "medium"
    assert decision["proposed_value"] == "high"
    assert decision["decision"] == "approve-apply-packet"
    assert decision["apply_preview_required"] is True
    assert decision["persistent_write_allowed"] is False
    assert len(decision["apply_decision_digest"]) == 64


def test_invalid_gate_status_is_blocked():
    gate = _gate()
    gate["gate_status"] = "blocked-invalid-transition-operations"

    packet = build_research_state_transition_apply_decision_packet(gate, _decisions())

    assert packet["decision_status"] == "blocked-invalid-apply-review-gate"
    assert packet["human_apply_decision_complete"] is False
    assert "source-status" in _categories(packet, "source_findings")


def test_unsafe_gate_is_blocked():
    gate = _gate()
    gate["persistent_research_state_write_allowed"] = True

    packet = build_research_state_transition_apply_decision_packet(gate, _decisions())

    assert packet["decision_status"] == "blocked-unsafe-apply-review-gate"
    assert "unsafe-flag" in _categories(packet, "safety_findings")


def test_missing_human_decision_is_blocked():
    packet = build_research_state_transition_apply_decision_packet(_gate(), _decisions()[:1])

    assert packet["decision_status"] == "blocked-invalid-apply-decisions"
    assert "decision-coverage" in _categories(packet, "decision_findings")


def test_invalid_decision_value_is_blocked():
    decisions = _decisions()
    decisions[0]["decision"] = "apply-now"

    packet = build_research_state_transition_apply_decision_packet(_gate(), decisions)

    assert packet["decision_status"] == "blocked-invalid-apply-decisions"
    assert "decision-value" in _categories(packet, "decision_findings")


def test_missing_decision_reason_is_blocked():
    decisions = _decisions()
    decisions[0]["decision_reason"] = ""

    packet = build_research_state_transition_apply_decision_packet(_gate(), decisions)

    assert packet["decision_status"] == "blocked-invalid-apply-decisions"
    assert "decision-reason" in _categories(packet, "decision_findings")


def test_decision_unsafe_flag_is_blocked():
    decisions = _decisions()
    decisions[0]["persistent_write_allowed"] = True

    packet = build_research_state_transition_apply_decision_packet(_gate(), decisions)

    assert packet["decision_status"] == "blocked-invalid-apply-decisions"
    assert "decision-unsafe-flag" in _categories(packet, "decision_findings")


def test_no_approved_decisions_blocks_preview_but_completes_decisions():
    decisions = _decisions()
    decisions[0]["decision"] = "reject-apply"

    packet = build_research_state_transition_apply_decision_packet(_gate(), decisions)

    assert packet["decision_status"] == "blocked-no-approved-apply-decisions"
    assert packet["human_apply_decision_complete"] is True
    assert packet["research_state_transition_apply_preview_ready"] is False
    assert packet["approved_apply_decision_count"] == 0


def test_unknown_decision_reference_is_medium_finding_only():
    decisions = _decisions()
    decisions.append(
        {
            "review_item_id": "RSTAR-999",
            "decision": "defer-apply",
            "decision_reason": "Unknown item should not block.",
            "persistent_write_allowed": False,
            "execution_allowed": False,
            "runtime_execution_allowed": False,
            "planning_only": True,
            "execution_state": "not_executed",
        }
    )

    packet = build_research_state_transition_apply_decision_packet(_gate(), decisions)

    assert packet["decision_status"] == "ready-for-research-state-transition-apply-preview"
    assert "decision-coverage" in _categories(packet, "decision_findings")


def test_packet_is_deterministic():
    first = _build()
    second = _build()

    assert first == second
    assert len(first["apply_decision_packet_digest"]) == 64


def test_builder_does_not_mutate_input():
    gate = _gate()
    decisions = _decisions()
    original_gate = copy.deepcopy(gate)
    original_decisions = copy.deepcopy(decisions)

    build_research_state_transition_apply_decision_packet(gate, decisions)

    assert gate == original_gate
    assert decisions == original_decisions


def test_build_from_files_round_trip(tmp_path):
    gate_file = tmp_path / "apply-review-gate.json"
    decisions_file = tmp_path / "decisions.json"
    output_file = tmp_path / "apply-decision-packet.json"
    gate_file.write_text(json.dumps(_gate()), encoding="utf-8")
    decisions_file.write_text(json.dumps(_decisions()), encoding="utf-8")

    packet = build_apply_decision_packet_from_files(gate_file, decisions_file, output_file)

    assert packet["decision_status"] == "ready-for-research-state-transition-apply-preview"
    assert load_json_object(output_file) == packet
