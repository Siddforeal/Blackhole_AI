import json
from pathlib import Path

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def test_save_browser_capture_command_creates_browser_evidence():
    capture = {
        "target_name": "demo-lab",
        "task_name": "capture dashboard",
        "start_url": "https://demo.example.com/dashboard",
        "browser": "chromium",
        "network_events": [
            {
                "method": "GET",
                "url": "https://demo.example.com/api/me",
                "status_code": 200,
                "resource_type": "fetch",
                "request_headers": {
                    "Authorization": "Bearer abc.def.ghi",
                },
                "response_body": '{"email":"sidd@example.com"}',
            }
        ],
        "screenshots": [
            {
                "path": "artifacts/dashboard.png",
                "sha256": "a" * 64,
            }
        ],
        "html_snapshots": [
            {
                "url": "https://demo.example.com/dashboard",
                "html": "<html>sidd@example.com</html>",
            }
        ],
        "execution_output": {
            "runner": "playwright",
            "status": "completed",
            "stdout": "loaded sidd@example.com",
        },
        "notes": "Browser capture for sidd@example.com",
    }

    with runner.isolated_filesystem():
        capture_path = Path("capture-result.json")
        capture_path.write_text(json.dumps(capture), encoding="utf-8")

        result = runner.invoke(app, ["save-browser-capture", str(capture_path)])

        assert result.exit_code == 0
        assert "Browser evidence saved" in result.output

        evidence_files = list(Path("data/evidence/demo-lab").glob("*.json"))
        assert len(evidence_files) == 1

        saved = json.loads(evidence_files[0].read_text(encoding="utf-8"))

        assert saved["kind"] == "browser"
        assert saved["target_name"] == "demo-lab"
        assert saved["task_name"] == "capture dashboard"
        assert saved["browser"] == "chromium"
        assert saved["network_events"][0]["request_headers"]["Authorization"] == "Bearer <redacted>"

        serialized = json.dumps(saved)
        assert "sidd@example.com" not in serialized
        assert "abc.def.ghi" not in serialized


def test_save_browser_capture_command_rejects_missing_required_fields():
    with runner.isolated_filesystem():
        capture_path = Path("bad-capture-result.json")
        capture_path.write_text(
            json.dumps(
                {
                    "target_name": "demo-lab",
                    "browser": "chromium",
                }
            ),
            encoding="utf-8",
        )

        result = runner.invoke(app, ["save-browser-capture", str(capture_path)])

        assert result.exit_code == 2
        assert "missing required fields" in result.output
        assert "task_name" in result.output
        assert "start_url" in result.output


def test_browser_capture_example_can_be_saved_and_reported(tmp_path):
    from bugintel.agents.report_agent import save_evidence_report

    example = Path("examples/browser_capture_result.example.json")
    assert example.exists()
    example_text = example.read_text(encoding="utf-8")

    with runner.isolated_filesystem():
        capture_path = Path("capture-result.json")
        capture_path.write_text(example_text, encoding="utf-8")

        result = runner.invoke(app, ["save-browser-capture", str(capture_path)])

        assert result.exit_code == 0
        assert "Browser evidence saved" in result.output

        evidence_files = list(Path("data/evidence/demo-lab").glob("*.json"))
        assert len(evidence_files) == 1

        report_path = Path("browser-report.md")
        save_evidence_report(evidence_files[0], report_path)

        report = report_path.read_text(encoding="utf-8")

        assert "Evidence Type: browser" in report
        assert "## Browser Network Events" in report
        assert "researcher@example.com" not in json.dumps(json.loads(evidence_files[0].read_text(encoding="utf-8")))
        assert "<email>" in report


def test_preview_playwright_command_writes_json_preview():
    scope_yaml = """
target_name: demo-lab
allowed_domains:
  - demo.example.com
  - "*.demo.example.com"
allowed_schemes:
  - https
allowed_methods:
  - GET
  - HEAD
  - OPTIONS
forbidden_paths:
  - /logout
  - /delete*
human_approval_required: true
"""

    with runner.isolated_filesystem():
        scope_path = Path("scope.yaml")
        output_path = Path("preview.json")
        scope_path.write_text(scope_yaml, encoding="utf-8")

        result = runner.invoke(
            app,
            [
                "preview-playwright",
                str(scope_path),
                "https://demo.example.com/dashboard",
                "--browser",
                "chromium",
                "--timeout-ms",
                "10000",
                "--screenshot-path",
                "artifacts/demo-dashboard.png",
                "--json-output",
                str(output_path),
            ],
        )

        assert result.exit_code == 0
        assert "Playwright Execution Preview" in result.output
        assert "Preview JSON saved" in result.output
        assert output_path.exists()

        preview = json.loads(output_path.read_text(encoding="utf-8"))

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


