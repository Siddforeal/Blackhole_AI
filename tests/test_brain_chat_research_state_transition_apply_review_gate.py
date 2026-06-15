import copy
import json

from bugintel.core.brain_chat_research_state_transition_apply_review_gate import (
    EXPECTED_GATE_KIND,
    EXPECTED_TRANSITION_KIND,
    EXPECTED_TRANSITION_STATUS,
    build_apply_review_gate_from_file,
    build_research_state_transition_apply_review_gate,
    load_json_object,
)


def _operation(index=1, hypothesis_id="HYP-001"):
    return {
        "operation_id": f"RSTO-{index:03d}",
        "transition_id": f"RST-{index:03d}",
        "decision_id": f"RSTD-{index:03d}",
        "source_update_id": f"HCU-{index:03d}",
        "hypothesis_id": hypothesis_id,
        "title": "Admin boundary hypothesis",
        "operation_type": "local-proposed-hypothesis-confidence-update",
        "field_path": f"hypotheses.{hypothesis_id}.confidence",
        "current_value": "medium",
        "proposed_value": "high",
        "decision": "approve-transition-packet",
        "decision_reason": "Approved for later apply review.",
        "source_update_digest": "u" * 64,
        "source_transition_candidate_digest": f"c{index}" * 32,
        "source_approved_transition_digest": f"a{index}" * 32,
        "apply_review_required": True,
        "persistent_write_ready": False,
        "persistent_write_allowed": False,
        "research_state_transition_allowed": False,
        "confidence_update_allowed": False,
        "hypothesis_mutation_allowed": False,
        "research_state_mutation_allowed": False,
        "execution_allowed": False,
        "runtime_execution_allowed": False,
        "planning_only": True,
        "execution_state": "not_executed",
        "operation_digest": f"o{index}" * 32,
    }


def _transition_packet():
    operations = [
        _operation(1, "HYP-001"),
        _operation(2, "HYP-002"),
    ]
    return {
        "kind": EXPECTED_TRANSITION_KIND,
        "source": "brain-chat-research-state-transition-packet",
        "target_name": "demo-target",
        "packet_status": EXPECTED_TRANSITION_STATUS,
        "summary": "2 transition operations ready for apply review.",
        "source_decision_digest": "d" * 64,
        "source_gate_digest": "g" * 64,
        "source_template_digest": "t" * 64,
        "source_update_digest": "u" * 64,
        "source_hypothesis_digest": "h" * 64,
        "source_feedback_digest": "f" * 64,
        "approved_transition_count": 2,
        "transition_operation_count": 2,
        "local_transition_packet_ready": True,
        "research_state_transition_apply_review_required": True,
        "persistent_research_state_write_ready": False,
        "persistent_research_state_write_allowed": False,
        "research_state_transition_ready": False,
        "transition_operations": operations,
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
        "report_submission_allowed": False,
        "vulnerability_confirmation_allowed": False,
        "planning_only": True,
        "execution_state": "not_executed",
        "transition_packet_digest": "p" * 64,
    }


def _build():
    return build_research_state_transition_apply_review_gate(_transition_packet())


def _categories(gate, key):
    return {item["category"] for item in gate[key]}


def test_constants():
    assert EXPECTED_TRANSITION_KIND == "brain_chat_research_state_transition_packet"
    assert EXPECTED_TRANSITION_STATUS == "ready-for-research-state-transition-apply-review"
    assert EXPECTED_GATE_KIND == "brain_chat_research_state_transition_apply_review_gate"


def test_ready_transition_packet_builds_apply_review_gate():
    gate = _build()

    assert gate["kind"] == EXPECTED_GATE_KIND
    assert gate["gate_status"] == "ready-for-human-apply-review"
    assert gate["apply_review_ready"] is True
    assert gate["human_apply_decision_required"] is True
    assert gate["human_apply_decision_complete"] is False
    assert gate["research_state_transition_apply_packet_ready"] is False
    assert gate["persistent_research_state_write_ready"] is False
    assert gate["persistent_research_state_write_allowed"] is False
    assert gate["research_state_transition_ready"] is False
    assert gate["apply_review_item_count"] == 2
    assert len(gate["apply_review_items"]) == 2
    assert gate["source_findings"] == []
    assert gate["safety_findings"] == []
    assert gate["operation_findings"] == []


def test_apply_review_gate_is_fail_closed():
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


