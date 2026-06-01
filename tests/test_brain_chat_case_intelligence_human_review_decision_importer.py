from dataclasses import replace

import pytest

from bugintel.core.brain_chat_case_intelligence_briefing_export import (
    build_case_intelligence_briefing_export,
)
from bugintel.core.brain_chat_case_intelligence_briefing_review_gate import (
    build_case_intelligence_briefing_review_gate,
)
from bugintel.core.brain_chat_case_intelligence_human_review_decision_importer import (
    import_case_intelligence_human_review_decision_data,
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
        blockers=("Effective approval is not granted.",),
        missing_evidence=("Redaction checklist",),
        chain_position=(CaseChainPosition("session", "not_executed", False),),
        evidence_counts={
            "total": 1,
            "missing": 1,
            "collected": 0,
            "review-needed": 0,
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


def test_decision_importer_blocks_premature_approval():
    request = _request(_blocked_summary())
    decision = import_case_intelligence_human_review_decision_data(
        request,
        {
            "decision": "approved-for-human-case-review",
            "reason": "Premature approval attempt.",
            "reviewer": "local-reviewer",
        },
    )
    data = decision.to_dict()

    assert data["decision"] == "approved-for-human-case-review"
    assert data["request_status"] == "blocked-pending-briefing-review-gate"
    assert data["human_review_request_ready"] is False
    assert data["case_review_ready"] is False
    assert data["approval_granted"] is False
    assert data["effective_human_review_approval_granted"] is False
    assert data["runtime_execution_allowed"] is False
    assert data["report_submission_allowed"] is False
    assert data["vulnerability_confirmation_allowed"] is False
    assert any("not effective" in item for item in data["rejected_next_steps"])

    assert data["safety"]["approval_granted"] is False
    assert data["safety"]["effective_human_review_approval_granted"] is False
    assert data["safety"]["human_approval_side_effects"] is False
    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["evidence_collection"] is False
    assert data["safety"]["validation_execution"] is False
    assert data["safety"]["report_submission"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_decision_importer_allows_effective_case_review_approval_when_request_ready():
    request = _request(_ready_summary())
    decision = import_case_intelligence_human_review_decision_data(
        request,
        {
            "decision": "approved-for-human-case-review",
            "reason": "Ready for human case review.",
            "reviewer": "local-reviewer",
        },
    )
    data = decision.to_dict()

    assert data["request_status"] == "ready-for-human-case-review"
    assert data["human_review_request_ready"] is True
    assert data["case_review_ready"] is True
    assert data["approval_granted"] is True
    assert data["effective_human_review_approval_granted"] is True
    assert any("human case review" in item for item in data["allowed_next_steps"])
    assert data["safety"]["approval_granted"] is True
    assert data["safety"]["human_approval_side_effects"] is False
    assert data["safety"]["validation_execution"] is False
    assert data["safety"]["report_submission"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_decision_importer_changes_requested_never_grants_approval():
    request = _request(_ready_summary())
    decision = import_case_intelligence_human_review_decision_data(
        request,
        {"decision": "changes-requested", "reason": "Need edits."},
    )
    data = decision.to_dict()

    assert data["decision"] == "changes-requested"
    assert data["approval_granted"] is False
    assert data["effective_human_review_approval_granted"] is False
    assert any("Apply requested local changes" in item for item in data["allowed_next_steps"])


def test_decision_importer_rejected_never_grants_approval():
    request = _request(_ready_summary())
    decision = import_case_intelligence_human_review_decision_data(
        request,
        {"decision": "rejected", "reason": "Not acceptable."},
    )
    data = decision.to_dict()

    assert data["decision"] == "rejected"
    assert data["approval_granted"] is False
    assert data["effective_human_review_approval_granted"] is False
    assert any("Stop this case-review path" in item for item in data["allowed_next_steps"])


def test_decision_importer_blocks_unsafe_ready_request():
    request = _request(_ready_summary())
    unsafe_request = replace(request, runtime_execution_allowed=True)

    decision = import_case_intelligence_human_review_decision_data(
        unsafe_request,
        {"decision": "approved-for-human-case-review"},
    )
    data = decision.to_dict()

    assert data["approval_granted"] is False
    assert data["effective_human_review_approval_granted"] is False


def test_decision_importer_invalid_decision_errors():
    request = _request(_blocked_summary())

    with pytest.raises(ValueError, match="Invalid case intelligence human review decision"):
        import_case_intelligence_human_review_decision_data(
            request,
            {"decision": "approved"},
        )


def test_decision_importer_markdown_is_readable():
    request = _request(_blocked_summary())
    decision = import_case_intelligence_human_review_decision_data(
        request,
        {"decision": "approved-for-human-case-review", "reason": "Premature."},
    )
    markdown = decision.to_markdown()

    assert "# Brain Chat Case Intelligence Human Review Decision" in markdown
    assert "Decision State" in markdown
    assert "Reason" in markdown
    assert "Missing Evidence Checklist" in markdown
    assert "Blockers Checklist" in markdown
    assert "Required Human Checks" in markdown
    assert "Allowed Next Steps" in markdown
    assert "Rejected Next Steps" in markdown
    assert "Safety" in markdown
    assert "\\n" not in markdown
