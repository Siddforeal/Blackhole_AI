import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def _review_item(index=1, hypothesis_id="HYP-001"):
    return {
        "write_execution_review_item_id": f"WERG-{index:03d}",
        "local_write_packet_preview_item_id": f"LWPP-{index:03d}",
        "persistence_write_decision_id": f"PWRD-{index:03d}",
        "persistence_write_review_item_id": f"PWRG-{index:03d}",
        "source_preview_item_id": f"RSTPV-{index:03d}",
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
        "write_preview_action": "preview-stored-state-field-update",
        "write_preview_summary": f"hypotheses.{hypothesis_id}.confidence: medium -> high",
        "source_local_write_packet_preview_item_digest": f"l{index}" * 32,
        "source_persistence_write_decision_digest": f"d{index}" * 32,
        "source_persistence_write_review_item_digest": f"r{index}" * 32,
        "source_apply_preview_item_digest": f"p{index}" * 32,
        "source_apply_decision_digest": f"a{index}" * 32,
        "source_operation_digest": f"o{index}" * 32,
        "human_write_execution_review_required": True,
        "human_write_execution_review_complete": False,
        "write_execution_decision_packet_ready": False,
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
        "write_execution_review_item_digest": f"w{index}" * 32,
    }


def _gate():
    review_items = [_review_item(1, "HYP-001"), _review_item(2, "HYP-002")]
    return {
        "kind": "brain_chat_research_state_write_execution_review_gate",
        "source": "brain-chat-research-state-write-execution-review-gate",
        "target_name": "demo-target",
        "gate_status": "ready-for-human-write-execution-review",
        "source_local_write_packet_preview_digest": "lw" * 32,
        "source_persistence_write_decision_packet_digest": "wd" * 32,
        "source_persistence_write_review_gate_digest": "wg" * 32,
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
        "local_write_packet_preview_item_count": 2,
        "write_execution_review_item_count": 2,
        "write_execution_review_ready": True,
        "human_write_execution_review_required": True,
        "human_write_execution_review_complete": False,
        "write_execution_decision_packet_ready": False,
        "persistent_research_state_write_ready": False,
        "persistent_research_state_write_allowed": False,
        "research_state_transition_ready": False,
        "review_items": review_items,
        "allowed_decisions": [
            "approve-write-execution-packet",
            "reject-write-execution",
            "request-changes",
            "defer-write-execution",
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
        "write_execution_review_gate_digest": "eg" * 32,
    }


def _decisions():
    return {
        "human_write_execution_decisions": [
            {
                "write_execution_review_item_id": "WERG-001",
                "decision": "approve-write-execution-packet",
                "decision_reason": "Approved for later local write execution packet.",
                "decision_actor": "human-reviewer",
            },
            {
                "write_execution_review_item_id": "WERG-002",
                "decision": "reject-write-execution",
                "decision_reason": "Not approved.",
                "decision_actor": "human-reviewer",
            },
        ]
    }


def test_write_execution_decision_packet_cli_writes_json(tmp_path):
    gate_file = tmp_path / "write-execution-review-gate.json"
    decisions_file = tmp_path / "human-write-execution-decisions.json"
    output_file = tmp_path / "write-execution-decision-packet.json"
    gate_file.write_text(json.dumps(_gate()), encoding="utf-8")
    decisions_file.write_text(json.dumps(_decisions()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-state-write-execution-decision-packet",
            "--write-execution-review-gate-file",
            str(gate_file),
            "--human-write-execution-decisions-file",
            str(decisions_file),
            "--json-output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Write Execution Decision Packet" in result.output
    assert "Saved write execution decision packet JSON" in result.output

    packet = json.loads(output_file.read_text(encoding="utf-8"))
    assert packet["kind"] == "brain_chat_research_state_write_execution_decision_packet"
    assert packet["decision_status"] == "ready-for-local-write-execution-packet"
    assert packet["human_write_execution_decision_complete"] is True
    assert packet["local_write_execution_packet_required"] is True
    assert packet["local_write_execution_packet_ready"] is False
    assert packet["persistent_research_state_write_ready"] is False
    assert packet["persistent_research_state_write_allowed"] is False
    assert packet["research_state_transition_ready"] is False
    assert packet["confidence_update_allowed"] is False
    assert packet["research_state_mutation_allowed"] is False
    assert packet["execution_allowed"] is False
    assert packet["target_interaction_allowed"] is False
    assert packet["vulnerability_confirmation_allowed"] is False


def test_write_execution_decision_packet_cli_prints_json_without_output(tmp_path):
    gate_file = tmp_path / "write-execution-review-gate.json"
    decisions_file = tmp_path / "human-write-execution-decisions.json"
    gate_file.write_text(json.dumps(_gate()), encoding="utf-8")
    decisions_file.write_text(json.dumps(_decisions()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-state-write-execution-decision-packet",
            "--execution-review-gate",
            str(gate_file),
            "--write-decisions",
            str(decisions_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert '"kind": "brain_chat_research_state_write_execution_decision_packet"' in result.output
    assert '"human_write_execution_decision_complete": true' in result.output
    assert '"persistent_research_state_write_allowed": false' in result.output
    assert '"research_state_transition_ready": false' in result.output


def test_write_execution_decision_packet_cli_missing_input_exits(tmp_path):
    decisions_file = tmp_path / "human-write-execution-decisions.json"
    decisions_file.write_text(json.dumps(_decisions()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-state-write-execution-decision-packet",
            "--write-execution-review-gate-file",
            str(tmp_path / "missing.json"),
            "--human-write-execution-decisions-file",
            str(decisions_file),
        ],
    )

    assert result.exit_code == 1
    assert "Write execution review gate JSON not found" in result.output
