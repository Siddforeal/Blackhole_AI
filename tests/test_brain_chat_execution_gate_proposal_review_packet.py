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
from bugintel.core.brain_chat_execution_gate_proposal_review_packet import (
    build_execution_gate_proposal_review_packet,
)
from bugintel.core.brain_chat_session import BrainChatSession, append_brain_chat_turn
from bugintel.core.brain_chat_validation_plan_step_review_gate import (
    build_validation_plan_step_review_gate,
)
from bugintel.core.brain_chat_validation_step_approval_decision_importer import (
    import_validation_step_approval_decision_data,
)
from bugintel.core.brain_chat_validation_step_approval_request import (
    build_validation_step_approval_request,
)
from bugintel.core.brain_chat_validation_step_execution_gate_proposal import (
    build_validation_step_execution_gate_proposal,
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


def _proposal(statuses, evidence_decision_data, planned_steps=None, step_decision_data=None):
    checklist = build_brain_chat_evidence_checklist(
        _session(),
        item_statuses=statuses,
    )
    gate = build_evidence_checklist_review_gate(checklist)
    approval_request = build_evidence_approval_request(gate)
    evidence_decision = import_evidence_approval_decision_data(
        approval_request,
        evidence_decision_data,
    )
    plan = build_evidence_approved_validation_plan(evidence_decision)
    if planned_steps is not None:
        plan = replace(plan, planned_validation_steps=planned_steps)
    step_gate = build_validation_plan_step_review_gate(plan)
    step_request = build_validation_step_approval_request(step_gate)
    step_decision = import_validation_step_approval_decision_data(
        step_request,
        step_decision_data or {
            "decision": "approved",
            "reason": "Step approval.",
        },
    )
    return build_validation_step_execution_gate_proposal(step_decision)


def test_review_packet_blocks_without_effective_step_approval():
    proposal = _proposal(
        {},
        {
            "decision": "approved",
            "reason": "Premature evidence approval.",
        },
    )

    packet = build_execution_gate_proposal_review_packet(proposal)
    data = packet.to_dict()

    assert data["kind"] == "brain_chat_execution_gate_proposal_review_packet"
    assert data["review_status"] == "blocked-pending-effective-step-approval"
    assert data["proposal_status"] == "blocked-pending-effective-step-approval"
    assert data["effective_step_approval_granted"] is False
    assert data["execution_gate_proposal_ready"] is False
    assert data["design_review_ready"] is False
    assert "Effective validation-step approval is not granted." in data["blockers"]
    assert data["safety"]["execution_gate_created"] is False
    assert data["safety"]["runtime_execution_allowed"] is False
    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["evidence_collection"] is False
    assert data["safety"]["validation_execution"] is False
    assert data["safety"]["report_submission"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_review_packet_ready_when_effective_proposal_has_all_safeguards():
    proposal = _proposal(
        {label: "collected" for label in LABELS},
        {
            "decision": "approved",
            "reason": "Evidence ready.",
        },
        planned_steps=("Prepare a minimal non-destructive validation checklist.",),
    )

    packet = build_execution_gate_proposal_review_packet(proposal)
    data = packet.to_dict()

    assert data["review_status"] == "ready-for-execution-gate-design-review"
    assert data["effective_step_approval_granted"] is True
    assert data["execution_gate_proposal_ready"] is True
    assert data["design_review_ready"] is True
    assert data["runtime_execution_allowed"] is False
    assert data["blockers"] == []
    assert data["human_review_items"] == []
    assert data["approved_steps"] == ["Prepare a minimal non-destructive validation checklist."]


def test_review_packet_needs_human_review_when_safeguards_are_incomplete():
    proposal = _proposal(
        {label: "collected" for label in LABELS},
        {
            "decision": "approved",
            "reason": "Evidence ready.",
        },
        planned_steps=("Prepare a minimal non-destructive validation checklist.",),
    )
    incomplete = replace(
        proposal,
        proposed_execution_gate_requirements=(
            "Require explicit human approval for the exact runtime command or browser action.",
            "Require scope confirmation immediately before runtime.",
        ),
    )

    packet = build_execution_gate_proposal_review_packet(incomplete)
    data = packet.to_dict()

    assert data["review_status"] == "needs-human-review"
    assert data["design_review_ready"] is False
    assert data["blockers"] == []
    assert any("missing safeguards" in item for item in data["human_review_items"])


def test_review_packet_markdown_is_readable():
    proposal = _proposal(
        {},
        {
            "decision": "approved",
            "reason": "Premature evidence approval.",
        },
    )
    packet = build_execution_gate_proposal_review_packet(proposal)
    markdown = packet.to_markdown()

    assert "# Brain Chat Execution Gate Proposal Review Packet" in markdown
    assert "Review Status" in markdown
    assert "Proposal Requirements" in markdown
    assert "Runtime Guards" in markdown
    assert "Rejected Actions" in markdown
    assert "Safety" in markdown
    assert "\\n" not in markdown
