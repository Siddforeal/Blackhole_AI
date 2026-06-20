import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def _review_item(index=1, hypothesis_id="HYP-001"):
    return {
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
        "decision": "approve-write-execution-packet",
        "decision_reason": "Approved for later local write execution packet.",
        "decision_actor": "human-reviewer",
        "allowed_human_decisions": [
            "approve-final-persistence-apply",
            "reject-final-persistence-apply",
            "request-changes",
            "defer-final-persistence-apply",
        ],
        "human_final_persistence_apply_decision_required": True,
        "human_final_persistence_apply_decision_complete": False,
        "final_persistence_apply_decision_packet_required": True,
        "final_persistence_apply_decision_packet_ready": False,
        "persistent_write_ready": False,
        "persistent_write_allowed": False,
        "research_state_transition_ready": False,
        "research_state_transition_allowed": False,
        "confidence_update_allowed": False,
        "hypothesis_mutation_allowed": False,
        "research_state_mutation_allowed": False,
        "execution_allowed": False,
        "runtime_execution_allowed": False,
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
        "final_persistence_apply_review_item_digest": f"z{index}" * 32,
    }


def _gate():
    review_items = [_review_item(1, "HYP-001"), _review_item(2, "HYP-002")]
    return {
        "kind": "brain_chat_research_state_final_persistence_apply_review_gate",
        "source": "brain-chat-research-state-final-persistence-apply-review-gate",
        "target_name": "demo-target",
        "gate_status": "ready-for-human-final-persistence-apply-review",
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
        "local_write_execution_packet_item_count": 2,
        "final_persistence_apply_review_item_count": 2,
        "human_final_persistence_apply_decision_required": True,
        "human_final_persistence_apply_decision_complete": False,
        "final_persistence_apply_decision_packet_required": True,
        "final_persistence_apply_decision_packet_ready": False,
        "persistent_research_state_write_ready": False,
        "persistent_research_state_write_allowed": False,
        "research_state_transition_ready": False,
        "final_persistence_apply_review_items": review_items,
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
        "final_persistence_apply_review_gate_digest": "fg" * 32,
    }


def _decisions():
    return {
        "human_final_apply_decisions": [
            {
                "human_final_apply_decision_id": "HFAD-001",
                "final_persistence_apply_review_item_id": "FPARG-001",
                "decision": "approve-final-persistence-apply",
                "decision_reason": "Approved for later final local apply preview.",
                "decision_actor": "human-reviewer",
            },
            {
                "human_final_apply_decision_id": "HFAD-002",
                "final_persistence_apply_review_item_id": "FPARG-002",
                "decision": "reject-final-persistence-apply",
                "decision_reason": "Rejected until more review context is available.",
                "decision_actor": "human-reviewer",
            },
        ]
    }


def test_human_final_apply_decision_packet_cli_writes_json(tmp_path):
    gate_file = tmp_path / "final-persistence-apply-review-gate.json"
    decisions_file = tmp_path / "human-final-apply-decisions.json"
    output_file = tmp_path / "human-final-apply-decision-packet.json"
    gate_file.write_text(json.dumps(_gate()), encoding="utf-8")
    decisions_file.write_text(json.dumps(_decisions()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-state-human-final-apply-decision-packet",
            "--final-persistence-apply-review-gate-file",
            str(gate_file),
            "--human-final-apply-decisions-file",
            str(decisions_file),
            "--json-output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Human Final Apply Decision Packet" in result.output
    assert "Saved human final apply decision packet JSON" in result.output

    packet = json.loads(output_file.read_text(encoding="utf-8"))
    assert packet["kind"] == "brain_chat_research_state_human_final_apply_decision_packet"
    assert packet["decision_status"] == "ready-for-final-local-apply-preview"
    assert packet["human_final_apply_decision_required"] is True
    assert packet["human_final_apply_decision_complete"] is True
    assert packet["final_local_apply_preview_required"] is True
    assert packet["final_local_apply_preview_ready"] is False
    assert packet["persistent_research_state_write_ready"] is False
    assert packet["persistent_research_state_write_allowed"] is False
    assert packet["research_state_transition_ready"] is False
    assert packet["confidence_update_allowed"] is False
    assert packet["research_state_mutation_allowed"] is False
    assert packet["execution_allowed"] is False
    assert packet["target_interaction_allowed"] is False
    assert packet["vulnerability_confirmation_allowed"] is False


def test_human_final_apply_decision_packet_cli_prints_json_without_output(tmp_path):
    gate_file = tmp_path / "final-persistence-apply-review-gate.json"
    decisions_file = tmp_path / "human-final-apply-decisions.json"
    gate_file.write_text(json.dumps(_gate()), encoding="utf-8")
    decisions_file.write_text(json.dumps(_decisions()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-state-human-final-apply-decision-packet",
            "--final-apply-review-gate",
            str(gate_file),
            "--final-apply-decisions",
            str(decisions_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert '"kind": "brain_chat_research_state_human_final_apply_decision_packet"' in result.output
    assert '"decision_status": "ready-for-final-local-apply-preview"' in result.output
    assert '"persistent_research_state_write_allowed": false' in result.output
    assert '"research_state_transition_ready": false' in result.output


def test_human_final_apply_decision_packet_cli_missing_gate_file_exits(tmp_path):
    decisions_file = tmp_path / "human-final-apply-decisions.json"
    decisions_file.write_text(json.dumps(_decisions()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-state-human-final-apply-decision-packet",
            "--final-persistence-apply-review-gate-file",
            str(tmp_path / "missing.json"),
            "--human-final-apply-decisions-file",
            str(decisions_file),
        ],
    )

    assert result.exit_code == 1
    assert "Final persistence apply review gate JSON not found" in result.output


def test_human_final_apply_decision_packet_cli_missing_decisions_file_exits(tmp_path):
    gate_file = tmp_path / "final-persistence-apply-review-gate.json"
    gate_file.write_text(json.dumps(_gate()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-state-human-final-apply-decision-packet",
            "--final-persistence-apply-review-gate-file",
            str(gate_file),
            "--human-final-apply-decisions-file",
            str(tmp_path / "missing.json"),
        ],
    )

    assert result.exit_code == 1
    assert "Human final apply decisions JSON not found" in result.output
