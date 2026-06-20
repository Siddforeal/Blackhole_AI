import copy
import json

from bugintel.core.brain_chat_research_state_final_persistence_apply_review_gate import (
    ALLOWED_HUMAN_DECISIONS,
    EXPECTED_GATE_KIND,
    EXPECTED_PACKET_KIND,
    EXPECTED_PACKET_STATUS,
    build_final_persistence_apply_review_gate_from_file,
    build_research_state_final_persistence_apply_review_gate,
    load_json_object,
)


def _local_item(index=1, hypothesis_id="HYP-001"):
    return {
        "local_write_execution_packet_item_id": f"LWEP-{index:03d}",
        "write_execution_decision_id": f"WEDP-{index:03d}",
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
        "decision": "approve-write-execution-packet",
        "decision_reason": "Approved for later local write execution packet.",
        "decision_actor": "human-reviewer",
        "source_write_execution_decision_digest": f"d{index}" * 32,
        "source_write_execution_review_item_digest": f"r{index}" * 32,
        "source_local_write_packet_preview_item_digest": f"l{index}" * 32,
        "source_persistence_write_decision_digest": f"p{index}" * 32,
        "source_persistence_write_review_item_digest": f"g{index}" * 32,
        "source_apply_preview_item_digest": f"a{index}" * 32,
        "source_apply_decision_digest": f"c{index}" * 32,
        "source_operation_digest": f"o{index}" * 32,
        "local_write_operation": "preview-persistent-research-state-field-write",
        "local_write_summary": f"hypotheses.{hypothesis_id}.confidence: medium -> high",
        "final_persistence_apply_review_required": True,
        "final_persistence_apply_review_ready": False,
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
        "local_write_execution_packet_item_digest": f"x{index}" * 32,
    }


def _packet():
    local_items = [_local_item(1, "HYP-001"), _local_item(2, "HYP-002")]
    return {
        "kind": EXPECTED_PACKET_KIND,
        "source": "brain-chat-research-state-local-write-execution-packet",
        "target_name": "demo-target",
        "packet_status": EXPECTED_PACKET_STATUS,
        "source_write_execution_decision_packet_digest": "ed" * 32,
        "source_write_execution_review_gate_digest": "eg" * 32,
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
        "approved_write_execution_decision_count": 2,
        "local_write_execution_packet_item_count": 2,
        "local_write_execution_packet_ready": True,
        "final_persistence_apply_review_gate_required": True,
        "final_persistence_apply_review_gate_ready": False,
        "persistent_research_state_write_ready": False,
        "persistent_research_state_write_allowed": False,
        "research_state_transition_ready": False,
        "local_write_execution_items": local_items,
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
        "local_write_execution_packet_digest": "lp" * 32,
    }


def _build():
    return build_research_state_final_persistence_apply_review_gate(_packet())


def _categories(packet, key):
    return {item["category"] for item in packet[key]}


def test_constants():
    assert EXPECTED_PACKET_KIND == "brain_chat_research_state_local_write_execution_packet"
    assert EXPECTED_PACKET_STATUS == "ready-for-final-persistence-apply-review-gate"
    assert EXPECTED_GATE_KIND == "brain_chat_research_state_final_persistence_apply_review_gate"
    assert "approve-final-persistence-apply" in ALLOWED_HUMAN_DECISIONS


def test_ready_local_packet_builds_final_persistence_apply_review_gate():
    gate = _build()

    assert gate["kind"] == EXPECTED_GATE_KIND
    assert gate["gate_status"] == "ready-for-human-final-persistence-apply-review"
    assert gate["human_final_persistence_apply_decision_required"] is True
    assert gate["human_final_persistence_apply_decision_complete"] is False
    assert gate["final_persistence_apply_decision_packet_required"] is True
    assert gate["final_persistence_apply_decision_packet_ready"] is False
    assert gate["persistent_research_state_write_ready"] is False
    assert gate["persistent_research_state_write_allowed"] is False
    assert gate["research_state_transition_ready"] is False
    assert gate["final_persistence_apply_review_item_count"] == 2
    assert len(gate["final_persistence_apply_review_items"]) == 2
    assert gate["source_findings"] == []
    assert gate["safety_findings"] == []
    assert gate["review_item_findings"] == []


def test_gate_is_fail_closed():
    gate = _build()

    assert gate["persistent_research_state_write_allowed"] is False
    assert gate["confidence_update_allowed"] is False
    assert gate["hypothesis_mutation_allowed"] is False
    assert gate["selection_mutation_allowed"] is False
    assert gate["investigation_plan_mutation_allowed"] is False
    assert gate["research_state_mutation_allowed"] is False
    assert gate["execution_allowed"] is False
    assert gate["runtime_execution_allowed"] is False
    assert gate["target_interaction_allowed"] is False
    assert gate["evidence_collection_allowed"] is False
    assert gate["report_submission_allowed"] is False
    assert gate["vulnerability_confirmation_allowed"] is False


