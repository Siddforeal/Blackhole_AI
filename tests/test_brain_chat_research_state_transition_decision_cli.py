import json

from typer.testing import CliRunner

from bugintel.cli import app
from bugintel.core.brain_chat_research_state_transition_decision_template import (
    build_research_state_transition_decision_template,
)


runner = CliRunner()


def _candidate(index=1, hypothesis_id="HYP-001"):
    return {
        "transition_id": f"RST-{index:03d}",
        "source_update_id": f"HCU-{index:03d}",
        "source_feedback_id": f"HFB-{index:03d}",
        "hypothesis_id": hypothesis_id,
        "title": "Admin boundary hypothesis",
        "proposed_state_change": "update-hypothesis-confidence",
        "current_confidence": "medium",
        "proposed_confidence": "high",
        "categorical_confidence_change": True,
        "net_confidence_delta": 3,
        "observation_ids": ["OBS-001"],
        "source_update_digest": "u" * 64,
        "review_decision": "pending-human-transition-decision",
        "human_review_required": True,
        "transition_packet_required_after_approval": True,
        "research_state_transition_allowed": False,
        "confidence_update_allowed": False,
        "hypothesis_mutation_allowed": False,
        "selection_mutation_allowed": False,
        "investigation_plan_mutation_allowed": False,
        "research_state_mutation_allowed": False,
        "execution_allowed": False,
        "runtime_execution_allowed": False,
        "planning_only": True,
        "execution_state": "not_executed",
        "transition_candidate_digest": f"{index}" * 64,
    }


def _gate():
    candidates = [_candidate(1, "HYP-001"), _candidate(2, "HYP-002")]
    return {
        "kind": "brain_chat_research_state_transition_review_gate",
        "target_name": "demo-target",
        "gate_status": "ready-for-human-transition-decision",
        "source_update_digest": "u" * 64,
        "source_hypothesis_digest": "h" * 64,
        "source_decision_digest": "d" * 64,
        "source_feedback_digest": "f" * 64,
        "transition_candidate_count": 2,
        "transition_review_ready": True,
        "human_transition_decision_required": True,
        "research_state_transition_packet_ready": False,
        "research_state_transition_ready": False,
        "transition_candidates": candidates,
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
        "gate_digest": "g" * 64,
    }


def _completed_template():
    template = build_research_state_transition_decision_template(_gate())

    template["transition_decisions"][0]["decision"] = "approve-transition-packet"
    template["transition_decisions"][0]["decision_reason"] = "Approved for later local state-transition packet."
    template["transition_decisions"][0]["approved_for_state_transition_packet"] = True
    template["transition_decisions"][0]["state_transition_packet_required"] = True
    template["transition_decisions"][0]["human_operator"] = "tester"
    template["transition_decisions"][0]["human_reviewed_at"] = "2026-06-14T00:00:00Z"

    template["transition_decisions"][1]["decision"] = "reject-transition"
    template["transition_decisions"][1]["decision_reason"] = "Rejected for now."
    template["transition_decisions"][1]["approved_for_state_transition_packet"] = False
    template["transition_decisions"][1]["state_transition_packet_required"] = False
    template["transition_decisions"][1]["human_operator"] = "tester"
    template["transition_decisions"][1]["human_reviewed_at"] = "2026-06-14T00:00:00Z"

    return template


def test_transition_decision_template_cli_writes_json(tmp_path):
    gate_file = tmp_path / "gate.json"
    output_file = tmp_path / "template.json"
    gate_file.write_text(json.dumps(_gate()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-state-transition-decision-template",
            "--gate-file",
            str(gate_file),
            "--json-output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Research-State Transition Decision Template" in result.output
    assert "Saved research-state transition decision template JSON" in result.output

    template = json.loads(output_file.read_text(encoding="utf-8"))
    assert template["kind"] == "brain_chat_research_state_transition_decision_template"
    assert template["template_status"] == "ready-for-human-transition-decision"
    assert template["human_transition_decision_complete"] is False
    assert template["research_state_transition_packet_ready"] is False
    assert template["research_state_mutation_allowed"] is False


def test_transition_decision_template_cli_missing_gate_exits(tmp_path):
    result = runner.invoke(
        app,
        [
            "brain-chat-research-state-transition-decision-template",
            "--gate-file",
            str(tmp_path / "missing.json"),
        ],
    )

    assert result.exit_code == 1
    assert "Research-state transition review gate JSON not found" in result.output


def test_transition_decision_packet_cli_writes_json(tmp_path):
    gate_file = tmp_path / "gate.json"
    template_file = tmp_path / "template.json"
    output_file = tmp_path / "decision.json"

    gate_file.write_text(json.dumps(_gate()), encoding="utf-8")
    template_file.write_text(json.dumps(_completed_template()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-state-transition-decision-packet",
            "--gate-file",
            str(gate_file),
            "--template-file",
            str(template_file),
            "--json-output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Research-State Transition Decision Packet" in result.output
    assert "Saved research-state transition decision packet JSON" in result.output

    packet = json.loads(output_file.read_text(encoding="utf-8"))
    assert packet["kind"] == "brain_chat_research_state_transition_decision_packet"
    assert packet["decision_status"] == "ready-for-research-state-transition-packet"
    assert packet["approved_transition_count"] == 1
    assert packet["research_state_transition_packet_ready"] is True
    assert packet["research_state_transition_ready"] is False
    assert packet["confidence_update_allowed"] is False
    assert packet["research_state_mutation_allowed"] is False
    assert packet["execution_allowed"] is False
    assert packet["target_interaction_allowed"] is False
    assert packet["vulnerability_confirmation_allowed"] is False


def test_transition_decision_packet_cli_missing_template_exits(tmp_path):
    gate_file = tmp_path / "gate.json"
    gate_file.write_text(json.dumps(_gate()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-state-transition-decision-packet",
            "--gate-file",
            str(gate_file),
            "--template-file",
            str(tmp_path / "missing.json"),
        ],
    )

    assert result.exit_code == 1
    assert "Research-state transition decision template JSON not found" in result.output