def test_preview_playwright_command_blocks_out_of_scope_url():
    scope_yaml = """
target_name: demo-lab
allowed_domains:
  - demo.example.com
allowed_schemes:
  - https
allowed_methods:
  - GET
  - HEAD
  - OPTIONS
forbidden_paths: []
human_approval_required: true
"""

    with runner.isolated_filesystem():
        scope_path = Path("scope.yaml")
        scope_path.write_text(scope_yaml, encoding="utf-8")

        result = runner.invoke(
            app,
            [
                "preview-playwright",
                str(scope_path),
                "https://evil.example.net/dashboard",
            ],
        )

        assert result.exit_code == 2
        assert "Browser plan blocked" in result.output
        assert "Domain not in" in result.output
        assert "scope: evil.example.net" in result.output


def test_execute_playwright_plan_command_blocks_by_default():
    scope_yaml = """
target_name: demo-lab
allowed_domains:
  - demo.example.com
allowed_schemes:
  - https
allowed_methods:
  - GET
  - HEAD
  - OPTIONS
forbidden_paths: []
human_approval_required: true
"""

    with runner.isolated_filesystem():
        scope_path = Path("scope.yaml")
        scope_path.write_text(scope_yaml, encoding="utf-8")

        result = runner.invoke(
            app,
            [
                "execute-playwright-plan",
                str(scope_path),
                "https://demo.example.com/dashboard",
            ],
        )

        assert result.exit_code == 2
        assert "Playwright execution blocked" in result.output
        assert "Live Playwright execution is disabled" in result.output


def test_execute_playwright_plan_command_blocks_out_of_scope_url():
    scope_yaml = """
target_name: demo-lab
allowed_domains:
  - demo.example.com
allowed_schemes:
  - https
allowed_methods:
  - GET
  - HEAD
  - OPTIONS
forbidden_paths: []
human_approval_required: true
"""

    with runner.isolated_filesystem():
        scope_path = Path("scope.yaml")
        scope_path.write_text(scope_yaml, encoding="utf-8")

        result = runner.invoke(
            app,
            [
                "execute-playwright-plan",
                str(scope_path),
                "https://evil.example.net/dashboard",
                "--allow-live-execution",
            ],
        )

        assert result.exit_code == 2
        assert "Playwright execution blocked" in result.output
        assert "Cannot execute blocked browser plan" in result.output
        assert "Domain not in" in result.output
        assert "scope: evil.example.net" in result.output


def test_execute_playwright_plan_command_blocks_by_default():
    scope_yaml = """
target_name: demo-lab
allowed_domains:
  - demo.example.com
allowed_schemes:
  - https
allowed_methods:
  - GET
  - HEAD
  - OPTIONS
forbidden_paths: []
human_approval_required: true
"""

    with runner.isolated_filesystem():
        scope_path = Path("scope.yaml")
        scope_path.write_text(scope_yaml, encoding="utf-8")

        result = runner.invoke(
            app,
            [
                "execute-playwright-plan",
                str(scope_path),
                "https://demo.example.com/dashboard",
            ],
        )

        assert result.exit_code == 2
        assert "Playwright execution blocked" in result.output
        assert "Live Playwright execution is disabled" in result.output


def test_execute_playwright_plan_command_blocks_out_of_scope_url():
    scope_yaml = """
target_name: demo-lab
allowed_domains:
  - demo.example.com
allowed_schemes:
  - https
allowed_methods:
  - GET
  - HEAD
  - OPTIONS
forbidden_paths: []
human_approval_required: true
"""

    with runner.isolated_filesystem():
        scope_path = Path("scope.yaml")
        scope_path.write_text(scope_yaml, encoding="utf-8")

        result = runner.invoke(
            app,
            [
                "execute-playwright-plan",
                str(scope_path),
                "https://evil.example.net/dashboard",
                "--allow-live-execution",
            ],
        )

        assert result.exit_code == 2
        assert "Playwright execution blocked" in result.output
        assert "Cannot execute blocked browser plan" in result.output
        assert "Domain not in" in result.output
        assert "scope: evil.example.net" in result.output


