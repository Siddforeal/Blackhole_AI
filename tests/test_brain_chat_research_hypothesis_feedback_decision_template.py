import copy
import json

from bugintel.core.brain_chat_research_hypothesis_feedback_decision_template import (
    EXPECTED_FEEDBACK_KIND,
    EXPECTED_FEEDBACK_STATUS,
    EXPECTED_TEMPLATE_KIND,
    build_research_hypothesis_feedback_decision_template,
    load_json_object,
    write_json,
)


def _proposal(
    feedback_id="HFB-001",
    hypothesis_id="HYP-001",
    current="medium",
    proposed="high",
    delta=3,
):
    return {
        "feedback_id": feedback_id,
        "hypothesis_id": hypothesis_id,
        "title": "Admin boundary hypothesis",
        "current_confidence": current,
        "proposed_confidence": proposed,
        "proposed_disposition": "propose-confidence-promotion",
        "categorical_confidence_change": current != proposed,
        "net_confidence_delta": delta,
        "evidence_direction": "strengthens",
        "observation_ids": ["OBS-001"],
        "proposal_digest": "a" * 64,
        "confidence_mutation_allowed": False,
        "state_mutation_allowed": False,
        "human_review_required": True,
        "required_review": "human-hypothesis-feedback-review",
        "planning_only": True,
        "execution_allowed": False,
        "runtime_execution_allowed": False,
    }


def _feedback_packet():
    return {
        "kind": EXPECTED_FEEDBACK_KIND,
        "target_name": "demo-target",
        "packet_status": EXPECTED_FEEDBACK_STATUS,
        "packet_ready": True,
        "hypothesis_feedback_review_ready": True,
        "feedback_digest": "b" * 64,
        "feedback_proposal_count": 2,
        "feedback_proposals": [
            _proposal("HFB-001", "HYP-001", "medium", "high", 3),
            _proposal("HFB-002", "HYP-002", "high", "high", 1),
        ],
        "confidence_update_ready": False,
        "research_state_transition_ready": False,
        "planning_only": True,
        "execution_allowed": False,
    }


def test_constants():
    assert EXPECTED_FEEDBACK_KIND == "brain_chat_research_hypothesis_feedback_packet"
    assert EXPECTED_FEEDBACK_STATUS == "ready-for-hypothesis-feedback-review"
    assert EXPECTED_TEMPLATE_KIND == "brain_chat_research_hypothesis_feedback_decision_input"


def test_template_covers_every_feedback_proposal():
    packet = _feedback_packet()
    template = build_research_hypothesis_feedback_decision_template(packet)

    assert template["kind"] == EXPECTED_TEMPLATE_KIND
    assert template["target_name"] == "demo-target"
    assert template["source_feedback_kind"] == EXPECTED_FEEDBACK_KIND
    assert template["source_feedback_status"] == EXPECTED_FEEDBACK_STATUS
    assert template["source_feedback_ready"] is True
    assert template["source_feedback_digest"] == "b" * 64
    assert template["source_feedback_proposal_count"] == 2
    assert template["decision_count"] == 2
    assert [item["feedback_id"] for item in template["decisions"]] == ["HFB-001", "HFB-002"]


def test_decisions_default_to_deferred():
    template = build_research_hypothesis_feedback_decision_template(_feedback_packet())

    assert template["reviewer"] == ""
    assert template["overall_reason"] == ""
    assert template["allowed_decisions"] == [
        "accepted",
        "rejected",
        "changes-requested",
        "deferred",
    ]
    assert all(item["decision"] == "deferred" for item in template["decisions"])
    assert all(item["accepted_proposed_confidence"] is False for item in template["decisions"])
    assert all(item["reason"] == "Pending explicit human decision." for item in template["decisions"])


def test_decision_items_preserve_proposal_context():
    template = build_research_hypothesis_feedback_decision_template(_feedback_packet())
    first = template["decisions"][0]

    assert first["hypothesis_id"] == "HYP-001"
    assert first["title"] == "Admin boundary hypothesis"
    assert first["current_confidence"] == "medium"
    assert first["proposed_confidence"] == "high"
    assert first["categorical_confidence_change"] is True
    assert first["net_confidence_delta"] == 3
    assert first["evidence_direction"] == "strengthens"
    assert first["observation_ids"] == ["OBS-001"]
    assert first["proposal_digest"] == "a" * 64


def test_template_is_fail_closed():
    template = build_research_hypothesis_feedback_decision_template(_feedback_packet())

    assert template["planning_only"] is True
    assert template["execution_state"] == "not_executed"
    assert template["confidence_update_ready"] is False
    assert template["selection_update_ready"] is False
    assert template["investigation_plan_update_ready"] is False
    assert template["research_state_transition_ready"] is False
    assert template["command_generation_allowed"] is False
    assert template["payload_generation_allowed"] is False
    assert template["package_installation_allowed"] is False
    assert template["execution_allowed"] is False
    assert template["runtime_execution_allowed"] is False
    assert template["network_interaction_allowed"] is False
    assert template["target_interaction_allowed"] is False
    assert template["evidence_collection_allowed"] is False
    assert template["validation_allowed"] is False
    assert template["hypothesis_mutation_allowed"] is False
    assert template["selection_mutation_allowed"] is False
    assert template["investigation_plan_mutation_allowed"] is False
    assert template["research_state_mutation_allowed"] is False
    assert template["report_submission_allowed"] is False
    assert template["vulnerability_confirmation_allowed"] is False


def test_builder_does_not_mutate_input():
    packet = _feedback_packet()
    before = copy.deepcopy(packet)

    build_research_hypothesis_feedback_decision_template(packet)

    assert packet == before


def test_non_object_and_missing_id_proposals_are_ignored():
    packet = _feedback_packet()
    packet["feedback_proposals"].append("bad")
    packet["feedback_proposals"].append({"hypothesis_id": "HYP-999"})

    template = build_research_hypothesis_feedback_decision_template(packet)

    assert template["source_feedback_proposal_count"] == 3
    assert template["decision_count"] == 2
    assert [item["feedback_id"] for item in template["decisions"]] == ["HFB-001", "HFB-002"]


def test_write_and_load_json_round_trip(tmp_path):
    template = build_research_hypothesis_feedback_decision_template(_feedback_packet())
    output = tmp_path / "nested" / "template.json"

    write_json(output, template)

    loaded = load_json_object(output)
    assert loaded == template
    assert json.loads(output.read_text(encoding="utf-8")) == template


def test_load_json_object_rejects_non_object(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("[]", encoding="utf-8")

    try:
        load_json_object(path)
    except ValueError as exc:
        assert "Expected JSON object" in str(exc)
    else:
        raise AssertionError("non-object JSON was accepted")
