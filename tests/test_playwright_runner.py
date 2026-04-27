from bugintel.core.scope_guard import TargetScope
from bugintel.integrations.playwright_runner import build_browser_plan


def make_scope():
    return TargetScope(
        target_name="demo-lab",
        allowed_domains=["demo.example.com", "*.demo.example.com"],
        allowed_schemes=["https"],
        allowed_methods=["GET", "HEAD", "OPTIONS"],
        forbidden_paths=["/logout", "/delete*"],
        human_approval_required=True,
    )


def test_build_browser_plan_allows_in_scope_url():
    scope = make_scope()

    plan = build_browser_plan(
        scope=scope,
        start_url="https://demo.example.com/dashboard",
        browser="chromium",
    )

    assert plan.allowed is True
    assert plan.browser == "chromium"
    assert plan.requires_human_approval is True

    action_types = [action.action_type for action in plan.actions]

    assert "navigate" in action_types
    assert "capture_network" in action_types
    assert "capture_screenshot" in action_types
    assert "extract_html" in action_types


def test_build_browser_plan_blocks_out_of_scope_url():
    scope = make_scope()

    plan = build_browser_plan(
        scope=scope,
        start_url="https://evil.example.net/dashboard",
        browser="chromium",
    )

    assert plan.allowed is False
    assert plan.actions == []
    assert "Domain not in scope" in plan.reason


def test_build_browser_plan_blocks_unsupported_browser():
    scope = make_scope()

    plan = build_browser_plan(
        scope=scope,
        start_url="https://demo.example.com/dashboard",
        browser="unknown-browser",
    )

    assert plan.allowed is False
    assert plan.actions == []
    assert "Unsupported browser" in plan.reason


def test_build_browser_plan_can_disable_optional_capture():
    scope = make_scope()

    plan = build_browser_plan(
        scope=scope,
        start_url="https://demo.example.com/dashboard",
        browser="firefox",
        capture_network=False,
        capture_screenshot=False,
    )

    action_types = [action.action_type for action in plan.actions]

    assert plan.allowed is True
    assert plan.browser == "firefox"
    assert "navigate" in action_types
    assert "extract_html" in action_types
    assert "capture_network" not in action_types
    assert "capture_screenshot" not in action_types
