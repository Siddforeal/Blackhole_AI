from dataclasses import replace

from bugintel.core.brain_chat_case_intelligence_briefing_export import (
    build_case_intelligence_briefing_export,
)
from bugintel.core.brain_chat_case_intelligence_briefing_review_gate import (
    build_case_intelligence_briefing_review_gate,
)
from bugintel.core.brain_chat_case_intelligence_human_review_request import (
    build_case_intelligence_human_review_request,
)
from bugintel.core.brain_chat_case_intelligence_status_summary import (
    BrainChatCaseIntelligenceStatusSummary,
    CaseChainPosition,
)


def _blocked_summary():
    return BrainChatCaseIntelligenceStatusSummary(
        target_name="demo.local",
        focus_endpoint="/api/accounts/123/users/{id}/permissions",
        current_stage="execution-gate-proposal-review",
        current_status="blocked-pending-effective-step-approval",
        blocked=True,
        validation_allowed=False,
        runtime_execution_allowed=False,
        report_submission_allowed=False,
        vulnerability_confirmation_allowed=False,
        safest_next_action="Collect or mark the missing local evidence items before requesting validation or approval.",
        blockers=(
            "Effective validation-step approval is not granted.",
            "Execution-gate proposal is not ready.",
        ),
        missing_evidence=(
            "Scope and authorization proof for `/api/accounts/123/users/{id}/permissions`",
            "Redaction checklist",
        ),
        chain_position=(
            CaseChainPosition("session", "not_executed", False),
            CaseChainPosition("execution-gate-proposal-review", "blocked-pending-effective-step-approval", False),
        ),
        evidence_counts={
            "total": 7,
            "missing": 2,
            "collected": 1,
            "review-needed": 1,
            "blocked": 0,
        },
    )


def _ready_summary():
    return BrainChatCaseIntelligenceStatusSummary(
        target_name="demo.local",
        focus_endpoint="/api/accounts/123/users/{id}/permissions",
        current_stage="case-intelligence-briefing-export",
        current_status="planning-only",
        blocked=False,
        validation_allowed=False,
        runtime_execution_allowed=False,
        report_submission_allowed=False,
        vulnerability_confirmation_allowed=False,
        safest_next_action="Continue with local human review only.",
        blockers=(),
        missing_evidence=(),
        chain_position=(
            CaseChainPosition("session", "loaded", True),
            CaseChainPosition("case-intelligence-briefing-export", "planning-only", True),
        ),
        evidence_counts={
            "total": 0,
            "missing": 0,
            "collected": 0,
            "review-needed": 0,
            "blocked": 0,
        },
    )


def _request(summary):
    briefing = build_case_intelligence_briefing_export(summary)
    gate = build_case_intelligence_briefing_review_gate(briefing)
    return build_case_intelligence_human_review_request(gate)


def test_human_review_request_blocks_incomplete_briefing():
    request = _request(_blocked_summary())
    data = request.to_dict()

    assert data["kind"] == "brain_chat_case_intelligence_human_review_request"
    assert data["request_status"] == "blocked-pending-briefing-review-gate"
    assert data["human_review_request_ready"] is False
    assert data["case_review_ready"] is False
    assert data["approval_granted"] is False
    assert len(data["missing_evidence_checklist"]) == 2
    assert len(data["blockers_checklist"]) == 2
    assert "changes-requested" in data["requested_human_decision_options"]
    assert "approved-for-human-case-review" not in data["requested_human_decision_options"]

    assert data["runtime_execution_allowed"] is False
    assert data["report_submission_allowed"] is False
    assert data["vulnerability_confirmation_allowed"] is False
    assert data["safety"]["approval_granted"] is False
    assert data["safety"]["human_approval_side_effects"] is False
    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["evidence_collection"] is False
    assert data["safety"]["validation_execution"] is False
    assert data["safety"]["report_submission"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_human_review_request_ready_when_review_gate_ready():
    request = _request(_ready_summary())
    data = request.to_dict()

    assert data["request_status"] == "ready-for-human-case-review"
    assert data["human_review_request_ready"] is True
    assert data["case_review_ready"] is True
    assert data["approval_granted"] is False
    assert data["missing_evidence_checklist"] == []
    assert data["blockers_checklist"] == []
    assert "approved-for-human-case-review" in data["requested_human_decision_options"]


def test_human_review_request_detects_unsafe_gate_flags():
    briefing = build_case_intelligence_briefing_export(_ready_summary())
    gate = build_case_intelligence_briefing_review_gate(briefing)
    unsafe_gate = replace(gate, runtime_execution_allowed=True)

    request = build_case_intelligence_human_review_request(unsafe_gate)
    data = request.to_dict()

    assert data["request_status"] == "blocked-pending-safe-review-gate"
    assert data["human_review_request_ready"] is False
    assert data["approval_granted"] is False


def test_human_review_request_markdown_is_readable():
    request = _request(_blocked_summary())
    markdown = request.to_markdown()

    assert "# Brain Chat Case Intelligence Human Review Request" in markdown
    assert "Request State" in markdown
    assert "Human Review Items" in markdown
    assert "Missing Evidence Checklist" in markdown
    assert "Blockers Checklist" in markdown
    assert "Required Human Checks" in markdown
    assert "Requested Human Decision Options" in markdown
    assert "Rejected Actions" in markdown
    assert "Safety" in markdown
    assert "\\n" not in markdown
