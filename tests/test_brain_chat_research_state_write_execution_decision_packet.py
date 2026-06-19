import copy
import json

from bugintel.core.brain_chat_research_state_write_execution_decision_packet import (
    ALLOWED_DECISIONS,
    EXPECTED_GATE_KIND,
    EXPECTED_GATE_STATUS,
    EXPECTED_PACKET_KIND,
    build_research_state_write_execution_decision_packet,
    build_write_execution_decision_packet_from_files,
    load_json_object,
)


def _review_item(index=1, hypothesis_id="HYP-001"):
    return {
        "write_execution_review_item_id": f"WERG-{index:03d}",
        "local_write_packet_preview_item_id": f"LWPP-{index:03d}",
        "persistence_write_decision_id": f"PWRD-{index:03d}",
        "persistence_write_review_item_id": f"PWRG-{index:03d}",
        "source_preview_item_id": f"RSTPV-{index:03d}",
        "apply_decision_id": f"RSTAD-{index:03d}",
        "apply_review_item_id": f"RSTAR-{index:03d}",
        "operation_id": f"RSTO-{index:03d}",
        "transition_id": f"RST-{index:03d}",
        "decision_id": f"RSTD-{index:03d}",
        "hypothesis_id": hypothesis_id,
        "field_path": f"hypotheses.{hypothesis_id}.confidence",
        "operation_type": "local-proposed-hypothesis-confidence-update",
        "current_value": "medium",
        "proposed_value": "high",
        "write_preview_action": "preview-stored-state-field-update",
        "write_preview_summary": f"hypotheses.{hypothesis_id}.confidence: medium -> high",
        "source_local_write_packet_preview_item_digest": f"l{index}" * 32,
        "source_persistence_write_decision_digest": f"d{index}" * 32,
        "source_persistence_write_review_item_digest": f"r{index}" * 32,
        "source_apply_preview_item_digest": f"p{index}" * 32,
        "source_apply_decision_digest": f"a{index}" * 32,
        "source_operation_digest": f"o{index}" * 32,
        "human_write_execution_review_required": True,
        "human_write_execution_review_complete": False,
        "write_execution_decision_packet_ready": False,
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
        "write_execution_review_item_digest": f"w{index}" * 32,
    }


def _gate():
    review_items = [_review_item(1, "HYP-001"), _review_item(2, "HYP-002")]
    return {
        "kind": EXPECTED_GATE_KIND,
        "source": "brain-chat-research-state-write-execution-review-gate",
        "target_name": "demo-target",
        "gate_status": EXPECTED_GATE_STATUS,
        "source_local_write_packet_preview_digest": "lw" * 32,
        "source_persistence_write_decision_packet_digest": "wd" * 32,
        "source_persistence_write_review_gate_digest": "wg" * 32,
        "source_apply_preview_digest": "v" * 64,
        "source_apply_decision_packet_digest": "ad" * 32,
        "source_apply_review_gate_digest": "ar" * 32,
        "source_transition_packet_digest": "tp" * 32,
        "source_decision_digest": "d" * 64,
        "source_gate_digest": "g" * 64,
        "source_template_digest": "t" * 64,
        "source_update_digest": "u" * 64,
        "source_hypothesis_digest": "h" * 64,
        "source_feedback_digest": "f" * 64,
        "local_write_packet_preview_item_count": 2,
        "write_execution_review_item_count": 2,
        "write_execution_review_ready": True,
        "human_write_execution_review_required": True,
        "human_write_execution_review_complete": False,
        "write_execution_decision_packet_ready": False,
        "persistent_research_state_write_ready": False,
        "persistent_research_state_write_allowed": False,
        "research_state_transition_ready": False,
        "review_items": review_items,
        "allowed_decisions": list(ALLOWED_DECISIONS),
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
        "write_execution_review_gate_digest": "eg" * 32,
    }


def _decisions(decision="approve-write-execution-packet"):
    return {
        "human_write_execution_decisions": [
            {
                "write_execution_review_item_id": "WERG-001",
                "decision": decision,
                "decision_reason": "Approved for later local write execution packet.",
                "decision_actor": "human-reviewer",
            },
            {
                "write_execution_review_item_id": "WERG-002",
                "decision": "reject-write-execution",
                "decision_reason": "Not approved.",
                "decision_actor": "human-reviewer",
            },
        ]
    }


def _build():
    return build_research_state_write_execution_decision_packet(_gate(), _decisions())


def _categories(packet, key):
    return {item["category"] for item in packet[key]}


def test_constants():
    assert EXPECTED_GATE_KIND == "brain_chat_research_state_write_execution_review_gate"
    assert EXPECTED_GATE_STATUS == "ready-for-human-write-execution-review"
    assert EXPECTED_PACKET_KIND == "brain_chat_research_state_write_execution_decision_packet"
    assert "approve-write-execution-packet" in ALLOWED_DECISIONS


def test_ready_gate_and_human_decisions_build_packet():
    packet = _build()

    assert packet["kind"] == EXPECTED_PACKET_KIND
    assert packet["decision_status"] == "ready-for-local-write-execution-packet"
    assert packet["human_write_execution_decision_required"] is True
    assert packet["human_write_execution_decision_complete"] is True
    assert packet["local_write_execution_packet_required"] is True
    assert packet["local_write_execution_packet_ready"] is False
    assert packet["persistent_research_state_write_ready"] is False
    assert packet["persistent_research_state_write_allowed"] is False
    assert packet["research_state_transition_ready"] is False
    assert packet["write_execution_decision_count"] == 2
    assert packet["approved_write_execution_decision_count"] == 1
    assert len(packet["approved_write_execution_items"]) == 1
    assert packet["source_findings"] == []
    assert packet["safety_findings"] == []
    assert packet["decision_findings"] == []


