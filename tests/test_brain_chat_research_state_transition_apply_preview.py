import copy
import json

from bugintel.core.brain_chat_research_state_transition_apply_preview import (
    EXPECTED_DECISION_KIND,
    EXPECTED_DECISION_STATUS,
    EXPECTED_PREVIEW_KIND,
    build_apply_preview_from_file,
    build_research_state_transition_apply_preview,
    load_json_object,
)


def _approved(index=1, hypothesis_id="HYP-001"):
    return {
        "apply_decision_id": f"RSTAD-{index:03d}",
        "review_item_id": f"RSTAR-{index:03d}",
        "operation_id": f"RSTO-{index:03d}",
        "transition_id": f"RST-{index:03d}",
        "decision_id": f"RSTD-{index:03d}",
        "hypothesis_id": hypothesis_id,
        "field_path": f"hypotheses.{hypothesis_id}.confidence",
        "operation_type": "local-proposed-hypothesis-confidence-update",
        "current_value": "medium",
        "proposed_value": "high",
        "decision": "approve-apply-packet",
        "decision_reason": "Approved for local apply preview.",
        "source_review_item_digest": f"r{index}" * 32,
        "source_operation_digest": f"o{index}" * 32,
        "human_apply_decision_complete": True,
        "apply_preview_required": True,
        "apply_preview_ready": False,
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
        "apply_decision_digest": f"a{index}" * 32,
    }


def _packet():
    approved = [_approved(1, "HYP-001"), _approved(2, "HYP-002")]
    return {
        "kind": EXPECTED_DECISION_KIND,
        "source": "brain-chat-research-state-transition-apply-decision-packet",
        "target_name": "demo-target",
        "decision_status": EXPECTED_DECISION_STATUS,
        "summary": "2 apply decisions ready for preview.",
        "source_apply_review_gate_digest": "ar" * 32,
        "source_transition_packet_digest": "tp" * 32,
        "source_decision_digest": "d" * 64,
        "source_gate_digest": "g" * 64,
        "source_template_digest": "t" * 64,
        "source_update_digest": "u" * 64,
        "source_hypothesis_digest": "h" * 64,
        "source_feedback_digest": "f" * 64,
        "apply_review_item_count": 2,
        "apply_decision_count": 2,
        "approved_apply_decision_count": 2,
        "human_apply_decision_complete": True,
        "human_apply_decision_required": False,
        "research_state_transition_apply_preview_required": True,
        "research_state_transition_apply_preview_ready": True,
        "persistent_research_state_write_ready": False,
        "persistent_research_state_write_allowed": False,
        "research_state_transition_ready": False,
        "apply_decisions": approved,
        "approved_apply_items": approved,
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
        "apply_decision_packet_digest": "p" * 64,
    }


def _build():
    return build_research_state_transition_apply_preview(_packet())


def _categories(preview, key):
    return {item["category"] for item in preview[key]}


def test_constants():
    assert EXPECTED_DECISION_KIND == "brain_chat_research_state_transition_apply_decision_packet"
    assert EXPECTED_DECISION_STATUS == "ready-for-research-state-transition-apply-preview"
    assert EXPECTED_PREVIEW_KIND == "brain_chat_research_state_transition_apply_preview"


def test_ready_apply_decision_packet_builds_preview():
    preview = _build()

    assert preview["kind"] == EXPECTED_PREVIEW_KIND
    assert preview["preview_status"] == "ready-for-persistence-write-review-gate"
    assert preview["apply_preview_ready"] is True
    assert preview["persistence_write_review_gate_required"] is True
    assert preview["persistence_write_review_gate_ready"] is False
    assert preview["persistent_research_state_write_ready"] is False
    assert preview["persistent_research_state_write_allowed"] is False
    assert preview["research_state_transition_ready"] is False
    assert preview["preview_item_count"] == 2
    assert len(preview["preview_items"]) == 2
    assert preview["source_findings"] == []
    assert preview["safety_findings"] == []
    assert preview["preview_findings"] == []


def test_apply_preview_is_fail_closed():
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


