import json

from typer.testing import CliRunner

from bugintel.cli import app


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


def _write_json(path, value):
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def test_cli_writes_decision_template_json(tmp_path):
    feedback_file = tmp_path / "feedback.json"
    output_file = tmp_path / "decision-template.json"
    _write_json(feedback_file, _feedback_packet())

    result = runner.invoke(
        app,
        [
            "brain-chat-research-hypothesis-feedback-decision-template",
            "--feedback-file",
            str(feedback_file),
            "--output-file",
            str(output_file),
        ],
    )

    assert result.exit_code == 0
    assert "Hypothesis Feedback Decision Template" in result.output
    assert "Saved hypothesis feedback decision template JSON" in result.output
    assert "Safety:" in result.output

    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert data["kind"] == "brain_chat_research_hypothesis_feedback_decision_input"
    assert data["target_name"] == "demo-target"
    assert data["decision_count"] == 1
    assert data["decisions"][0]["feedback_id"] == "HFB-001"
    assert data["decisions"][0]["decision"] == "deferred"
    assert data["confidence_update_ready"] is False
    assert data["research_state_mutation_allowed"] is False
    assert data["execution_allowed"] is False


def test_cli_aliases_and_nested_output_work(tmp_path):
    feedback_file = tmp_path / "feedback.json"
    output_file = tmp_path / "nested" / "decision-template.json"
    _write_json(feedback_file, _feedback_packet())

    result = runner.invoke(
        app,
        [
            "brain-chat-research-hypothesis-feedback-decision-template",
            "--feedback-packet",
            str(feedback_file),
            "--output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0
    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert data["decision_count"] == 1


def test_cli_output_is_deterministic(tmp_path):
    feedback_file = tmp_path / "feedback.json"
    one = tmp_path / "one.json"
    two = tmp_path / "two.json"
    _write_json(feedback_file, _feedback_packet())

    args = [
        "brain-chat-research-hypothesis-feedback-decision-template",
        "--feedback-file",
        str(feedback_file),
    ]

    first = runner.invoke(app, args + ["--output-file", str(one)])
    second = runner.invoke(app, args + ["--output-file", str(two)])

    assert first.exit_code == 0
    assert second.exit_code == 0
    assert one.read_text(encoding="utf-8") == two.read_text(encoding="utf-8")


def test_cli_does_not_mutate_input_file(tmp_path):
    feedback_file = tmp_path / "feedback.json"
    output_file = tmp_path / "decision-template.json"
    _write_json(feedback_file, _feedback_packet())
    before = feedback_file.read_text(encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-hypothesis-feedback-decision-template",
            "--feedback-file",
            str(feedback_file),
            "--output-file",
            str(output_file),
        ],
    )

    assert result.exit_code == 0
    assert feedback_file.read_text(encoding="utf-8") == before


def test_cli_missing_file_errors(tmp_path):
    result = runner.invoke(
        app,
        [
            "brain-chat-research-hypothesis-feedback-decision-template",
            "--feedback-file",
            str(tmp_path / "missing.json"),
            "--output-file",
            str(tmp_path / "out.json"),
        ],
    )

    assert result.exit_code == 1
    assert "Hypothesis feedback packet JSON not found" in result.output


def test_cli_invalid_json_errors(tmp_path):
    feedback_file = tmp_path / "feedback.json"
    feedback_file.write_text("{", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-hypothesis-feedback-decision-template",
            "--feedback-file",
            str(feedback_file),
            "--output-file",
            str(tmp_path / "out.json"),
        ],
    )

    assert result.exit_code == 2
    assert "Invalid hypothesis feedback packet JSON" in result.output


def test_cli_non_object_json_errors(tmp_path):
    feedback_file = tmp_path / "feedback.json"
    feedback_file.write_text("[]", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-hypothesis-feedback-decision-template",
            "--feedback-file",
            str(feedback_file),
            "--output-file",
            str(tmp_path / "out.json"),
        ],
    )

    assert result.exit_code == 2
    assert "Invalid hypothesis feedback decision-template input" in result.output


def test_cli_help_lists_options():
    result = runner.invoke(
        app,
        [
            "brain-chat-research-hypothesis-feedback-decision-template",
            "--help",
        ],
    )

    assert result.exit_code == 0
    assert "Usage:" in result.output
