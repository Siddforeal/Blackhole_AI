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
