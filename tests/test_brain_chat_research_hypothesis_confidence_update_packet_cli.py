import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def _hypothesis(hypothesis_id="HYP-001", title="Admin boundary hypothesis", confidence="medium"):
    return {
        "hypothesis_id": hypothesis_id,
        "title": title,
        "attack_surface": "admin",
        "hypothesis_type": "authorization-boundary",
        "rationale": "Local planning hypothesis.",
        "local_review_questions": ["What local evidence exists?"],
        "evidence_needed": ["Reviewed observation packet."],
        "allowed_local_checks": ["Review local artifacts only."],
        "rejected_actions": ["Do not execute tools."],
        "priority": "high",
        "confidence": confidence,
        "tags": ["authz"],
    }


def _hypothesis_packet():
    return {
        "kind": "brain_chat_research_hypothesis_packet",
        "source": "brain-chat-research-hypothesis-packet",
        "target_name": "demo-target",
        "packet_status": "ready-for-hypothesis-review",
        "source_packet_status": "ready-for-hypothesis-generation",
        "hypothesis_count": 2,
        "hypotheses": [
            _hypothesis("HYP-001", "Admin boundary hypothesis", "medium"),
            _hypothesis("HYP-002", "Worker boundary hypothesis", "high"),
        ],
        "source_gaps": [],
        "hypothesis_gaps": [],
        "allowed_local_next_steps": ["Review hypotheses."],
        "rejected_actions": ["Do not execute tools."],
        "planning_only": True,
        "execution_state": "not_executed",
    }


def _accepted_feedback(feedback_id="HFB-001", hypothesis_id="HYP-001", current="medium", proposed="high", delta=3):
    return {
        "feedback_id": feedback_id,
        "hypothesis_id": hypothesis_id,
        "title": "Admin boundary hypothesis",
        "current_confidence": current,
        "proposed_confidence": proposed,
        "categorical_confidence_change": current != proposed,
        "net_confidence_delta": delta,
        "proposed_disposition": "propose-confidence-promotion",
        "observation_ids": ["OBS-001"],
        "proposal_digest": "a" * 64,
        "decision": "accepted",
        "decision_reason": "Human accepted confidence update.",
        "accepted_proposed_confidence": True,
        "effective_confidence_update_granted": True,
        "confidence_update_packet_required": True,
        "confidence_update_allowed": False,
        "hypothesis_mutation_allowed": False,
        "research_state_mutation_allowed": False,
        "planning_only": True,
        "execution_allowed": False,
        "runtime_execution_allowed": False,
        "decision_digest": "c" * 64,
    }


def _decision_packet():
    accepted = [
        _accepted_feedback("HFB-001", "HYP-001", "medium", "high", 3),
        _accepted_feedback("HFB-002", "HYP-002", "high", "confirmed", 2),
    ]
    return {
        "kind": "brain_chat_research_hypothesis_feedback_decision_packet",
        "source": "brain-chat-research-hypothesis-feedback-decision-packet",
        "target_name": "demo-target",
        "decision_status": "ready-for-hypothesis-confidence-update-packet",
        "summary": "2 accepted feedback decisions.",
        "reviewer": "Sidd",
        "overall_reason": "Accepted after human review.",
        "source_feedback_digest": "b" * 64,
        "decision_digest": "d" * 64,
        "feedback_proposal_count": 2,
        "decision_count": 2,
        "decision_ready": True,
        "hypothesis_confidence_update_packet_ready": True,
        "effective_acceptance_granted": True,
        "confidence_update_ready": False,
        "research_state_transition_ready": False,
        "accepted_feedback_count": 2,
        "accepted_feedback": accepted,
        "feedback_decisions": accepted,
        "rejected_feedback": [],
        "changes_requested_feedback": [],
        "deferred_feedback": [],
        "unresolved_feedback_ids": [],
        "source_findings": [],
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
        "hypothesis_mutation_allowed": False,
        "selection_mutation_allowed": False,
        "investigation_plan_mutation_allowed": False,
        "research_state_mutation_allowed": False,
        "report_submission_allowed": False,
        "vulnerability_confirmation_allowed": False,
        "planning_only": True,
        "execution_state": "not_executed",
    }


def test_confidence_update_packet_cli_writes_json(tmp_path):
    hypothesis_file = tmp_path / "hypothesis.json"
    decision_file = tmp_path / "decision.json"
    output_file = tmp_path / "update.json"

    hypothesis_file.write_text(json.dumps(_hypothesis_packet()), encoding="utf-8")
    decision_file.write_text(json.dumps(_decision_packet()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-hypothesis-confidence-update-packet",
            "--hypothesis-file",
            str(hypothesis_file),
            "--decision-file",
            str(decision_file),
            "--json-output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Hypothesis Confidence Update Packet" in result.output
    assert "Saved hypothesis confidence update packet JSON" in result.output
    assert "does not mutate hypothesis confidence" in result.output

    packet = json.loads(output_file.read_text(encoding="utf-8"))
    assert packet["kind"] == "brain_chat_research_hypothesis_confidence_update_packet"
    assert packet["update_status"] == "ready-for-research-state-transition-review"
    assert packet["confidence_update_count"] == 2
    assert packet["research_state_transition_ready"] is False


def test_confidence_update_packet_cli_prints_json_without_output(tmp_path):
    hypothesis_file = tmp_path / "hypothesis.json"
    decision_file = tmp_path / "decision.json"

    hypothesis_file.write_text(json.dumps(_hypothesis_packet()), encoding="utf-8")
    decision_file.write_text(json.dumps(_decision_packet()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-hypothesis-confidence-update-packet",
            "--hypothesis-packet",
            str(hypothesis_file),
            "--decision-packet",
            str(decision_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert '"kind": "brain_chat_research_hypothesis_confidence_update_packet"' in result.output
    assert '"confidence_update_allowed": false' in result.output
    assert '"research_state_mutation_allowed": false' in result.output


def test_confidence_update_packet_cli_missing_hypothesis_file_exits(tmp_path):
    decision_file = tmp_path / "decision.json"
    decision_file.write_text(json.dumps(_decision_packet()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-hypothesis-confidence-update-packet",
            "--hypothesis-file",
            str(tmp_path / "missing.json"),
            "--decision-file",
            str(decision_file),
        ],
    )

    assert result.exit_code == 1
    assert "Hypothesis packet JSON not found" in result.output


def test_confidence_update_packet_cli_missing_decision_file_exits(tmp_path):
    hypothesis_file = tmp_path / "hypothesis.json"
    hypothesis_file.write_text(json.dumps(_hypothesis_packet()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-hypothesis-confidence-update-packet",
            "--hypothesis-file",
            str(hypothesis_file),
            "--decision-file",
            str(tmp_path / "missing.json"),
        ],
    )

    assert result.exit_code == 1
    assert "Feedback decision packet JSON not found" in result.output
