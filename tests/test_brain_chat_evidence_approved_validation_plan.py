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


def _decision(statuses, decision_data):
    checklist = build_brain_chat_evidence_checklist(
        _session(),
        item_statuses=statuses,
    )
    gate = build_evidence_checklist_review_gate(checklist)
    request = build_evidence_approval_request(gate)
    return import_evidence_approval_decision_data(request, decision_data)


def test_validation_plan_blocks_without_effective_approval():
    decision = _decision(
        {},
        {
            "decision": "approved",
            "reason": "Premature approval attempt.",
        },
    )

    plan = build_evidence_approved_validation_plan(decision)
    data = plan.to_dict()

    assert data["kind"] == "brain_chat_evidence_approved_validation_plan"
    assert data["plan_status"] == "blocked-pending-effective-approval"
    assert data["decision"] == "approved"
    assert data["effective_approval_granted"] is False
    assert data["validation_allowed"] is False
    assert data["planned_validation_steps"] == []
    assert "Do not execute network" in data["rejected_actions"][0]
    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["evidence_collection"] is False
    assert data["safety"]["validation_execution"] is False
    assert data["safety"]["report_submission"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_validation_plan_ready_when_effective_approval_is_granted():
    decision = _decision(
        {label: "collected" for label in LABELS},
        {
            "decision": "approved",
            "reason": "All evidence collected.",
            "reviewer": "local-reviewer",
        },
    )

    plan = build_evidence_approved_validation_plan(decision)
    data = plan.to_dict()

    assert data["plan_status"] == "ready-for-manual-validation-planning"
    assert data["effective_approval_granted"] is True
    assert data["validation_allowed"] is True
    assert "Prepare a minimal non-destructive validation checklist." in data["planned_validation_steps"]
    assert "Human must approve every runtime validation step separately." in data["required_runtime_guards"]
    assert "Do not execute this plan automatically." in data["rejected_actions"]


def test_validation_plan_blocks_rejected_decision_even_when_gate_ready():
    decision = _decision(
        {label: "collected" for label in LABELS},
        {
            "decision": "rejected",
            "reason": "Scope not approved.",
        },
    )

    plan = build_evidence_approved_validation_plan(decision)
    data = plan.to_dict()

    assert data["plan_status"] == "blocked-pending-effective-approval"
    assert data["decision"] == "rejected"
    assert data["effective_approval_granted"] is False
    assert data["validation_allowed"] is False


def test_validation_plan_markdown_is_readable():
    decision = _decision(
        {},
        {
            "decision": "approved",
            "reason": "Premature approval attempt.",
        },
    )
    plan = build_evidence_approved_validation_plan(decision)
    markdown = plan.to_markdown()

    assert "# Brain Chat Evidence Approved Validation Plan" in markdown
    assert "Plan Status" in markdown
    assert "Required Runtime Guards" in markdown
    assert "Rejected Actions" in markdown
    assert "Safety" in markdown
    assert "\\n" not in markdown
