from bugintel.core.brain_chat import BrainChatReply
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


def _gate_with(statuses):
    checklist = build_brain_chat_evidence_checklist(
        _session(),
        item_statuses=statuses,
    )
    return build_evidence_checklist_review_gate(checklist)


def test_approval_request_blocks_when_review_gate_is_blocked():
    gate = build_evidence_checklist_review_gate(
        build_brain_chat_evidence_checklist(_session())
    )

    request = build_evidence_approval_request(gate)
    data = request.to_dict()

    assert data["kind"] == "brain_chat_evidence_approval_request"
    assert data["approval_status"] == "blocked-pending-review-gate"
    assert data["gate_status"] == "blocked"
    assert data["validation_approval_ready"] is False
    assert "Do not request validation approval yet." in data["requested_action"]
    assert "7 evidence item(s) are still missing." in data["blockers"]
    assert data["safety"]["approval_granted"] is False
    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["evidence_collection"] is False
    assert data["safety"]["report_submission"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_approval_request_blocks_when_review_gate_needs_review():
    statuses = {label: "collected" for label in LABELS}
    statuses["Authorization decision diff"] = "review-needed"

    request = build_evidence_approval_request(_gate_with(statuses))
    data = request.to_dict()

    assert data["approval_status"] == "blocked-pending-review-gate"
    assert data["gate_status"] == "needs-review"
    assert data["validation_approval_ready"] is False
    assert "1 evidence item(s) still need review." in data["blockers"]


def test_approval_request_ready_when_gate_is_ready():
    statuses = {label: "collected" for label in LABELS}

    request = build_evidence_approval_request(_gate_with(statuses))
    data = request.to_dict()

    assert data["approval_status"] == "ready-for-human-approval"
    assert data["gate_status"] == "ready-for-validation-approval"
    assert data["validation_approval_ready"] is True
    assert data["blockers"] == []
    assert "Request human approval" in data["requested_action"]
    assert "Confirm the target and endpoint" in data["required_human_checks"][0]
    assert "Prepare a human-reviewed validation plan." in data["allowed_after_approval"]
    assert "Do not execute network" in data["rejected_without_approval"][0]


def test_approval_request_markdown_is_readable():
    request = build_evidence_approval_request(
        build_evidence_checklist_review_gate(
            build_brain_chat_evidence_checklist(_session())
        )
    )
    markdown = request.to_markdown()

    assert "# Brain Chat Evidence Approval Request" in markdown
    assert "Approval Status" in markdown
    assert "Required Human Checks" in markdown
    assert "Rejected Without Approval" in markdown
    assert "Safety" in markdown
    assert "\\n" not in markdown
