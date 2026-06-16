import copy
import json

from bugintel.core.brain_chat_research_state_local_write_packet_preview import (
    EXPECTED_DECISION_KIND,
    EXPECTED_DECISION_STATUS,
    EXPECTED_PREVIEW_KIND,
    build_local_write_packet_preview_from_file,
    build_research_state_local_write_packet_preview,
    load_json_object,
)


def _approved(index=1, hypothesis_id="HYP-001"):
    return {
        "persistence_write_decision_id": f"PWRD-{index:03d}",
        "persistence_write_review_item_id": f"PWRG-{index:03d}",
        "preview_item_id": f"RSTPV-{index:03d}",
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
        "source_review_item_digest": f"r{index}" * 32,
        "source_preview_item_digest": f"p{index}" * 32,
        "source_apply_decision_digest": f"a{index}" * 32,
        "source_operation_digest": f"o{index}" * 32,
        "decision": "approve-persistence-write-packet",
        "decision_valid": True,
        "decision_reason": "Approved for local write packet preview.",
        "decision_actor": "human-reviewer",
        "human_persistence_write_decision_complete": True,
        "local_write_packet_preview_required": True,
        "local_write_packet_preview_ready": False,
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
        "persistence_write_decision_digest": f"d{index}" * 32,
    }


def _packet():
    approved = [_approved(1, "HYP-001"), _approved(2, "HYP-002")]
    return {
        "kind": EXPECTED_DECISION_KIND,
        "source": "brain-chat-research-state-persistence-write-decision-packet",
        "target_name": "demo-target",
        "decision_status": EXPECTED_DECISION_STATUS,
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
        "persistence_write_review_item_count": 2,
        "persistence_write_decision_count": 2,
        "approved_persistence_write_decision_count": 2,
        "human_persistence_write_decision_required": True,
        "human_persistence_write_decision_complete": True,
        "local_write_packet_preview_required": True,
        "local_write_packet_preview_ready": True,
        "persistent_research_state_write_ready": False,
        "persistent_research_state_write_allowed": False,
        "research_state_transition_ready": False,
        "persistence_write_decisions": approved,
        "approved_persistence_write_items": approved,
        "source_findings": [],
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
        "persistent_research_state_write_allowed": False,
        "report_submission_allowed": False,
        "vulnerability_confirmation_allowed": False,
        "planning_only": True,
        "execution_state": "not_executed",
        "persistence_write_decision_packet_digest": "wd" * 32,
    }


def _build():
    return build_research_state_local_write_packet_preview(_packet())


def _categories(preview, key):
    return {item["category"] for item in preview[key]}


def test_constants():
    assert EXPECTED_DECISION_KIND == "brain_chat_research_state_persistence_write_decision_packet"
    assert EXPECTED_DECISION_STATUS == "ready-for-local-write-packet-preview"
    assert EXPECTED_PREVIEW_KIND == "brain_chat_research_state_local_write_packet_preview"


def test_ready_decision_packet_builds_local_write_preview():
    preview = _build()

    assert preview["kind"] == EXPECTED_PREVIEW_KIND
    assert preview["preview_status"] == "ready-for-write-execution-review-gate"
    assert preview["local_write_packet_preview_ready"] is True
    assert preview["write_execution_review_gate_required"] is True
    assert preview["write_execution_review_gate_ready"] is False
    assert preview["persistent_research_state_write_ready"] is False
    assert preview["persistent_research_state_write_allowed"] is False
    assert preview["research_state_transition_ready"] is False
    assert preview["local_write_packet_preview_item_count"] == 2
    assert len(preview["preview_items"]) == 2
    assert preview["source_findings"] == []
    assert preview["safety_findings"] == []
    assert preview["preview_findings"] == []


def test_local_write_preview_is_fail_closed():
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


def test_preview_items_preserve_write_context():
    item = _build()["preview_items"][0]

    assert item["local_write_packet_preview_item_id"] == "LWPP-001"
    assert item["persistence_write_decision_id"] == "PWRD-001"
    assert item["persistence_write_review_item_id"] == "PWRG-001"
    assert item["source_preview_item_id"] == "RSTPV-001"
    assert item["operation_id"] == "RSTO-001"
    assert item["hypothesis_id"] == "HYP-001"
    assert item["field_path"] == "hypotheses.HYP-001.confidence"
    assert item["current_value"] == "medium"
    assert item["proposed_value"] == "high"
    assert item["write_preview_action"] == "preview-stored-state-field-update"
    assert item["write_preview_summary"] == "hypotheses.HYP-001.confidence: medium -> high"
    assert item["write_execution_review_required"] is True
    assert item["persistent_write_allowed"] is False
    assert len(item["local_write_packet_preview_item_digest"]) == 64


