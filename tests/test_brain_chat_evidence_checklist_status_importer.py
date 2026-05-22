import json

import pytest

from bugintel.core.brain_chat import BrainChatReply
from bugintel.core.brain_chat_evidence_checklist_status_importer import (
    import_evidence_checklist_status_data,
    import_evidence_checklist_status_file,
)
from bugintel.core.brain_chat_session import BrainChatSession, append_brain_chat_turn


def _reply(question="What evidence do we need?"):
    return BrainChatReply(
        question=question,
        answer="Evidence planning answer.",
        target_name="demo.local",
        focus_endpoint="/api/accounts/123/users/{id}/permissions",
        decision="blocked-pending-scope-and-controls",
        approval_status="blocked-pending-approval",
        execution_gate="blocked-manifest-execution-disabled",
        execution_allowed=False,
    )


def _session():
    session = BrainChatSession()
    session = append_brain_chat_turn(session, _reply("What should I test first?"))
    session = append_brain_chat_turn(session, _reply("What evidence do we need?"))
    return session


def test_status_importer_updates_checklist_from_items_data():
    data = {
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

    result = import_evidence_checklist_status_data(_session(), data)
    output = result.to_dict()
    checklist = output["checklist"]

    assert output["kind"] == "brain_chat_evidence_checklist_status_import_result"
    assert checklist["counts"]["total"] == 7
    assert checklist["counts"]["missing"] == 5
    assert checklist["counts"]["collected"] == 1
    assert checklist["counts"]["review_needed"] == 1
    assert checklist["complete"] is False
    assert output["imported"]["unmatched_labels"] == []
    assert output["imported"]["safety"]["evidence_collection"] is False
    assert output["checklist"]["safety"]["tool_execution"] is False


def test_status_importer_supports_mapping_data_and_unmatched_labels():
    data = {
        "Authorization decision diff": {
            "status": "blocked",
            "notes": "Waiting for controlled account B.",
        },
        "Unknown evidence item": {
            "status": "collected",
        },
    }

    result = import_evidence_checklist_status_data(_session(), data)
    output = result.to_dict()
    checklist = output["checklist"]
    item = next(
        item for item in checklist["items"]
        if item["label"] == "Authorization decision diff"
    )

    assert item["status"] == "blocked"
    assert item["notes"] == "Waiting for controlled account B."
    assert checklist["counts"]["blocked"] == 1
    assert output["imported"]["unmatched_labels"] == ["Unknown evidence item"]


def test_status_importer_reads_local_json_file(tmp_path):
    status_file = tmp_path / "evidence-status.json"
    status_file.write_text(
        json.dumps(
            {
                "items": [
                    {
                        "label": "Redaction checklist",
                        "status": "collected",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    result = import_evidence_checklist_status_file(_session(), status_file)
    output = result.to_dict()

    assert output["imported"]["source_file"] == str(status_file)
    assert output["checklist"]["counts"]["collected"] == 1
    assert output["checklist"]["counts"]["missing"] == 6


def test_status_importer_missing_file_errors(tmp_path):
    with pytest.raises(FileNotFoundError):
        import_evidence_checklist_status_file(_session(), tmp_path / "missing.json")


def test_status_importer_invalid_status_raises():
    with pytest.raises(ValueError, match="Invalid evidence status"):
        import_evidence_checklist_status_data(
            _session(),
            {
                "items": [
                    {
                        "label": "Authorization decision diff",
                        "status": "done",
                    }
                ]
            },
        )
