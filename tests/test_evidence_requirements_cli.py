import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def test_evidence_requirements_cli_builds_plan(tmp_path):
    input_file = tmp_path / "endpoints.txt"
    output_file = tmp_path / "evidence-requirements.json"

    input_file.write_text(
        "\n".join(
            [
                "/api/status",
                "/api/accounts/123/users/{id}/permissions",
                "/api/files/{id}/download",
                "/api/integrations/webhooks",
            ]
        )
        + "\n"
    )

    result = runner.invoke(
        app,
        [
            "evidence-requirements",
            str(input_file),
            "--json-output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0
    assert "Evidence Requirements Summary" in result.output
    assert "controlled-account-role-matrix" in result.output
    assert "file-access-control-evidence" in result.output
    assert "integration-secret-redaction-proof" in result.output
    assert "low-signal-deprioritization-note" in result.output
    assert "planning-only" in result.output
    assert output_file.exists()

    data = json.loads(output_file.read_text())

    assert data["endpoint_count"] == 4
    assert data["planning_only"] is True
    assert data["execution_state"] == "not_executed"
    assert data["endpoint_plans"][0]["endpoint"] == "/api/accounts/123/users/{id}/permissions"
    assert data["endpoint_plans"][0]["requirements"]


def test_evidence_requirements_cli_missing_file_exits_nonzero(tmp_path):
    missing = tmp_path / "missing.txt"

    result = runner.invoke(app, ["evidence-requirements", str(missing)])

    assert result.exit_code == 1
    assert "Input file not found" in result.output
