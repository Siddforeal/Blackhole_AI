from bugintel.core.case_intake_brain_handoff_question_set_runner import (
    DEFAULT_CASE_INTAKE_BRAIN_HANDOFF_QUESTIONS,
    run_case_intake_brain_handoff_question_set,
)
from tests.test_case_intake_brain_handoff_answerer import _handoff


def test_question_set_runs_default_questions() -> None:
    question_set = run_case_intake_brain_handoff_question_set(_handoff())

    assert question_set.target_name == "demo-program"
    assert question_set.blocked is False
    assert question_set.planning_only is True
    assert question_set.validation_allowed is False
    assert question_set.runtime_execution_allowed is False
    assert question_set.report_submission_allowed is False
    assert question_set.vulnerability_confirmation_allowed is False
    assert len(question_set.answers) == len(DEFAULT_CASE_INTAKE_BRAIN_HANDOFF_QUESTIONS)

    routes = {answer.route for answer in question_set.answers}
    assert "test-first" in routes
    assert "strongest-potential" in routes
    assert "missing-evidence" in routes
    assert "deferred" in routes
    assert "safe-manual-tests" in routes


def test_question_set_serializes_safety_metadata() -> None:
    data = run_case_intake_brain_handoff_question_set(_handoff()).to_dict()

    assert data["kind"] == "case_intake_brain_handoff_question_set"
    assert data["answer_count"] == 5
    assert data["safety"]["network_requests"] is False
    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["browser_execution"] is False
    assert data["safety"]["evidence_collection"] is False
    assert data["safety"]["target_mutation"] is False
    assert data["safety"]["report_submission"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_question_set_markdown_is_readable() -> None:
    markdown = run_case_intake_brain_handoff_question_set(_handoff()).to_markdown()

    assert "# Case Intake Brain Handoff Question Set" in markdown
    assert "What should I test first?" in markdown
    assert "Which endpoint has strongest P1/P2 potential?" in markdown
    assert "No network requests" in markdown
    assert "/api/admin/users/{id}/permissions" in markdown
