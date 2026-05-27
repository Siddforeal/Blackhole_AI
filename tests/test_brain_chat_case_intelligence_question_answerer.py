from bugintel.core.brain_chat_case_intelligence_question_answerer import (
    answer_case_intelligence_question,
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


def test_question_answerer_explains_blockers():
    answer = answer_case_intelligence_question(_summary(), "What is blocking this case?")
    data = answer.to_dict()

    assert data["kind"] == "brain_chat_case_intelligence_answer"
    assert data["route"] == "blockers"
    assert "blocked at `execution-gate-proposal-review`" in data["answer"]
    assert "Effective validation-step approval is not granted." in data["supporting_points"]
    assert data["validation_allowed"] is False
    assert data["runtime_execution_allowed"] is False
    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["evidence_collection"] is False
    assert data["safety"]["validation_execution"] is False
    assert data["safety"]["report_submission"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_question_answerer_lists_missing_evidence():
    answer = answer_case_intelligence_question(_summary(), "What evidence is missing?")
    data = answer.to_dict()

    assert data["route"] == "missing-evidence"
    assert "2 evidence item(s) are missing." in data["answer"]
    assert "Redaction checklist" in data["supporting_points"]


def test_question_answerer_returns_safest_next_action():
    answer = answer_case_intelligence_question(_summary(), "What should I do next?")
    data = answer.to_dict()

    assert data["route"] == "next-action"
    assert data["answer"] == "Collect or mark the missing local evidence items before requesting validation or approval."
    assert data["recommended_next_action"] == data["answer"]


def test_question_answerer_blocks_validation_runtime_and_reporting():
    validation = answer_case_intelligence_question(_summary(), "Is validation allowed?").to_dict()
    runtime = answer_case_intelligence_question(_summary(), "Why is runtime execution blocked?").to_dict()
    report = answer_case_intelligence_question(_summary(), "Can I submit the report?").to_dict()
    confirmed = answer_case_intelligence_question(_summary(), "Is this vulnerability confirmed?").to_dict()

    assert validation["route"] == "validation"
    assert "not allowed" in validation["answer"]

    assert runtime["route"] == "runtime-execution"
    assert "not allowed" in runtime["answer"]

    assert report["route"] == "report-submission"
    assert "not allowed" in report["answer"]

    assert confirmed["route"] == "vulnerability-confirmation"
    assert "not allowed" in confirmed["answer"]


def test_question_answerer_reports_chain_position():
    answer = answer_case_intelligence_question(_summary(), "Where am I in the chain?")
    data = answer.to_dict()

    assert data["route"] == "chain-position"
    assert "latest chain stage" in data["answer"]
    assert "session: not_executed ready=False" in data["supporting_points"]
    assert "execution-gate-proposal-review: blocked-pending-effective-step-approval ready=False" in data["supporting_points"]


def test_question_answerer_safety_route():
    answer = answer_case_intelligence_question(_summary(), "Is it safe?")
    data = answer.to_dict()

    assert data["route"] == "safety"
    assert "local, deterministic, and planning-only" in data["answer"]
    assert "Tool execution: false" in data["supporting_points"]


def test_question_answerer_default_status_route():
    answer = answer_case_intelligence_question(_summary(), "Tell me status")
    data = answer.to_dict()

    assert data["route"] == "status"
    assert "blocked-pending-effective-step-approval" in data["answer"]
    assert "Missing evidence: 2" in data["supporting_points"]


def test_question_answerer_markdown_is_readable():
    answer = answer_case_intelligence_question(_summary(), "What is blocking this case?")
    markdown = answer.to_markdown()

    assert "# Brain Chat Case Intelligence Answer" in markdown
    assert "Question" in markdown
    assert "Answer" in markdown
    assert "Supporting Points" in markdown
    assert "Recommended Next Action" in markdown
    assert "Safety" in markdown
    assert "\\n" not in markdown
