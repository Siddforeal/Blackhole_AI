import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def test_orchestrate_prints_attack_surface_groups(tmp_path):
    input_file = tmp_path / "endpoints.txt"
    output_file = tmp_path / "orchestration.json"

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
            "orchestrate",
            str(input_file),
            "--target",
            "demo",
            "--json-output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0
    assert "Attack Surface Groups" in result.output
    assert "identity-access" in result.output
    assert "file-surface" in result.output
    assert "integration-webhook" in result.output
    assert output_file.exists()

    data = json.loads(output_file.read_text())

    assert data["attack_surface_map"]["planning_only"] is True
    group_names = [group["name"] for group in data["attack_surface_map"]["groups"]]
    assert "identity-access" in group_names
    assert "file-surface" in group_names
    assert "integration-webhook" in group_names


def test_attack_surface_table_helper_handles_none_and_empty(capsys):
    from bugintel.cli import _print_attack_surface_table

    _print_attack_surface_table(None)

    captured = capsys.readouterr()
    assert captured.out == ""
