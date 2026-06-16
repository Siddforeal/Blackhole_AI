import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def _approved(index=1, hypothesis_id="HYP-001"):
    return {
        "persistence_write_decision_id": f"PWRD-{index:03d}",
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
        "source_review_item_digest": f"r{index}" * 32,
        "source_preview_item_digest": f"p{index}" * 32,
        "source_apply_decision_digest": f"a{index}" * 32,
        "source_operation_digest": f"o{index}" * 32,
        "decision": "approve-persistence-write-packet",
        "decision_valid": True,
        "decision_reason": "Approved for local write packet preview.",
        "decision_actor": "human-reviewer",
        "human_persistence_write_decision_complete": True,
        "local_write_packet_preview_required": True,
        "local_write_packet_preview_ready": False,
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
        "persistence_write_decision_digest": f"d{index}" * 32,
    }


def _packet():
    approved = [_approved(1, "HYP-001"), _approved(2, "HYP-002")]
    return {
        "kind": "brain_chat_research_state_persistence_write_decision_packet",
        "source": "brain-chat-research-state-persistence-write-decision-packet",
        "target_name": "demo-target",
        "decision_status": "ready-for-local-write-packet-preview",
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
        "persistence_write_review_item_count": 2,
        "persistence_write_decision_count": 2,
        "approved_persistence_write_decision_count": 2,
        "human_persistence_write_decision_required": True,
        "human_persistence_write_decision_complete": True,
        "local_write_packet_preview_required": True,
        "local_write_packet_preview_ready": True,
        "persistent_research_state_write_ready": False,
        "persistent_research_state_write_allowed": False,
        "research_state_transition_ready": False,
        "persistence_write_decisions": approved,
        "approved_persistence_write_items": approved,
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
        "persistence_write_decision_packet_digest": "wd" * 32,
    }


def test_local_write_packet_preview_cli_writes_json(tmp_path):
    packet_file = tmp_path / "write-decision-packet.json"
    output_file = tmp_path / "local-write-preview.json"
    packet_file.write_text(json.dumps(_packet()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-state-local-write-packet-preview",
            "--persistence-write-decision-packet-file",
            str(packet_file),
            "--json-output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Local Write Packet Preview" in result.output
    assert "Saved local write packet preview JSON" in result.output

    preview = json.loads(output_file.read_text(encoding="utf-8"))
    assert preview["kind"] == "brain_chat_research_state_local_write_packet_preview"
    assert preview["preview_status"] == "ready-for-write-execution-review-gate"
    assert preview["local_write_packet_preview_ready"] is True
    assert preview["write_execution_review_gate_required"] is True
    assert preview["write_execution_review_gate_ready"] is False
    assert preview["persistent_research_state_write_ready"] is False
    assert preview["persistent_research_state_write_allowed"] is False
    assert preview["research_state_transition_ready"] is False
    assert preview["confidence_update_allowed"] is False
    assert preview["research_state_mutation_allowed"] is False
    assert preview["execution_allowed"] is False
    assert preview["target_interaction_allowed"] is False
    assert preview["vulnerability_confirmation_allowed"] is False


def test_local_write_packet_preview_cli_prints_json_without_output(tmp_path):
    packet_file = tmp_path / "write-decision-packet.json"
    packet_file.write_text(json.dumps(_packet()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-state-local-write-packet-preview",
            "--write-decision-packet",
            str(packet_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert '"kind": "brain_chat_research_state_local_write_packet_preview"' in result.output
    assert '"local_write_packet_preview_ready": true' in result.output
    assert '"persistent_research_state_write_allowed": false' in result.output
    assert '"research_state_transition_ready": false' in result.output


def test_local_write_packet_preview_cli_missing_packet_file_exits(tmp_path):
    result = runner.invoke(
        app,
        [
            "brain-chat-research-state-local-write-packet-preview",
            "--persistence-write-decision-packet-file",
            str(tmp_path / "missing.json"),
        ],
    )

    assert result.exit_code == 1
    assert "Persistence write decision packet JSON not found" in result.output
