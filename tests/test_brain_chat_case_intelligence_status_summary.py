from bugintel.core.brain_chat import BrainChatReply
from bugintel.core.brain_chat_case_intelligence_status_summary import (
    build_case_intelligence_status_summary,
)
from bugintel.core.brain_chat_evidence_approval_decision_importer import (
    import_evidence_approval_decision_data,
)
from bugintel.core.brain_chat_evidence_approval_request import build_evidence_approval_request
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


def _full_blocked_chain():
    session = _session()
    checklist = build_brain_chat_evidence_checklist(
        session,
        item_statuses={
            "Baseline request/response sample": "collected",
            "Authorization decision diff": "review-needed",
        },
    )
    evidence_gate = build_evidence_checklist_review_gate(checklist)
    approval_request = build_evidence_approval_request(evidence_gate)
    approval_decision = import_evidence_approval_decision_data(
        approval_request,
        {
            "decision": "approved",
            "reason": "Testing premature approval.",
        },
    )
    validation_plan = build_evidence_approved_validation_plan(approval_decision)
    step_gate = build_validation_plan_step_review_gate(validation_plan)
    step_request = build_validation_step_approval_request(step_gate)
    step_decision = import_validation_step_approval_decision_data(
        step_request,
        {
            "decision": "approved",
            "reason": "Testing premature step approval.",
        },
    )
    execution_proposal = build_validation_step_execution_gate_proposal(step_decision)
    execution_review = build_execution_gate_proposal_review_packet(execution_proposal)
    return {
        "session": session,
        "checklist": checklist,
        "evidence_review_gate": evidence_gate,
        "approval_request": approval_request,
        "approval_decision": approval_decision,
        "validation_plan": validation_plan,
        "step_review_gate": step_gate,
        "step_approval_request": step_request,
        "step_approval_decision": step_decision,
        "execution_gate_proposal": execution_proposal,
        "execution_gate_review_packet": execution_review,
    }


def test_case_intelligence_summary_reports_blocked_latest_stage():
    summary = build_case_intelligence_status_summary(**_full_blocked_chain())
    data = summary.to_dict()

    assert data["kind"] == "brain_chat_case_intelligence_status_summary"
    assert data["target_name"] == "demo.local"
    assert data["focus_endpoint"] == "/api/accounts/123/users/{id}/permissions"
    assert data["current_stage"] == "execution-gate-proposal-review"
    assert data["current_status"] == "blocked-pending-effective-step-approval"
    assert data["blocked"] is True
    assert data["validation_allowed"] is False
    assert data["runtime_execution_allowed"] is False
    assert data["report_submission_allowed"] is False
    assert data["vulnerability_confirmation_allowed"] is False
    assert "Collect or mark the missing local evidence items" in data["safest_next_action"]
    assert data["evidence_counts"]["total"] == 7
    assert data["evidence_counts"]["missing"] == 5
    assert len(data["missing_evidence"]) == 5
    assert any(
        item["stage"] == "execution-gate-proposal-review"
        for item in data["chain_position"]
    )
    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["evidence_collection"] is False
    assert data["safety"]["validation_execution"] is False
    assert data["safety"]["report_submission"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_case_intelligence_summary_from_session_only_is_safe():
    summary = build_case_intelligence_status_summary(session=_session())
    data = summary.to_dict()

    assert data["current_stage"] == "session"
    assert data["target_name"] == "demo.local"
    assert data["focus_endpoint"] == "/api/accounts/123/users/{id}/permissions"
    assert data["validation_allowed"] is False
    assert data["runtime_execution_allowed"] is False
    assert data["report_submission_allowed"] is False
    assert data["vulnerability_confirmation_allowed"] is False


def test_case_intelligence_summary_no_artifacts_is_safe():
    summary = build_case_intelligence_status_summary()
    data = summary.to_dict()

    assert data["target_name"] == "unknown"
    assert data["current_stage"] == "case"
    assert data["current_status"] == "no-local-case-artifacts"
    assert data["blocked"] is True
    assert data["runtime_execution_allowed"] is False


def test_case_intelligence_summary_markdown_is_readable():
    summary = build_case_intelligence_status_summary(**_full_blocked_chain())
    markdown = summary.to_markdown()

    assert "# Brain Chat Case Intelligence Status Summary" in markdown
    assert "Current State" in markdown
    assert "Safest Next Action" in markdown
    assert "Blockers" in markdown
    assert "Missing Evidence" in markdown
    assert "Chain Position" in markdown
    assert "Safety" in markdown
    assert "\\n" not in markdown