def test_invalid_decision_packet_kind_is_blocked():
    packet = _packet()
    packet["kind"] = "wrong-kind"

    preview = build_research_state_local_write_packet_preview(packet)

    assert preview["preview_status"] == "blocked-invalid-persistence-write-decision-packet"
    assert "source-schema" in _categories(preview, "source_findings")


def test_invalid_decision_packet_status_is_blocked():
    packet = _packet()
    packet["decision_status"] = "blocked-invalid-persistence-write-decisions"

    preview = build_research_state_local_write_packet_preview(packet)

    assert preview["preview_status"] == "blocked-invalid-persistence-write-decision-packet"
    assert "source-status" in _categories(preview, "source_findings")


def test_incomplete_human_decision_packet_is_blocked():
    packet = _packet()
    packet["human_persistence_write_decision_complete"] = False

    preview = build_research_state_local_write_packet_preview(packet)

    assert preview["preview_status"] == "blocked-invalid-persistence-write-decision-packet"
    assert "source-readiness" in _categories(preview, "source_findings")


def test_unsafe_decision_packet_is_blocked():
    packet = _packet()
    packet["persistent_research_state_write_allowed"] = True

    preview = build_research_state_local_write_packet_preview(packet)

    assert preview["preview_status"] == "blocked-unsafe-persistence-write-decision-packet"
    assert "unsafe-flag" in _categories(preview, "safety_findings")


def test_no_approved_items_is_blocked():
    packet = _packet()
    packet["approved_persistence_write_items"] = []
    packet["approved_persistence_write_decision_count"] = 0

    preview = build_research_state_local_write_packet_preview(packet)

    assert preview["preview_status"] == "blocked-invalid-persistence-write-decision-packet"
    assert "source-content" in _categories(preview, "source_findings")


def test_duplicate_approved_decisions_are_blocked():
    packet = _packet()
    packet["approved_persistence_write_items"][1]["persistence_write_decision_id"] = "PWRD-001"

    preview = build_research_state_local_write_packet_preview(packet)

    assert preview["preview_status"] == "blocked-invalid-local-write-packet-preview-items"
    assert "preview-coverage" in _categories(preview, "preview_findings")


def test_duplicate_field_paths_are_blocked():
    packet = _packet()
    packet["approved_persistence_write_items"][1]["field_path"] = "hypotheses.HYP-001.confidence"

    preview = build_research_state_local_write_packet_preview(packet)

    assert preview["preview_status"] == "blocked-invalid-local-write-packet-preview-items"
    assert "preview-coverage" in _categories(preview, "preview_findings")


def test_non_approved_decision_is_blocked():
    packet = _packet()
    packet["approved_persistence_write_items"][0]["decision"] = "defer-persistence-write"

    preview = build_research_state_local_write_packet_preview(packet)

    assert preview["preview_status"] == "blocked-invalid-local-write-packet-preview-items"
    assert "preview-decision" in _categories(preview, "preview_findings")


def test_invalid_decision_marker_is_blocked():
    packet = _packet()
    packet["approved_persistence_write_items"][0]["decision_valid"] = False

    preview = build_research_state_local_write_packet_preview(packet)

    assert preview["preview_status"] == "blocked-invalid-local-write-packet-preview-items"
    assert "preview-decision" in _categories(preview, "preview_findings")


def test_approved_item_unsafe_flag_is_blocked():
    packet = _packet()
    packet["approved_persistence_write_items"][0]["persistent_write_allowed"] = True

    preview = build_research_state_local_write_packet_preview(packet)

    assert preview["preview_status"] == "blocked-invalid-local-write-packet-preview-items"
    assert "preview-unsafe-flag" in _categories(preview, "preview_findings")


def test_preview_is_deterministic():
    first = _build()
    second = _build()

    assert first == second
    assert len(first["local_write_packet_preview_digest"]) == 64


def test_builder_does_not_mutate_input():
    packet = _packet()
    original = copy.deepcopy(packet)

    build_research_state_local_write_packet_preview(packet)

    assert packet == original


def test_build_from_file_round_trip(tmp_path):
    packet_file = tmp_path / "write-decision-packet.json"
    output_file = tmp_path / "local-write-preview.json"
    packet_file.write_text(json.dumps(_packet()), encoding="utf-8")

    preview = build_local_write_packet_preview_from_file(packet_file, output_file)

    assert preview["preview_status"] == "ready-for-write-execution-review-gate"
    assert load_json_object(output_file) == preview
