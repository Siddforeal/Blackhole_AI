import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def _local_item(index=1, hypothesis_id="HYP-001"):
    return {
        "local_write_execution_packet_item_id": f"LWEP-{index:03d}",
        "write_execution_decision_id": f"WEDP-{index:03d}",
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
        "decision": "approve-write-execution-packet",
        "decision_reason": "Approved for later local write execution packet.",
        "decision_actor": "human-reviewer",
        "source_write_execution_decision_digest": f"d{index}" * 32,
        "source_write_execution_review_item_digest": f"r{index}" * 32,
        "source_local_write_packet_preview_item_digest": f"l{index}" * 32,
        "source_persistence_write_decision_digest": f"p{index}" * 32,
        "source_persistence_write_review_item_digest": f"g{index}" * 32,
        "source_apply_preview_item_digest": f"a{index}" * 32,
        "source_apply_decision_digest": f"c{index}" * 32,
        "source_operation_digest": f"o{index}" * 32,
        "local_write_operation": "preview-persistent-research-state-field-write",
        "local_write_summary": f"hypotheses.{hypothesis_id}.confidence: medium -> high",
        "final_persistence_apply_review_required": True,
        "final_persistence_apply_review_ready": False,
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
        "local_write_execution_packet_item_digest": f"x{index}" * 32,
    }


def _packet():
    local_items = [_local_item(1, "HYP-001"), _local_item(2, "HYP-002")]
    return {
        "kind": "brain_chat_research_state_local_write_execution_packet",
        "source": "brain-chat-research-state-local-write-execution-packet",
        "target_name": "demo-target",
        "packet_status": "ready-for-final-persistence-apply-review-gate",
        "source_write_execution_decision_packet_digest": "ed" * 32,
        "source_write_execution_review_gate_digest": "eg" * 32,
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
        "approved_write_execution_decision_count": 2,
        "local_write_execution_packet_item_count": 2,
        "local_write_execution_packet_ready": True,
        "final_persistence_apply_review_gate_required": True,
        "final_persistence_apply_review_gate_ready": False,
        "persistent_research_state_write_ready": False,
        "persistent_research_state_write_allowed": False,
        "research_state_transition_ready": False,
        "local_write_execution_items": local_items,
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
        "local_write_execution_packet_digest": "lp" * 32,
    }


def test_final_persistence_apply_review_gate_cli_writes_json(tmp_path):
    packet_file = tmp_path / "local-write-execution-packet.json"
    output_file = tmp_path / "final-persistence-apply-review-gate.json"
    packet_file.write_text(json.dumps(_packet()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-state-final-persistence-apply-review-gate",
            "--local-write-execution-packet-file",
            str(packet_file),
            "--json-output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Final Persistence Apply Review Gate" in result.output
    assert "Saved final persistence apply review gate JSON" in result.output

    gate = json.loads(output_file.read_text(encoding="utf-8"))
    assert gate["kind"] == "brain_chat_research_state_final_persistence_apply_review_gate"
    assert gate["gate_status"] == "ready-for-human-final-persistence-apply-review"
    assert gate["human_final_persistence_apply_decision_required"] is True
    assert gate["human_final_persistence_apply_decision_complete"] is False
    assert gate["final_persistence_apply_decision_packet_required"] is True
    assert gate["final_persistence_apply_decision_packet_ready"] is False
    assert gate["persistent_research_state_write_ready"] is False
    assert gate["persistent_research_state_write_allowed"] is False
    assert gate["research_state_transition_ready"] is False
    assert gate["confidence_update_allowed"] is False
    assert gate["research_state_mutation_allowed"] is False
    assert gate["execution_allowed"] is False
    assert gate["target_interaction_allowed"] is False
    assert gate["vulnerability_confirmation_allowed"] is False


def test_final_persistence_apply_review_gate_cli_prints_json_without_output(tmp_path):
    packet_file = tmp_path / "local-write-execution-packet.json"
    packet_file.write_text(json.dumps(_packet()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-state-final-persistence-apply-review-gate",
            "--local-write-packet",
            str(packet_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert '"kind": "brain_chat_research_state_final_persistence_apply_review_gate"' in result.output
    assert '"gate_status": "ready-for-human-final-persistence-apply-review"' in result.output
    assert '"persistent_research_state_write_allowed": false' in result.output
    assert '"research_state_transition_ready": false' in result.output


def test_final_persistence_apply_review_gate_cli_missing_packet_file_exits(tmp_path):
    result = runner.invoke(
        app,
        [
            "brain-chat-research-state-final-persistence-apply-review-gate",
            "--local-write-execution-packet-file",
            str(tmp_path / "missing.json"),
        ],
    )

    assert result.exit_code == 1
    assert "Local write execution packet JSON not found" in result.output
