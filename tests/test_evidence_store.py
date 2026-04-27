import json

from bugintel.core.evidence_store import EvidenceStore


def test_save_http_evidence_creates_file(tmp_path):
    store = EvidenceStore(base_dir=tmp_path)

    path = store.save_http_evidence(
        target_name="demo-lab",
        task_name="check users endpoint",
        url="https://demo.example.com/api/users",
        method="GET",
        request={
            "headers": {
                "Authorization": "Bearer abc.def.ghi",
            }
        },
        response_headers={
            "content-type": "application/json",
        },
        response_body='{"email":"sidd@example.com","role":"admin"}',
        status_code=200,
        notes="Contact sidd@example.com",
    )

    assert path.exists()

    data = json.loads(path.read_text())

    assert data["target_name"] == "demo-lab"
    assert data["task_name"] == "check users endpoint"
    assert data["method"] == "GET"
    assert data["status_code"] == 200
    assert data["request"]["headers"]["Authorization"] == "Bearer <redacted>"
    assert "<email>" in data["response_body_preview"]
    assert "sidd@example.com" not in data["response_body_preview"]
    assert "sidd@example.com" not in data["notes"]
    assert len(data["response_body_sha256"]) == 64

def test_save_browser_evidence_creates_redacted_file(tmp_path):
    store = EvidenceStore(base_dir=tmp_path)

    path = store.save_browser_evidence(
        target_name="demo-lab",
        task_name="capture dashboard",
        start_url="https://demo.example.com/dashboard",
        browser="chromium",
        network_events=[
            {
                "method": "post",
                "url": "https://demo.example.com/api/session",
                "status_code": 200,
                "resource_type": "fetch",
                "request_headers": {
                    "Authorization": "Bearer abc.def.ghi",
                },
                "response_headers": {
                    "content-type": "application/json",
                },
                "request_post_data": '{"email":"sidd@example.com"}',
                "response_body": '{"email":"sidd@example.com","role":"admin"}',
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
                "html": '<html><body>sidd@example.com</body></html>',
            }
        ],
        execution_output={
            "runner": "playwright",
            "status": "completed",
            "stdout": "loaded page for sidd@example.com",
            "stderr": "Authorization: Bearer abc.def.ghi",
            "artifacts": {
                "trace": "artifacts/trace.zip",
            },
        },
        notes="Browser capture contains sidd@example.com",
    )

    assert path.exists()

    data = json.loads(path.read_text())

    assert data["kind"] == "browser"
    assert data["target_name"] == "demo-lab"
    assert data["task_name"] == "capture dashboard"
    assert data["start_url"] == "https://demo.example.com/dashboard"
    assert data["browser"] == "chromium"

    event = data["network_events"][0]
    assert event["method"] == "POST"
    assert event["request_headers"]["Authorization"] == "Bearer <redacted>"
    assert "response_body" not in event
    assert "request_post_data" not in event
    assert len(event["response_body_sha256"]) == 64
    assert "<email>" in event["response_body_preview"]

    assert data["screenshots"][0]["path"] == "artifacts/dashboard.png"
    assert data["screenshots"][0]["content_type"] == "image/png"

    html_snapshot = data["html_snapshots"][0]
    assert "<email>" in html_snapshot["html_preview"]
    assert len(html_snapshot["html_sha256"]) == 64

    assert data["execution_output"]["runner"] == "playwright"
    assert "<email>" in data["execution_output"]["stdout_preview"]
    assert "Bearer <redacted>" in data["execution_output"]["stderr_preview"]

    serialized = json.dumps(data)
    assert "sidd@example.com" not in serialized
    assert "abc.def.ghi" not in serialized
