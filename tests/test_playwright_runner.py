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


def test_build_browser_capture_result_matches_evidence_store_shape(tmp_path):
    from bugintel.core.evidence_store import EvidenceStore
    from bugintel.integrations.playwright_runner import build_browser_capture_result

    scope = make_scope()
    plan = build_browser_plan(
        scope=scope,
        start_url="https://demo.example.com/dashboard",
        browser="chromium",
    )

    result = build_browser_capture_result(
        plan=plan,
        task_name="capture dashboard",
        network_events=[
            {
                "method": "GET",
                "url": "https://demo.example.com/api/me",
                "status_code": 200,
                "resource_type": "fetch",
                "response_body": '{"email":"sidd@example.com"}',
            }
        ],
        screenshots=[
            {
                "path": "artifacts/dashboard.png",
                "sha256": "a" * 64,
            }
        ],
        html_snapshots=[
            {
                "url": "https://demo.example.com/dashboard",
                "html": "<html>sidd@example.com</html>",
            }
        ],
        execution_output={
            "runner": "playwright",
            "status": "completed",
            "stdout": "loaded page",
        },
        notes="Future Playwright result adapter",
    )

    assert result.target_name == "demo-lab"
    assert result.task_name == "capture dashboard"
    assert result.start_url == "https://demo.example.com/dashboard"
    assert result.browser == "chromium"
    assert result.network_events[0]["method"] == "GET"

    kwargs = result.to_evidence_kwargs()

    assert kwargs["target_name"] == "demo-lab"
    assert kwargs["task_name"] == "capture dashboard"
    assert kwargs["start_url"] == "https://demo.example.com/dashboard"
    assert kwargs["browser"] == "chromium"
    assert kwargs["network_events"][0]["url"] == "https://demo.example.com/api/me"

    store = EvidenceStore(base_dir=tmp_path)
    evidence_path = store.save_browser_evidence(**kwargs)

    assert evidence_path.exists()


def test_build_browser_capture_result_rejects_blocked_plan():
    from bugintel.integrations.playwright_runner import build_browser_capture_result

    scope = make_scope()
    plan = build_browser_plan(
        scope=scope,
        start_url="https://evil.example.net/dashboard",
        browser="chromium",
    )

    try:
        build_browser_capture_result(
            plan=plan,
            task_name="blocked capture",
        )
    except ValueError as exc:
        assert "Cannot build capture result from blocked browser plan" in str(exc)
    else:
        raise AssertionError("Expected blocked browser plan to raise ValueError")


def test_build_playwright_execution_preview_is_safe_by_default():
    from bugintel.integrations.playwright_runner import (
        BrowserExecutionConfig,
        build_browser_capture_result,
        build_playwright_execution_preview,
    )

    scope = make_scope()
    plan = build_browser_plan(
        scope=scope,
        start_url="https://demo.example.com/dashboard",
        browser="chromium",
    )

    preview = build_playwright_execution_preview(
        plan=plan,
        config=BrowserExecutionConfig(
            headless=True,
            timeout_ms=10000,
            screenshot_path="artifacts/demo-dashboard.png",
        ),
    )

    assert preview["runner"] == "playwright"
    assert preview["status"] == "preview"
    assert preview["live_execution_allowed"] is False
    assert preview["browser"] == "chromium"
    assert preview["start_url"] == "https://demo.example.com/dashboard"
    assert preview["timeout_ms"] == 10000
    assert preview["screenshot_path"] == "artifacts/demo-dashboard.png"
    assert preview["capture_network"] is True
    assert preview["capture_screenshot"] is True
    assert preview["capture_html"] is True

    action_types = [
        action["action_type"]
        for action in preview["planned_actions"]
    ]

    assert "navigate" in action_types
    assert "capture_network" in action_types
    assert "capture_screenshot" in action_types
    assert "extract_html" in action_types

    result = build_browser_capture_result(
        plan=plan,
        task_name="playwright preview",
        execution_output=preview,
        notes="Execution preview only; browser not launched.",
    )

    assert result.execution_output["runner"] == "playwright"
    assert result.execution_output["status"] == "preview"
    assert result.execution_output["live_execution_allowed"] is False


