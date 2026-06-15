import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


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
        "kind": "brain_chat_research_state_persistence_write_review_gate",
        "source": "brain-chat-research-state-persistence-write-review-gate",
        "target_name": "demo-target",
        "gate_status": "ready-for-human-persistence-write-review",
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


def test_persistence_write_decision_packet_cli_writes_json(tmp_path):
    gate_file = tmp_path / "write-review-gate.json"
    human_file = tmp_path / "human-write-decisions.json"
    output_file = tmp_path / "write-decision-packet.json"
    gate_file.write_text(json.dumps(_gate()), encoding="utf-8")
    human_file.write_text(json.dumps(_human()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-state-persistence-write-decision-packet",
            "--persistence-write-review-gate-file",
            str(gate_file),
            "--human-persistence-write-decisions-file",
            str(human_file),
            "--json-output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Human Persistence Write Decision Packet" in result.output
    assert "Saved human persistence write decision packet JSON" in result.output

    packet = json.loads(output_file.read_text(encoding="utf-8"))
    assert packet["kind"] == "brain_chat_research_state_persistence_write_decision_packet"
    assert packet["decision_status"] == "ready-for-local-write-packet-preview"
    assert packet["approved_persistence_write_decision_count"] == 1
    assert packet["human_persistence_write_decision_complete"] is True
    assert packet["local_write_packet_preview_required"] is True
    assert packet["local_write_packet_preview_ready"] is True
    assert packet["persistent_research_state_write_ready"] is False
    assert packet["persistent_research_state_write_allowed"] is False
    assert packet["research_state_transition_ready"] is False
    assert packet["confidence_update_allowed"] is False
    assert packet["research_state_mutation_allowed"] is False
    assert packet["execution_allowed"] is False
    assert packet["target_interaction_allowed"] is False
    assert packet["vulnerability_confirmation_allowed"] is False


def test_persistence_write_decision_packet_cli_prints_json_without_output(tmp_path):
    gate_file = tmp_path / "write-review-gate.json"
    human_file = tmp_path / "human-write-decisions.json"
    gate_file.write_text(json.dumps(_gate()), encoding="utf-8")
    human_file.write_text(json.dumps(_human()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-state-persistence-write-decision-packet",
            "--write-review-gate",
            str(gate_file),
            "--write-decisions",
            str(human_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert '"kind": "brain_chat_research_state_persistence_write_decision_packet"' in result.output
    assert '"local_write_packet_preview_ready": true' in result.output
    assert '"persistent_research_state_write_allowed": false' in result.output
    assert '"research_state_transition_ready": false' in result.output


def test_persistence_write_decision_packet_cli_missing_gate_file_exits(tmp_path):
    human_file = tmp_path / "human-write-decisions.json"
    human_file.write_text(json.dumps(_human()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-state-persistence-write-decision-packet",
            "--persistence-write-review-gate-file",
            str(tmp_path / "missing.json"),
            "--human-persistence-write-decisions-file",
            str(human_file),
        ],
    )

    assert result.exit_code == 1
    assert "Persistence write review gate JSON not found" in result.output


def test_persistence_write_decision_packet_cli_missing_human_file_exits(tmp_path):
    gate_file = tmp_path / "write-review-gate.json"
    gate_file.write_text(json.dumps(_gate()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-state-persistence-write-decision-packet",
            "--persistence-write-review-gate-file",
            str(gate_file),
            "--human-persistence-write-decisions-file",
            str(tmp_path / "missing-human.json"),
        ],
    )

    assert result.exit_code == 1
    assert "Human persistence write decisions JSON not found" in result.output
