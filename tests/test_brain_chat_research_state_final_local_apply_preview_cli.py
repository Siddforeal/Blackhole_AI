import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def _approved(index=1, hypothesis_id="HYP-001"):
    return {
        "human_final_apply_decision_id": f"HFAD-{index:03d}",
        "final_persistence_apply_review_item_id": f"FPARG-{index:03d}",
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
        "local_write_operation": "preview-persistent-research-state-field-write",
        "local_write_summary": f"hypotheses.{hypothesis_id}.confidence: medium -> high",
        "decision": "approve-final-persistence-apply",
        "decision_valid": True,
        "decision_reason": "Approved for later final local apply preview.",
        "decision_actor": "human-reviewer",
        "human_final_apply_decision_complete": True,
        "final_local_apply_preview_required": True,
        "final_local_apply_preview_ready": False,
        "persistent_write_ready": False,
        "persistent_write_allowed": False,
        "research_state_transition_ready": False,
        "research_state_transition_allowed": False,
        "confidence_update_allowed": False,
        "hypothesis_mutation_allowed": False,
        "research_state_mutation_allowed": False,
        "execution_allowed": False,
        "runtime_execution_allowed": False,
        "source_final_persistence_apply_review_item_digest": f"z{index}" * 32,
        "source_local_write_execution_packet_item_digest": f"x{index}" * 32,
        "source_write_execution_decision_digest": f"d{index}" * 32,
        "source_write_execution_review_item_digest": f"r{index}" * 32,
        "source_local_write_packet_preview_item_digest": f"l{index}" * 32,
        "source_persistence_write_decision_digest": f"p{index}" * 32,
        "source_persistence_write_review_item_digest": f"g{index}" * 32,
        "source_apply_preview_item_digest": f"a{index}" * 32,
        "source_apply_decision_digest": f"c{index}" * 32,
        "source_operation_digest": f"o{index}" * 32,
        "planning_only": True,
        "execution_state": "not_executed",
        "human_final_apply_decision_digest": f"h{index}" * 32,
    }


def _packet():
    approved = [_approved(1, "HYP-001"), _approved(2, "HYP-002")]
    return {
        "kind": "brain_chat_research_state_human_final_apply_decision_packet",
        "source": "brain-chat-research-state-human-final-apply-decision-packet",
        "target_name": "demo-target",
        "decision_status": "ready-for-final-local-apply-preview",
        "source_final_persistence_apply_review_gate_digest": "fg" * 32,
        "source_local_write_execution_packet_digest": "lp" * 32,
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
        "human_final_apply_decision_required": True,
        "human_final_apply_decision_complete": True,
        "final_local_apply_preview_required": True,
        "final_local_apply_preview_ready": False,
        "persistent_research_state_write_ready": False,
        "persistent_research_state_write_allowed": False,
        "research_state_transition_ready": False,
        "final_persistence_apply_review_item_count": 2,
        "human_final_apply_decision_count": 2,
        "approved_final_apply_decision_count": 2,
        "final_apply_decisions": approved,
        "approved_final_apply_items": approved,
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
        "human_final_apply_decision_packet_digest": "hp" * 32,
    }


def test_final_local_apply_preview_cli_writes_json(tmp_path):
    packet_file = tmp_path / "human-final-apply-decision-packet.json"
    output_file = tmp_path / "final-local-apply-preview.json"
    packet_file.write_text(json.dumps(_packet()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-state-final-local-apply-preview",
            "--human-final-apply-decision-packet-file",
            str(packet_file),
            "--json-output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Final Local Apply Preview" in result.output
    assert "Saved final local apply preview JSON" in result.output

    preview = json.loads(output_file.read_text(encoding="utf-8"))
    assert preview["kind"] == "brain_chat_research_state_final_local_apply_preview"
    assert preview["preview_status"] == "ready-for-final-apply-execution-review-gate"
    assert preview["final_local_apply_preview_ready"] is True
    assert preview["final_apply_execution_review_gate_required"] is True
    assert preview["final_apply_execution_review_gate_ready"] is False
    assert preview["persistent_research_state_write_ready"] is False
    assert preview["persistent_research_state_write_allowed"] is False
    assert preview["research_state_transition_ready"] is False
    assert preview["confidence_update_allowed"] is False
    assert preview["research_state_mutation_allowed"] is False
    assert preview["execution_allowed"] is False
    assert preview["target_interaction_allowed"] is False
    assert preview["vulnerability_confirmation_allowed"] is False


def test_final_local_apply_preview_cli_prints_json_without_output(tmp_path):
    packet_file = tmp_path / "human-final-apply-decision-packet.json"
    packet_file.write_text(json.dumps(_packet()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-state-final-local-apply-preview",
            "--final-apply-decision-packet",
            str(packet_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert '"kind": "brain_chat_research_state_final_local_apply_preview"' in result.output
    assert '"preview_status": "ready-for-final-apply-execution-review-gate"' in result.output
    assert '"persistent_research_state_write_allowed": false' in result.output
    assert '"research_state_transition_ready": false' in result.output


def test_final_local_apply_preview_cli_missing_packet_file_exits(tmp_path):
    result = runner.invoke(
        app,
        [
            "brain-chat-research-state-final-local-apply-preview",
            "--human-final-apply-decision-packet-file",
            str(tmp_path / "missing.json"),
        ],
    )

    assert result.exit_code == 1
    assert "Human final apply decision packet JSON not found" in result.output
