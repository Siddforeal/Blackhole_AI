import json

from bugintel.core.evidence_workspace import (
    build_evidence_workspace_manifest,
    materialize_evidence_workspace,
    slugify_endpoint,
)
from bugintel.core.orchestrator import create_orchestration_plan


def test_slugify_endpoint_creates_stable_folder_name():
    assert slugify_endpoint("/api/accounts/123/users/{id}/permissions") == "api-accounts-123-users-id-permissions"
    assert slugify_endpoint("https://example.com/api/files/{id}/download").startswith("example-com-api-files-id-download")


def test_build_evidence_workspace_manifest_from_orchestration():
    plan = create_orchestration_plan(
        target_name="demo",
        endpoints=[
            "/api/accounts/123/users/{id}/permissions",
            "/api/files/{id}/download",
        ],
    )

    manifest = build_evidence_workspace_manifest(plan.to_dict(), "/tmp/demo-case")
    data = manifest.to_dict()

    assert data["target_name"] == "demo"
    assert data["endpoint_count"] == 2
    assert data["planning_only"] is True
    assert data["execution_state"] == "not_executed"
    assert data["files"]
    assert data["endpoints"][0]["files"]
    assert "controlled-account-role-matrix" in data["endpoints"][0]["requirement_names"]


def test_materialize_evidence_workspace_creates_files(tmp_path):
    plan = create_orchestration_plan(
        target_name="demo",
        endpoints=["/api/accounts/123/users/{id}/permissions"],
    )

    manifest = build_evidence_workspace_manifest(plan.to_dict(), tmp_path / "case")
    materialize_evidence_workspace(manifest)

    root = tmp_path / "case"
    manifest_file = root / "manifest.json"
    readme_file = root / "README.md"

    assert manifest_file.exists()
    assert readme_file.exists()
    assert (root / "redaction-checklist.md").exists()
    assert (root / "report-notes.md").exists()

    data = json.loads(manifest_file.read_text())
    endpoint_slug = data["endpoints"][0]["slug"]

    assert (root / "endpoints" / endpoint_slug / "README.md").exists()
    assert (root / "endpoints" / endpoint_slug / "checklist.md").exists()
    assert (root / "endpoints" / endpoint_slug / "notes.md").exists()
    assert (root / "endpoints" / endpoint_slug / "requests" / ".gitkeep").exists()
    assert data["planning_only"] is True
