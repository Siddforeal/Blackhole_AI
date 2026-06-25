from bugintel.core.bug_bounty_case_intake import build_bug_bounty_case_intake_workflow
from bugintel.core.bug_bounty_case_intake_brain_handoff import build_case_intake_brain_handoff
from bugintel.core.case_intake_brain_handoff_answerer import (
    answer_case_intake_brain_handoff_question,
)


def _handoff():
    intake = build_bug_bounty_case_intake_workflow(
        """
        GET /api/status
        GET /api/admin/users/{id}/permissions
        GET /api/files/{id}/download
        """,
        target_name="demo-program",
        top_n=3,
    ).to_dict()

    return build_case_intake_brain_handoff(intake).to_dict()


def test_handoff_answerer_recommends_first_endpoint_safely():
    answer = answer_case_intake_brain_handoff_question(_handoff(), "What should I test first?")
    data = answer.to_dict()

    assert data["kind"] == "case_intake_brain_handoff_answer"
    assert data["route"] == "test-first"
    assert data["target_name"] == "demo-program"
    assert data["focus_endpoint"] == "/api/admin/users/{id}/permissions"
    assert "Start with `/api/admin/users/{id}/permissions`" in data["answer"]
    assert data["validation_allowed"] is False
    assert data["runtime_execution_allowed"] is False
    assert data["report_submission_allowed"] is False
    assert data["vulnerability_confirmation_allowed"] is False
    assert data["planning_only"] is True
    assert data["execution_state"] == "not_executed"
    assert data["safety"]["network_requests"] is False
    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["evidence_collection"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_handoff_answerer_identifies_strongest_p1_p2_endpoint():
    answer = answer_case_intake_brain_handoff_question(
        _handoff(),
        "Which endpoint has strongest P1/P2 potential?",
    )
    data = answer.to_dict()

    assert data["route"] == "strongest-potential"
    assert data["focus_endpoint"] == "/api/admin/users/{id}/permissions"
    assert "strongest P1/P2 potential" in data["answer"]
    assert any("Why focus:" in point for point in data["supporting_points"])


def test_handoff_answerer_lists_missing_evidence():
    answer = answer_case_intake_brain_handoff_question(_handoff(), "What evidence is missing?")
    data = answer.to_dict()

    assert data["route"] == "missing-evidence"
    assert data["evidence_gap_count"] >= 1
    assert "evidence gap item" in data["answer"]
    assert any("scope-proof" in point for point in data["supporting_points"])


def test_handoff_answerer_lists_deferred_endpoints():
    answer = answer_case_intake_brain_handoff_question(_handoff(), "What should I ignore or defer?")
    data = answer.to_dict()

    assert data["route"] == "deferred"
    assert data["deferred_endpoint_count"] == 1
    assert "Deferred endpoint: `/api/status`" in data["supporting_points"]


def test_handoff_answerer_describes_safe_manual_tests():
    answer = answer_case_intake_brain_handoff_question(
        _handoff(),
        "What safe manual tests are possible with controlled accounts?",
    )
    data = answer.to_dict()

    assert data["route"] == "safe-manual-tests"
    assert "controlled-account" in data["recommended_next_action"]
    assert any("controlled accounts" in point for point in data["supporting_points"])
    assert any("synthetic object IDs" in point for point in data["supporting_points"])
    assert data["safety"]["validation_execution"] is False


def test_handoff_answerer_blocks_invalid_handoff():
    answer = answer_case_intake_brain_handoff_question({"kind": "wrong"}, "What should I test first?")
    data = answer.to_dict()

    assert data["blocked"] is True
    assert "invalid" in data["answer"]
    assert data["focus_endpoint"] is None
    assert data["runtime_execution_allowed"] is False


def test_handoff_answerer_markdown_is_readable():
    markdown = answer_case_intake_brain_handoff_question(
        _handoff(),
        "What evidence is missing?",
    ).to_markdown()

    assert "# Case Intake Brain Handoff Answer" in markdown
    assert "## Question" in markdown
    assert "## Answer" in markdown
    assert "## Supporting Points" in markdown
    assert "## Recommended Next Action" in markdown
    assert "## Safety" in markdown
    assert "\\n" not in markdown
