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


def _write_approval_decision(tmp_path, decision="approved"):
    decision_file = tmp_path / "approval-decision.json"
    decision_file.write_text(
        json.dumps(
            {
                "decision": decision,
                "reason": "Evidence approval decision.",
                "reviewer": "local-reviewer",
            }
        ),
        encoding="utf-8",
    )
    return decision_file


def _write_step_decision(tmp_path, decision="approved"):
    decision_file = tmp_path / "validation-step-decision.json"
    decision_file.write_text(
        json.dumps(
            {
                "decision": decision,
                "reason": "Validation step approval decision.",
                "reviewer": "local-reviewer",
            }
        ),
        encoding="utf-8",
    )
    return decision_file


def test_case_intelligence_status_cli_summarizes_full_blocked_chain(tmp_path):
    session_file = _write_session(tmp_path)
    status_file = _write_status(
        tmp_path,
        {
            "Baseline request/response sample": "collected",
            "Authorization decision diff": "review-needed",
        },
    )
    approval_decision_file = _write_approval_decision(tmp_path, "approved")
    step_decision_file = _write_step_decision(tmp_path, "approved")
    json_output = tmp_path / "case-intelligence.json"

    result = runner.invoke(
        app,
        [
            "brain-chat-case-intelligence-status",
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
        ],
    )

    assert result.exit_code == 0
    assert "Brain Chat Case Intelligence Status Summary" in result.output
    assert "execution-gate-proposal-review" in result.output
    assert "blocked-pending-effective-step-approval" in result.output
    assert "Collect or mark the missing local evidence items" in result.output
    assert json_output.exists()

    data = json.loads(json_output.read_text())
    assert data["kind"] == "brain_chat_case_intelligence_status_summary"
    assert data["target_name"] == "demo.local"
    assert data["current_stage"] == "execution-gate-proposal-review"
    assert data["current_status"] == "blocked-pending-effective-step-approval"
    assert data["blocked"] is True
    assert data["validation_allowed"] is False
    assert data["runtime_execution_allowed"] is False
    assert data["report_submission_allowed"] is False
    assert data["vulnerability_confirmation_allowed"] is False
    assert data["evidence_counts"]["missing"] == 5
    assert len(data["missing_evidence"]) == 5
    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["evidence_collection"] is False
    assert data["safety"]["validation_execution"] is False
    assert data["safety"]["report_submission"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_case_intelligence_status_cli_session_only(tmp_path):
    session_file = _write_session(tmp_path)

    result = runner.invoke(
        app,
        [
            "brain-chat-case-intelligence-status",
            "--session-file",
            str(session_file),
        ],
    )

    assert result.exit_code == 0
    assert "demo.local" in result.output
    assert "evidence-approval-request" in result.output
    assert "Validation allowed" in result.output
    assert "False" in result.output


def test_case_intelligence_status_cli_no_artifacts_is_safe(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["brain-chat-case-intelligence-status"])

    assert result.exit_code == 0
    assert "no-local-case-artifacts" in result.output
    assert "unknown" in result.output
    assert "Runtime execution allowed" in result.output
    assert "False" in result.output


def test_case_intelligence_status_cli_missing_session_file_errors(tmp_path):
    result = runner.invoke(
        app,
        [
            "brain-chat-case-intelligence-status",
            "--session-file",
            str(tmp_path / "missing-session.json"),
        ],
    )

    assert result.exit_code == 1
    assert "Brain chat session JSON not found" in result.output


def test_case_intelligence_status_cli_invalid_step_decision_errors(tmp_path):
    session_file = _write_session(tmp_path)
    approval_decision_file = _write_approval_decision(tmp_path, "approved")
    step_decision_file = _write_step_decision(tmp_path, "maybe")

    result = runner.invoke(
        app,
        [
            "brain-chat-case-intelligence-status",
            "--session-file",
            str(session_file),
            "--approval-decision-file",
            str(approval_decision_file),
            "--step-decision-file",
            str(step_decision_file),
        ],
    )

    assert result.exit_code == 1
    assert "Invalid validation step approval decision" in result.output
