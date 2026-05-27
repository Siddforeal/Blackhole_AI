from bugintel.core.brain_chat_case_intelligence_briefing_export import (
    build_case_intelligence_briefing_export,
)
from bugintel.core.brain_chat_case_intelligence_question_set_runner import (
    run_case_intelligence_question_set,
)
from bugintel.core.brain_chat_case_intelligence_status_summary import (
    BrainChatCaseIntelligenceStatusSummary,
    CaseChainPosition,
)


def _summary():
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
            "No approved validation steps are available for execution-gate design review.",
        ),
        missing_evidence=(
            "Scope and authorization proof for `/api/accounts/123/users/{id}/permissions`",
            "Redaction checklist",
        ),
        chain_position=(
            CaseChainPosition("session", "not_executed", False),
            CaseChainPosition("evidence-checklist", "blocked-review", False),
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


def test_briefing_export_combines_summary_and_question_set():
    briefing = build_case_intelligence_briefing_export(_summary())
    data = briefing.to_dict()

    assert data["kind"] == "brain_chat_case_intelligence_briefing_export"
    assert data["target_name"] == "demo.local"
    assert data["current_stage"] == "execution-gate-proposal-review"
    assert data["current_status"] == "blocked-pending-effective-step-approval"
    assert data["briefing_status"] == "blocked"
    assert data["blocked"] is True
    assert data["validation_allowed"] is False
    assert data["runtime_execution_allowed"] is False
    assert data["report_submission_allowed"] is False
    assert data["vulnerability_confirmation_allowed"] is False
    assert len(data["missing_evidence"]) == 2
    assert len(data["blockers"]) == 3
    assert data["question_set"]["question_count"] == 10
    assert "The case is blocked" in data["briefing_summary"]

    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["evidence_collection"] is False
    assert data["safety"]["validation_execution"] is False
    assert data["safety"]["report_submission"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_briefing_export_accepts_existing_question_set():
    question_set = run_case_intelligence_question_set(
        _summary(),
        questions=(
            "What evidence is missing?",
            "Is it safe?",
        ),
    )
    briefing = build_case_intelligence_briefing_export(_summary(), question_set=question_set)
    data = briefing.to_dict()

    assert data["question_set"]["question_count"] == 2
    assert [answer["route"] for answer in data["question_set"]["answers"]] == [
        "missing-evidence",
        "safety",
    ]


def test_briefing_export_markdown_is_readable():
    briefing = build_case_intelligence_briefing_export(_summary())
    markdown = briefing.to_markdown()

    assert "# Brain Chat Case Intelligence Briefing Export" in markdown
    assert "Briefing Summary" in markdown
    assert "Case State" in markdown
    assert "Safest Next Action" in markdown
    assert "Missing Evidence" in markdown
    assert "Blockers" in markdown
    assert "Chain Position" in markdown
    assert "Question Set Answers" in markdown
    assert "Safety" in markdown
    assert "\\n" not in markdown


def test_briefing_export_planning_only_summary():
    summary = BrainChatCaseIntelligenceStatusSummary(
        target_name="demo.local",
        focus_endpoint=None,
        current_stage="session",
        current_status="loaded",
        blocked=False,
        validation_allowed=False,
        runtime_execution_allowed=False,
        report_submission_allowed=False,
        vulnerability_confirmation_allowed=False,
        safest_next_action="Continue with local human review only.",
        blockers=(),
        missing_evidence=(),
        chain_position=(CaseChainPosition("session", "loaded", True),),
        evidence_counts={
            "total": 0,
            "missing": 0,
            "collected": 0,
            "review-needed": 0,
            "blocked": 0,
        },
    )

    briefing = build_case_intelligence_briefing_export(summary)
    data = briefing.to_dict()

    assert data["briefing_status"] == "planning-only"
    assert "planning-only state" in data["briefing_summary"]
    assert data["runtime_execution_allowed"] is False
