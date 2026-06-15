import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def _approved(index=1, hypothesis_id="HYP-001"):
    item = {
        "decision_id": f"RSTD-{index:03d}",
        "transition_id": f"RST-{index:03d}",
        "source_update_id": f"HCU-{index:03d}",
        "hypothesis_id": hypothesis_id,
        "title": "Admin boundary hypothesis",
        "proposed_state_change": "update-hypothesis-confidence",
        "current_confidence": "medium",
        "proposed_confidence": "high",
        "decision": "approve-transition-packet",
        "decision_reason": "Approved for later local state-transition packet.",
        "source_update_digest": "u" * 64,
        "source_transition_candidate_digest": f"c{index}" * 32,
        "state_transition_packet_required": True,
        "research_state_transition_allowed": False,
        "confidence_update_allowed": False,
        "research_state_mutation_allowed": False,
        "execution_allowed": False,
        "runtime_execution_allowed": False,
        "planning_only": True,
        "execution_state": "not_executed",
    }
    item["approved_transition_digest"] = f"a{index}" * 32
    return item


def _decision_packet():
    approved = [_approved(1, "HYP-001"), _approved(2, "HYP-002")]
    return {
        "kind": "brain_chat_research_state_transition_decision_packet",
        "source": "brain-chat-research-state-transition-decision-packet",
        "target_name": "demo-target",
        "decision_status": "ready-for-research-state-transition-packet",
        "summary": "2 approved transitions.",
        "source_gate_digest": "g" * 64,
        "source_template_digest": "t" * 64,
        "source_update_digest": "u" * 64,
        "source_hypothesis_digest": "h" * 64,
        "source_feedback_digest": "f" * 64,
        "approved_transition_count": 2,
        "human_transition_decision_complete": True,
        "research_state_transition_packet_ready": True,
        "research_state_transition_ready": False,
        "approved_transition_candidates": approved,
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
        "decision_digest": "d" * 64,
    }


def test_transition_packet_cli_writes_json(tmp_path):
    decision_file = tmp_path / "decision.json"
    output_file = tmp_path / "transition.json"
    decision_file.write_text(json.dumps(_decision_packet()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-state-transition-packet",
            "--decision-file",
            str(decision_file),
            "--json-output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Local Research-State Transition Packet" in result.output
    assert "Saved local research-state transition packet JSON" in result.output

    packet = json.loads(output_file.read_text(encoding="utf-8"))
    assert packet["kind"] == "brain_chat_research_state_transition_packet"
    assert packet["packet_status"] == "ready-for-research-state-transition-apply-review"
    assert packet["local_transition_packet_ready"] is True
    assert packet["research_state_transition_apply_review_required"] is True
    assert packet["persistent_research_state_write_ready"] is False
    assert packet["persistent_research_state_write_allowed"] is False
    assert packet["research_state_transition_ready"] is False
    assert packet["confidence_update_allowed"] is False
    assert packet["research_state_mutation_allowed"] is False
    assert packet["execution_allowed"] is False
    assert packet["target_interaction_allowed"] is False
    assert packet["vulnerability_confirmation_allowed"] is False


def test_transition_packet_cli_prints_json_without_output(tmp_path):
    decision_file = tmp_path / "decision.json"
    decision_file.write_text(json.dumps(_decision_packet()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-state-transition-packet",
            "--transition-decision-packet",
            str(decision_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert '"kind": "brain_chat_research_state_transition_packet"' in result.output
    assert '"persistent_research_state_write_allowed": false' in result.output
    assert '"research_state_transition_ready": false' in result.output


def test_transition_packet_cli_missing_decision_file_exits(tmp_path):
    result = runner.invoke(
        app,
        [
            "brain-chat-research-state-transition-packet",
            "--decision-file",
            str(tmp_path / "missing.json"),
        ],
    )

    assert result.exit_code == 1
    assert "Research-state transition decision packet JSON not found" in result.output
