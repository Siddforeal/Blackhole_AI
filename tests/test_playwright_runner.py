from pathlib import Path
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
    from bugintel.integrations.playwright_runner import (
        BrowserHtmlSnapshot,
        BrowserNetworkEvent,
        BrowserScreenshot,
        build_browser_capture_result,
    )

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
    assert isinstance(result.network_events[0], BrowserNetworkEvent)
    assert isinstance(result.screenshots[0], BrowserScreenshot)
    assert isinstance(result.html_snapshots[0], BrowserHtmlSnapshot)
    assert result.network_events[0].method == "GET"

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


def test_build_playwright_artifact_plan_returns_safe_paths():
    from bugintel.integrations.playwright_runner import build_playwright_artifact_plan

    artifacts = build_playwright_artifact_plan(
        target_name="Demo Lab",
        task_name="Capture Dashboard / Admin",
        base_dir="tmp/artifacts",
    )

    assert artifacts.artifact_dir == "tmp/artifacts/demo-lab/capture-dashboard---admin"
    assert artifacts.screenshot_path.endswith("/screenshot.png")
    assert artifacts.html_snapshot_path.endswith("/page.html")
    assert artifacts.network_log_path.endswith("/network.json")
    assert artifacts.trace_path.endswith("/trace.zip")

    data = artifacts.to_dict()

    assert data["artifact_dir"] == artifacts.artifact_dir
    assert data["screenshot_path"] == artifacts.screenshot_path
    assert data["html_snapshot_path"] == artifacts.html_snapshot_path
    assert data["network_log_path"] == artifacts.network_log_path
    assert data["trace_path"] == artifacts.trace_path


def test_build_playwright_execution_request_is_pre_execution_only():
    from bugintel.integrations.playwright_runner import (
        BrowserExecutionConfig,
        build_playwright_execution_request,
    )

    scope = make_scope()
    plan = build_browser_plan(
        scope=scope,
        start_url="https://demo.example.com/dashboard",
        browser="chromium",
    )

    request = build_playwright_execution_request(
        plan=plan,
        task_name="Capture Dashboard",
        config=BrowserExecutionConfig(
            headless=True,
            timeout_ms=10000,
            allow_live_execution=False,
        ),
        base_artifact_dir="tmp/artifacts",
    )

    assert request.target_name == "demo-lab"
    assert request.task_name == "Capture Dashboard"
    assert request.start_url == "https://demo.example.com/dashboard"
    assert request.browser == "chromium"
    assert request.config.timeout_ms == 10000
    assert request.config.allow_live_execution is False
    assert request.artifacts.artifact_dir == "tmp/artifacts/demo-lab/capture-dashboard"

    action_types = [
        action["action_type"]
        for action in request.planned_actions
    ]

    assert "navigate" in action_types
    assert "capture_network" in action_types
    assert "capture_screenshot" in action_types
    assert "extract_html" in action_types

    data = request.to_dict()

    assert data["target_name"] == "demo-lab"
    assert data["config"]["allow_live_execution"] is False
    assert data["artifacts"]["network_log_path"].endswith("/network.json")


def test_build_playwright_execution_request_rejects_blocked_plan():
    from bugintel.integrations.playwright_runner import build_playwright_execution_request

    scope = make_scope()
    plan = build_browser_plan(
        scope=scope,
        start_url="https://evil.example.net/dashboard",
        browser="chromium",
    )

    try:
        build_playwright_execution_request(
            plan=plan,
            task_name="Blocked Capture",
        )
    except ValueError as exc:
        assert "Cannot build Playwright execution request from blocked browser plan" in str(exc)
        assert "Domain not in scope" in str(exc)
    else:
        raise AssertionError("Expected blocked browser plan to raise ValueError")



