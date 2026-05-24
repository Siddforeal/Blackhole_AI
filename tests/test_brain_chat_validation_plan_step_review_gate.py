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


def _plan(statuses, decision_data):
    checklist = build_brain_chat_evidence_checklist(
        _session(),
        item_statuses=statuses,
    )
    gate = build_evidence_checklist_review_gate(checklist)
    request = build_evidence_approval_request(gate)
    decision = import_evidence_approval_decision_data(request, decision_data)
    return build_evidence_approved_validation_plan(decision)


def test_step_review_gate_blocks_without_effective_approval():
    plan = _plan(
        {},
        {
            "decision": "approved",
            "reason": "Premature approval attempt.",
        },
    )

    gate = build_validation_plan_step_review_gate(plan)
    data = gate.to_dict()

    assert data["kind"] == "brain_chat_validation_plan_step_review_gate"
    assert data["gate_status"] == "blocked-pending-approved-validation-plan"
    assert data["validation_allowed"] is False
    assert data["step_review_ready"] is False
    assert data["counts"]["total"] == 0
    assert "Effective approval is not granted." in data["blocking_reasons"]
    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["evidence_collection"] is False
    assert data["safety"]["validation_execution"] is False
    assert data["safety"]["report_submission"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_step_review_gate_reviews_ready_plan_steps():
    plan = _plan(
        {label: "collected" for label in LABELS},
        {
            "decision": "approved",
            "reason": "Ready.",
        },
    )

    gate = build_validation_plan_step_review_gate(plan)
    data = gate.to_dict()

    assert data["gate_status"] == "needs-scope-check"
    assert data["validation_allowed"] is True
    assert data["step_review_ready"] is False
    assert data["counts"]["total"] == 5
    assert data["counts"]["allowed_for_manual_review"] >= 1
    assert data["counts"]["needs_scope_check"] >= 1
    assert data["counts"]["rejected_unsafe"] == 0
    assert any(
        item["status"] == "allowed-for-manual-review"
        for item in data["reviewed_steps"]
    )
    assert any(
        item["status"] == "needs-scope-check"
        for item in data["reviewed_steps"]
    )


def test_step_review_gate_rejects_unsafe_step():
    plan = _plan(
        {label: "collected" for label in LABELS},
        {
            "decision": "approved",
            "reason": "Ready.",
        },
    )
    unsafe_plan = replace(
        plan,
        planned_validation_steps=(
            *plan.planned_validation_steps,
            "Run high-volume destructive exploit traffic against the target.",
        ),
    )

    gate = build_validation_plan_step_review_gate(unsafe_plan)
    data = gate.to_dict()

    assert data["gate_status"] == "blocked-unsafe-validation-step"
    assert data["step_review_ready"] is False
    assert data["counts"]["rejected_unsafe"] == 1
    assert any(
        item["status"] == "rejected-unsafe"
        for item in data["reviewed_steps"]
    )


def test_step_review_gate_can_be_ready_for_manual_step_review():
    plan = _plan(
        {label: "collected" for label in LABELS},
        {
            "decision": "approved",
            "reason": "Ready.",
        },
    )
    simple_plan = replace(
        plan,
        planned_validation_steps=(
            "Prepare a minimal non-destructive validation checklist.",
        ),
    )

    gate = build_validation_plan_step_review_gate(simple_plan)
    data = gate.to_dict()

    assert data["gate_status"] == "ready-for-manual-step-review"
    assert data["step_review_ready"] is True
    assert data["counts"]["total"] == 1
    assert data["counts"]["allowed_for_manual_review"] == 1
    assert data["counts"]["needs_scope_check"] == 0
    assert data["counts"]["rejected_unsafe"] == 0


def test_step_review_gate_markdown_is_readable():
    plan = _plan(
        {},
        {
            "decision": "approved",
            "reason": "Premature approval attempt.",
        },
    )
    gate = build_validation_plan_step_review_gate(plan)
    markdown = gate.to_markdown()

    assert "# Brain Chat Validation Plan Step Review Gate" in markdown
    assert "Gate Status" in markdown
    assert "Reviewed Steps" in markdown
    assert "Rejected Actions" in markdown
    assert "Safety" in markdown
    assert "\\n" not in markdown
