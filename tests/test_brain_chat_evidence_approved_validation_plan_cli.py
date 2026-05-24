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


def _write_decision(tmp_path, decision="approved"):
    decision_file = tmp_path / "approval-decision.json"
    decision_file.write_text(
        json.dumps(
            {
                "decision": decision,
                "reason": "Local reviewer decision.",
                "reviewer": "local-reviewer",
            }
        ),
        encoding="utf-8",
    )
    return decision_file


def test_approved_validation_plan_cli_blocks_without_effective_approval(tmp_path):
    session_file = _write_session(tmp_path)
    decision_file = _write_decision(tmp_path, "approved")
    json_output = tmp_path / "validation-plan.json"

    result = runner.invoke(
        app,
        [
            "brain-chat-evidence-approved-validation-plan",
            str(decision_file),
            "--session-file",
            str(session_file),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0
    assert "Brain Chat Evidence Approved Validation Plan" in result.output
    assert "blocked-pending-effective-approval" in result.output
    assert "Validation allowed" in result.output
    assert "False" in result.output
    assert json_output.exists()

    data = json.loads(json_output.read_text())
    assert data["kind"] == "brain_chat_evidence_approved_validation_plan"
    assert data["plan_status"] == "blocked-pending-effective-approval"
    assert data["effective_approval_granted"] is False
    assert data["validation_allowed"] is False
    assert data["planned_validation_steps"] == []
    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["evidence_collection"] is False
    assert data["safety"]["validation_execution"] is False
    assert data["safety"]["report_submission"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_approved_validation_plan_cli_ready_when_effective_approval_granted(tmp_path):
    session_file = _write_session(tmp_path)
    status_file = _write_status(tmp_path, {label: "collected" for label in LABELS})
    decision_file = _write_decision(tmp_path, "approved")

    result = runner.invoke(
        app,
        [
            "brain-chat-evidence-approved-validation-plan",
            str(decision_file),
            "--status-file",
            str(status_file),
            "--session-file",
            str(session_file),
        ],
    )

    assert result.exit_code == 0
    assert "ready-for-manual-validation-planning" in result.output
    assert "Validation allowed" in result.output
    assert "True" in result.output
    assert "Prepare a minimal non-destructive validation checklist." in result.output
    assert "Do not execute this plan automatically." in result.output


def test_approved_validation_plan_cli_rejects_missing_decision_file(tmp_path):
    session_file = _write_session(tmp_path)

    result = runner.invoke(
        app,
        [
            "brain-chat-evidence-approved-validation-plan",
            str(tmp_path / "missing.json"),
            "--session-file",
            str(session_file),
        ],
    )

    assert result.exit_code == 1
    assert "Evidence approval decision JSON not found" in result.output


def test_approved_validation_plan_cli_invalid_decision_errors(tmp_path):
    session_file = _write_session(tmp_path)
    decision_file = _write_decision(tmp_path, "maybe")

    result = runner.invoke(
        app,
        [
            "brain-chat-evidence-approved-validation-plan",
            str(decision_file),
            "--session-file",
            str(session_file),
        ],
    )

    assert result.exit_code == 1
    assert "Invalid approval decision" in result.output
