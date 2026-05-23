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
        json.dumps(
            {
                "items": [
                    {"label": label, "status": status}
                    for label, status in statuses.items()
                ]
            }
        ),
        encoding="utf-8",
    )
    return status_file


def test_approval_request_cli_blocks_missing_by_default(tmp_path):
    session_file = _write_session(tmp_path)
    json_output = tmp_path / "approval-request.json"

    result = runner.invoke(
        app,
        [
            "brain-chat-evidence-approval-request",
            "--session-file",
            str(session_file),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0
    assert "Brain Chat Evidence Approval Request" in result.output
    assert "blocked-pending-review-gate" in result.output
    assert "Do not request validation approval yet." in result.output
    assert json_output.exists()

    data = json.loads(json_output.read_text())
    assert data["kind"] == "brain_chat_evidence_approval_request"
    assert data["approval_status"] == "blocked-pending-review-gate"
    assert data["gate_status"] == "blocked"
    assert data["validation_approval_ready"] is False
    assert data["safety"]["approval_granted"] is False
    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["evidence_collection"] is False
    assert data["safety"]["report_submission"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_approval_request_cli_ready_when_all_collected(tmp_path):
    session_file = _write_session(tmp_path)
    status_file = _write_status(tmp_path, {label: "collected" for label in LABELS})

    result = runner.invoke(
        app,
        [
            "brain-chat-evidence-approval-request",
            str(status_file),
            "--session-file",
            str(session_file),
        ],
    )

    assert result.exit_code == 0
    assert "ready-for-human-approval" in result.output
    assert "ready-for-validation-approval" in result.output
    assert "Request human approval" in result.output
    assert "Approval granted" in result.output
    assert "false" in result.output


def test_approval_request_cli_blocks_needs_review(tmp_path):
    session_file = _write_session(tmp_path)
    statuses = {label: "collected" for label in LABELS}
    statuses["Authorization decision diff"] = "review-needed"
    status_file = _write_status(tmp_path, statuses)

    result = runner.invoke(
        app,
        [
            "brain-chat-evidence-approval-request",
            str(status_file),
            "--session-file",
            str(session_file),
        ],
    )

    assert result.exit_code == 0
    assert "blocked-pending-review-gate" in result.output
    assert "needs-review" in result.output
    assert "1 evidence item(s) still need review." in result.output


def test_approval_request_cli_missing_status_file_errors(tmp_path):
    session_file = _write_session(tmp_path)

    result = runner.invoke(
        app,
        [
            "brain-chat-evidence-approval-request",
            str(tmp_path / "missing.json"),
            "--session-file",
            str(session_file),
        ],
    )

    assert result.exit_code == 1
    assert "Evidence checklist status JSON not found" in result.output
