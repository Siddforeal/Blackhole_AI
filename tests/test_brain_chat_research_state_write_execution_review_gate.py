import copy
import json

from bugintel.core.brain_chat_research_state_write_execution_review_gate import (
    EXPECTED_GATE_KIND,
    EXPECTED_PREVIEW_KIND,
    EXPECTED_PREVIEW_STATUS,
    build_research_state_write_execution_review_gate,
    build_write_execution_review_gate_from_file,
    load_json_object,
)


def _preview_item(index=1, hypothesis_id="HYP-001"):
    return {
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
        "source_persistence_write_decision_digest": f"d{index}" * 32,
        "source_persistence_write_review_item_digest": f"r{index}" * 32,
        "source_apply_preview_item_digest": f"p{index}" * 32,
        "source_apply_decision_digest": f"a{index}" * 32,
        "source_operation_digest": f"o{index}" * 32,
        "write_execution_review_required": True,
        "write_execution_review_ready": False,
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
        "local_write_packet_preview_item_digest": f"l{index}" * 32,
    }


def _preview():
    items = [_preview_item(1, "HYP-001"), _preview_item(2, "HYP-002")]
    return {
        "kind": EXPECTED_PREVIEW_KIND,
        "source": "brain-chat-research-state-local-write-packet-preview",
        "target_name": "demo-target",
        "preview_status": EXPECTED_PREVIEW_STATUS,
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
        "approved_persistence_write_decision_count": 2,
        "local_write_packet_preview_item_count": 2,
        "local_write_packet_preview_ready": True,
        "write_execution_review_gate_required": True,
        "write_execution_review_gate_ready": False,
        "persistent_research_state_write_ready": False,
        "persistent_research_state_write_allowed": False,
        "research_state_transition_ready": False,
        "preview_items": items,
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
        "local_write_packet_preview_digest": "lw" * 32,
    }


def _build():
    return build_research_state_write_execution_review_gate(_preview())


def _categories(gate, key):
    return {item["category"] for item in gate[key]}


def test_constants():
    assert EXPECTED_PREVIEW_KIND == "brain_chat_research_state_local_write_packet_preview"
    assert EXPECTED_PREVIEW_STATUS == "ready-for-write-execution-review-gate"
    assert EXPECTED_GATE_KIND == "brain_chat_research_state_write_execution_review_gate"


def test_ready_preview_builds_write_execution_review_gate():
    gate = _build()

    assert gate["kind"] == EXPECTED_GATE_KIND
    assert gate["gate_status"] == "ready-for-human-write-execution-review"
    assert gate["write_execution_review_ready"] is True
    assert gate["human_write_execution_review_required"] is True
    assert gate["human_write_execution_review_complete"] is False
    assert gate["write_execution_decision_packet_ready"] is False
    assert gate["persistent_research_state_write_ready"] is False
    assert gate["persistent_research_state_write_allowed"] is False
    assert gate["research_state_transition_ready"] is False
    assert gate["write_execution_review_item_count"] == 2
    assert len(gate["review_items"]) == 2
    assert gate["source_findings"] == []
    assert gate["safety_findings"] == []
    assert gate["review_findings"] == []


def test_write_execution_review_gate_is_fail_closed():
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


def test_review_items_preserve_preview_context():
    item = _build()["review_items"][0]

    assert item["write_execution_review_item_id"] == "WERG-001"
    assert item["local_write_packet_preview_item_id"] == "LWPP-001"
    assert item["persistence_write_decision_id"] == "PWRD-001"
    assert item["persistence_write_review_item_id"] == "PWRG-001"
    assert item["operation_id"] == "RSTO-001"
    assert item["hypothesis_id"] == "HYP-001"
    assert item["field_path"] == "hypotheses.HYP-001.confidence"
    assert item["current_value"] == "medium"
    assert item["proposed_value"] == "high"
    assert item["human_write_execution_review_required"] is True
    assert item["persistent_write_allowed"] is False
    assert "approve-write-execution-packet" in item["allowed_decisions"]
    assert len(item["write_execution_review_item_digest"]) == 64


