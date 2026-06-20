import copy
import json

from bugintel.core.brain_chat_research_state_local_write_execution_packet import (
    EXPECTED_DECISION_KIND,
    EXPECTED_DECISION_STATUS,
    EXPECTED_PACKET_KIND,
    build_local_write_execution_packet_from_file,
    build_research_state_local_write_execution_packet,
    load_json_object,
)


def _approved(index=1, hypothesis_id="HYP-001"):
    return {
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
        "decision_valid": True,
        "decision_reason": "Approved for later local write execution packet.",
        "decision_actor": "human-reviewer",
        "source_write_execution_review_item_digest": f"w{index}" * 32,
        "source_local_write_packet_preview_item_digest": f"l{index}" * 32,
        "source_persistence_write_decision_digest": f"d{index}" * 32,
        "source_persistence_write_review_item_digest": f"r{index}" * 32,
        "source_apply_preview_item_digest": f"p{index}" * 32,
        "source_apply_decision_digest": f"a{index}" * 32,
        "source_operation_digest": f"o{index}" * 32,
        "human_write_execution_decision_complete": True,
        "local_write_execution_packet_required": True,
        "local_write_execution_packet_ready": False,
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
        "write_execution_decision_digest": f"x{index}" * 32,
    }


def _packet():
    approved = [_approved(1, "HYP-001"), _approved(2, "HYP-002")]
    return {
        "kind": EXPECTED_DECISION_KIND,
        "source": "brain-chat-research-state-write-execution-decision-packet",
        "target_name": "demo-target",
        "decision_status": EXPECTED_DECISION_STATUS,
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
        "write_execution_review_item_count": 2,
        "write_execution_decision_count": 2,
        "approved_write_execution_decision_count": 2,
        "human_write_execution_decision_required": True,
        "human_write_execution_decision_complete": True,
        "local_write_execution_packet_required": True,
        "local_write_execution_packet_ready": False,
        "persistent_research_state_write_ready": False,
        "persistent_research_state_write_allowed": False,
        "research_state_transition_ready": False,
        "write_execution_decisions": approved,
        "approved_write_execution_items": approved,
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
        "write_execution_decision_packet_digest": "dp" * 32,
    }


def _build():
    return build_research_state_local_write_execution_packet(_packet())


def _categories(packet, key):
    return {item["category"] for item in packet[key]}


def test_constants():
    assert EXPECTED_DECISION_KIND == "brain_chat_research_state_write_execution_decision_packet"
    assert EXPECTED_DECISION_STATUS == "ready-for-local-write-execution-packet"
    assert EXPECTED_PACKET_KIND == "brain_chat_research_state_local_write_execution_packet"


def test_ready_decision_packet_builds_local_write_execution_packet():
    packet = _build()

    assert packet["kind"] == EXPECTED_PACKET_KIND
    assert packet["packet_status"] == "ready-for-final-persistence-apply-review-gate"
    assert packet["local_write_execution_packet_ready"] is True
    assert packet["final_persistence_apply_review_gate_required"] is True
    assert packet["final_persistence_apply_review_gate_ready"] is False
    assert packet["persistent_research_state_write_ready"] is False
    assert packet["persistent_research_state_write_allowed"] is False
    assert packet["research_state_transition_ready"] is False
    assert packet["local_write_execution_packet_item_count"] == 2
    assert len(packet["local_write_execution_items"]) == 2
    assert packet["source_findings"] == []
    assert packet["safety_findings"] == []
    assert packet["local_packet_findings"] == []


def test_local_write_execution_packet_is_fail_closed():
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


def test_local_items_preserve_decision_context():
    item = _build()["local_write_execution_items"][0]

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
    assert item["local_write_summary"] == "hypotheses.HYP-001.confidence: medium -> high"
    assert item["final_persistence_apply_review_required"] is True
    assert item["persistent_write_allowed"] is False
    assert len(item["local_write_execution_packet_item_digest"]) == 64


def test_invalid_decision_packet_kind_is_blocked():
    packet = _packet()
    packet["kind"] = "wrong-kind"

    result = build_research_state_local_write_execution_packet(packet)

    assert result["packet_status"] == "blocked-invalid-write-execution-decision-packet"
    assert "source-schema" in _categories(result, "source_findings")


