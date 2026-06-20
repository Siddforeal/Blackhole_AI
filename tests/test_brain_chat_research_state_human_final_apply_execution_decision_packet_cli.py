import importlib.util
import json
from pathlib import Path

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


_HELPERS_PATH = Path(__file__).with_name(
    "test_brain_chat_research_state_human_final_apply_execution_decision_packet.py"
)
_SPEC = importlib.util.spec_from_file_location("v135_human_final_execution_helpers", _HELPERS_PATH)
_HELPERS = importlib.util.module_from_spec(_SPEC)
assert _SPEC is not None
assert _SPEC.loader is not None
_SPEC.loader.exec_module(_HELPERS)


def _gate():
    return _HELPERS._gate()


def _decisions():
    return _HELPERS._decisions()


def test_human_final_apply_execution_decision_packet_cli_writes_json(tmp_path):
    gate_file = tmp_path / "final-apply-execution-review-gate.json"
    decisions_file = tmp_path / "human-final-apply-execution-decisions.json"
    output_file = tmp_path / "human-final-apply-execution-decision-packet.json"
    gate_file.write_text(json.dumps(_gate()), encoding="utf-8")
    decisions_file.write_text(json.dumps(_decisions()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-state-human-final-apply-execution-decision-packet",
            "--final-apply-execution-review-gate-file",
            str(gate_file),
            "--human-final-apply-execution-decisions-file",
            str(decisions_file),
            "--json-output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Human Final Apply Execution Decision Packet" in result.output
    assert "Saved human final apply execution decision packet JSON" in result.output

    packet = json.loads(output_file.read_text(encoding="utf-8"))
    assert packet["kind"] == "brain_chat_research_state_human_final_apply_execution_decision_packet"
    assert packet["decision_status"] == "ready-for-final-apply-execution-packet"
    assert packet["human_final_apply_execution_decision_complete"] is True
    assert packet["final_apply_execution_packet_required"] is True
    assert packet["final_apply_execution_packet_ready"] is False
    assert packet["persistent_research_state_write_ready"] is False
    assert packet["persistent_research_state_write_allowed"] is False
    assert packet["research_state_transition_ready"] is False
    assert packet["confidence_update_allowed"] is False
    assert packet["research_state_mutation_allowed"] is False
    assert packet["execution_allowed"] is False
    assert packet["target_interaction_allowed"] is False
    assert packet["vulnerability_confirmation_allowed"] is False


def test_human_final_apply_execution_decision_packet_cli_prints_json_without_output(tmp_path):
    gate_file = tmp_path / "final-apply-execution-review-gate.json"
    decisions_file = tmp_path / "human-final-apply-execution-decisions.json"
    gate_file.write_text(json.dumps(_gate()), encoding="utf-8")
    decisions_file.write_text(json.dumps(_decisions()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-state-human-final-apply-execution-decision-packet",
            "--final-execution-review-gate",
            str(gate_file),
            "--final-execution-decisions",
            str(decisions_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert '"kind": "brain_chat_research_state_human_final_apply_execution_decision_packet"' in result.output
    assert '"decision_status": "ready-for-final-apply-execution-packet"' in result.output
    assert '"persistent_research_state_write_allowed": false' in result.output
    assert '"research_state_transition_ready": false' in result.output


def test_human_final_apply_execution_decision_packet_cli_missing_gate_file_exits(tmp_path):
    decisions_file = tmp_path / "human-final-apply-execution-decisions.json"
    decisions_file.write_text(json.dumps(_decisions()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-state-human-final-apply-execution-decision-packet",
            "--final-apply-execution-review-gate-file",
            str(tmp_path / "missing-gate.json"),
            "--human-final-apply-execution-decisions-file",
            str(decisions_file),
        ],
    )

    assert result.exit_code == 1
    assert "Final apply execution review gate JSON not found" in result.output


def test_human_final_apply_execution_decision_packet_cli_missing_decisions_file_exits(tmp_path):
    gate_file = tmp_path / "final-apply-execution-review-gate.json"
    gate_file.write_text(json.dumps(_gate()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-state-human-final-apply-execution-decision-packet",
            "--final-apply-execution-review-gate-file",
            str(gate_file),
            "--human-final-apply-execution-decisions-file",
            str(tmp_path / "missing-decisions.json"),
        ],
    )

    assert result.exit_code == 1
    assert "Human final apply execution decisions JSON not found" in result.output
