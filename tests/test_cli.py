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