def test_execute_playwright_plan_command_writes_json_when_skeleton_reaches_handoff(monkeypatch):
    import bugintel.cli as cli_module
    from bugintel.integrations.playwright_runner import BrowserCaptureResult

    scope_yaml = """
target_name: demo-lab
allowed_domains:
  - demo.example.com
allowed_schemes:
  - https
allowed_methods:
  - GET
  - HEAD
  - OPTIONS
forbidden_paths: []
human_approval_required: true
"""

    def fake_execute_playwright_plan(plan, task_name, config, notes):
        return BrowserCaptureResult(
            target_name=plan.target_name,
            task_name=task_name,
            start_url=plan.start_url,
            browser=plan.browser,
            execution_output={
                "runner": "playwright",
                "status": "not_implemented",
                "reason": "Mocked handoff; browser not launched.",
                "live_execution_allowed": config.allow_live_execution,
                "playwright_available": True,
            },
            notes=notes,
        )

    monkeypatch.setattr(
        cli_module,
        "execute_playwright_plan",
        fake_execute_playwright_plan,
    )

    with runner.isolated_filesystem():
        scope_path = Path("scope.yaml")
        output_path = Path("capture-result.json")
        scope_path.write_text(scope_yaml, encoding="utf-8")

        result = runner.invoke(
            app,
            [
                "execute-playwright-plan",
                str(scope_path),
                "https://demo.example.com/dashboard",
                "--task-name",
                "mocked cli handoff",
                "--allow-live-execution",
                "--json-output",
                str(output_path),
            ],
        )

        assert result.exit_code == 0
        assert "Playwright Execution Skeleton" in result.output
        assert "Capture result JSON saved" in result.output
        assert output_path.exists()

        data = json.loads(output_path.read_text(encoding="utf-8"))

        assert data["target_name"] == "demo-lab"
        assert data["task_name"] == "mocked cli handoff"
        assert data["start_url"] == "https://demo.example.com/dashboard"
        assert data["browser"] == "chromium"
        assert data["execution_output"]["runner"] == "playwright"
        assert data["execution_output"]["status"] == "not_implemented"
        assert data["execution_output"]["live_execution_allowed"] is True
        assert data["execution_output"]["playwright_available"] is True
        assert data["network_events"] == []
        assert data["screenshots"] == []
        assert data["html_snapshots"] == []



def test_execute_playwright_json_handoff_can_be_saved_and_reported(monkeypatch):
    import bugintel.cli as cli_module
    from bugintel.integrations.playwright_runner import BrowserCaptureResult

    scope_yaml = """
target_name: demo-lab
allowed_domains:
  - demo.example.com
allowed_schemes:
  - https
allowed_methods:
  - GET
  - HEAD
  - OPTIONS
forbidden_paths: []
human_approval_required: true
"""

    def fake_execute_playwright_plan(plan, task_name, config, notes):
        return BrowserCaptureResult(
            target_name=plan.target_name,
            task_name=task_name,
            start_url=plan.start_url,
            browser=plan.browser,
            execution_output={
                "runner": "playwright",
                "status": "not_implemented",
                "reason": "Mocked handoff; browser not launched.",
                "live_execution_allowed": config.allow_live_execution,
                "playwright_available": True,
            },
            notes=notes,
        )

    monkeypatch.setattr(
        cli_module,
        "execute_playwright_plan",
        fake_execute_playwright_plan,
    )

    with runner.isolated_filesystem():
        scope_path = Path("scope.yaml")
        capture_result_path = Path("capture-result.json")
        report_path = Path("report.md")

        scope_path.write_text(scope_yaml, encoding="utf-8")

        execute_result = runner.invoke(
            app,
            [
                "execute-playwright-plan",
                str(scope_path),
                "https://demo.example.com/dashboard",
                "--task-name",
                "mocked full cli chain",
                "--allow-live-execution",
                "--json-output",
                str(capture_result_path),
            ],
        )

        assert execute_result.exit_code == 0
        assert capture_result_path.exists()

        save_result = runner.invoke(
            app,
            [
                "save-browser-capture",
                str(capture_result_path),
            ],
        )

        assert save_result.exit_code == 0
        assert "Browser evidence saved" in save_result.output

        evidence_files = list(Path("data/evidence/demo-lab").glob("*.json"))
        assert len(evidence_files) == 1

        report_result = runner.invoke(
            app,
            [
                "generate-report",
                str(evidence_files[0]),
                "--output",
                str(report_path),
            ],
        )

        assert report_result.exit_code == 0
        assert report_path.exists()

        report = report_path.read_text(encoding="utf-8")

        assert "Evidence Type: browser" in report
        assert "## Browser Execution Output" in report
        assert "Runner: playwright" in report
        assert "Status: not_implemented" in report
        assert "Mocked handoff; browser not launched." in report



