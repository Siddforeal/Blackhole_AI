from bugintel.core.brain_chat_case_intelligence_question_set_runner import (
    DEFAULT_CASE_INTELLIGENCE_QUESTIONS,
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


def test_question_set_runner_answers_default_question_set():
    result = run_case_intelligence_question_set(_summary())
    data = result.to_dict()

    assert data["kind"] == "brain_chat_case_intelligence_question_set"
    assert data["target_name"] == "demo.local"
    assert data["current_stage"] == "execution-gate-proposal-review"
    assert data["current_status"] == "blocked-pending-effective-step-approval"
    assert data["blocked"] is True
    assert data["validation_allowed"] is False
    assert data["runtime_execution_allowed"] is False
    assert data["report_submission_allowed"] is False
    assert data["vulnerability_confirmation_allowed"] is False
    assert data["question_count"] == len(DEFAULT_CASE_INTELLIGENCE_QUESTIONS)
    assert len(data["answers"]) == len(DEFAULT_CASE_INTELLIGENCE_QUESTIONS)

    routes = {answer["route"] for answer in data["answers"]}
    assert "status" in routes
    assert "blockers" in routes
    assert "missing-evidence" in routes
    assert "next-action" in routes
    assert "validation" in routes
    assert "runtime-execution" in routes
    assert "report-submission" in routes
    assert "vulnerability-confirmation" in routes
    assert "chain-position" in routes
    assert "safety" in routes

    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["evidence_collection"] is False
    assert data["safety"]["validation_execution"] is False
    assert data["safety"]["report_submission"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_question_set_runner_accepts_custom_questions():
    result = run_case_intelligence_question_set(
        _summary(),
        questions=(
            "What evidence is missing?",
            "What should I do next?",
            "Why is runtime execution blocked?",
        ),
    )
    data = result.to_dict()

    assert data["question_count"] == 3
    assert [answer["route"] for answer in data["answers"]] == [
        "missing-evidence",
        "next-action",
        "runtime-execution",
    ]


def test_question_set_runner_skips_blank_custom_questions():
    result = run_case_intelligence_question_set(
        _summary(),
        questions=(
            "",
            "   ",
            "What is blocking this case?",
        ),
    )
    data = result.to_dict()

    assert data["question_count"] == 1
    assert data["answers"][0]["route"] == "blockers"


def test_question_set_runner_markdown_is_readable():
    result = run_case_intelligence_question_set(
        _summary(),
        questions=(
            "What evidence is missing?",
            "Is it safe?",
        ),
    )
    markdown = result.to_markdown()

    assert "# Brain Chat Case Intelligence Question Set" in markdown
    assert "Case State" in markdown
    assert "Answers" in markdown
    assert "What evidence is missing?" in markdown
    assert "Is it safe?" in markdown
    assert "Safety" in markdown
    assert "\\n" not in markdown
