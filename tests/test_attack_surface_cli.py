import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def test_attack_surface_cli_groups_endpoint_file(tmp_path):
    input_file = tmp_path / "endpoints.txt"
    output_file = tmp_path / "attack-surface.json"

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
            "attack-surface",
            str(input_file),
            "--json-output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0
    assert "Attack Surface Summary" in result.output
    assert "Attack Surface Groups" in result.output
    assert "identity-access" in result.output
    assert "file-surface" in result.output
    assert "integration-webhook" in result.output
    assert "low-signal" in result.output
    assert "planning-only" in result.output
    assert output_file.exists()

    data = json.loads(output_file.read_text())
    group_names = [group["name"] for group in data["groups"]]

    assert data["endpoint_count"] == 4
    assert data["planning_only"] is True
    assert data["execution_state"] == "not_executed"
    assert "identity-access" in group_names
    assert "file-surface" in group_names
    assert "integration-webhook" in group_names
    assert "low-signal" in group_names


def test_attack_surface_cli_missing_file_exits_nonzero(tmp_path):
    missing = tmp_path / "missing.txt"

    result = runner.invoke(app, ["attack-surface", str(missing)])

    assert result.exit_code == 1
    assert "Input file not found" in result.output
