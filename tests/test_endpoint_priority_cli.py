import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def test_endpoint_priority_cli_scores_sensitive_endpoint():
    result = runner.invoke(
        app,
        [
            "endpoint-priority",
            "/api/accounts/123/users/{id}/permissions",
        ],
    )

    assert result.exit_code == 0
    assert "Endpoint Priority Score" in result.output
    assert "critical" in result.output
    assert "authorization-sensitive" in result.output
    assert "object-reference" in result.output
    assert "category:authorization-sensitive" in result.output
    assert "planning-only" in result.output


def test_endpoint_priority_cli_writes_json(tmp_path):
    output_file = tmp_path / "priority.json"

    result = runner.invoke(
        app,
        [
            "endpoint-priority",
            "/api/projects/{projectId}/exports",
            "--json-output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0
    assert output_file.exists()

    data = json.loads(output_file.read_text())

    assert data["endpoint"] == "/api/projects/{projectId}/exports"
    assert data["score"] > 0
    assert data["planning_only"] is True
    assert data["execution_state"] == "not_executed"
    assert data["signals"]
    assert data["recommended_next_steps"]


def test_prioritize_endpoints_cli_sorts_and_writes_json(tmp_path):
    input_file = tmp_path / "endpoints.txt"
    output_file = tmp_path / "prioritized.json"

    input_file.write_text(
        "\n".join(
            [
                "/api/status",
                "/api/accounts/123/users/{id}/permissions",
                "/api/files/{id}/download",
            ]
        )
        + "\n"
    )

    result = runner.invoke(
        app,
        [
            "prioritize-endpoints",
            str(input_file),
            "--json-output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0
    assert "Prioritized Endpoints" in result.output
    assert "Priority order" in result.output
    assert "/api/accounts/123/users/{id}/permissions" in result.output
    assert output_file.exists()

    data = json.loads(output_file.read_text())

    assert data["planning_only"] is True
    assert data["execution_state"] == "not_executed"
    assert data["endpoint_count"] == 3
    assert data["results"][0]["endpoint"] == "/api/accounts/123/users/{id}/permissions"
    assert data["results"][0]["score"] >= data["results"][1]["score"] >= data["results"][2]["score"]


def test_prioritize_endpoints_cli_missing_file_exits_nonzero(tmp_path):
    missing = tmp_path / "missing.txt"

    result = runner.invoke(app, ["prioritize-endpoints", str(missing)])

    assert result.exit_code == 1
    assert "Input file not found" in result.output
