from dataclasses import replace

from bugintel.core.brain_chat import BrainChatReply
from bugintel.core.brain_chat_evidence_approval_decision_importer import (
    import_evidence_approval_decision_data,
)
from bugintel.core.brain_chat_evidence_approval_request import (
    build_evidence_approval_request,
)
from bugintel.core.brain_chat_evidence_approved_validation_plan import (
    build_evidence_approved_validation_plan,
)
from bugintel.core.brain_chat_evidence_checklist import build_brain_chat_evidence_checklist
from bugintel.core.brain_chat_evidence_checklist_review_gate import (
    build_evidence_checklist_review_gate,
)
from bugintel.core.brain_chat_session import BrainChatSession, append_brain_chat_turn
from bugintel.core.brain_chat_validation_plan_step_review_gate import (
    build_validation_plan_step_review_gate,
)
from bugintel.core.brain_chat_validation_step_approval_request import (
    build_validation_step_approval_request,
)


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


def _step_gate(statuses, decision_data, planned_steps=None):
    checklist = build_brain_chat_evidence_checklist(
        _session(),
        item_statuses=statuses,
    )
    gate = build_evidence_checklist_review_gate(checklist)
    approval_request = build_evidence_approval_request(gate)
    decision = import_evidence_approval_decision_data(approval_request, decision_data)
    plan = build_evidence_approved_validation_plan(decision)
    if planned_steps is not None:
        plan = replace(plan, planned_validation_steps=planned_steps)
    return build_validation_plan_step_review_gate(plan)


def test_step_approval_request_blocks_when_step_gate_is_blocked():
    step_gate = _step_gate(
        {},
        {
            "decision": "approved",
            "reason": "Premature approval attempt.",
        },
    )

    request = build_validation_step_approval_request(step_gate)
    data = request.to_dict()

    assert data["kind"] == "brain_chat_validation_step_approval_request"
    assert data["request_status"] == "blocked-pending-step-review-gate"
    assert data["gate_status"] == "blocked-pending-approved-validation-plan"
    assert data["step_review_ready"] is False
    assert data["validation_allowed"] is False
    assert data["steps_for_human_approval"] == []
    assert "Effective approval is not granted." in data["blockers"]
    assert data["safety"]["step_approval_granted"] is False
    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["evidence_collection"] is False
    assert data["safety"]["validation_execution"] is False
    assert data["safety"]["report_submission"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_step_approval_request_blocks_when_scope_check_is_needed():
    step_gate = _step_gate(
        {label: "collected" for label in LABELS},
        {
            "decision": "approved",
            "reason": "Ready.",
        },
    )

    request = build_validation_step_approval_request(step_gate)
    data = request.to_dict()

    assert data["request_status"] == "blocked-pending-step-review-gate"
    assert data["gate_status"] == "needs-scope-check"
    assert data["step_review_ready"] is False
    assert data["reviewed_step_count"] == 5
    assert any("validation step(s) need scope check" in item for item in data["blockers"])


def test_step_approval_request_ready_when_step_gate_is_ready():
    step_gate = _step_gate(
        {label: "collected" for label in LABELS},
        {
            "decision": "approved",
            "reason": "Ready.",
        },
        planned_steps=("Prepare a minimal non-destructive validation checklist.",),
    )

    request = build_validation_step_approval_request(step_gate)
    data = request.to_dict()

    assert data["request_status"] == "ready-for-human-step-approval"
    assert data["gate_status"] == "ready-for-manual-step-review"
    assert data["step_review_ready"] is True
    assert data["validation_allowed"] is True
    assert data["reviewed_step_count"] == 1
    assert data["blockers"] == []
    assert data["steps_for_human_approval"] == [
        "Prepare a minimal non-destructive validation checklist."
    ]
    assert "Request human approval" in data["requested_action"]


def test_step_approval_request_markdown_is_readable():
    step_gate = _step_gate(
        {},
        {
            "decision": "approved",
            "reason": "Premature approval attempt.",
        },
    )
    request = build_validation_step_approval_request(step_gate)
    markdown = request.to_markdown()

    assert "# Brain Chat Validation Step Approval Request" in markdown
    assert "Request Status" in markdown
    assert "Steps For Human Approval" in markdown
    assert "Required Human Checks" in markdown
    assert "Rejected Without Approval" in markdown
    assert "Safety" in markdown
    assert "\\n" not in markdown
