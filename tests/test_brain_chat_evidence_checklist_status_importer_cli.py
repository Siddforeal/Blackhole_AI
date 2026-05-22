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


def test_brain_chat_evidence_checklist_import_status_cli_reads_local_json(tmp_path):
    session_file = tmp_path / "brain-chat-session.json"
    status_file = tmp_path / "evidence-status.json"
    output_file = tmp_path / "imported-checklist.md"
    json_output = tmp_path / "imported-checklist.json"

    session_file.write_text(json.dumps(_session_data()), encoding="utf-8")
    status_file.write_text(
        json.dumps(
            {
                "items": [
                    {
                        "label": "Authorization decision diff",
                        "status": "review-needed",
                        "notes": "Needs reviewer confirmation.",
                    },
                    {
                        "label": "Baseline request/response sample",
                        "status": "collected",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "brain-chat-evidence-checklist-import-status",
            str(status_file),
            "--session-file",
            str(session_file),
            "--output-file",
            str(output_file),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0
    assert "Brain Chat Evidence Checklist Status Import" in result.output
    assert "[review-needed] Authorization decision diff" in result.output
    assert "[collected] Baseline request/response sample" in result.output
    assert output_file.exists()
    assert json_output.exists()

    data = json.loads(json_output.read_text())
    assert data["kind"] == "brain_chat_evidence_checklist_status_import_result"
    assert data["checklist"]["counts"]["collected"] == 1
    assert data["checklist"]["counts"]["review_needed"] == 1
    assert data["checklist"]["counts"]["missing"] == 5
    assert data["imported"]["unmatched_labels"] == []
    assert data["checklist"]["safety"]["evidence_collection"] is False


def test_brain_chat_evidence_checklist_import_status_cli_defaults_to_current_session(tmp_path, monkeypatch):
    session_file = tmp_path / "brain-chat-session.json"
    status_file = tmp_path / "evidence-status.json"

    session_file.write_text(json.dumps(_session_data()), encoding="utf-8")
    status_file.write_text(
        json.dumps({"Authorization decision diff": "blocked"}),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        [
            "brain-chat-evidence-checklist-import-status",
            str(status_file),
        ],
    )

    assert result.exit_code == 0
    assert "Brain Chat Evidence Checklist Status Import" in result.output
    assert "[blocked] Authorization decision diff" in result.output


def test_brain_chat_evidence_checklist_import_status_cli_missing_status_file_errors(tmp_path):
    session_file = tmp_path / "brain-chat-session.json"
    session_file.write_text(json.dumps(_session_data()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-evidence-checklist-import-status",
            str(tmp_path / "missing.json"),
            "--session-file",
            str(session_file),
        ],
    )

    assert result.exit_code == 1
    assert "Evidence checklist status JSON not found" in result.output


def test_brain_chat_evidence_checklist_import_status_cli_invalid_status_errors(tmp_path):
    session_file = tmp_path / "brain-chat-session.json"
    status_file = tmp_path / "evidence-status.json"

    session_file.write_text(json.dumps(_session_data()), encoding="utf-8")
    status_file.write_text(
        json.dumps(
            {
                "items": [
                    {
                        "label": "Authorization decision diff",
                        "status": "done",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "brain-chat-evidence-checklist-import-status",
            str(status_file),
            "--session-file",
            str(session_file),
        ],
    )

    assert result.exit_code == 1
    assert "Invalid evidence status" in result.output
