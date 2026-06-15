import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def _review_item(index=1, hypothesis_id="HYP-001"):
    return {
        "review_item_id": f"RSTAR-{index:03d}",
        "operation_id": f"RSTO-{index:03d}",
        "transition_id": f"RST-{index:03d}",
        "decision_id": f"RSTD-{index:03d}",
        "hypothesis_id": hypothesis_id,
        "field_path": f"hypotheses.{hypothesis_id}.confidence",
        "operation_type": "local-proposed-hypothesis-confidence-update",
        "current_value": "medium",
        "proposed_value": "high",
        "decision_reason": "Approved for later apply review.",
        "source_operation_digest": f"o{index}" * 32,
        "human_apply_decision_required": True,
        "allowed_decisions": [
            "approve-apply-packet",
            "reject-apply",
            "request-changes",
            "defer-apply",
        ],
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
        "review_item_digest": f"r{index}" * 32,
    }


def _gate():
    return {
        "kind": "brain_chat_research_state_transition_apply_review_gate",
        "source": "brain-chat-research-state-transition-apply-review-gate",
        "target_name": "demo-target",
        "gate_status": "ready-for-human-apply-review",
        "source_transition_packet_digest": "p" * 64,
        "source_decision_digest": "d" * 64,
        "source_gate_digest": "g" * 64,
        "source_template_digest": "t" * 64,
        "source_update_digest": "u" * 64,
        "source_hypothesis_digest": "h" * 64,
        "source_feedback_digest": "f" * 64,
        "transition_operation_count": 2,
        "apply_review_item_count": 2,
        "apply_review_ready": True,
        "human_apply_decision_required": True,
        "human_apply_decision_complete": False,
        "research_state_transition_apply_packet_ready": False,
        "persistent_research_state_write_ready": False,
        "persistent_research_state_write_allowed": False,
        "research_state_transition_ready": False,
        "apply_review_items": [
            _review_item(1, "HYP-001"),
            _review_item(2, "HYP-002"),
        ],
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
        "apply_review_gate_digest": "a" * 64,
    }


def _decisions():
    return [
        {
            "review_item_id": "RSTAR-001",
            "decision": "approve-apply-packet",
            "decision_reason": "Approved for local apply preview.",
            "persistent_write_allowed": False,
            "execution_allowed": False,
            "runtime_execution_allowed": False,
            "planning_only": True,
            "execution_state": "not_executed",
        },
        {
            "review_item_id": "RSTAR-002",
            "decision": "defer-apply",
            "decision_reason": "Defer until more review.",
            "persistent_write_allowed": False,
            "execution_allowed": False,
            "runtime_execution_allowed": False,
            "planning_only": True,
            "execution_state": "not_executed",
        },
    ]


def test_apply_decision_packet_cli_writes_json(tmp_path):
    gate_file = tmp_path / "apply-review-gate.json"
    decisions_file = tmp_path / "decisions.json"
    output_file = tmp_path / "apply-decision-packet.json"
    gate_file.write_text(json.dumps(_gate()), encoding="utf-8")
    decisions_file.write_text(json.dumps(_decisions()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-state-transition-apply-decision-packet",
            "--apply-review-gate-file",
            str(gate_file),
            "--human-apply-decisions-file",
            str(decisions_file),
            "--json-output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Research-State Transition Apply Decision Packet" in result.output
    assert "Saved research-state transition apply decision packet JSON" in result.output

    packet = json.loads(output_file.read_text(encoding="utf-8"))
    assert packet["kind"] == "brain_chat_research_state_transition_apply_decision_packet"
    assert packet["decision_status"] == "ready-for-research-state-transition-apply-preview"
    assert packet["human_apply_decision_complete"] is True
    assert packet["human_apply_decision_required"] is False
    assert packet["research_state_transition_apply_preview_ready"] is True
    assert packet["persistent_research_state_write_ready"] is False
    assert packet["persistent_research_state_write_allowed"] is False
    assert packet["research_state_transition_ready"] is False
    assert packet["confidence_update_allowed"] is False
    assert packet["research_state_mutation_allowed"] is False
    assert packet["execution_allowed"] is False
    assert packet["target_interaction_allowed"] is False
    assert packet["vulnerability_confirmation_allowed"] is False


def test_apply_decision_packet_cli_prints_json_without_output(tmp_path):
    gate_file = tmp_path / "apply-review-gate.json"
    decisions_file = tmp_path / "decisions.json"
    gate_file.write_text(json.dumps(_gate()), encoding="utf-8")
    decisions_file.write_text(json.dumps(_decisions()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-state-transition-apply-decision-packet",
            "--apply-review-gate",
            str(gate_file),
            "--apply-decisions",
            str(decisions_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert '"kind": "brain_chat_research_state_transition_apply_decision_packet"' in result.output
    assert '"research_state_transition_apply_preview_ready": true' in result.output
    assert '"persistent_research_state_write_allowed": false' in result.output
    assert '"research_state_transition_ready": false' in result.output


def test_apply_decision_packet_cli_missing_gate_file_exits(tmp_path):
    decisions_file = tmp_path / "decisions.json"
    decisions_file.write_text(json.dumps(_decisions()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-state-transition-apply-decision-packet",
            "--apply-review-gate-file",
            str(tmp_path / "missing.json"),
            "--human-apply-decisions-file",
            str(decisions_file),
        ],
    )

    assert result.exit_code == 1
    assert "Research-state transition apply review gate JSON not found" in result.output


def test_apply_decision_packet_cli_missing_decisions_file_exits(tmp_path):
    gate_file = tmp_path / "apply-review-gate.json"
    gate_file.write_text(json.dumps(_gate()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-state-transition-apply-decision-packet",
            "--apply-review-gate-file",
            str(gate_file),
            "--human-apply-decisions-file",
            str(tmp_path / "missing.json"),
        ],
    )

    assert result.exit_code == 1
    assert "Human apply decisions JSON not found" in result.output