def test_build_playwright_adapter_context_is_safe_by_default():
    from bugintel.integrations.playwright_runner import (
        BrowserExecutionConfig,
        build_playwright_adapter_context,
        build_playwright_execution_request,
    )

    scope = make_scope()
    plan = build_browser_plan(
        scope=scope,
        start_url="https://demo.example.com/dashboard",
        browser="chromium",
    )

    request = build_playwright_execution_request(
        plan=plan,
        task_name="Capture Dashboard",
        config=BrowserExecutionConfig(allow_live_execution=False),
        base_artifact_dir="tmp/artifacts",
    )

    context = build_playwright_adapter_context(request)

    assert context.request == request
    assert context.artifact_dir_created is False
    assert context.browser_launch_implemented is False
    assert "No browser launched." in context.safety_notes
    assert "No network captured." in context.safety_notes
    assert "No screenshots captured." in context.safety_notes

    data = context.to_dict()

    assert data["request"]["target_name"] == "demo-lab"
    assert data["request"]["task_name"] == "Capture Dashboard"
    assert data["artifact_dir_created"] is False
    assert data["browser_launch_implemented"] is False
    assert "No browser launched." in data["safety_notes"]


def test_build_playwright_adapter_context_can_create_only_artifact_directory(tmp_path):
    from bugintel.integrations.playwright_runner import (
        BrowserExecutionConfig,
        build_playwright_adapter_context,
        build_playwright_execution_request,
    )

    scope = make_scope()
    plan = build_browser_plan(
        scope=scope,
        start_url="https://demo.example.com/dashboard",
        browser="chromium",
    )

    request = build_playwright_execution_request(
        plan=plan,
        task_name="Capture Dashboard",
        config=BrowserExecutionConfig(allow_live_execution=False),
        base_artifact_dir=tmp_path / "artifacts",
    )

    assert not Path(request.artifacts.artifact_dir).exists()

    context = build_playwright_adapter_context(
        request,
        create_artifact_dir=True,
    )

    assert context.artifact_dir_created is True
    assert Path(request.artifacts.artifact_dir).is_dir()
    assert not Path(request.artifacts.screenshot_path).exists()
    assert not Path(request.artifacts.html_snapshot_path).exists()
    assert not Path(request.artifacts.network_log_path).exists()
    assert not Path(request.artifacts.trace_path).exists()
    assert context.browser_launch_implemented is False



def test_run_playwright_adapter_stub_returns_not_implemented_capture_result():
    from bugintel.integrations.playwright_runner import (
        BrowserExecutionConfig,
        build_playwright_adapter_context,
        build_playwright_execution_request,
        run_playwright_adapter_stub,
    )

    scope = make_scope()
    plan = build_browser_plan(
        scope=scope,
        start_url="https://demo.example.com/dashboard",
        browser="chromium",
    )

    request = build_playwright_execution_request(
        plan=plan,
        task_name="Capture Dashboard",
        config=BrowserExecutionConfig(allow_live_execution=False),
        base_artifact_dir="tmp/artifacts",
    )

    context = build_playwright_adapter_context(request)
    result = run_playwright_adapter_stub(context)

    assert result.target_name == "demo-lab"
    assert result.task_name == "Capture Dashboard"
    assert result.start_url == "https://demo.example.com/dashboard"
    assert result.browser == "chromium"

    assert result.network_events == []
    assert result.screenshots == []
    assert result.html_snapshots == []

    output = result.execution_output

    assert output["runner"] == "playwright"
    assert output["status"] == "not_implemented"
    assert output["browser_launch_implemented"] is False
    assert output["artifact_dir_created"] is False
    assert output["live_execution_allowed"] is False
    assert output["artifacts"]["network_log_path"].endswith("/network.json")
    assert "No browser launched." in output["safety_notes"]
    assert "not implemented yet" in output["reason"]