def test_review_items_preserve_local_write_context():
    item = _build()["final_persistence_apply_review_items"][0]

    assert item["final_persistence_apply_review_item_id"] == "FPARG-001"
    assert item["local_write_execution_packet_item_id"] == "LWEP-001"
    assert item["write_execution_decision_id"] == "WEDP-001"
    assert item["write_execution_review_item_id"] == "WERG-001"
    assert item["local_write_packet_preview_item_id"] == "LWPP-001"
    assert item["persistence_write_decision_id"] == "PWRD-001"
    assert item["operation_id"] == "RSTO-001"
    assert item["hypothesis_id"] == "HYP-001"
    assert item["field_path"] == "hypotheses.HYP-001.confidence"
    assert item["current_value"] == "medium"
    assert item["proposed_value"] == "high"
    assert item["local_write_operation"] == "preview-persistent-research-state-field-write"
    assert item["human_final_persistence_apply_decision_required"] is True
    assert item["persistent_write_allowed"] is False
    assert "approve-final-persistence-apply" in item["allowed_human_decisions"]
    assert len(item["final_persistence_apply_review_item_digest"]) == 64


def test_invalid_local_packet_kind_is_blocked():
    packet = _packet()
    packet["kind"] = "wrong-kind"

    result = build_research_state_final_persistence_apply_review_gate(packet)

    assert result["gate_status"] == "blocked-invalid-local-write-execution-packet"
    assert "source-schema" in _categories(result, "source_findings")


def test_invalid_local_packet_status_is_blocked():
    packet = _packet()
    packet["packet_status"] = "blocked-invalid-local-write-execution-packet-items"

    result = build_research_state_final_persistence_apply_review_gate(packet)

    assert result["gate_status"] == "blocked-invalid-local-write-execution-packet"
    assert "source-status" in _categories(result, "source_findings")


def test_unready_local_packet_is_blocked():
    packet = _packet()
    packet["local_write_execution_packet_ready"] = False

    result = build_research_state_final_persistence_apply_review_gate(packet)

    assert result["gate_status"] == "blocked-invalid-local-write-execution-packet"
    assert "source-readiness" in _categories(result, "source_findings")


def test_unsafe_local_packet_is_blocked():
    packet = _packet()
    packet["persistent_research_state_write_allowed"] = True

    result = build_research_state_final_persistence_apply_review_gate(packet)

    assert result["gate_status"] == "blocked-invalid-local-write-execution-packet"
    assert "source-safety" in _categories(result, "source_findings")


def test_no_local_items_is_blocked():
    packet = _packet()
    packet["local_write_execution_items"] = []
    packet["local_write_execution_packet_item_count"] = 0

    result = build_research_state_final_persistence_apply_review_gate(packet)

    assert result["gate_status"] == "blocked-invalid-local-write-execution-packet"
    assert "source-content" in _categories(result, "source_findings")


def test_duplicate_local_item_ids_are_blocked():
    packet = _packet()
    packet["local_write_execution_items"][1]["local_write_execution_packet_item_id"] = "LWEP-001"

    result = build_research_state_final_persistence_apply_review_gate(packet)

    assert result["gate_status"] == "blocked-invalid-final-persistence-apply-review-items"
    assert "review-coverage" in _categories(result, "review_item_findings")


def test_duplicate_field_paths_are_blocked():
    packet = _packet()
    packet["local_write_execution_items"][1]["field_path"] = "hypotheses.HYP-001.confidence"

    result = build_research_state_final_persistence_apply_review_gate(packet)

    assert result["gate_status"] == "blocked-invalid-final-persistence-apply-review-items"
    assert "review-coverage" in _categories(result, "review_item_findings")


def test_missing_required_local_item_field_is_blocked():
    packet = _packet()
    packet["local_write_execution_items"][0]["operation_id"] = ""

    result = build_research_state_final_persistence_apply_review_gate(packet)

    assert result["gate_status"] == "blocked-invalid-final-persistence-apply-review-items"
    assert "review-schema" in _categories(result, "review_item_findings")


def test_unsupported_local_write_operation_is_blocked():
    packet = _packet()
    packet["local_write_execution_items"][0]["local_write_operation"] = "write-now"

    result = build_research_state_final_persistence_apply_review_gate(packet)

    assert result["gate_status"] == "blocked-invalid-final-persistence-apply-review-items"
    assert "review-operation" in _categories(result, "review_item_findings")


def test_local_item_unsafe_flag_is_blocked():
    packet = _packet()
    packet["local_write_execution_items"][0]["persistent_write_allowed"] = True

    result = build_research_state_final_persistence_apply_review_gate(packet)

    assert result["gate_status"] == "blocked-invalid-final-persistence-apply-review-items"
    assert "review-unsafe-flag" in _categories(result, "review_item_findings")


def test_packet_is_deterministic():
    first = _build()
    second = _build()

    assert first == second
    assert len(first["final_persistence_apply_review_gate_digest"]) == 64


def test_builder_does_not_mutate_input():
    packet = _packet()
    original = copy.deepcopy(packet)

    build_research_state_final_persistence_apply_review_gate(packet)

    assert packet == original


def test_build_from_file_round_trip(tmp_path):
    packet_file = tmp_path / "local-write-execution-packet.json"
    output_file = tmp_path / "final-persistence-apply-review-gate.json"
    packet_file.write_text(json.dumps(_packet()), encoding="utf-8")

    result = build_final_persistence_apply_review_gate_from_file(packet_file, output_file)

    assert result["gate_status"] == "ready-for-human-final-persistence-apply-review"
    assert load_json_object(output_file) == result
