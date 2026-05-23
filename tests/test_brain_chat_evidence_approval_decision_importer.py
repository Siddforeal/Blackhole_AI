import json

import pytest

from bugintel.core.brain_chat import BrainChatReply
from bugintel.core.brain_chat_evidence_approval_decision_importer import (
    import_evidence_approval_decision_data,
    import_evidence_approval_decision_file,
)
from bugintel.core.brain_chat_evidence_approval_request import (
    build_evidence_approval_request,
)
from bugintel.core.brain_chat_evidence_checklist import build_brain_chat_evidence_checklist
from bugintel.core.brain_chat_evidence_checklist_review_gate import (
    build_evidence_checklist_review_gate,
)
from bugintel.core.brain_chat_session import BrainChatSession, append_brain_chat_turn


LABELS = (
    "Scope and authorization proof for `/api/accounts/123/users/{id}/permissions`",
    "Baseline request/response sample",
    "Redaction checklist",
    "Controlled account / role / object matrix",
    "Authorization decision diff",
    "Identifier source map",
    "Owned / foreign / random response matrix",
)


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


def _approval_request(statuses):
    checklist = build_brain_chat_evidence_checklist(
        _session(),
        item_statuses=statuses,
    )
    gate = build_evidence_checklist_review_gate(checklist)
    return build_evidence_approval_request(gate)


def test_decision_importer_approves_only_ready_request():
    request = _approval_request({label: "collected" for label in LABELS})

    decision = import_evidence_approval_decision_data(
        request,
        {
            "decision": "approved",
            "reason": "All evidence is collected.",
            "reviewer": "local-reviewer",
        },
    )
    data = decision.to_dict()

    assert data["kind"] == "brain_chat_evidence_approval_decision"
    assert data["decision"] == "approved"
    assert data["approval_request_status"] == "ready-for-human-approval"
    assert data["gate_status"] == "ready-for-validation-approval"
    assert data["effective_approval_granted"] is True
    assert "Prepare a human-reviewed non-destructive validation plan." in data["allowed_next_steps"]
    assert data["safety"]["approval_side_effects"] is False
    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["evidence_collection"] is False
    assert data["safety"]["report_submission"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_decision_importer_does_not_approve_blocked_request():
    request = _approval_request({})

    decision = import_evidence_approval_decision_data(
        request,
        {
            "decision": "approved",
            "reason": "Premature approval attempt.",
        },
    )
    data = decision.to_dict()

    assert data["decision"] == "approved"
    assert data["approval_request_status"] == "blocked-pending-review-gate"
    assert data["effective_approval_granted"] is False
    assert "Do not treat this decision as execution approval." in data["rejected_next_steps"]


def test_decision_importer_tracks_changes_requested():
    request = _approval_request({label: "collected" for label in LABELS})

    decision = import_evidence_approval_decision_data(
        request,
        {
            "decision": "changes_requested",
            "reason": "Need redaction notes.",
            "reviewer": "analyst",
        },
    )
    data = decision.to_dict()

    assert data["decision"] == "changes-requested"
    assert data["effective_approval_granted"] is False
    assert data["reviewer"] == "analyst"
    assert "Update checklist evidence statuses and notes." in data["allowed_next_steps"]


def test_decision_importer_tracks_rejection():
    request = _approval_request({label: "collected" for label in LABELS})

    decision = import_evidence_approval_decision_data(
        request,
        {
            "decision": "rejected",
            "reason": "Scope is not confirmed.",
        },
    )
    data = decision.to_dict()

    assert data["decision"] == "rejected"
    assert data["effective_approval_granted"] is False
    assert data["allowed_next_steps"] == []


def test_decision_importer_reads_local_json_file(tmp_path):
    request = _approval_request({label: "collected" for label in LABELS})
    decision_file = tmp_path / "approval-decision.json"
    decision_file.write_text(
        json.dumps(
            {
                "decision": "approved",
                "reason": "Ready.",
                "reviewer": "local",
            }
        ),
        encoding="utf-8",
    )

    decision = import_evidence_approval_decision_file(request, decision_file)
    data = decision.to_dict()

    assert data["source_file"] == str(decision_file)
    assert data["effective_approval_granted"] is True


def test_decision_importer_missing_file_errors(tmp_path):
    request = _approval_request({label: "collected" for label in LABELS})

    with pytest.raises(FileNotFoundError):
        import_evidence_approval_decision_file(request, tmp_path / "missing.json")


def test_decision_importer_invalid_decision_raises():
    request = _approval_request({label: "collected" for label in LABELS})

    with pytest.raises(ValueError, match="Invalid approval decision"):
        import_evidence_approval_decision_data(
            request,
            {"decision": "maybe"},
        )


def test_decision_importer_markdown_is_readable():
    request = _approval_request({})
    decision = import_evidence_approval_decision_data(
        request,
        {"decision": "rejected", "reason": "Not ready."},
    )
    markdown = decision.to_markdown()

    assert "# Brain Chat Evidence Approval Decision" in markdown
    assert "Decision" in markdown
    assert "Rejected Next Steps" in markdown
    assert "Safety" in markdown
    assert "\\n" not in markdown
