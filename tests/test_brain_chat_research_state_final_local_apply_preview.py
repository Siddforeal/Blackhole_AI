import copy
import json

from bugintel.core.brain_chat_research_state_final_local_apply_preview import (
    EXPECTED_PACKET_KIND,
    EXPECTED_PACKET_STATUS,
    EXPECTED_PREVIEW_KIND,
    build_final_local_apply_preview_from_file,
    build_research_state_final_local_apply_preview,
    load_json_object,
)


def _approved(index=1, hypothesis_id="HYP-001"):
    return {
        "human_final_apply_decision_id": f"HFAD-{index:03d}",
        "final_persistence_apply_review_item_id": f"FPARG-{index:03d}",
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
        "local_write_operation": "preview-persistent-research-state-field-write",
        "local_write_summary": f"hypotheses.{hypothesis_id}.confidence: medium -> high",
        "decision": "approve-final-persistence-apply",
        "decision_valid": True,
        "decision_reason": "Approved for later final local apply preview.",
        "decision_actor": "human-reviewer",
        "human_final_apply_decision_complete": True,
        "final_local_apply_preview_required": True,
        "final_local_apply_preview_ready": False,
        "persistent_write_ready": False,
        "persistent_write_allowed": False,
        "research_state_transition_ready": False,
        "research_state_transition_allowed": False,
        "confidence_update_allowed": False,
        "hypothesis_mutation_allowed": False,
        "research_state_mutation_allowed": False,
        "execution_allowed": False,
        "runtime_execution_allowed": False,
        "source_final_persistence_apply_review_item_digest": f"z{index}" * 32,
        "source_local_write_execution_packet_item_digest": f"x{index}" * 32,
        "source_write_execution_decision_digest": f"d{index}" * 32,
        "source_write_execution_review_item_digest": f"r{index}" * 32,
        "source_local_write_packet_preview_item_digest": f"l{index}" * 32,
        "source_persistence_write_decision_digest": f"p{index}" * 32,
        "source_persistence_write_review_item_digest": f"g{index}" * 32,
        "source_apply_preview_item_digest": f"a{index}" * 32,
        "source_apply_decision_digest": f"c{index}" * 32,
        "source_operation_digest": f"o{index}" * 32,
        "planning_only": True,
        "execution_state": "not_executed",
        "human_final_apply_decision_digest": f"h{index}" * 32,
    }


def _packet():
    approved = [_approved(1, "HYP-001"), _approved(2, "HYP-002")]
    return {
        "kind": EXPECTED_PACKET_KIND,
        "source": "brain-chat-research-state-human-final-apply-decision-packet",
        "target_name": "demo-target",
        "decision_status": EXPECTED_PACKET_STATUS,
        "source_final_persistence_apply_review_gate_digest": "fg" * 32,
        "source_local_write_execution_packet_digest": "lp" * 32,
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
        "human_final_apply_decision_required": True,
        "human_final_apply_decision_complete": True,
        "final_local_apply_preview_required": True,
        "final_local_apply_preview_ready": False,
        "persistent_research_state_write_ready": False,
        "persistent_research_state_write_allowed": False,
        "research_state_transition_ready": False,
        "final_persistence_apply_review_item_count": 2,
        "human_final_apply_decision_count": 2,
        "approved_final_apply_decision_count": 2,
        "final_apply_decisions": approved,
        "approved_final_apply_items": approved,
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
        "human_final_apply_decision_packet_digest": "hp" * 32,
    }


def _build():
    return build_research_state_final_local_apply_preview(_packet())


def _categories(packet, key):
    return {item["category"] for item in packet[key]}


def test_constants():
    assert EXPECTED_PACKET_KIND == "brain_chat_research_state_human_final_apply_decision_packet"
    assert EXPECTED_PACKET_STATUS == "ready-for-final-local-apply-preview"
    assert EXPECTED_PREVIEW_KIND == "brain_chat_research_state_final_local_apply_preview"


def test_ready_decision_packet_builds_final_local_apply_preview():
    preview = _build()

    assert preview["kind"] == EXPECTED_PREVIEW_KIND
    assert preview["preview_status"] == "ready-for-final-apply-execution-review-gate"
    assert preview["final_local_apply_preview_ready"] is True
    assert preview["final_apply_execution_review_gate_required"] is True
    assert preview["final_apply_execution_review_gate_ready"] is False
    assert preview["persistent_research_state_write_ready"] is False
    assert preview["persistent_research_state_write_allowed"] is False
    assert preview["research_state_transition_ready"] is False
    assert preview["final_local_apply_preview_item_count"] == 2
    assert len(preview["final_local_apply_preview_items"]) == 2
    assert preview["source_findings"] == []
    assert preview["safety_findings"] == []
    assert preview["preview_item_findings"] == []


def test_final_local_apply_preview_is_fail_closed():
    preview = _build()

    assert preview["persistent_research_state_write_allowed"] is False
    assert preview["confidence_update_allowed"] is False
    assert preview["hypothesis_mutation_allowed"] is False
    assert preview["selection_mutation_allowed"] is False
    assert preview["investigation_plan_mutation_allowed"] is False
    assert preview["research_state_mutation_allowed"] is False
    assert preview["execution_allowed"] is False
    assert preview["runtime_execution_allowed"] is False
    assert preview["target_interaction_allowed"] is False
    assert preview["evidence_collection_allowed"] is False
    assert preview["report_submission_allowed"] is False
    assert preview["vulnerability_confirmation_allowed"] is False


