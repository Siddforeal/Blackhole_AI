import json

from bugintel.agents.report_agent import (
    generate_evidence_report,
    load_evidence,
    save_evidence_report,
)


def sample_evidence():
    return {
        "target_name": "local-demo-api",
        "task_name": "curl GET http://127.0.0.1:8765/api/users/me",
        "method": "GET",
        "url": "http://127.0.0.1:8765/api/users/me",
        "status_code": 200,
        "created_at": "2026-04-27T13:17:00+00:00",
        "response_headers": {
            "content-type": "application/json",
            "server": "BaseHTTP/0.6 Python/3.13.12",
        },
        "response_body_preview": '{"id": 1, "email": "<email>", "role": "researcher"}',
        "response_body_sha256": "a" * 64,
        "notes": "Captured by bugintel run-curl",
    }


def test_generate_evidence_report_contains_key_sections():
    report = generate_evidence_report(sample_evidence())

    assert "# Evidence Report:" in report
    assert "## Summary" in report
    assert "## Response Headers" in report
    assert "## Response Body Preview" in report
    assert "## Analyst Review Checklist" in report
    assert "<email>" in report
    assert "Status Code: 200" in report


def test_save_and_load_evidence_report(tmp_path):
    evidence_path = tmp_path / "evidence.json"
    output_path = tmp_path / "report.md"

    evidence_path.write_text(json.dumps(sample_evidence()), encoding="utf-8")

    loaded = load_evidence(evidence_path)
    assert loaded["target_name"] == "local-demo-api"

    saved = save_evidence_report(evidence_path, output_path)

    assert saved.exists()
    content = saved.read_text(encoding="utf-8")
    assert "local-demo-api" in content
    assert "Analyst Review Checklist" in content


def sample_browser_evidence():
    return {
        "kind": "browser",
        "target_name": "demo-lab",
        "task_name": "capture dashboard",
        "start_url": "https://demo.example.com/dashboard",
        "browser": "chromium",
        "created_at": "2026-04-27T18:30:00+00:00",
        "network_events": [
            {
                "method": "POST",
                "url": "https://demo.example.com/api/session",
                "status_code": 200,
                "resource_type": "fetch",
                "request_headers": {
                    "Authorization": "Bearer <redacted>",
                },
                "response_headers": {
                    "content-type": "application/json",
                },
                "request_post_data_preview": '{"email":"<email>"}',
                "response_body_preview": '{"email":"<email>","role":"admin"}',
                "response_body_sha256": "b" * 64,
            }
        ],
        "screenshots": [
            {
                "path": "artifacts/dashboard.png",
                "sha256": "c" * 64,
                "content_type": "image/png",
            }
        ],
        "html_snapshots": [
            {
                "url": "https://demo.example.com/dashboard",
                "html_preview": "<html><body><email></body></html>",
                "html_sha256": "d" * 64,
            }
        ],
        "execution_output": {
            "runner": "playwright",
            "status": "completed",
            "stdout_preview": "loaded dashboard for <email>",
            "stderr_preview": "",
            "artifacts": {
                "trace": "artifacts/trace.zip",
            },
        },
        "notes": "Captured by browser evidence model",
    }


def test_generate_browser_evidence_report_contains_browser_sections():
    report = generate_evidence_report(sample_browser_evidence())

    assert "# Evidence Report: capture dashboard" in report
    assert "Evidence Type: browser" in report
    assert "Browser: chromium" in report
    assert "Start URL: https://demo.example.com/dashboard" in report
    assert "Network Events: 1" in report
    assert "Screenshots: 1" in report
    assert "HTML Snapshots: 1" in report

    assert "## Browser Network Events" in report
    assert "POST https://demo.example.com/api/session" in report
    assert "Status Code: 200" in report
    assert "Bearer <redacted>" in report

    assert "## Screenshots" in report
    assert "artifacts/dashboard.png" in report

    assert "## HTML Snapshots" in report
    assert "HTML SHA256" in report

    assert "## Browser Execution Output" in report
    assert "Runner: playwright" in report
    assert "trace: artifacts/trace.zip" in report

    assert "Validate impact manually" in report
