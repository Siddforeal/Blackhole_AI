import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


LABELS = (
    "Scope and authorization proof for `/api/accounts/123/users/{id}/permissions`",
    "Baseline request/response sample",
    "Redaction checklist",
    "Controlled account / role / object matrix",
    "Authorization decision diff",
    "Identifier source map",
    "Owned / foreign / random response matrix",
)


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


def _write_status(tmp_path, statuses):
    status_file = tmp_path / "evidence-status.json"
    status_file.write_text(
        json.dumps({"items": [{"label": label, "status": status} for label, status in statuses.items()]}),
        encoding="utf-8",
    )
    return status_file


def _write_decision(tmp_path, decision, reason="Ready.", reviewer="local-reviewer"):
    decision_file = tmp_path / "approval-decision.json"
    decision_file.write_text(
        json.dumps(
            {
                "decision": decision,
                "reason": reason,
                "reviewer": reviewer,
            }
        ),
        encoding="utf-8",
    )
    return decision_file


def test_approval_decision_import_cli_grants_effective_approval_only_when_ready(tmp_path):
    session_file = _write_session(tmp_path)
    status_file = _write_status(tmp_path, {label: "collected" for label in LABELS})
    decision_file = _write_decision(tmp_path, "approved")
    json_output = tmp_path / "approval-decision-result.json"

    result = runner.invoke(
        app,
        [
            "brain-chat-evidence-approval-decision-import",
            str(decision_file),
            "--status-file",
            str(status_file),
            "--session-file",
            str(session_file),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0
    assert "Brain Chat Evidence Approval Decision" in result.output
    assert "approved" in result.output
    assert "Effective approval granted" in result.output
    assert "True" in result.output
    assert json_output.exists()

    data = json.loads(json_output.read_text())
    assert data["kind"] == "brain_chat_evidence_approval_decision"
    assert data["decision"] == "approved"
    assert data["effective_approval_granted"] is True
    assert data["approval_request_status"] == "ready-for-human-approval"
    assert data["gate_status"] == "ready-for-validation-approval"
    assert data["safety"]["approval_side_effects"] is False
    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["evidence_collection"] is False
    assert data["safety"]["report_submission"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_approval_decision_import_cli_does_not_approve_blocked_request(tmp_path):
    session_file = _write_session(tmp_path)
    decision_file = _write_decision(tmp_path, "approved", "Premature approval attempt.")

    result = runner.invoke(
        app,
        [
            "brain-chat-evidence-approval-decision-import",
            str(decision_file),
            "--session-file",
            str(session_file),
        ],
    )

    assert result.exit_code == 0
    assert "approved" in result.output
    assert "Effective approval granted" in result.output
    assert "False" in result.output
    assert "Do not treat this decision as execution approval." in result.output


def test_approval_decision_import_cli_tracks_changes_requested(tmp_path):
    session_file = _write_session(tmp_path)
    status_file = _write_status(tmp_path, {label: "collected" for label in LABELS})
    decision_file = _write_decision(tmp_path, "changes-requested", "Need redaction notes.")

    result = runner.invoke(
        app,
        [
            "brain-chat-evidence-approval-decision-import",
            str(decision_file),
            "--status-file",
            str(status_file),
            "--session-file",
            str(session_file),
        ],
    )

    assert result.exit_code == 0
    assert "changes-requested" in result.output
    assert "Update checklist evidence statuses and notes." in result.output
    assert "Need redaction notes." in result.output


def test_approval_decision_import_cli_missing_decision_file_errors(tmp_path):
    session_file = _write_session(tmp_path)

    result = runner.invoke(
        app,
        [
            "brain-chat-evidence-approval-decision-import",
            str(tmp_path / "missing.json"),
            "--session-file",
            str(session_file),
        ],
    )

    assert result.exit_code == 1
    assert "Evidence approval decision JSON not found" in result.output


def test_approval_decision_import_cli_invalid_decision_errors(tmp_path):
    session_file = _write_session(tmp_path)
    decision_file = _write_decision(tmp_path, "maybe")

    result = runner.invoke(
        app,
        [
            "brain-chat-evidence-approval-decision-import",
            str(decision_file),
            "--session-file",
            str(session_file),
        ],
    )

    assert result.exit_code == 1
    assert "Invalid approval decision" in result.output
