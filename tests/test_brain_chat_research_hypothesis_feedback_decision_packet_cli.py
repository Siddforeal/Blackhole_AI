import json

from typer.testing import CliRunner

from bugintel.cli import app
from bugintel.core.brain_chat_research_hypothesis_feedback_decision_template import (
    build_research_hypothesis_feedback_decision_template,
)


runner = CliRunner()


def _feedback_packet():
    return {
        "kind": "brain_chat_research_hypothesis_feedback_packet",
        "target_name": "demo-target",
        "packet_status": "ready-for-hypothesis-feedback-review",
        "packet_ready": True,
        "hypothesis_feedback_review_ready": True,
        "feedback_digest": "b" * 64,
        "feedback_proposal_count": 1,
        "feedback_proposals": [
            {
                "feedback_id": "HFB-001",
                "hypothesis_id": "HYP-001",
                "title": "Admin boundary hypothesis",
                "current_confidence": "medium",
                "proposed_confidence": "high",
                "proposed_disposition": "propose-confidence-promotion",
                "categorical_confidence_change": True,
                "net_confidence_delta": 3,
                "evidence_direction": "strengthens",
                "observation_ids": ["OBS-001"],
                "proposal_digest": "a" * 64,
                "confidence_mutation_allowed": False,
                "state_mutation_allowed": False,
                "human_review_required": True,
                "required_review": "human-hypothesis-feedback-review",
                "planning_only": True,
                "execution_allowed": False,
                "runtime_execution_allowed": False,
            }
        ],
        "confidence_update_ready": False,
        "research_state_transition_ready": False,
        "planning_only": True,
        "execution_allowed": False,
    }


def _decision_input(decision="accepted", confirmed=True):
    value = build_research_hypothesis_feedback_decision_template(
        _feedback_packet()
    )
    value["reviewer"] = "Sidd"
    value["overall_reason"] = "Human CLI decision recorded."
    value["decisions"][0]["decision"] = decision
    value["decisions"][0]["accepted_proposed_confidence"] = (
        confirmed if decision == "accepted" else False
    )
    value["decisions"][0]["reason"] = (
        f"Human decision recorded as {decision}."
    )
    return value


