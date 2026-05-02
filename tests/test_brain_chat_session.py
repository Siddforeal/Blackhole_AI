import json

from bugintel.core.brain_chat import BrainChatReply
from bugintel.core.brain_chat_session import (
    append_brain_chat_turn,
    load_brain_chat_session,
    render_brain_chat_session_summary,
    save_brain_chat_session,
)


def _reply(question="hello"):
    return BrainChatReply(
        question=question,
        answer="Hello Sidd. I am Blackhole AI Workbench.",
        target_name="demo",
        focus_endpoint="/api/accounts/123/users/{id}/permissions",
        decision="blocked-pending-scope-and-controls",
        approval_status="blocked-pending-approval",
        execution_gate="blocked-manifest-execution-disabled",
        execution_allowed=False,
    )


def test_load_missing_session_returns_empty(tmp_path):
    session = load_brain_chat_session(tmp_path / "missing.json")

    assert session.turns == ()
    assert session.planning_only is True
    assert session.execution_state == "not_executed"


def test_append_brain_chat_turn_adds_turn():
    session = load_brain_chat_session.__annotations__  # keeps import used
    empty = load_brain_chat_session.__globals__["BrainChatSession"]()

    updated = append_brain_chat_turn(empty, _reply())

    assert len(updated.turns) == 1
    assert updated.turns[0].question == "hello"
    assert updated.turns[0].target_name == "demo"
    assert updated.turns[0].execution_allowed is False


def test_save_and_load_session_round_trip(tmp_path):
    path = tmp_path / "session.json"

    session = load_brain_chat_session(path)
    session = append_brain_chat_turn(session, _reply("hello"))
    session = append_brain_chat_turn(session, _reply("status"))
    save_brain_chat_session(session, path)

    loaded = load_brain_chat_session(path)
    data = json.loads(path.read_text())

    assert len(loaded.turns) == 2
    assert data["turn_count"] == 2
    assert data["planning_only"] is True
    assert loaded.turns[1].question == "status"


def test_render_brain_chat_session_summary():
    session = load_brain_chat_session.__globals__["BrainChatSession"]()
    session = append_brain_chat_turn(session, _reply("hello"))

    summary = render_brain_chat_session_summary(session)

    assert "# Blackhole Brain Chat Session" in summary
    assert "Turns: `1`" in summary
    assert "blocked-pending-scope-and-controls" in summary