def test_review_items_preserve_operation_fields():
    item = _build()["apply_review_items"][0]

    assert item["review_item_id"] == "RSTAR-001"
    assert item["operation_id"] == "RSTO-001"
    assert item["transition_id"] == "RST-001"
    assert item["decision_id"] == "RSTD-001"
    assert item["hypothesis_id"] == "HYP-001"
    assert item["field_path"] == "hypotheses.HYP-001.confidence"
    assert item["current_value"] == "medium"
    assert item["proposed_value"] == "high"
    assert item["human_apply_decision_required"] is True
    assert "approve-apply-packet" in item["allowed_decisions"]
    assert item["persistent_write_allowed"] is False
    assert item["research_state_transition_ready"] is False
    assert len(item["review_item_digest"]) == 64


def test_invalid_transition_status_is_blocked():
    packet = _transition_packet()
    packet["packet_status"] = "blocked-invalid-transition-operations"

    gate = build_research_state_transition_apply_review_gate(packet)

    assert gate["gate_status"] == "blocked-invalid-transition-packet"
    assert gate["apply_review_ready"] is False
    assert "source-status" in _categories(gate, "source_findings")


def test_missing_apply_review_requirement_is_blocked():
    packet = _transition_packet()
    packet["research_state_transition_apply_review_required"] = False

    gate = build_research_state_transition_apply_review_gate(packet)

    assert gate["gate_status"] == "blocked-invalid-transition-packet"
    assert "source-readiness" in _categories(gate, "source_findings")


def test_persistent_write_ready_source_is_blocked():
    packet = _transition_packet()
    packet["persistent_research_state_write_ready"] = True

    gate = build_research_state_transition_apply_review_gate(packet)

    assert gate["gate_status"] == "blocked-invalid-transition-packet"
    assert "source-safety" in _categories(gate, "source_findings")


def test_unsafe_source_flag_is_blocked():
    packet = _transition_packet()
    packet["persistent_research_state_write_allowed"] = True

    gate = build_research_state_transition_apply_review_gate(packet)

    assert gate["gate_status"] == "blocked-unsafe-transition-packet"
    assert "unsafe-flag" in _categories(gate, "safety_findings")


def test_no_operations_is_blocked():
    packet = _transition_packet()
    packet["transition_operations"] = []
    packet["transition_operation_count"] = 0

    gate = build_research_state_transition_apply_review_gate(packet)

    assert gate["gate_status"] == "blocked-invalid-transition-packet"
    assert "source-content" in _categories(gate, "source_findings")


def test_duplicate_operation_ids_are_blocked():
    packet = _transition_packet()
    packet["transition_operations"][1]["operation_id"] = "RSTO-001"

    gate = build_research_state_transition_apply_review_gate(packet)

    assert gate["gate_status"] == "blocked-invalid-transition-operations"
    assert "operation-coverage" in _categories(gate, "operation_findings")


def test_duplicate_field_paths_are_blocked():
    packet = _transition_packet()
    packet["transition_operations"][1]["field_path"] = "hypotheses.HYP-001.confidence"

    gate = build_research_state_transition_apply_review_gate(packet)

    assert gate["gate_status"] == "blocked-invalid-transition-operations"
    assert "operation-coverage" in _categories(gate, "operation_findings")


def test_unsupported_operation_type_is_blocked():
    packet = _transition_packet()
    packet["transition_operations"][0]["operation_type"] = "local-persistent-write"

    gate = build_research_state_transition_apply_review_gate(packet)

    assert gate["gate_status"] == "blocked-invalid-transition-operations"
    assert "operation-type" in _categories(gate, "operation_findings")


def test_operation_unsafe_flag_is_blocked():
    packet = _transition_packet()
    packet["transition_operations"][0]["persistent_write_allowed"] = True

    gate = build_research_state_transition_apply_review_gate(packet)

    assert gate["gate_status"] == "blocked-invalid-transition-operations"
    assert "operation-unsafe-flag" in _categories(gate, "operation_findings")


def test_gate_is_deterministic():
    first = _build()
    second = _build()

    assert first == second
    assert len(first["apply_review_gate_digest"]) == 64


def test_builder_does_not_mutate_input():
    packet = _transition_packet()
    original = copy.deepcopy(packet)

    build_research_state_transition_apply_review_gate(packet)

    assert packet == original


def test_build_from_file_round_trip(tmp_path):
    packet_file = tmp_path / "transition.json"
    output_file = tmp_path / "apply-review-gate.json"
    packet_file.write_text(json.dumps(_transition_packet()), encoding="utf-8")

    gate = build_apply_review_gate_from_file(packet_file, output_file)

    assert gate["gate_status"] == "ready-for-human-apply-review"
    assert load_json_object(output_file) == gate