def test_build_playwright_request_command_writes_json_request():
    scope_yaml = """
target_name: demo-lab
allowed_domains:
  - demo.example.com
allowed_schemes:
  - https
allowed_methods:
  - GET
  - HEAD
  - OPTIONS
forbidden_paths: []
human_approval_required: true
"""

    with runner.isolated_filesystem():
        scope_path = Path("scope.yaml")
        output_path = Path("request.json")
        scope_path.write_text(scope_yaml, encoding="utf-8")

        result = runner.invoke(
            app,
            [
                "build-playwright-request",
                str(scope_path),
                "https://demo.example.com/dashboard",
                "--task-name",
                "Capture Dashboard",
                "--browser",
                "chromium",
                "--timeout-ms",
                "10000",
                "--base-artifact-dir",
                "tmp/artifacts",
                "--json-output",
                str(output_path),
            ],
        )

        assert result.exit_code == 0
        assert "Playwright Execution Request" in result.output
        assert "Request JSON saved" in result.output
        assert output_path.exists()

        data = json.loads(output_path.read_text(encoding="utf-8"))

        assert data["target_name"] == "demo-lab"
        assert data["task_name"] == "Capture Dashboard"
        assert data["start_url"] == "https://demo.example.com/dashboard"
        assert data["browser"] == "chromium"
        assert data["config"]["timeout_ms"] == 10000
        assert data["config"]["allow_live_execution"] is False
        assert data["artifacts"]["artifact_dir"] == "tmp/artifacts/demo-lab/capture-dashboard"
        assert data["artifacts"]["screenshot_path"].endswith("/screenshot.png")
        assert data["artifacts"]["html_snapshot_path"].endswith("/page.html")
        assert data["artifacts"]["network_log_path"].endswith("/network.json")
        assert data["artifacts"]["trace_path"].endswith("/trace.zip")

        action_types = [
            action["action_type"]
            for action in data["planned_actions"]
        ]

        assert "navigate" in action_types
        assert "capture_network" in action_types
        assert "capture_screenshot" in action_types
        assert "extract_html" in action_types


def test_build_playwright_request_command_blocks_out_of_scope_url():
    scope_yaml = """
target_name: demo-lab
allowed_domains:
  - demo.example.com
allowed_schemes:
  - https
allowed_methods:
  - GET
  - HEAD
  - OPTIONS
forbidden_paths: []
human_approval_required: true
"""

    with runner.isolated_filesystem():
        scope_path = Path("scope.yaml")
        scope_path.write_text(scope_yaml, encoding="utf-8")

        result = runner.invoke(
            app,
            [
                "build-playwright-request",
                str(scope_path),
                "https://evil.example.net/dashboard",
            ],
        )

        assert result.exit_code == 2
        assert "Playwright request blocked" in result.output
        assert "Domain not in" in result.output
        assert "scope: evil.example.net" in result.output



def test_playwright_request_example_matches_request_shape():
    example = Path("examples/playwright_request.example.json")
    assert example.exists()

    data = json.loads(example.read_text(encoding="utf-8"))

    assert data["target_name"] == "demo-lab"
    assert data["task_name"] == "Capture Dashboard"
    assert data["start_url"] == "https://demo.example.com/dashboard"
    assert data["browser"] == "chromium"

    assert data["config"]["allow_live_execution"] is False
    assert data["config"]["capture_network"] is True
    assert data["config"]["capture_screenshot"] is True
    assert data["config"]["capture_html"] is True

    assert data["artifacts"]["artifact_dir"] == "artifacts/browser/demo-lab/capture-dashboard"
    assert data["artifacts"]["screenshot_path"].endswith("/screenshot.png")
    assert data["artifacts"]["html_snapshot_path"].endswith("/page.html")
    assert data["artifacts"]["network_log_path"].endswith("/network.json")
    assert data["artifacts"]["trace_path"].endswith("/trace.zip")

    action_types = [
        action["action_type"]
        for action in data["planned_actions"]
    ]

    assert action_types == [
        "navigate",
        "capture_network",
        "capture_screenshot",
        "extract_html",
    ]



def test_preview_playwright_request_command_writes_json_preview():
    example = Path("examples/playwright_request.example.json")
    assert example.exists()
    example_text = example.read_text(encoding="utf-8")

    with runner.isolated_filesystem():
        request_path = Path("request.json")
        output_path = Path("preview.json")
        request_path.write_text(example_text, encoding="utf-8")

        result = runner.invoke(
            app,
            [
                "preview-playwright-request",
                str(request_path),
                "--json-output",
                str(output_path),
            ],
        )

        assert result.exit_code == 0
        assert "Playwright Request Preview" in result.output
        assert "Preview JSON saved" in result.output
        assert output_path.exists()

        preview = json.loads(output_path.read_text(encoding="utf-8"))

        assert preview["target_name"] == "demo-lab"
        assert preview["task_name"] == "Capture Dashboard"
        assert preview["runner"] == "playwright"
        assert preview["status"] == "preview"
        assert preview["browser"] == "chromium"
        assert preview["start_url"] == "https://demo.example.com/dashboard"
        assert preview["live_execution_allowed"] is False
        assert preview["artifacts"]["network_log_path"].endswith("/network.json")

        action_types = [
            action["action_type"]
            for action in preview["planned_actions"]
        ]

        assert action_types == [
            "navigate",
            "capture_network",
            "capture_screenshot",
            "extract_html",
        ]


