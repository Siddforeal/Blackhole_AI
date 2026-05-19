from bugintel.core.brain_chat import BrainChatReply
from bugintel.core.brain_chat_case_dashboard_review_packet import (
    build_brain_chat_case_dashboard_review_packet,
)
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


def test_case_dashboard_review_packet_blocks_reportability_from_dashboard_state():
    session = BrainChatSession()
    session = append_brain_chat_turn(session, _reply("What should I test first?"))
    session = append_brain_chat_turn(session, _reply("What evidence do we need?"))

    packet = build_brain_chat_case_dashboard_review_packet(session)
    data = packet.to_dict()

    assert data["kind"] == "brain_chat_case_dashboard_review_packet"
    assert data["target_name"] == "demo.local"
    assert data["focus_endpoint"] == "/api/accounts/123/users/{id}/permissions"
    assert data["review_status"] == "blocked-review"
    assert data["reportable"] is False
    assert data["execution_allowed"] is False
    assert "Dashboard state is not reportable by itself." in data["blockers"]
    assert "Authorization decision diff" in data["required_evidence"]
    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_case_dashboard_review_packet_markdown_is_readable():
    session = append_brain_chat_turn(BrainChatSession(), _reply())
    packet = build_brain_chat_case_dashboard_review_packet(session)
    markdown = packet.to_markdown()

    assert "# Brain Chat Case Dashboard Review Packet" in markdown
    assert "Review Status" in markdown
    assert "Required Evidence" in markdown
    assert "Rejected Actions" in markdown
    assert "\\n" not in markdown
