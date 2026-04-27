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
