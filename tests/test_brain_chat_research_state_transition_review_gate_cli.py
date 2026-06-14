import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def _update_record(update_id="HCU-001", hypothesis_id="HYP-001", current="medium", proposed="high"):
    return {
        "update_id": update_id,
        "feedback_id": "HFB-001",
        "hypothesis_id": hypothesis_id,
        "title": "Admin boundary hypothesis",
        "current_confidence": current,
        "proposed_confidence": proposed,
        "decision_current_confidence": current,
        "categorical_confidence_change": current != proposed,
        "net_confidence_delta": 3,
        "proposed_disposition": "propose-confidence-promotion",
        "observation_ids": ["OBS-001"],
        "source_feedback_id": "HFB-001",
        "source_proposal_digest": "a" * 64,
        "source_decision_digest": "c" * 64,
        "effective_confidence_update_ready": True,
        "research_state_transition_review_required": True,
        "confidence_update_allowed": False,
        "hypothesis_mutation_allowed": False,
        "selection_mutation_allowed": False,
        "investigation_plan_mutation_allowed": False,
        "research_state_mutation_allowed": False,
        "execution_allowed": False,
        "runtime_execution_allowed": False,
        "planning_only": True,
        "execution_state": "not_executed",
        "update_digest": "d" * 64,
    }


def _update_packet():
    updates = [
        _update_record("HCU-001", "HYP-001", "medium", "high"),
        _update_record("HCU-002", "HYP-002", "high", "confirmed"),
    ]
    return {
        "kind": "brain_chat_research_hypothesis_confidence_update_packet",
        "source": "brain-chat-research-hypothesis-confidence-update-packet",
        "target_name": "demo-target",
        "update_status": "ready-for-research-state-transition-review",
        "summary": "2 proposed confidence updates.",
        "source_hypothesis_digest": "h" * 64,
        "source_decision_digest": "d" * 64,
        "source_feedback_digest": "f" * 64,
        "hypothesis_count": 2,
        "accepted_feedback_count": 2,
        "confidence_update_count": 2,
        "confidence_update_packet_ready": True,
        "research_state_transition_review_required": True,
        "research_state_transition_ready": False,
        "confidence_updates": updates,
        "hypothesis_findings": [],
        "decision_findings": [],
        "safety_findings": [],
        "consistency_findings": [],
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
        "update_digest": "u" * 64,
    }


def test_transition_review_gate_cli_writes_json(tmp_path):
    update_file = tmp_path / "update.json"
    output_file = tmp_path / "gate.json"
    update_file.write_text(json.dumps(_update_packet()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-state-transition-review-gate",
            "--update-file",
            str(update_file),
            "--json-output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Research-State Transition Review Gate" in result.output
    assert "Saved research-state transition review gate JSON" in result.output
    gate = json.loads(output_file.read_text(encoding="utf-8"))
    assert gate["kind"] == "brain_chat_research_state_transition_review_gate"
    assert gate["gate_status"] == "ready-for-human-transition-decision"
    assert gate["transition_candidate_count"] == 2
    assert gate["research_state_transition_packet_ready"] is False
    assert gate["research_state_transition_ready"] is False
    assert gate["confidence_update_allowed"] is False
    assert gate["hypothesis_mutation_allowed"] is False
    assert gate["research_state_mutation_allowed"] is False
    assert gate["execution_allowed"] is False
    assert gate["runtime_execution_allowed"] is False
    assert gate["target_interaction_allowed"] is False
    assert gate["report_submission_allowed"] is False
    assert gate["vulnerability_confirmation_allowed"] is False


def test_transition_review_gate_cli_prints_json_without_output(tmp_path):
    update_file = tmp_path / "update.json"
    update_file.write_text(json.dumps(_update_packet()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-state-transition-review-gate",
            "--confidence-update-packet",
            str(update_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert '"kind": "brain_chat_research_state_transition_review_gate"' in result.output
    assert '"research_state_mutation_allowed": false' in result.output
    assert '"research_state_transition_ready": false' in result.output


def test_transition_review_gate_cli_missing_update_file_exits(tmp_path):
    result = runner.invoke(
        app,
        [
            "brain-chat-research-state-transition-review-gate",
            "--update-file",
            str(tmp_path / "missing.json"),
        ],
    )

    assert result.exit_code == 1
    assert "Confidence update packet JSON not found" in result.output
