import copy
import json

from bugintel.core.brain_chat_research_state_persistence_write_decision_packet import (
    EXPECTED_DECISION_KIND,
    EXPECTED_GATE_KIND,
    EXPECTED_GATE_STATUS,
    build_persistence_write_decision_packet_from_files,
    build_research_state_persistence_write_decision_packet,
    load_json_object,
)


def _review_item(index=1, hypothesis_id="HYP-001"):
    return {
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
        "source_preview_item_digest": f"p{index}" * 32,
        "source_apply_decision_digest": f"a{index}" * 32,
        "source_operation_digest": f"o{index}" * 32,
        "review_question": "Should this proposed stored-state field update be approved?",
        "allowed_decisions": [
            "approve-persistence-write-packet",
            "reject-persistence-write",
            "request-changes",
            "defer-persistence-write",
        ],
        "human_persistence_write_decision_required": True,
        "human_persistence_write_decision_complete": False,
        "persistence_write_decision_packet_ready": False,
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
        "persistence_write_review_item_digest": f"r{index}" * 32,
    }


def _gate():
    items = [_review_item(1, "HYP-001"), _review_item(2, "HYP-002")]
    return {
        "kind": EXPECTED_GATE_KIND,
        "source": "brain-chat-research-state-persistence-write-review-gate",
        "target_name": "demo-target",
        "gate_status": EXPECTED_GATE_STATUS,
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
        "apply_preview_item_count": 2,
        "persistence_write_review_item_count": 2,
        "persistence_write_review_ready": True,
        "human_persistence_write_decision_required": True,
        "human_persistence_write_decision_complete": False,
        "persistence_write_decision_packet_ready": False,
        "persistent_research_state_write_ready": False,
        "persistent_research_state_write_allowed": False,
        "research_state_transition_ready": False,
        "review_items": items,
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
        "persistence_write_review_gate_digest": "w" * 64,
    }


def _human():
    return {
        "source": "human-persistence-write-decisions",
        "planning_only": True,
        "persistence_write_decisions": [
            {
                "persistence_write_review_item_id": "PWRG-001",
                "decision": "approve-persistence-write-packet",
                "decision_reason": "Approved for local write packet preview.",
                "decision_actor": "human-reviewer",
                "human_persistence_write_decision_complete": True,
                "persistent_write_allowed": False,
                "persistent_research_state_write_allowed": False,
                "execution_allowed": False,
                "runtime_execution_allowed": False,
                "planning_only": True,
            },
            {
                "persistence_write_review_item_id": "PWRG-002",
                "decision": "defer-persistence-write",
                "decision_reason": "Needs more review before preview.",
                "decision_actor": "human-reviewer",
                "human_persistence_write_decision_complete": True,
                "persistent_write_allowed": False,
                "persistent_research_state_write_allowed": False,
                "execution_allowed": False,
                "runtime_execution_allowed": False,
                "planning_only": True,
            },
        ],
    }


def _build():
    return build_research_state_persistence_write_decision_packet(_gate(), _human())


def _categories(packet, key):
    return {item["category"] for item in packet[key]}


def test_constants():
    assert EXPECTED_GATE_KIND == "brain_chat_research_state_persistence_write_review_gate"
    assert EXPECTED_GATE_STATUS == "ready-for-human-persistence-write-review"
    assert EXPECTED_DECISION_KIND == "brain_chat_research_state_persistence_write_decision_packet"


def test_ready_gate_and_human_decisions_build_decision_packet():
    packet = _build()

    assert packet["kind"] == EXPECTED_DECISION_KIND
    assert packet["decision_status"] == "ready-for-local-write-packet-preview"
    assert packet["human_persistence_write_decision_required"] is True
    assert packet["human_persistence_write_decision_complete"] is True
    assert packet["local_write_packet_preview_required"] is True
    assert packet["local_write_packet_preview_ready"] is True
    assert packet["persistent_research_state_write_ready"] is False
    assert packet["persistent_research_state_write_allowed"] is False
    assert packet["research_state_transition_ready"] is False
    assert packet["persistence_write_decision_count"] == 2
    assert packet["approved_persistence_write_decision_count"] == 1
    assert len(packet["approved_persistence_write_items"]) == 1
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
    item = _build()["approved_persistence_write_items"][0]

    assert item["persistence_write_decision_id"] == "PWRD-001"
    assert item["persistence_write_review_item_id"] == "PWRG-001"
    assert item["preview_item_id"] == "RSTPV-001"
    assert item["operation_id"] == "RSTO-001"
    assert item["hypothesis_id"] == "HYP-001"
    assert item["field_path"] == "hypotheses.HYP-001.confidence"
    assert item["current_value"] == "medium"
    assert item["proposed_value"] == "high"
    assert item["decision"] == "approve-persistence-write-packet"
    assert item["decision_valid"] is True
    assert item["local_write_packet_preview_required"] is True
    assert item["local_write_packet_preview_ready"] is False
    assert item["persistent_write_allowed"] is False
    assert len(item["persistence_write_decision_digest"]) == 64