def test_preview_playwright_request_command_rejects_missing_required_fields():
    with runner.isolated_filesystem():
        request_path = Path("bad-request.json")
        request_path.write_text(
            json.dumps(
                {
                    "target_name": "demo-lab",
                    "browser": "chromium",
                }
            ),
            encoding="utf-8",
        )

        result = runner.invoke(
            app,
            [
                "preview-playwright-request",
                str(request_path),
            ],
        )

        assert result.exit_code == 2
        assert "missing required fields" in result.output
        assert "task_name" in result.output
        assert "start_url" in result.output
        assert "config" in result.output



def test_execute_playwright_request_command_blocks_by_default():
    request_example = Path("examples/playwright_request.example.json")
    scope_example = Path("examples/target.example.yaml")
    assert request_example.exists()
    assert scope_example.exists()

    request_text = request_example.read_text(encoding="utf-8")
    scope_text = scope_example.read_text(encoding="utf-8")

    with runner.isolated_filesystem():
        request_path = Path("request.json")
        scope_path = Path("scope.yaml")

        request_path.write_text(request_text, encoding="utf-8")
        scope_path.write_text(scope_text, encoding="utf-8")

        result = runner.invoke(
            app,
            [
                "execute-playwright-request",
                str(request_path),
                str(scope_path),
            ],
        )

        assert result.exit_code == 2
        assert "Playwright request execution blocked" in result.output
        assert "Live Playwright execution is disabled" in result.output


def test_execute_playwright_request_command_revalidates_scope():
    request_example = Path("examples/playwright_request.example.json")
    assert request_example.exists()

    request_data = json.loads(request_example.read_text(encoding="utf-8"))
    request_data["start_url"] = "https://evil.example.net/dashboard"

    scope_yaml = """
target_name: demo-lab
allowed_domains:
  - demo.example.com
allowed_schemes:
  - https
allowed_methods:
  - GET
  - HEAD
  - OPTIONS
forbidden_paths: []
human_approval_required: true
"""

    with runner.isolated_filesystem():
        request_path = Path("request.json")
        scope_path = Path("scope.yaml")

        request_path.write_text(json.dumps(request_data), encoding="utf-8")
        scope_path.write_text(scope_yaml, encoding="utf-8")

        result = runner.invoke(
            app,
            [
                "execute-playwright-request",
                str(request_path),
                str(scope_path),
                "--allow-live-execution",
            ],
        )

        assert result.exit_code == 2
        assert "Playwright request execution blocked" in result.output
        assert "Domain not in" in result.output
        assert "scope: evil.example.net" in result.output


def test_execute_playwright_request_command_writes_json_when_handoff_reached(monkeypatch):
    import bugintel.cli as cli_module
    from bugintel.integrations.playwright_runner import BrowserCaptureResult

    request_example = Path("examples/playwright_request.example.json")
    scope_example = Path("examples/target.example.yaml")
    assert request_example.exists()
    assert scope_example.exists()

    request_text = request_example.read_text(encoding="utf-8")
    scope_text = scope_example.read_text(encoding="utf-8")

    def fake_execute_playwright_plan(plan, task_name, config, notes):
        return BrowserCaptureResult(
            target_name=plan.target_name,
            task_name=task_name,
            start_url=plan.start_url,
            browser=plan.browser,
            execution_output={
                "runner": "playwright",
                "status": "not_implemented",
                "reason": "Mocked request handoff; browser not launched.",
                "live_execution_allowed": config.allow_live_execution,
                "playwright_available": True,
            },
            notes=notes,
        )

    monkeypatch.setattr(
        cli_module,
        "execute_playwright_plan",
        fake_execute_playwright_plan,
    )

    with runner.isolated_filesystem():
        request_path = Path("request.json")
        scope_path = Path("scope.yaml")
        output_path = Path("capture-result.json")

        request_path.write_text(request_text, encoding="utf-8")
        scope_path.write_text(scope_text, encoding="utf-8")

        result = runner.invoke(
            app,
            [
                "execute-playwright-request",
                str(request_path),
                str(scope_path),
                "--allow-live-execution",
                "--json-output",
                str(output_path),
            ],
        )

        assert result.exit_code == 0
        assert "Playwright Request Execution Skeleton" in result.output
        assert "Capture result JSON saved" in result.output
        assert output_path.exists()

        data = json.loads(output_path.read_text(encoding="utf-8"))

        assert data["target_name"] == "demo-lab"
        assert data["task_name"] == "Capture Dashboard"
        assert data["start_url"] == "https://demo.example.com/dashboard"
        assert data["browser"] == "chromium"
        assert data["execution_output"]["runner"] == "playwright"
        assert data["execution_output"]["status"] == "not_implemented"
        assert data["execution_output"]["live_execution_allowed"] is True
        assert data["execution_output"]["playwright_available"] is True