def test_run_playwright_adapter_stub_preserves_artifact_directory_state(tmp_path):
    from bugintel.integrations.playwright_runner import (
        BrowserExecutionConfig,
        build_playwright_adapter_context,
        build_playwright_execution_request,
        run_playwright_adapter_stub,
    )

    scope = make_scope()
    plan = build_browser_plan(
        scope=scope,
        start_url="https://demo.example.com/dashboard",
        browser="chromium",
    )

    request = build_playwright_execution_request(
        plan=plan,
        task_name="Capture Dashboard",
        config=BrowserExecutionConfig(allow_live_execution=True),
        base_artifact_dir=tmp_path / "artifacts",
    )

    context = build_playwright_adapter_context(
        request,
        create_artifact_dir=True,
    )

    result = run_playwright_adapter_stub(
        context,
        notes="Stub handoff test.",
    )

    output = result.execution_output

    assert output["status"] == "not_implemented"
    assert output["artifact_dir_created"] is True
    assert output["live_execution_allowed"] is True
    assert Path(request.artifacts.artifact_dir).is_dir()

    assert not Path(request.artifacts.screenshot_path).exists()
    assert not Path(request.artifacts.html_snapshot_path).exists()
    assert not Path(request.artifacts.network_log_path).exists()
    assert not Path(request.artifacts.trace_path).exists()

    assert result.notes == "Stub handoff test."



def test_execute_playwright_plan_routes_through_adapter_stub_after_safety_gates(monkeypatch):
    import bugintel.integrations.playwright_runner as playwright_runner

    from bugintel.integrations.playwright_runner import (
        BrowserExecutionConfig,
        PlaywrightAvailability,
        execute_playwright_plan,
    )

    def fake_playwright_available():
        return PlaywrightAvailability(
            available=True,
            reason="Playwright mocked as available for adapter-stub routing test.",
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
        task_name="adapter stub route",
        config=BrowserExecutionConfig(allow_live_execution=True),
        notes="Adapter stub route test.",
    )

    output = result.execution_output

    assert result.target_name == "demo-lab"
    assert result.task_name == "adapter stub route"
    assert result.network_events == []
    assert result.screenshots == []
    assert result.html_snapshots == []
    assert result.notes == "Adapter stub route test."

    assert output["runner"] == "playwright"
    assert output["status"] == "not_implemented"
    assert output["browser_launch_implemented"] is False
    assert output["artifact_dir_created"] is False
    assert output["live_execution_allowed"] is True
    assert output["playwright_available"] is True
    assert output["playwright_availability_reason"] == "Playwright mocked as available for adapter-stub routing test."
    assert output["artifacts"]["screenshot_path"].endswith("/screenshot.png")
    assert output["artifacts"]["html_snapshot_path"].endswith("/page.html")
    assert output["artifacts"]["network_log_path"].endswith("/network.json")
    assert output["artifacts"]["trace_path"].endswith("/trace.zip")
    assert "No browser launched." in output["safety_notes"]


def test_load_browser_capture_result_from_artifacts_reads_planned_files(tmp_path):
    import json

    from bugintel.core.evidence_store import EvidenceStore
    from bugintel.integrations.playwright_runner import (
        BrowserExecutionConfig,
        BrowserHtmlSnapshot,
        BrowserNetworkEvent,
        BrowserScreenshot,
        build_browser_plan,
        build_playwright_adapter_context,
        build_playwright_execution_request,
        load_browser_capture_result_from_artifacts,
    )

    scope = make_scope()
    plan = build_browser_plan(
        scope=scope,
        start_url="https://demo.example.com/dashboard",
        browser="chromium",
    )

    request = build_playwright_execution_request(
        plan=plan,
        task_name="Capture Dashboard",
        config=BrowserExecutionConfig(allow_live_execution=True),
        base_artifact_dir=tmp_path / "artifacts",
    )

    context = build_playwright_adapter_context(
        request,
        create_artifact_dir=True,
    )

    network_path = Path(request.artifacts.network_log_path)
    html_path = Path(request.artifacts.html_snapshot_path)
    screenshot_path = Path(request.artifacts.screenshot_path)

    network_path.write_text(
        json.dumps(
            [
                {
                    "method": "GET",
                    "url": "https://demo.example.com/api/me",
                    "status_code": 200,
                    "resource_type": "fetch",
                    "response_body": '{"email":"sidd@example.com"}',
                }
            ]
        ),
        encoding="utf-8",
    )

    html_path.write_text("<html>sidd@example.com</html>", encoding="utf-8")
    screenshot_path.write_bytes(b"fake png bytes")

    result = load_browser_capture_result_from_artifacts(
        context,
        notes="Loaded planned browser artifacts.",
    )

    assert result.target_name == "demo-lab"
    assert result.task_name == "Capture Dashboard"
    assert result.start_url == "https://demo.example.com/dashboard"
    assert result.browser == "chromium"

    assert isinstance(result.network_events[0], BrowserNetworkEvent)
    assert isinstance(result.screenshots[0], BrowserScreenshot)
    assert isinstance(result.html_snapshots[0], BrowserHtmlSnapshot)

    assert result.network_events[0].method == "GET"
    assert result.screenshots[0].path == str(screenshot_path)
    assert len(result.screenshots[0].sha256) == 64
    assert result.html_snapshots[0].url == "https://demo.example.com/dashboard"

    output = result.execution_output
    assert output["runner"] == "playwright"
    assert output["status"] == "artifacts_loaded"
    assert output["loaded_network_events"] == 1
    assert output["loaded_screenshots"] == 1
    assert output["loaded_html_snapshots"] == 1

    store = EvidenceStore(base_dir=tmp_path / "evidence")
    evidence_path = store.save_browser_evidence(**result.to_evidence_kwargs())

    data = json.loads(evidence_path.read_text(encoding="utf-8"))
    serialized = json.dumps(data)

    assert "sidd@example.com" not in serialized
    assert "<email>" in serialized