def test_invalid_gate_kind_is_blocked():
    gate = _gate()
    gate["kind"] = "wrong-kind"

    packet = build_research_state_persistence_write_decision_packet(gate, _human())

    assert packet["decision_status"] == "blocked-invalid-persistence-write-review-gate"
    assert "source-schema" in _categories(packet, "source_findings")


def test_invalid_gate_status_is_blocked():
    gate = _gate()
    gate["gate_status"] = "blocked-invalid-persistence-write-review-items"

    packet = build_research_state_persistence_write_decision_packet(gate, _human())

    assert packet["decision_status"] == "blocked-invalid-persistence-write-review-gate"
    assert "source-status" in _categories(packet, "source_findings")


def test_unsafe_gate_is_blocked():
    gate = _gate()
    gate["persistent_research_state_write_allowed"] = True

    packet = build_research_state_persistence_write_decision_packet(gate, _human())

    assert packet["decision_status"] == "blocked-unsafe-persistence-write-review-gate"
    assert "unsafe-flag" in _categories(packet, "safety_findings")


def test_missing_human_decision_is_blocked():
    human = _human()
    human["persistence_write_decisions"] = human["persistence_write_decisions"][:1]

    packet = build_research_state_persistence_write_decision_packet(_gate(), human)

    assert packet["decision_status"] == "blocked-invalid-persistence-write-decisions"
    assert "decision-coverage" in _categories(packet, "decision_findings")


def test_unknown_human_decision_reference_is_blocked():
    human = _human()
    human["persistence_write_decisions"][1]["persistence_write_review_item_id"] = "PWRG-999"

    packet = build_research_state_persistence_write_decision_packet(_gate(), human)

    assert packet["decision_status"] == "blocked-invalid-persistence-write-decisions"
    assert "decision-coverage" in _categories(packet, "decision_findings")


def test_invalid_decision_value_is_blocked():
    human = _human()
    human["persistence_write_decisions"][0]["decision"] = "write-now"

    packet = build_research_state_persistence_write_decision_packet(_gate(), human)

    assert packet["decision_status"] == "blocked-invalid-persistence-write-decisions"
    assert "decision-value" in _categories(packet, "decision_findings")


def test_missing_decision_reason_is_blocked():
    human = _human()
    human["persistence_write_decisions"][0]["decision_reason"] = ""

    packet = build_research_state_persistence_write_decision_packet(_gate(), human)

    assert packet["decision_status"] == "blocked-invalid-persistence-write-decisions"
    assert "decision-reason" in _categories(packet, "decision_findings")


def test_incomplete_human_decision_is_blocked():
    human = _human()
    human["persistence_write_decisions"][0]["human_persistence_write_decision_complete"] = False

    packet = build_research_state_persistence_write_decision_packet(_gate(), human)

    assert packet["decision_status"] == "blocked-invalid-persistence-write-decisions"
    assert "decision-complete" in _categories(packet, "decision_findings")


def test_decision_enabling_write_is_blocked():
    human = _human()
    human["persistence_write_decisions"][0]["persistent_write_allowed"] = True

    packet = build_research_state_persistence_write_decision_packet(_gate(), human)

    assert packet["decision_status"] == "blocked-invalid-persistence-write-decisions"
    assert "decision-unsafe-flag" in _categories(packet, "decision_findings")


def test_no_approved_decisions_is_blocked():
    human = _human()
    human["persistence_write_decisions"][0]["decision"] = "reject-persistence-write"

    packet = build_research_state_persistence_write_decision_packet(_gate(), human)

    assert packet["decision_status"] == "blocked-no-approved-persistence-write-decisions"
    assert packet["approved_persistence_write_decision_count"] == 0
    assert packet["local_write_packet_preview_ready"] is False


def test_packet_is_deterministic():
    first = _build()
    second = _build()

    assert first == second
    assert len(first["persistence_write_decision_packet_digest"]) == 64


def test_builder_does_not_mutate_inputs():
    gate = _gate()
    human = _human()
    original_gate = copy.deepcopy(gate)
    original_human = copy.deepcopy(human)

    build_research_state_persistence_write_decision_packet(gate, human)

    assert gate == original_gate
    assert human == original_human


def test_build_from_files_round_trip(tmp_path):
    gate_file = tmp_path / "write-review-gate.json"
    human_file = tmp_path / "human-decisions.json"
    output_file = tmp_path / "write-decision-packet.json"
    gate_file.write_text(json.dumps(_gate()), encoding="utf-8")
    human_file.write_text(json.dumps(_human()), encoding="utf-8")

    packet = build_persistence_write_decision_packet_from_files(gate_file, human_file, output_file)

    assert packet["decision_status"] == "ready-for-local-write-packet-preview"
    assert load_json_object(output_file) == packet
