import pytest

from bugintel.core.brain_chat import BrainChatReply
from bugintel.core.brain_chat_evidence_checklist import (
    build_brain_chat_evidence_checklist,
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


def test_brain_chat_evidence_checklist_defaults_required_evidence_to_missing():
    checklist = build_brain_chat_evidence_checklist(_session())
    data = checklist.to_dict()

    assert data["kind"] == "brain_chat_evidence_checklist"
    assert data["target_name"] == "demo.local"
    assert data["focus_endpoint"] == "/api/accounts/123/users/{id}/permissions"
    assert data["review_status"] == "blocked-review"
    assert data["reportable"] is False
    assert data["execution_allowed"] is False
    assert data["counts"]["total"] == 7
    assert data["counts"]["missing"] == 7
    assert data["counts"]["collected"] == 0
    assert data["complete"] is False
    assert "Dashboard state is not reportable by itself." in data["blockers"]
    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["evidence_collection"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_brain_chat_evidence_checklist_can_track_statuses_and_notes():
    label = "Authorization decision diff"
    checklist = build_brain_chat_evidence_checklist(
        _session(),
        item_statuses={label: "review_needed"},
        item_notes={label: "Needs reviewer confirmation."},
    )
    data = checklist.to_dict()
    item = next(item for item in data["items"] if item["label"] == label)

    assert item["status"] == "review-needed"
    assert item["notes"] == "Needs reviewer confirmation."
    assert data["counts"]["review_needed"] == 1
    assert data["counts"]["missing"] == 6


def test_brain_chat_evidence_checklist_rejects_invalid_status():
    with pytest.raises(ValueError, match="Invalid evidence status"):
        build_brain_chat_evidence_checklist(
            _session(),
            item_statuses={"Authorization decision diff": "done"},
        )


def test_brain_chat_evidence_checklist_markdown_is_readable():
    checklist = build_brain_chat_evidence_checklist(_session())
    markdown = checklist.to_markdown()

    assert "# Brain Chat Evidence Checklist" in markdown
    assert "Evidence Items" in markdown
    assert "[missing] Authorization decision diff" in markdown
    assert "Safety" in markdown
    assert "\\n" not in markdown