def test_preview_items_preserve_decision_context():
    item = _build()["final_local_apply_preview_items"][0]

    assert item["final_local_apply_preview_item_id"] == "FLAP-001"
    assert item["human_final_apply_decision_id"] == "HFAD-001"
    assert item["final_persistence_apply_review_item_id"] == "FPARG-001"
    assert item["local_write_execution_packet_item_id"] == "LWEP-001"
    assert item["operation_id"] == "RSTO-001"
    assert item["hypothesis_id"] == "HYP-001"
    assert item["field_path"] == "hypotheses.HYP-001.confidence"
    assert item["current_value"] == "medium"
    assert item["proposed_value"] == "high"
    assert item["final_local_apply_action"] == "preview-final-persistent-research-state-field-write"
    assert item["final_local_apply_summary"] == "hypotheses.HYP-001.confidence: medium -> high"
    assert item["final_apply_execution_review_required"] is True
    assert item["persistent_write_allowed"] is False
    assert len(item["final_local_apply_preview_item_digest"]) == 64


def test_invalid_packet_kind_is_blocked():
    packet = _packet()
    packet["kind"] = "wrong-kind"

    result = build_research_state_final_local_apply_preview(packet)

    assert result["preview_status"] == "blocked-invalid-human-final-apply-decision-packet"
    assert "source-schema" in _categories(result, "source_findings")


def test_invalid_packet_status_is_blocked():
    packet = _packet()
    packet["decision_status"] = "blocked-invalid-human-final-apply-decisions"

    result = build_research_state_final_local_apply_preview(packet)

    assert result["preview_status"] == "blocked-invalid-human-final-apply-decision-packet"
    assert "source-status" in _categories(result, "source_findings")


def test_incomplete_human_decision_packet_is_blocked():
    packet = _packet()
    packet["human_final_apply_decision_complete"] = False

    result = build_research_state_final_local_apply_preview(packet)

    assert result["preview_status"] == "blocked-invalid-human-final-apply-decision-packet"
    assert "source-readiness" in _categories(result, "source_findings")


def test_unsafe_decision_packet_is_blocked():
    packet = _packet()
    packet["persistent_research_state_write_allowed"] = True

    result = build_research_state_final_local_apply_preview(packet)

    assert result["preview_status"] == "blocked-invalid-human-final-apply-decision-packet"
    assert "source-safety" in _categories(result, "source_findings")


def test_no_approved_items_is_blocked():
    packet = _packet()
    packet["approved_final_apply_items"] = []
    packet["approved_final_apply_decision_count"] = 0

    result = build_research_state_final_local_apply_preview(packet)

    assert result["preview_status"] == "blocked-invalid-human-final-apply-decision-packet"
    assert "source-content" in _categories(result, "source_findings")


def test_duplicate_approved_decisions_are_blocked():
    packet = _packet()
    packet["approved_final_apply_items"][1]["human_final_apply_decision_id"] = "HFAD-001"

    result = build_research_state_final_local_apply_preview(packet)

    assert result["preview_status"] == "blocked-invalid-final-local-apply-preview-items"
    assert "preview-coverage" in _categories(result, "preview_item_findings")


def test_duplicate_field_paths_are_blocked():
    packet = _packet()
    packet["approved_final_apply_items"][1]["field_path"] = "hypotheses.HYP-001.confidence"

    result = build_research_state_final_local_apply_preview(packet)

    assert result["preview_status"] == "blocked-invalid-final-local-apply-preview-items"
    assert "preview-coverage" in _categories(result, "preview_item_findings")


def test_non_approved_decision_is_blocked():
    packet = _packet()
    packet["approved_final_apply_items"][0]["decision"] = "reject-final-persistence-apply"

    result = build_research_state_final_local_apply_preview(packet)

    assert result["preview_status"] == "blocked-invalid-final-local-apply-preview-items"
    assert "preview-decision" in _categories(result, "preview_item_findings")


def test_invalid_decision_marker_is_blocked():
    packet = _packet()
    packet["approved_final_apply_items"][0]["decision_valid"] = False

    result = build_research_state_final_local_apply_preview(packet)

    assert result["preview_status"] == "blocked-invalid-final-local-apply-preview-items"
    assert "preview-decision" in _categories(result, "preview_item_findings")


def test_approved_item_unsafe_flag_is_blocked():
    packet = _packet()
    packet["approved_final_apply_items"][0]["persistent_write_allowed"] = True

    result = build_research_state_final_local_apply_preview(packet)

    assert result["preview_status"] == "blocked-invalid-final-local-apply-preview-items"
    assert "preview-unsafe-flag" in _categories(result, "preview_item_findings")


def test_packet_is_deterministic():
    first = _build()
    second = _build()

    assert first == second
    assert len(first["final_local_apply_preview_digest"]) == 64


def test_builder_does_not_mutate_input():
    packet = _packet()
    original = copy.deepcopy(packet)

    build_research_state_final_local_apply_preview(packet)

    assert packet == original


def test_build_from_file_round_trip(tmp_path):
    packet_file = tmp_path / "human-final-apply-decision-packet.json"
    output_file = tmp_path / "final-local-apply-preview.json"
    packet_file.write_text(json.dumps(_packet()), encoding="utf-8")

    result = build_final_local_apply_preview_from_file(packet_file, output_file)

    assert result["preview_status"] == "ready-for-final-apply-execution-review-gate"
    assert load_json_object(output_file) == result
