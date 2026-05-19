from bugintel.core.brain_chat import BrainChatReply
from bugintel.core.brain_chat_case_dashboard import build_brain_chat_case_dashboard
from bugintel.core.brain_chat_session import BrainChatSession, append_brain_chat_turn


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


def test_brain_chat_case_dashboard_combines_session_and_next_step():
    session = BrainChatSession()
    session = append_brain_chat_turn(session, _reply("What should I test first?"))
    session = append_brain_chat_turn(session, _reply("What evidence do we need?"))

    dashboard = build_brain_chat_case_dashboard(session)
    data = dashboard.to_dict()

    assert data["kind"] == "brain_chat_case_dashboard"
    assert data["target_name"] == "demo.local"
    assert data["focus_endpoint"] == "/api/accounts/123/users/{id}/permissions"
    assert data["turn_count"] == 2
    assert data["decision"] == "blocked-pending-scope-and-controls"
    assert data["execution_allowed"] is False
    assert data["reportable"] is False
    assert data["recommendation"] == "resolve-blockers-before-validation"
    assert "Authorization decision diff" in data["next_evidence"]
    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_brain_chat_case_dashboard_markdown_is_readable():
    session = append_brain_chat_turn(BrainChatSession(), _reply())
    dashboard = build_brain_chat_case_dashboard(session)
    markdown = dashboard.to_markdown()

    assert "# Brain Chat Case Dashboard" in markdown
    assert "Current Case" in markdown
    assert "Gate State" in markdown
    assert "Next Evidence" in markdown
    assert "\\n" not in markdown
