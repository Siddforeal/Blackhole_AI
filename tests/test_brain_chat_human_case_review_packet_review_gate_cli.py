import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def _session_data():
    return {
        "turn_count": 2,
        "planning_only": True,
        "execution_state": "not_executed",
        "turns": [
            {
                "question": "What should I test first?",
                "answer": "Focus endpoint.",
                "target_name": "demo.local",
                "focus_endpoint": "/api/accounts/123/users/{id}/permissions",
                "decision": "blocked-pending-scope-and-controls",
                "approval_status": "blocked-pending-approval",
                "execution_gate": "blocked-manifest-execution-disabled",
                "execution_allowed": False,
                "created_at": "2026-01-01T00:00:00+00:00",
            },
            {
                "question": "What evidence do we need?",
                "answer": "Evidence planning.",
                "target_name": "demo.local",
                "focus_endpoint": "/api/accounts/123/users/{id}/permissions",
                "decision": "blocked-pending-scope-and-controls",
                "approval_status": "blocked-pending-approval",
                "execution_gate": "blocked-manifest-execution-disabled",
                "execution_allowed": False,
                "created_at": "2026-01-01T00:01:00+00:00",
            },
        ],
    }


def _write_session(tmp_path):
    session_file = tmp_path / "brain-chat-session.json"
    session_file.write_text(json.dumps(_session_data()), encoding="utf-8")
    return session_file


def _write_status(tmp_path):
    status_file = tmp_path / "evidence-status.json"
    status_file.write_text(
        json.dumps(
            {
                "items": [
                    {"label": "Authorization decision diff", "status": "review-needed"},
                    {"label": "Baseline request/response sample", "status": "collected"},
                ]
            }
        ),
        encoding="utf-8",
    )
    return status_file


def _write_approval_decision(tmp_path):
    decision_file = tmp_path / "approval-decision.json"
    decision_file.write_text(
        json.dumps(
            {
                "decision": "approved",
                "reason": "Evidence approval decision.",
                "reviewer": "local-reviewer",
            }
        ),
        encoding="utf-8",
    )
    return decision_file


def _write_step_decision(tmp_path):
    decision_file = tmp_path / "validation-step-decision.json"
    decision_file.write_text(
        json.dumps(
            {
                "decision": "approved",
                "reason": "Validation step approval decision.",
                "reviewer": "local-reviewer",
            }
        ),
        encoding="utf-8",
    )
    return decision_file


def _write_human_decision(tmp_path, decision="approved-for-human-case-review"):
    decision_file = tmp_path / "human-review-decision.json"
    decision_file.write_text(
        json.dumps(
            {
                "decision": decision,
                "reason": "Human review decision.",
                "reviewer": "local-reviewer",
            }
        ),
        encoding="utf-8",
    )
    return decision_file


def test_packet_review_gate_cli_blocks_premature_approval(tmp_path):
    session_file = _write_session(tmp_path)
    status_file = _write_status(tmp_path)
    approval_decision_file = _write_approval_decision(tmp_path)
    step_decision_file = _write_step_decision(tmp_path)
    human_decision_file = _write_human_decision(tmp_path)
    json_output = tmp_path / "human-case-review-packet-review-gate.json"
    markdown_output = tmp_path / "human-case-review-packet-review-gate.md"

    result = runner.invoke(
        app,
        [
            "brain-chat-human-case-review-packet-review-gate",
            str(human_decision_file),
            "--session-file",
            str(session_file),
            "--status-file",
            str(status_file),
            "--approval-decision-file",
            str(approval_decision_file),
            "--step-decision-file",
            str(step_decision_file),
            "--json-output",
            str(json_output),
            "--output-file",
            str(markdown_output),
        ],
    )

    assert result.exit_code == 0
    assert "Brain Chat Human Case Review Packet Review Gate" in result.output
    assert "blocked-pending-human-case-review-packet" in result.output
    assert json_output.exists()
    assert markdown_output.exists()

    data = json.loads(json_output.read_text())
    assert data["kind"] == "brain_chat_human_case_review_packet_review_gate"
    assert data["packet_review_status"] == "blocked-pending-human-case-review-packet"
    assert data["human_case_review_ready"] is False
    assert data["effective_human_review_approval_granted"] is False
    assert data["approval_granted"] is False
    assert data["validation_allowed"] is False
    assert data["runtime_execution_allowed"] is False
    assert data["report_submission_allowed"] is False
    assert data["vulnerability_confirmation_allowed"] is False
    assert data["safety"]["human_approval_side_effects"] is False
    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["evidence_collection"] is False
    assert data["safety"]["validation_execution"] is False
    assert data["safety"]["report_submission"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_packet_review_gate_cli_changes_requested(tmp_path):
    session_file = _write_session(tmp_path)
    human_decision_file = _write_human_decision(tmp_path, "changes-requested")

    result = runner.invoke(
        app,
        [
            "brain-chat-human-case-review-packet-review-gate",
            str(human_decision_file),
            "--session-file",
            str(session_file),
        ],
    )

    assert result.exit_code == 0
    assert "changes-requested" in result.output
    assert "Apply requested local changes" in result.output


def test_packet_review_gate_cli_rejected(tmp_path):
    session_file = _write_session(tmp_path)
    human_decision_file = _write_human_decision(tmp_path, "rejected")

    result = runner.invoke(
        app,
        [
            "brain-chat-human-case-review-packet-review-gate",
            str(human_decision_file),
            "--session-file",
            str(session_file),
        ],
    )

    assert result.exit_code == 0
    assert "rejected" in result.output
    assert "Stop this human case-review path" in result.output


def test_packet_review_gate_cli_no_artifacts_keeps_packet_blocked(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    human_decision_file = _write_human_decision(tmp_path)

    result = runner.invoke(
        app,
        [
            "brain-chat-human-case-review-packet-review-gate",
            str(human_decision_file),
        ],
    )

    assert result.exit_code == 0
    assert "blocked-pending-human-case-review-packet" in result.output
    assert "Human case review ready" in result.output
    assert "False" in result.output


def test_packet_review_gate_cli_missing_decision_file_errors(tmp_path):
    result = runner.invoke(
        app,
        [
            "brain-chat-human-case-review-packet-review-gate",
            str(tmp_path / "missing-human-review-decision.json"),
        ],
    )

    assert result.exit_code == 1
    assert "Human review decision JSON not found" in result.output


def test_packet_review_gate_cli_invalid_decision_errors(tmp_path):
    session_file = _write_session(tmp_path)
    human_decision_file = _write_human_decision(tmp_path, "approved")

    result = runner.invoke(
        app,
        [
            "brain-chat-human-case-review-packet-review-gate",
            str(human_decision_file),
            "--session-file",
            str(session_file),
        ],
    )

    assert result.exit_code == 1
    assert "Invalid case intelligence human review decision" in result.output