def test_load_browser_artifacts_command_writes_capture_result_json():
    request_example = Path("examples/playwright_request.example.json")
    assert request_example.exists()

    request_data = json.loads(request_example.read_text(encoding="utf-8"))

    with runner.isolated_filesystem():
        request_path = Path("request.json")
        output_path = Path("capture-result.json")

        request_path.write_text(json.dumps(request_data), encoding="utf-8")

        artifacts = request_data["artifacts"]
        network_path = Path(artifacts["network_log_path"])
        html_path = Path(artifacts["html_snapshot_path"])
        screenshot_path = Path(artifacts["screenshot_path"])

        network_path.parent.mkdir(parents=True, exist_ok=True)

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

        result = runner.invoke(
            app,
            [
                "load-browser-artifacts",
                str(request_path),
                "--json-output",
                str(output_path),
            ],
        )

        assert result.exit_code == 0
        assert "Browser Artifacts Loaded" in result.output
        assert "Capture result JSON saved" in result.output
        assert output_path.exists()

        data = json.loads(output_path.read_text(encoding="utf-8"))

        assert data["target_name"] == "demo-lab"
        assert data["task_name"] == "Capture Dashboard"
        assert data["browser"] == "chromium"
        assert data["execution_output"]["status"] == "artifacts_loaded"
        assert data["execution_output"]["loaded_network_events"] == 1
        assert data["execution_output"]["loaded_screenshots"] == 1
        assert data["execution_output"]["loaded_html_snapshots"] == 1
        assert data["network_events"][0]["url"] == "https://demo.example.com/api/me"
        assert data["html_snapshots"][0]["url"] == "https://demo.example.com/dashboard"
        assert len(data["screenshots"][0]["sha256"]) == 64


def test_build_playwright_request_command_records_real_adapter_flag():
    scope_yaml = """
target_name: demo-lab
allowed_domains:
  - demo.example.com
allowed_schemes:
  - https
allowed_methods:
  - GET
  - HEAD
  - OPTIONS
forbidden_paths: []
human_approval_required: true
"""

    with runner.isolated_filesystem():
        scope_path = Path("scope.yaml")
        output_path = Path("request.json")
        scope_path.write_text(scope_yaml, encoding="utf-8")

        result = runner.invoke(
            app,
            [
                "build-playwright-request",
                str(scope_path),
                "https://demo.example.com/dashboard",
                "--allow-live-execution",
                "--use-real-adapter",
                "--json-output",
                str(output_path),
            ],
        )

        assert result.exit_code == 0
        assert "Use real adapter" in result.output
        assert output_path.exists()

        data = json.loads(output_path.read_text(encoding="utf-8"))

        assert data["config"]["allow_live_execution"] is True
        assert data["config"]["use_real_adapter"] is True


def test_execute_playwright_plan_command_passes_real_adapter_flag(monkeypatch):
    import bugintel.cli as cli_module
    from bugintel.integrations.playwright_runner import BrowserCaptureResult

    scope_yaml = """
target_name: demo-lab
allowed_domains:
  - demo.example.com
allowed_schemes:
  - https
allowed_methods:
  - GET
  - HEAD
  - OPTIONS
forbidden_paths: []
human_approval_required: true
"""

    def fake_execute_playwright_plan(plan, task_name, config, notes):
        return BrowserCaptureResult(
            target_name=plan.target_name,
            task_name=task_name,
            start_url=plan.start_url,
            browser=plan.browser,
            execution_output={
                "runner": "playwright",
                "status": "completed",
                "reason": "Mocked real adapter route.",
                "live_execution_allowed": config.allow_live_execution,
                "use_real_adapter": config.use_real_adapter,
                "playwright_available": True,
            },
            notes=notes,
        )

    monkeypatch.setattr(
        cli_module,
        "execute_playwright_plan",
        fake_execute_playwright_plan,
    )

    with runner.isolated_filesystem():
        scope_path = Path("scope.yaml")
        output_path = Path("capture-result.json")
        scope_path.write_text(scope_yaml, encoding="utf-8")

        result = runner.invoke(
            app,
            [
                "execute-playwright-plan",
                str(scope_path),
                "https://demo.example.com/dashboard",
                "--allow-live-execution",
                "--use-real-adapter",
                "--json-output",
                str(output_path),
            ],
        )

        assert result.exit_code == 0
        assert "Use real adapter" in result.output
        assert output_path.exists()

        data = json.loads(output_path.read_text(encoding="utf-8"))

        assert data["execution_output"]["live_execution_allowed"] is True
        assert data["execution_output"]["use_real_adapter"] is True


