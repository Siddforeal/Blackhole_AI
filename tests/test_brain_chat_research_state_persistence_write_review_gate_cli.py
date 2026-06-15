import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def _preview_item(index=1, hypothesis_id="HYP-001"):
    return {
        "preview_item_id": f"RSTPV-{index:03d}",
        "apply_decision_id": f"RSTAD-{index:03d}",
        "review_item_id": f"RSTAR-{index:03d}",
        "operation_id": f"RSTO-{index:03d}",
        "transition_id": f"RST-{index:03d}",
        "decision_id": f"RSTD-{index:03d}",
        "hypothesis_id": hypothesis_id,
        "field_path": f"hypotheses.{hypothesis_id}.confidence",
        "operation_type": "local-proposed-hypothesis-confidence-update",
        "current_value": "medium",
        "proposed_value": "high",
        "source_apply_decision_digest": f"a{index}" * 32,
        "source_operation_digest": f"o{index}" * 32,
        "persistence_write_review_required": True,
        "persistence_write_review_ready": False,
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
        "preview_item_digest": f"p{index}" * 32,
    }


def _preview():
    items = [_preview_item(1, "HYP-001"), _preview_item(2, "HYP-002")]
    return {
        "kind": "brain_chat_research_state_transition_apply_preview",
        "source": "brain-chat-research-state-transition-apply-preview",
        "target_name": "demo-target",
        "preview_status": "ready-for-persistence-write-review-gate",
        "source_apply_decision_packet_digest": "ad" * 32,
        "source_apply_review_gate_digest": "ar" * 32,
        "source_transition_packet_digest": "tp" * 32,
        "source_decision_digest": "d" * 64,
        "source_gate_digest": "g" * 64,
        "source_template_digest": "t" * 64,
        "source_update_digest": "u" * 64,
        "source_hypothesis_digest": "h" * 64,
        "source_feedback_digest": "f" * 64,
        "approved_apply_decision_count": 2,
        "preview_item_count": 2,
        "apply_preview_ready": True,
        "persistence_write_review_gate_required": True,
        "persistence_write_review_gate_ready": False,
        "persistent_research_state_write_ready": False,
        "persistent_research_state_write_allowed": False,
        "research_state_transition_ready": False,
        "preview_items": items,
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
        "apply_preview_digest": "v" * 64,
    }


def test_persistence_write_review_gate_cli_writes_json(tmp_path):
    preview_file = tmp_path / "apply-preview.json"
    output_file = tmp_path / "write-review-gate.json"
    preview_file.write_text(json.dumps(_preview()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-state-persistence-write-review-gate",
            "--apply-preview-file",
            str(preview_file),
            "--json-output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Research-State Persistence Write Review Gate" in result.output
    assert "Saved persistence write review gate JSON" in result.output

    gate = json.loads(output_file.read_text(encoding="utf-8"))
    assert gate["kind"] == "brain_chat_research_state_persistence_write_review_gate"
    assert gate["gate_status"] == "ready-for-human-persistence-write-review"
    assert gate["persistence_write_review_ready"] is True
    assert gate["human_persistence_write_decision_required"] is True
    assert gate["human_persistence_write_decision_complete"] is False
    assert gate["persistence_write_decision_packet_ready"] is False
    assert gate["persistent_research_state_write_ready"] is False
    assert gate["persistent_research_state_write_allowed"] is False
    assert gate["research_state_transition_ready"] is False
    assert gate["confidence_update_allowed"] is False
    assert gate["research_state_mutation_allowed"] is False
    assert gate["execution_allowed"] is False
    assert gate["target_interaction_allowed"] is False
    assert gate["vulnerability_confirmation_allowed"] is False


def test_persistence_write_review_gate_cli_prints_json_without_output(tmp_path):
    preview_file = tmp_path / "apply-preview.json"
    preview_file.write_text(json.dumps(_preview()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-state-persistence-write-review-gate",
            "--apply-preview",
            str(preview_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert '"kind": "brain_chat_research_state_persistence_write_review_gate"' in result.output
    assert '"persistence_write_review_ready": true' in result.output
    assert '"persistent_research_state_write_allowed": false' in result.output
    assert '"research_state_transition_ready": false' in result.output


def test_persistence_write_review_gate_cli_missing_preview_file_exits(tmp_path):
    result = runner.invoke(
        app,
        [
            "brain-chat-research-state-persistence-write-review-gate",
            "--apply-preview-file",
            str(tmp_path / "missing.json"),
        ],
    )

    assert result.exit_code == 1
    assert "Research-state transition apply preview JSON not found" in result.output