def test_decision_packet_is_fail_closed():
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


def test_approved_item_preserves_review_context():
    item = _build()["approved_write_execution_items"][0]

    assert item["write_execution_decision_id"] == "WEDP-001"
    assert item["write_execution_review_item_id"] == "WERG-001"
    assert item["local_write_packet_preview_item_id"] == "LWPP-001"
    assert item["persistence_write_decision_id"] == "PWRD-001"
    assert item["operation_id"] == "RSTO-001"
    assert item["hypothesis_id"] == "HYP-001"
    assert item["field_path"] == "hypotheses.HYP-001.confidence"
    assert item["current_value"] == "medium"
    assert item["proposed_value"] == "high"
    assert item["decision"] == "approve-write-execution-packet"
    assert item["decision_valid"] is True
    assert item["local_write_execution_packet_required"] is True
    assert item["persistent_write_allowed"] is False
    assert len(item["write_execution_decision_digest"]) == 64


def test_invalid_gate_kind_is_blocked():
    gate = _gate()
    gate["kind"] = "wrong-kind"

    packet = build_research_state_write_execution_decision_packet(gate, _decisions())

    assert packet["decision_status"] == "blocked-invalid-write-execution-review-gate"
    assert "source-schema" in _categories(packet, "source_findings")


def test_invalid_gate_status_is_blocked():
    gate = _gate()
    gate["gate_status"] = "blocked-invalid-write-execution-review-items"

    packet = build_research_state_write_execution_decision_packet(gate, _decisions())

    assert packet["decision_status"] == "blocked-invalid-write-execution-review-gate"
    assert "source-status" in _categories(packet, "source_findings")


def test_completed_gate_is_blocked():
    gate = _gate()
    gate["human_write_execution_review_complete"] = True

    packet = build_research_state_write_execution_decision_packet(gate, _decisions())

    assert packet["decision_status"] == "blocked-invalid-write-execution-review-gate"
    assert "source-safety" in _categories(packet, "source_findings")


def test_unsafe_gate_is_blocked():
    gate = _gate()
    gate["persistent_research_state_write_allowed"] = True

    packet = build_research_state_write_execution_decision_packet(gate, _decisions())

    assert packet["decision_status"] == "blocked-unsafe-write-execution-review-gate"
    assert "unsafe-flag" in _categories(packet, "safety_findings")


def test_no_review_items_is_blocked():
    gate = _gate()
    gate["review_items"] = []
    gate["write_execution_review_item_count"] = 0

    packet = build_research_state_write_execution_decision_packet(gate, _decisions())

    assert packet["decision_status"] == "blocked-no-write-execution-review-items"
    assert "source-content" in _categories(packet, "source_findings")


def test_empty_decisions_are_blocked():
    packet = build_research_state_write_execution_decision_packet(_gate(), {"human_write_execution_decisions": []})

    assert packet["decision_status"] == "blocked-invalid-write-execution-decisions"
    assert "decision-content" in _categories(packet, "decision_findings")


def test_unknown_decision_target_is_blocked():
    decisions = _decisions()
    decisions["human_write_execution_decisions"][0]["write_execution_review_item_id"] = "WERG-999"

    packet = build_research_state_write_execution_decision_packet(_gate(), decisions)

    assert packet["decision_status"] == "blocked-invalid-write-execution-decisions"
    assert "decision-coverage" in _categories(packet, "decision_findings")


def test_duplicate_decision_target_is_blocked():
    decisions = _decisions()
    decisions["human_write_execution_decisions"][1]["write_execution_review_item_id"] = "WERG-001"

    packet = build_research_state_write_execution_decision_packet(_gate(), decisions)

    assert packet["decision_status"] == "blocked-invalid-write-execution-decisions"
    assert "decision-coverage" in _categories(packet, "decision_findings")


def test_unsupported_decision_is_blocked():
    decisions = _decisions("approve-everything-now")

    packet = build_research_state_write_execution_decision_packet(_gate(), decisions)

    assert packet["decision_status"] == "blocked-invalid-write-execution-decisions"
    assert "decision-value" in _categories(packet, "decision_findings")


def test_no_approved_decisions_is_blocked():
    decisions = _decisions("reject-write-execution")

    packet = build_research_state_write_execution_decision_packet(_gate(), decisions)

    assert packet["decision_status"] == "blocked-no-approved-write-execution-decisions"
    assert packet["approved_write_execution_decision_count"] == 0


def test_decision_packet_is_deterministic():
    first = _build()
    second = _build()

    assert first == second
    assert len(first["write_execution_decision_packet_digest"]) == 64


def test_builder_does_not_mutate_inputs():
    gate = _gate()
    decisions = _decisions()
    original_gate = copy.deepcopy(gate)
    original_decisions = copy.deepcopy(decisions)

    build_research_state_write_execution_decision_packet(gate, decisions)

    assert gate == original_gate
    assert decisions == original_decisions


def test_build_from_files_round_trip(tmp_path):
    gate_file = tmp_path / "write-execution-review-gate.json"
    decisions_file = tmp_path / "human-write-execution-decisions.json"
    output_file = tmp_path / "write-execution-decision-packet.json"
    gate_file.write_text(json.dumps(_gate()), encoding="utf-8")
    decisions_file.write_text(json.dumps(_decisions()), encoding="utf-8")

    packet = build_write_execution_decision_packet_from_files(gate_file, decisions_file, output_file)

    assert packet["decision_status"] == "ready-for-local-write-execution-packet"
    assert load_json_object(output_file) == packet
