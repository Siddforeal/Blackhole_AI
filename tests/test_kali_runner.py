import subprocess

from bugintel.core.scope_guard import TargetScope
from bugintel.integrations.kali_runner import build_curl_plan, execute_curl_plan


def make_scope():
    return TargetScope(
        target_name="demo-lab",
        allowed_domains=["demo.example.com", "*.demo.example.com"],
        allowed_schemes=["https"],
        allowed_methods=["GET", "HEAD", "OPTIONS"],
        forbidden_paths=["/logout", "/delete*"],
        human_approval_required=True,
    )


def test_builds_allowed_curl_plan():
    scope = make_scope()

    plan = build_curl_plan(
        scope=scope,
        url="https://demo.example.com/api/users/me",
        method="GET",
    )

    assert plan.allowed is True
    assert "curl" in plan.command
    assert "https://demo.example.com/api/users/me" in plan.command
    assert "Accept: application/json" in plan.command
    assert plan.requires_human_approval is True


def test_blocks_out_of_scope_curl_plan():
    scope = make_scope()

    plan = build_curl_plan(
        scope=scope,
        url="https://evil.example.net/api/users/me",
        method="GET",
    )

    assert plan.allowed is False
    assert plan.command == []
    assert "Domain not in scope" in plan.reason


def test_blocks_write_method_curl_plan():
    scope = make_scope()

    plan = build_curl_plan(
        scope=scope,
        url="https://demo.example.com/api/users/me",
        method="POST",
    )

    assert plan.allowed is False
    assert plan.command == []
    assert "HTTP method not allowed" in plan.reason


def test_execute_blocked_plan_does_not_run():
    scope = make_scope()

    plan = build_curl_plan(
        scope=scope,
        url="https://evil.example.net/api/users/me",
        method="GET",
    )

    result = execute_curl_plan(plan)

    assert result.allowed is False
    assert result.exit_code is None
    assert result.stdout == ""
    assert "Domain not in scope" in result.reason


def test_execute_allowed_plan_uses_subprocess(monkeypatch):
    scope = make_scope()

    plan = build_curl_plan(
        scope=scope,
        url="https://demo.example.com/api/users/me",
        method="GET",
    )

    class FakeCompleted:
        returncode = 0
        stdout = "HTTP/2 200\ncontent-type: application/json\n\n{\"ok\":true}"
        stderr = ""

    def fake_run(*args, **kwargs):
        assert args[0] == plan.command
        assert kwargs["capture_output"] is True
        assert kwargs["text"] is True
        assert kwargs["check"] is False
        return FakeCompleted()

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = execute_curl_plan(plan)

    assert result.allowed is True
    assert result.exit_code == 0
    assert "HTTP/2 200" in result.stdout