def test_invalid_preview_kind_is_blocked():
    preview = _preview()
    preview["kind"] = "wrong-kind"

    gate = build_research_state_write_execution_review_gate(preview)

    assert gate["gate_status"] == "blocked-invalid-local-write-packet-preview"
    assert "source-schema" in _categories(gate, "source_findings")


def test_invalid_preview_status_is_blocked():
    preview = _preview()
    preview["preview_status"] = "blocked-invalid-local-write-packet-preview-items"

    gate = build_research_state_write_execution_review_gate(preview)

    assert gate["gate_status"] == "blocked-invalid-local-write-packet-preview"
    assert "source-status" in _categories(gate, "source_findings")


def test_not_ready_preview_is_blocked():
    preview = _preview()
    preview["local_write_packet_preview_ready"] = False

    gate = build_research_state_write_execution_review_gate(preview)

    assert gate["gate_status"] == "blocked-invalid-local-write-packet-preview"
    assert "source-readiness" in _categories(gate, "source_findings")


def test_unsafe_preview_is_blocked():
    preview = _preview()
    preview["persistent_research_state_write_allowed"] = True

    gate = build_research_state_write_execution_review_gate(preview)

    assert gate["gate_status"] == "blocked-unsafe-local-write-packet-preview"
    assert "unsafe-flag" in _categories(gate, "safety_findings")


def test_no_preview_items_is_blocked():
    preview = _preview()
    preview["preview_items"] = []
    preview["local_write_packet_preview_item_count"] = 0

    gate = build_research_state_write_execution_review_gate(preview)

    assert gate["gate_status"] == "blocked-no-local-write-packet-preview-items"
    assert "source-content" in _categories(gate, "source_findings")


def test_duplicate_preview_items_are_blocked():
    preview = _preview()
    preview["preview_items"][1]["local_write_packet_preview_item_id"] = "LWPP-001"

    gate = build_research_state_write_execution_review_gate(preview)

    assert gate["gate_status"] == "blocked-invalid-write-execution-review-items"
    assert "review-coverage" in _categories(gate, "review_findings")


def test_duplicate_field_paths_are_blocked():
    preview = _preview()
    preview["preview_items"][1]["field_path"] = "hypotheses.HYP-001.confidence"

    gate = build_research_state_write_execution_review_gate(preview)

    assert gate["gate_status"] == "blocked-invalid-write-execution-review-items"
    assert "review-coverage" in _categories(gate, "review_findings")


def test_missing_required_preview_field_is_blocked():
    preview = _preview()
    preview["preview_items"][0]["operation_id"] = ""

    gate = build_research_state_write_execution_review_gate(preview)

    assert gate["gate_status"] == "blocked-invalid-write-execution-review-items"
    assert "review-schema" in _categories(gate, "review_findings")


def test_preview_item_unsafe_flag_is_blocked():
    preview = _preview()
    preview["preview_items"][0]["persistent_write_allowed"] = True

    gate = build_research_state_write_execution_review_gate(preview)

    assert gate["gate_status"] == "blocked-invalid-write-execution-review-items"
    assert "review-unsafe-flag" in _categories(gate, "review_findings")


def test_preview_item_not_planning_only_is_blocked():
    preview = _preview()
    preview["preview_items"][0]["planning_only"] = False

    gate = build_research_state_write_execution_review_gate(preview)

    assert gate["gate_status"] == "blocked-invalid-write-execution-review-items"
    assert "review-planning-only" in _categories(gate, "review_findings")


def test_gate_is_deterministic():
    first = _build()
    second = _build()

    assert first == second
    assert len(first["write_execution_review_gate_digest"]) == 64


def test_builder_does_not_mutate_input():
    preview = _preview()
    original = copy.deepcopy(preview)

    build_research_state_write_execution_review_gate(preview)

    assert preview == original


def test_build_from_file_round_trip(tmp_path):
    preview_file = tmp_path / "local-write-preview.json"
    output_file = tmp_path / "write-execution-review-gate.json"
    preview_file.write_text(json.dumps(_preview()), encoding="utf-8")

    gate = build_write_execution_review_gate_from_file(preview_file, output_file)

    assert gate["gate_status"] == "ready-for-human-write-execution-review"
    assert load_json_object(output_file) == gate