def test_run_playwright_adapter_uses_factory_and_loads_artifacts(tmp_path):
    from bugintel.integrations.playwright_runner import (
        BrowserExecutionConfig,
        BrowserHtmlSnapshot,
        BrowserNetworkEvent,
        BrowserScreenshot,
        build_browser_plan,
        build_playwright_adapter_context,
        build_playwright_execution_request,
        run_playwright_adapter,
    )

    class FakeRequest:
        method = "GET"
        resource_type = "document"
        headers = {"Authorization": "Bearer abc.def.ghi"}
        post_data = ""

    class FakeResponse:
        request = FakeRequest()
        url = "https://demo.example.com/api/me"
        status = 200
        headers = {"content-type": "application/json"}

    class FakePage:
        def __init__(self):
            self.handlers = {}

        def on(self, event_name, handler):
            self.handlers[event_name] = handler

        def goto(self, url, wait_until, timeout):
            assert url == "https://demo.example.com/dashboard"
            assert wait_until == "load"
            assert timeout == 15000
            self.handlers["response"](FakeResponse())

        def content(self):
            return "<html>sidd@example.com</html>"

        def screenshot(self, path, full_page):
            assert full_page is True
            Path(path).write_bytes(b"fake png bytes")

    class FakeBrowser:
        def __init__(self):
            self.closed = False

        def new_page(self):
            return FakePage()

        def close(self):
            self.closed = True

    class FakeLauncher:
        def launch(self, **kwargs):
            assert kwargs["headless"] is True
            return FakeBrowser()

    class FakePlaywright:
        chromium = FakeLauncher()
        firefox = FakeLauncher()

    class FakePlaywrightManager:
        def __enter__(self):
            return FakePlaywright()

        def __exit__(self, exc_type, exc, tb):
            return False

    scope = make_scope()
    plan = build_browser_plan(
        scope=scope,
        start_url="https://demo.example.com/dashboard",
        browser="chromium",
    )

    request = build_playwright_execution_request(
        plan=plan,
        task_name="Real Adapter Smoke",
        config=BrowserExecutionConfig(allow_live_execution=True),
        base_artifact_dir=tmp_path / "artifacts",
    )

    context = build_playwright_adapter_context(request)

    result = run_playwright_adapter(
        context,
        notes="Fake Playwright adapter run.",
        playwright_factory=FakePlaywrightManager,
    )

    assert result.target_name == "demo-lab"
    assert result.task_name == "Real Adapter Smoke"
    assert result.start_url == "https://demo.example.com/dashboard"
    assert result.browser == "chromium"

    assert isinstance(result.network_events[0], BrowserNetworkEvent)
    assert isinstance(result.screenshots[0], BrowserScreenshot)
    assert isinstance(result.html_snapshots[0], BrowserHtmlSnapshot)

    assert result.network_events[0].url == "https://demo.example.com/api/me"
    assert result.network_events[0].method == "GET"
    assert result.screenshots[0].path == request.artifacts.screenshot_path
    assert len(result.screenshots[0].sha256) == 64
    assert result.html_snapshots[0].html == "<html>sidd@example.com</html>"

    output = result.execution_output

    assert output["runner"] == "playwright"
    assert output["status"] == "completed"
    assert output["reason"] == "Playwright execution completed."
    assert output["browser_launch_implemented"] is True
    assert output["artifact_dir_created"] is True
    assert output["live_execution_allowed"] is True
    assert output["loaded_network_events"] == 1
    assert output["loaded_screenshots"] == 1
    assert output["loaded_html_snapshots"] == 1