def test_execute_playwright_request_command_passes_real_adapter_flag(monkeypatch):
    import bugintel.cli as cli_module
    from bugintel.integrations.playwright_runner import BrowserCaptureResult

    request_example = Path("examples/playwright_request.example.json")
    scope_example = Path("examples/target.example.yaml")
    assert request_example.exists()
    assert scope_example.exists()

    request_text = request_example.read_text(encoding="utf-8")
    scope_text = scope_example.read_text(encoding="utf-8")

    def fake_execute_playwright_plan(plan, task_name, config, notes):
        return BrowserCaptureResult(
            target_name=plan.target_name,
            task_name=task_name,
            start_url=plan.start_url,
            browser=plan.browser,
            execution_output={
                "runner": "playwright",
                "status": "completed",
                "reason": "Mocked request real adapter route.",
                "live_execution_allowed": config.allow_live_execution,
                "use_real_adapter": config.use_real_adapter,
                "playwright_available": True,
            },
            notes=notes,
        )

    monkeypatch.setattr(
        cli_module,
        "execute_playwright_plan",
        fake_execute_playwright_plan,
    )

    with runner.isolated_filesystem():
        request_path = Path("request.json")
        scope_path = Path("scope.yaml")
        output_path = Path("capture-result.json")

        request_path.write_text(request_text, encoding="utf-8")
        scope_path.write_text(scope_text, encoding="utf-8")

        result = runner.invoke(
            app,
            [
                "execute-playwright-request",
                str(request_path),
                str(scope_path),
                "--allow-live-execution",
                "--use-real-adapter",
                "--json-output",
                str(output_path),
            ],
        )

        assert result.exit_code == 0
        assert "Use real adapter" in result.output
        assert output_path.exists()

        data = json.loads(output_path.read_text(encoding="utf-8"))

        assert data["execution_output"]["live_execution_allowed"] is True
        assert data["execution_output"]["use_real_adapter"] is True


def test_plan_research_command_writes_json_plan():
    evidence = {
        "target_name": "demo-lab",
        "task_name": "capture dashboard",
        "evidence_type": "browser",
        "network_events": [
            {
                "method": "GET",
                "url": "https://demo.example.com/api/accounts/123/users",
                "status_code": 200,
                "resource_type": "fetch",
            }
        ],
        "screenshots": [
            {
                "path": "artifacts/browser/demo/screenshot.png",
                "sha256": "a" * 64,
            }
        ],
        "html_snapshots": [
            {
                "url": "https://demo.example.com/dashboard",
                "html_sha256": "b" * 64,
            }
        ],
    }

    with runner.isolated_filesystem():
        evidence_path = Path("browser-evidence.json")
        output_path = Path("research-plan.json")

        evidence_path.write_text(json.dumps(evidence), encoding="utf-8")

        result = runner.invoke(
            app,
            [
                "plan-research",
                str(evidence_path),
                "--json-output",
                str(output_path),
            ],
        )

        assert result.exit_code == 0
        assert "Research Plan" in result.output
        assert "Research Hypotheses" in result.output
        assert "Research Recommendations" in result.output
        assert "Research plan JSON saved" in result.output
        assert output_path.exists()

        data = json.loads(output_path.read_text(encoding="utf-8"))

        assert data["target_name"] == "demo-lab"
        assert data["source_evidence_type"] == "browser"
        assert data["generated_by"] == "deterministic"
        assert len(data["hypotheses"]) >= 2
        assert data["recommendations"][0]["priority"] == 1


def test_plan_research_command_blocks_missing_file():
    with runner.isolated_filesystem():
        result = runner.invoke(
            app,
            [
                "plan-research",
                "missing.json",
            ],
        )

        assert result.exit_code == 1
        assert "Evidence file not found" in result.output


def test_plan_research_command_blocks_invalid_json():
    with runner.isolated_filesystem():
        evidence_path = Path("broken.json")
        evidence_path.write_text("{not-json", encoding="utf-8")

        result = runner.invoke(
            app,
            [
                "plan-research",
                str(evidence_path),
            ],
        )

        assert result.exit_code == 2
        assert "Invalid JSON evidence file" in result.output


