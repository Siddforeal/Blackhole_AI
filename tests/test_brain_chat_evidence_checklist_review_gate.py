from bugintel.core.brain_chat import BrainChatReply
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


def _checklist_with(statuses):
    return build_brain_chat_evidence_checklist(
        _session(),
        item_statuses=statuses,
    )


def test_evidence_checklist_review_gate_blocks_missing_evidence():
    checklist = build_brain_chat_evidence_checklist(_session())
    gate = build_evidence_checklist_review_gate(checklist)
    data = gate.to_dict()

    assert data["kind"] == "brain_chat_evidence_checklist_review_gate"
    assert data["gate_status"] == "blocked"
    assert data["validation_approval_ready"] is False
    assert data["counts"]["missing"] == 7
    assert "7 evidence item(s) are still missing." in data["blocking_reasons"]
    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["evidence_collection"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_evidence_checklist_review_gate_needs_review_when_review_items_remain():
    statuses = {label: "collected" for label in LABELS}
    statuses["Authorization decision diff"] = "review-needed"

    gate = build_evidence_checklist_review_gate(_checklist_with(statuses))
    data = gate.to_dict()

    assert data["gate_status"] == "needs-review"
    assert data["validation_approval_ready"] is False
    assert data["counts"]["missing"] == 0
    assert data["counts"]["review_needed"] == 1
    assert "1 evidence item(s) still need review." in data["review_reasons"]


def test_evidence_checklist_review_gate_blocks_blocked_items():
    statuses = {label: "collected" for label in LABELS}
    statuses["Authorization decision diff"] = "blocked"

    gate = build_evidence_checklist_review_gate(_checklist_with(statuses))
    data = gate.to_dict()

    assert data["gate_status"] == "blocked"
    assert data["validation_approval_ready"] is False
    assert data["counts"]["blocked"] == 1
    assert "1 evidence item(s) are blocked." in data["blocking_reasons"]


def test_evidence_checklist_review_gate_ready_when_all_collected():
    statuses = {label: "collected" for label in LABELS}

    gate = build_evidence_checklist_review_gate(_checklist_with(statuses))
    data = gate.to_dict()

    assert data["gate_status"] == "ready-for-validation-approval"
    assert data["validation_approval_ready"] is True
    assert data["checklist_complete"] is True
    assert data["counts"]["collected"] == 7
    assert data["blocking_reasons"] == []
    assert data["review_reasons"] == []
    assert "Confirm scope and authorization" in data["approval_requirements"][0]


def test_evidence_checklist_review_gate_markdown_is_readable():
    checklist = build_brain_chat_evidence_checklist(_session())
    gate = build_evidence_checklist_review_gate(checklist)
    markdown = gate.to_markdown()

    assert "# Brain Chat Evidence Checklist Review Gate" in markdown
    assert "Gate Decision" in markdown
    assert "Approval Requirements" in markdown
    assert "Safety" in markdown
    assert "\\n" not in markdown