def test_build_playwright_execution_preview_rejects_blocked_plan():
    from bugintel.integrations.playwright_runner import build_playwright_execution_preview

    scope = make_scope()
    plan = build_browser_plan(
        scope=scope,
        start_url="https://evil.example.net/dashboard",
        browser="chromium",
    )

    try:
        build_playwright_execution_preview(plan=plan)
    except ValueError as exc:
        assert "Cannot build Playwright execution preview from blocked browser plan" in str(exc)
    else:
        raise AssertionError("Expected blocked browser plan to raise ValueError")


def test_execute_playwright_plan_blocks_when_live_execution_not_allowed():
    from bugintel.integrations.playwright_runner import (
        BrowserExecutionConfig,
        PlaywrightExecutionSafetyError,
        execute_playwright_plan,
    )

    scope = make_scope()
    plan = build_browser_plan(
        scope=scope,
        start_url="https://demo.example.com/dashboard",
        browser="chromium",
    )

    try:
        execute_playwright_plan(
            plan=plan,
            task_name="blocked live execution",
            config=BrowserExecutionConfig(allow_live_execution=False),
        )
    except PlaywrightExecutionSafetyError as exc:
        assert "Live Playwright execution is disabled" in str(exc)
    else:
        raise AssertionError("Expected live execution safety gate to block execution")


def test_execute_playwright_plan_blocks_out_of_scope_plan():
    from bugintel.integrations.playwright_runner import (
        BrowserExecutionConfig,
        PlaywrightExecutionSafetyError,
        execute_playwright_plan,
    )

    scope = make_scope()
    plan = build_browser_plan(
        scope=scope,
        start_url="https://evil.example.net/dashboard",
        browser="chromium",
    )

    try:
        execute_playwright_plan(
            plan=plan,
            task_name="blocked out-of-scope execution",
            config=BrowserExecutionConfig(allow_live_execution=True),
        )
    except PlaywrightExecutionSafetyError as exc:
        assert "Cannot execute blocked browser plan" in str(exc)
        assert "Domain not in scope" in str(exc)
    else:
        raise AssertionError("Expected out-of-scope browser plan to block execution")


def test_execute_playwright_plan_blocks_when_playwright_missing():
    from bugintel.integrations.playwright_runner import (
        BrowserExecutionConfig,
        PlaywrightExecutionSafetyError,
        check_playwright_available,
        execute_playwright_plan,
    )

    availability = check_playwright_available()

    if availability.available:
        return

    scope = make_scope()
    plan = build_browser_plan(
        scope=scope,
        start_url="https://demo.example.com/dashboard",
        browser="chromium",
    )

    try:
        execute_playwright_plan(
            plan=plan,
            task_name="blocked missing playwright",
            config=BrowserExecutionConfig(allow_live_execution=True),
        )
    except PlaywrightExecutionSafetyError as exc:
        assert "playwright" in str(exc).lower()
    else:
        raise AssertionError("Expected missing Playwright package to block execution")


def test_execute_playwright_plan_reaches_not_implemented_handoff_when_all_gates_pass(monkeypatch):
    import bugintel.integrations.playwright_runner as playwright_runner

    from bugintel.integrations.playwright_runner import (
        BrowserExecutionConfig,
        PlaywrightAvailability,
        execute_playwright_plan,
    )

    def fake_playwright_available():
        return PlaywrightAvailability(
            available=True,
            reason="Playwright mocked as available for safety-gate test.",
        )

    monkeypatch.setattr(
        playwright_runner,
        "check_playwright_available",
        fake_playwright_available,
    )

    scope = make_scope()
    plan = build_browser_plan(
        scope=scope,
        start_url="https://demo.example.com/dashboard",
        browser="chromium",
    )

    result = execute_playwright_plan(
        plan=plan,
        task_name="mocked safe handoff",
        config=BrowserExecutionConfig(allow_live_execution=True),
        notes="All gates passed, but live browser launch remains unimplemented.",
    )

    assert result.target_name == "demo-lab"
    assert result.task_name == "mocked safe handoff"
    assert result.start_url == "https://demo.example.com/dashboard"
    assert result.browser == "chromium"

    output = result.execution_output

    assert output["runner"] == "playwright"
    assert output["status"] == "not_implemented"
    assert output["live_execution_allowed"] is True
    assert output["playwright_available"] is True
    assert "not implemented yet" in output["reason"]
    assert result.network_events == []
    assert result.screenshots == []
    assert result.html_snapshots == []
