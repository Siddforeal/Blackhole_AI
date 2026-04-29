import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def test_endpoint_investigation_cli_prints_profile():
    result = runner.invoke(
        app,
        [
            "endpoint-investigation",
            "/api/accounts/123/users/{id}/permissions",
        ],
    )

    assert result.exit_code == 0
    assert "Endpoint Investigation Profile" in result.output
    assert "authorization-sensitive" in result.output
    assert "object-reference" in result.output
    assert "Planned Investigation Tasks" in result.output
    assert "planning-only" in result.output


def test_endpoint_investigation_cli_writes_json(tmp_path):
    output_file = tmp_path / "endpoint-profile.json"

    result = runner.invoke(
        app,
        [
            "endpoint-investigation",
            "/api/projects/{projectId}/exports",
            "--json-output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0
    assert output_file.exists()

    data = json.loads(output_file.read_text())
    task_types = {task["task_type"] for task in data["tasks"]}

    assert data["endpoint"] == "/api/projects/{projectId}/exports"
    assert data["normalized_path"] == "/api/projects/{projectId}/exports"
    assert "authorization-sensitive" in data["categories"]
    assert "object-reference" in data["categories"]
    assert "authorization-boundary-plan" in task_types
    assert "object-reference-mutation-plan" in task_types
    assert "evidence-checklist" in task_types


def test_endpoint_investigation_cli_detects_file_surface():
    result = runner.invoke(
        app,
        [
            "endpoint-investigation",
            "/api/files/{id}/download",
        ],
    )

    assert result.exit_code == 0
    assert "file-surface" in result.output
    assert "file-surface-safety-review" in result.output
    assert "download-authorization-review" in result.output
