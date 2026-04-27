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