def _write_json(path, value):
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def test_cli_writes_decision_packet_json(tmp_path):
    feedback_file = tmp_path / "feedback.json"
    decision_file = tmp_path / "decisions.json"
    output_file = tmp_path / "packet.json"
    _write_json(feedback_file, _feedback_packet())
    _write_json(decision_file, _decision_input())

    result = runner.invoke(
        app,
        [
            "brain-chat-research-hypothesis-feedback-decision-packet",
            "--feedback-file",
            str(feedback_file),
            "--decision-file",
            str(decision_file),
            "--json-output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0
    assert "Hypothesis Feedback Decision Packet" in result.output
    assert "Saved hypothesis feedback decision packet JSON" in result.output
    assert "Safety:" in result.output

    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert data["kind"] == "brain_chat_research_hypothesis_feedback_decision_packet"
    assert data["decision_status"] == "ready-for-hypothesis-confidence-update-packet"
    assert data["accepted_feedback_count"] == 1
    assert data["hypothesis_confidence_update_packet_ready"] is True
    assert data["confidence_update_ready"] is False
    assert data["hypothesis_mutation_allowed"] is False
    assert data["research_state_mutation_allowed"] is False
    assert data["execution_allowed"] is False


def test_cli_aliases_and_nested_output_work(tmp_path):
    feedback_file = tmp_path / "feedback.json"
    decision_file = tmp_path / "decisions.json"
    output_file = tmp_path / "nested" / "packet.json"
    _write_json(feedback_file, _feedback_packet())
    _write_json(decision_file, _decision_input())

    result = runner.invoke(
        app,
        [
            "brain-chat-research-hypothesis-feedback-decision-packet",
            "--feedback-packet",
            str(feedback_file),
            "--decisions",
            str(decision_file),
            "--output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0
    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert data["accepted_feedback_count"] == 1


def test_cli_changes_requested_status(tmp_path):
    feedback_file = tmp_path / "feedback.json"
    decision_file = tmp_path / "decisions.json"
    output_file = tmp_path / "packet.json"
    decision = _decision_input("changes-requested", confirmed=False)
    _write_json(feedback_file, _feedback_packet())
    _write_json(decision_file, decision)

    result = runner.invoke(
        app,
        [
            "brain-chat-research-hypothesis-feedback-decision-packet",
            "--feedback-file",
            str(feedback_file),
            "--decision-file",
            str(decision_file),
            "--json-output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0
    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert data["decision_status"] == "changes-requested"
    assert data["hypothesis_confidence_update_packet_ready"] is False


def test_cli_output_is_deterministic(tmp_path):
    feedback_file = tmp_path / "feedback.json"
    decision_file = tmp_path / "decisions.json"
    one = tmp_path / "one.json"
    two = tmp_path / "two.json"
    _write_json(feedback_file, _feedback_packet())
    _write_json(decision_file, _decision_input())

    base = [
        "brain-chat-research-hypothesis-feedback-decision-packet",
        "--feedback-file",
        str(feedback_file),
        "--decision-file",
        str(decision_file),
    ]

    first = runner.invoke(app, base + ["--json-output", str(one)])
    second = runner.invoke(app, base + ["--json-output", str(two)])

    assert first.exit_code == 0
    assert second.exit_code == 0
    assert one.read_text(encoding="utf-8") == two.read_text(encoding="utf-8")


def test_cli_missing_feedback_file_errors(tmp_path):
    decision_file = tmp_path / "decisions.json"
    _write_json(decision_file, _decision_input())

    result = runner.invoke(
        app,
        [
            "brain-chat-research-hypothesis-feedback-decision-packet",
            "--feedback-file",
            str(tmp_path / "missing.json"),
            "--decision-file",
            str(decision_file),
            "--json-output",
            str(tmp_path / "out.json"),
        ],
    )

    assert result.exit_code == 1
    assert "Hypothesis feedback packet JSON not found" in result.output


def test_cli_missing_decision_file_errors(tmp_path):
    feedback_file = tmp_path / "feedback.json"
    _write_json(feedback_file, _feedback_packet())

    result = runner.invoke(
        app,
        [
            "brain-chat-research-hypothesis-feedback-decision-packet",
            "--feedback-file",
            str(feedback_file),
            "--decision-file",
            str(tmp_path / "missing.json"),
            "--json-output",
            str(tmp_path / "out.json"),
        ],
    )

    assert result.exit_code == 1
    assert "Hypothesis feedback decision JSON not found" in result.output


def test_cli_invalid_json_errors(tmp_path):
    feedback_file = tmp_path / "feedback.json"
    decision_file = tmp_path / "decisions.json"
    feedback_file.write_text("{", encoding="utf-8")
    _write_json(decision_file, _decision_input())

    result = runner.invoke(
        app,
        [
            "brain-chat-research-hypothesis-feedback-decision-packet",
            "--feedback-file",
            str(feedback_file),
            "--decision-file",
            str(decision_file),
            "--json-output",
            str(tmp_path / "out.json"),
        ],
    )

    assert result.exit_code == 2
    assert "Invalid hypothesis feedback decision input JSON" in result.output


def test_cli_non_object_json_errors(tmp_path):
    feedback_file = tmp_path / "feedback.json"
    decision_file = tmp_path / "decisions.json"
    feedback_file.write_text("[]", encoding="utf-8")
    _write_json(decision_file, _decision_input())

    result = runner.invoke(
        app,
        [
            "brain-chat-research-hypothesis-feedback-decision-packet",
            "--feedback-file",
            str(feedback_file),
            "--decision-file",
            str(decision_file),
            "--json-output",
            str(tmp_path / "out.json"),
        ],
    )

    assert result.exit_code == 2
    assert "Invalid hypothesis feedback decision packet input" in result.output


def test_cli_help_renders():
    result = runner.invoke(
        app,
        [
            "brain-chat-research-hypothesis-feedback-decision-packet",
            "--help",
        ],
    )

    assert result.exit_code == 0
    assert "Usage:" in result.output
