import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def _operation(index=1, hypothesis_id="HYP-001"):
    return {
        "operation_id": f"RSTO-{index:03d}",
        "transition_id": f"RST-{index:03d}",
        "decision_id": f"RSTD-{index:03d}",
        "hypothesis_id": hypothesis_id,
        "operation_type": "local-proposed-hypothesis-confidence-update",
        "field_path": f"hypotheses.{hypothesis_id}.confidence",
        "current_value": "medium",
        "proposed_value": "high",
        "decision_reason": "Approved for later apply review.",
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
    operations = [_operation(1, "HYP-001"), _operation(2, "HYP-002")]
    return {
        "kind": "brain_chat_research_state_transition_packet",
        "source": "brain-chat-research-state-transition-packet",
        "target_name": "demo-target",
        "packet_status": "ready-for-research-state-transition-apply-review",
        "source_decision_digest": "d" * 64,
        "source_gate_digest": "g" * 64,
        "source_template_digest": "t" * 64,
        "source_update_digest": "u" * 64,
        "source_hypothesis_digest": "h" * 64,
        "source_feedback_digest": "f" * 64,
        "transition_operation_count": 2,
        "local_transition_packet_ready": True,
        "research_state_transition_apply_review_required": True,
        "persistent_research_state_write_ready": False,
        "persistent_research_state_write_allowed": False,
        "research_state_transition_ready": False,
        "transition_operations": operations,
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
        "transition_packet_digest": "p" * 64,
    }


def test_apply_review_gate_cli_writes_json(tmp_path):
    packet_file = tmp_path / "transition.json"
    output_file = tmp_path / "apply-review-gate.json"
    packet_file.write_text(json.dumps(_transition_packet()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-state-transition-apply-review-gate",
            "--transition-packet-file",
            str(packet_file),
            "--json-output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Research-State Transition Apply Review Gate" in result.output
    assert "Saved research-state transition apply review gate JSON" in result.output

    gate = json.loads(output_file.read_text(encoding="utf-8"))
    assert gate["kind"] == "brain_chat_research_state_transition_apply_review_gate"
    assert gate["gate_status"] == "ready-for-human-apply-review"
    assert gate["apply_review_ready"] is True
    assert gate["human_apply_decision_required"] is True
    assert gate["human_apply_decision_complete"] is False
    assert gate["research_state_transition_apply_packet_ready"] is False
    assert gate["persistent_research_state_write_ready"] is False
    assert gate["persistent_research_state_write_allowed"] is False
    assert gate["research_state_transition_ready"] is False
    assert gate["confidence_update_allowed"] is False
    assert gate["research_state_mutation_allowed"] is False
    assert gate["execution_allowed"] is False
    assert gate["target_interaction_allowed"] is False
    assert gate["vulnerability_confirmation_allowed"] is False


def test_apply_review_gate_cli_prints_json_without_output(tmp_path):
    packet_file = tmp_path / "transition.json"
    packet_file.write_text(json.dumps(_transition_packet()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-state-transition-apply-review-gate",
            "--transition-packet",
            str(packet_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert '"kind": "brain_chat_research_state_transition_apply_review_gate"' in result.output
    assert '"apply_review_ready": true' in result.output
    assert '"persistent_research_state_write_allowed": false' in result.output
    assert '"research_state_transition_ready": false' in result.output


def test_apply_review_gate_cli_missing_transition_packet_exits(tmp_path):
    result = runner.invoke(
        app,
        [
            "brain-chat-research-state-transition-apply-review-gate",
            "--transition-packet-file",
            str(tmp_path / "missing.json"),
        ],
    )

    assert result.exit_code == 1
    assert "Research-state transition packet JSON not found" in result.output
