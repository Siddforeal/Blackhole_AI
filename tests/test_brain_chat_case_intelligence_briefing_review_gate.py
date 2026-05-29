from dataclasses import replace

from bugintel.core.brain_chat_case_intelligence_briefing_export import (
    build_case_intelligence_briefing_export,
)
from bugintel.core.brain_chat_case_intelligence_briefing_review_gate import (
    build_case_intelligence_briefing_review_gate,
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


def test_briefing_review_gate_blocks_missing_evidence_and_blockers():
    briefing = build_case_intelligence_briefing_export(_blocked_summary())
    gate = build_case_intelligence_briefing_review_gate(briefing)
    data = gate.to_dict()

    assert data["kind"] == "brain_chat_case_intelligence_briefing_review_gate"
    assert data["review_status"] == "blocked-briefing"
    assert data["case_review_ready"] is False
    assert data["briefing_status"] == "blocked"
    assert len(data["missing_evidence"]) == 2
    assert len(data["blockers"]) == 2
    assert any("missing evidence" in item for item in data["human_review_items"])
    assert any("Collect or mark every missing evidence" in item for item in data["required_human_checks"])
    assert data["runtime_execution_allowed"] is False
    assert data["report_submission_allowed"] is False
    assert data["vulnerability_confirmation_allowed"] is False
    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["evidence_collection"] is False
    assert data["safety"]["validation_execution"] is False
    assert data["safety"]["report_submission"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_briefing_review_gate_ready_for_human_case_review_when_complete():
    briefing = build_case_intelligence_briefing_export(_ready_summary())
    gate = build_case_intelligence_briefing_review_gate(briefing)
    data = gate.to_dict()

    assert data["review_status"] == "ready-for-human-case-review"
    assert data["case_review_ready"] is True
    assert data["missing_evidence"] == []
    assert data["blockers"] == []
    assert any("scope" in item for item in data["required_human_checks"])


def test_briefing_review_gate_detects_unsafe_runtime_flags():
    briefing = build_case_intelligence_briefing_export(_ready_summary())
    unsafe = replace(briefing, runtime_execution_allowed=True)
    gate = build_case_intelligence_briefing_review_gate(unsafe)
    data = gate.to_dict()

    assert data["review_status"] == "blocked-briefing"
    assert data["case_review_ready"] is False
    assert any("Runtime execution is unexpectedly allowed" in item for item in data["blockers"])


def test_briefing_review_gate_markdown_is_readable():
    briefing = build_case_intelligence_briefing_export(_blocked_summary())
    gate = build_case_intelligence_briefing_review_gate(briefing)
    markdown = gate.to_markdown()

    assert "# Brain Chat Case Intelligence Briefing Review Gate" in markdown
    assert "Review State" in markdown
    assert "Missing Evidence" in markdown
    assert "Blockers" in markdown
    assert "Human Review Items" in markdown
    assert "Required Human Checks" in markdown
    assert "Rejected Actions" in markdown
    assert "Safety" in markdown
    assert "\\n" not in markdown