def test_preview_items_show_before_after_fields():
    item = _build()["preview_items"][0]

    assert item["preview_item_id"] == "RSTPV-001"
    assert item["apply_decision_id"] == "RSTAD-001"
    assert item["review_item_id"] == "RSTAR-001"
    assert item["operation_id"] == "RSTO-001"
    assert item["hypothesis_id"] == "HYP-001"
    assert item["field_path"] == "hypotheses.HYP-001.confidence"
    assert item["current_value"] == "medium"
    assert item["proposed_value"] == "high"
    assert item["change_summary"] == "hypotheses.HYP-001.confidence: medium -> high"
    assert item["persistence_write_review_required"] is True
    assert item["persistent_write_allowed"] is False
    assert len(item["preview_item_digest"]) == 64


def test_invalid_decision_status_is_blocked():
    packet = _packet()
    packet["decision_status"] = "blocked-invalid-apply-decisions"

    preview = build_research_state_transition_apply_preview(packet)

    assert preview["preview_status"] == "blocked-invalid-apply-decision-packet"
    assert preview["apply_preview_ready"] is False
    assert "source-status" in _categories(preview, "source_findings")


def test_incomplete_human_decision_is_blocked():
    packet = _packet()
    packet["human_apply_decision_complete"] = False

    preview = build_research_state_transition_apply_preview(packet)

    assert preview["preview_status"] == "blocked-invalid-apply-decision-packet"
    assert "source-readiness" in _categories(preview, "source_findings")


def test_unsafe_packet_is_blocked():
    packet = _packet()
    packet["persistent_research_state_write_allowed"] = True

    preview = build_research_state_transition_apply_preview(packet)

    assert preview["preview_status"] == "blocked-unsafe-apply-decision-packet"
    assert "unsafe-flag" in _categories(preview, "safety_findings")


def test_no_approved_apply_items_is_blocked():
    packet = _packet()
    packet["approved_apply_items"] = []
    packet["approved_apply_decision_count"] = 0

    preview = build_research_state_transition_apply_preview(packet)

    assert preview["preview_status"] == "blocked-invalid-apply-decision-packet"
    assert "source-content" in _categories(preview, "source_findings")


def test_duplicate_approved_decisions_are_blocked():
    packet = _packet()
    packet["approved_apply_items"][1]["apply_decision_id"] = "RSTAD-001"

    preview = build_research_state_transition_apply_preview(packet)

    assert preview["preview_status"] == "blocked-invalid-apply-preview-items"
    assert "preview-coverage" in _categories(preview, "preview_findings")


def test_duplicate_field_paths_are_blocked():
    packet = _packet()
    packet["approved_apply_items"][1]["field_path"] = "hypotheses.HYP-001.confidence"

    preview = build_research_state_transition_apply_preview(packet)

    assert preview["preview_status"] == "blocked-invalid-apply-preview-items"
    assert "preview-coverage" in _categories(preview, "preview_findings")


def test_non_approved_item_is_blocked():
    packet = _packet()
    packet["approved_apply_items"][0]["decision"] = "defer-apply"

    preview = build_research_state_transition_apply_preview(packet)

    assert preview["preview_status"] == "blocked-invalid-apply-preview-items"
    assert "preview-decision" in _categories(preview, "preview_findings")


def test_preview_unsafe_flag_is_blocked():
    packet = _packet()
    packet["approved_apply_items"][0]["persistent_write_allowed"] = True

    preview = build_research_state_transition_apply_preview(packet)

    assert preview["preview_status"] == "blocked-invalid-apply-preview-items"
    assert "preview-unsafe-flag" in _categories(preview, "preview_findings")


def test_preview_is_deterministic():
    first = _build()
    second = _build()

    assert first == second
    assert len(first["apply_preview_digest"]) == 64


def test_builder_does_not_mutate_input():
    packet = _packet()
    original = copy.deepcopy(packet)

    build_research_state_transition_apply_preview(packet)

    assert packet == original


def test_build_from_file_round_trip(tmp_path):
    packet_file = tmp_path / "apply-decision-packet.json"
    output_file = tmp_path / "apply-preview.json"
    packet_file.write_text(json.dumps(_packet()), encoding="utf-8")

    preview = build_apply_preview_from_file(packet_file, output_file)

    assert preview["preview_status"] == "ready-for-persistence-write-review-gate"
    assert load_json_object(output_file) == preview