def test_run_playwright_adapter_blocks_without_live_execution(tmp_path):
    from bugintel.integrations.playwright_runner import (
        BrowserExecutionConfig,
        PlaywrightExecutionSafetyError,
        build_browser_plan,
        build_playwright_adapter_context,
        build_playwright_execution_request,
        run_playwright_adapter,
    )

    scope = make_scope()
    plan = build_browser_plan(
        scope=scope,
        start_url="https://demo.example.com/dashboard",
        browser="chromium",
    )

    request = build_playwright_execution_request(
        plan=plan,
        task_name="Blocked Adapter Run",
        config=BrowserExecutionConfig(allow_live_execution=False),
        base_artifact_dir=tmp_path / "artifacts",
    )

    context = build_playwright_adapter_context(request)

    try:
        run_playwright_adapter(context)
    except PlaywrightExecutionSafetyError as exc:
        assert "Live Playwright execution is disabled" in str(exc)
    else:
        raise AssertionError("Expected live execution safety gate to block adapter run")


def test_execute_playwright_plan_uses_real_adapter_only_when_enabled(monkeypatch):
    import bugintel.integrations.playwright_runner as playwright_runner

    from bugintel.integrations.playwright_runner import (
        BrowserCaptureResult,
        BrowserExecutionConfig,
        PlaywrightAvailability,
        build_browser_plan,
        execute_playwright_plan,
    )

    called = {"real_adapter": False}

    def fake_playwright_available():
        return PlaywrightAvailability(
            available=True,
            reason="Playwright mocked as available.",
        )

    def fake_run_playwright_adapter(context, notes=""):
        called["real_adapter"] = True

        assert context.request.config.allow_live_execution is True
        assert context.request.config.use_real_adapter is True
        assert notes == "Route to real adapter."

        return BrowserCaptureResult(
            target_name=context.request.target_name,
            task_name=context.request.task_name,
            start_url=context.request.start_url,
            browser=context.request.browser,
            execution_output={
                "runner": "playwright",
                "status": "completed",
                "reason": "Mocked real adapter.",
                "live_execution_allowed": True,
                "use_real_adapter": True,
            },
            notes=notes,
        )

    monkeypatch.setattr(
        playwright_runner,
        "check_playwright_available",
        fake_playwright_available,
    )
    monkeypatch.setattr(
        playwright_runner,
        "run_playwright_adapter",
        fake_run_playwright_adapter,
    )

    scope = make_scope()
    plan = build_browser_plan(
        scope=scope,
        start_url="https://demo.example.com/dashboard",
        browser="chromium",
    )

    result = execute_playwright_plan(
        plan=plan,
        task_name="real adapter route",
        config=BrowserExecutionConfig(
            allow_live_execution=True,
            use_real_adapter=True,
        ),
        notes="Route to real adapter.",
    )

    assert called["real_adapter"] is True
    assert result.execution_output["status"] == "completed"
    assert result.execution_output["use_real_adapter"] is True
    assert result.notes == "Route to real adapter."


def test_browser_execution_config_defaults_to_stub_adapter():
    from bugintel.integrations.playwright_runner import BrowserExecutionConfig

    config = BrowserExecutionConfig(allow_live_execution=True)

    assert config.allow_live_execution is True
    assert config.use_real_adapter is False