def test_invalid_decision_packet_status_is_blocked():
    packet = _packet()
    packet["decision_status"] = "blocked-invalid-write-execution-decisions"

    result = build_research_state_local_write_execution_packet(packet)

    assert result["packet_status"] == "blocked-invalid-write-execution-decision-packet"
    assert "source-status" in _categories(result, "source_findings")


def test_incomplete_human_decision_packet_is_blocked():
    packet = _packet()
    packet["human_write_execution_decision_complete"] = False

    result = build_research_state_local_write_execution_packet(packet)

    assert result["packet_status"] == "blocked-invalid-write-execution-decision-packet"
    assert "source-readiness" in _categories(result, "source_findings")


def test_unsafe_decision_packet_is_blocked():
    packet = _packet()
    packet["persistent_research_state_write_allowed"] = True

    result = build_research_state_local_write_execution_packet(packet)

    assert result["packet_status"] == "blocked-unsafe-write-execution-decision-packet"
    assert "unsafe-flag" in _categories(result, "safety_findings")


def test_no_approved_items_is_blocked():
    packet = _packet()
    packet["approved_write_execution_items"] = []
    packet["approved_write_execution_decision_count"] = 0

    result = build_research_state_local_write_execution_packet(packet)

    assert result["packet_status"] == "blocked-invalid-write-execution-decision-packet"
    assert "source-content" in _categories(result, "source_findings")


def test_duplicate_approved_decisions_are_blocked():
    packet = _packet()
    packet["approved_write_execution_items"][1]["write_execution_decision_id"] = "WEDP-001"

    result = build_research_state_local_write_execution_packet(packet)

    assert result["packet_status"] == "blocked-invalid-local-write-execution-packet-items"
    assert "local-coverage" in _categories(result, "local_packet_findings")


def test_duplicate_field_paths_are_blocked():
    packet = _packet()
    packet["approved_write_execution_items"][1]["field_path"] = "hypotheses.HYP-001.confidence"

    result = build_research_state_local_write_execution_packet(packet)

    assert result["packet_status"] == "blocked-invalid-local-write-execution-packet-items"
    assert "local-coverage" in _categories(result, "local_packet_findings")


def test_non_approved_decision_is_blocked():
    packet = _packet()
    packet["approved_write_execution_items"][0]["decision"] = "reject-write-execution"

    result = build_research_state_local_write_execution_packet(packet)

    assert result["packet_status"] == "blocked-invalid-local-write-execution-packet-items"
    assert "local-decision" in _categories(result, "local_packet_findings")


def test_invalid_decision_marker_is_blocked():
    packet = _packet()
    packet["approved_write_execution_items"][0]["decision_valid"] = False

    result = build_research_state_local_write_execution_packet(packet)

    assert result["packet_status"] == "blocked-invalid-local-write-execution-packet-items"
    assert "local-decision" in _categories(result, "local_packet_findings")


def test_approved_item_unsafe_flag_is_blocked():
    packet = _packet()
    packet["approved_write_execution_items"][0]["persistent_write_allowed"] = True

    result = build_research_state_local_write_execution_packet(packet)

    assert result["packet_status"] == "blocked-invalid-local-write-execution-packet-items"
    assert "local-unsafe-flag" in _categories(result, "local_packet_findings")


def test_packet_is_deterministic():
    first = _build()
    second = _build()

    assert first == second
    assert len(first["local_write_execution_packet_digest"]) == 64


def test_builder_does_not_mutate_input():
    packet = _packet()
    original = copy.deepcopy(packet)

    build_research_state_local_write_execution_packet(packet)

    assert packet == original


def test_build_from_file_round_trip(tmp_path):
    packet_file = tmp_path / "write-execution-decision-packet.json"
    output_file = tmp_path / "local-write-execution-packet.json"
    packet_file.write_text(json.dumps(_packet()), encoding="utf-8")

    result = build_local_write_execution_packet_from_file(packet_file, output_file)

    assert result["packet_status"] == "ready-for-final-persistence-apply-review-gate"
    assert load_json_object(output_file) == result