def test_plan_research_command_accepts_saved_evidence_wrapper():
    evidence = {
        "target_name": "saved-lab",
        "task_name": "saved browser evidence",
        "evidence_type": "browser",
        "payload": {
            "network_events": [
                {
                    "method": "GET",
                    "url": "https://demo.example.com/api/accounts/123/users",
                    "status_code": 200,
                    "resource_type": "fetch",
                }
            ],
            "screenshots": [],
            "html_snapshots": [],
        },
    }

    with runner.isolated_filesystem():
        evidence_path = Path("saved-evidence.json")
        output_path = Path("research-plan.json")

        evidence_path.write_text(json.dumps(evidence), encoding="utf-8")

        result = runner.invoke(
            app,
            [
                "plan-research",
                str(evidence_path),
                "--json-output",
                str(output_path),
            ],
        )

        assert result.exit_code == 0
        assert "Research Plan" in result.output
        assert output_path.exists()

        data = json.loads(output_path.read_text(encoding="utf-8"))

        assert data["target_name"] == "saved-lab"
        assert data["source_evidence_type"] == "browser"
        assert len(data["hypotheses"]) >= 2


def test_plan_research_command_writes_markdown_plan():
    evidence = {
        "target_name": "demo-lab",
        "task_name": "capture dashboard",
        "evidence_type": "browser",
        "network_events": [
            {
                "method": "GET",
                "url": "https://demo.example.com/api/accounts/123/users",
                "status_code": 200,
                "resource_type": "fetch",
            }
        ],
    }

    with runner.isolated_filesystem():
        evidence_path = Path("browser-evidence.json")
        output_path = Path("research-plan.md")

        evidence_path.write_text(json.dumps(evidence), encoding="utf-8")

        result = runner.invoke(
            app,
            [
                "plan-research",
                str(evidence_path),
                "--markdown-output",
                str(output_path),
            ],
        )

        assert result.exit_code == 0
        assert "Research plan Markdown saved" in result.output
        assert output_path.exists()

        markdown = output_path.read_text(encoding="utf-8")

        assert "# Research Plan: demo-lab" in markdown
        assert "## Hypotheses" in markdown
        assert "## Recommendations" in markdown
        assert "Browser-observed API surface" in markdown


def test_build_llm_prompt_command_writes_json_and_markdown():
    research_plan = {
        "target_name": "demo-lab",
        "source_evidence_type": "browser",
        "generated_by": "deterministic",
        "hypotheses": [
            {
                "title": "API route may need authorization review",
                "category": "api-authorization",
                "rationale": "Browser evidence includes API requests.",
                "confidence": "medium",
                "evidence": [
                    {
                        "evidence_type": "browser",
                        "source": "capture dashboard",
                        "locator": "network_events",
                        "summary": "GET /api/accounts/123/users",
                        "tags": ["api"],
                    }
                ],
                "suggested_tests": [
                    "Compare own-object, foreign-object, random-object, and unauthenticated responses."
                ],
                "tags": ["api", "bac"],
            }
        ],
        "recommendations": [
            {
                "priority": 1,
                "title": "Review browser-observed API routes",
                "reason": "The plan identified API routes.",
                "next_actions": ["Group API requests by authorization boundary."],
                "related_hypotheses": ["API route may need authorization review"],
                "safety_notes": ["Keep tests in scope."],
            }
        ],
        "safety_notes": ["Use Scope Guard before testing."],
    }

    with runner.isolated_filesystem():
        plan_path = Path("research-plan.json")
        json_path = Path("llm-prompt.json")
        markdown_path = Path("llm-prompt.md")

        plan_path.write_text(json.dumps(research_plan), encoding="utf-8")

        result = runner.invoke(
            app,
            [
                "build-llm-prompt",
                str(plan_path),
                "--json-output",
                str(json_path),
                "--markdown-output",
                str(markdown_path),
            ],
        )

        assert result.exit_code == 0
        assert "LLM Prompt Package" in result.output
        assert "LLM prompt package JSON saved" in result.output
        assert "LLM prompt package Markdown saved" in result.output
        assert json_path.exists()
        assert markdown_path.exists()

        data = json.loads(json_path.read_text(encoding="utf-8"))
        markdown = markdown_path.read_text(encoding="utf-8")

        assert data["source"] == "research_plan"
        assert "Review this deterministic BugIntel research plan" in data["user_prompt"]
        assert "# LLM Prompt Package" in markdown
        assert "## System Prompt" in markdown
        assert "## User Prompt" in markdown


def test_build_llm_prompt_command_blocks_missing_file():
    with runner.isolated_filesystem():
        result = runner.invoke(
            app,
            [
                "build-llm-prompt",
                "missing-plan.json",
            ],
        )

        assert result.exit_code == 1
        assert "Research plan file not found" in result.output


def test_build_llm_prompt_command_blocks_invalid_json():
    with runner.isolated_filesystem():
        plan_path = Path("broken-plan.json")
        plan_path.write_text("{not-json", encoding="utf-8")

        result = runner.invoke(
            app,
            [
                "build-llm-prompt",
                str(plan_path),
            ],
        )

        assert result.exit_code == 2
        assert "Invalid research plan JSON" in result.output
