import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def test_orchestrate_prints_endpoint_priorities(tmp_path):
    input_file = tmp_path / "endpoints.txt"
    output_file = tmp_path / "orchestration.json"

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
            "orchestrate",
            str(input_file),
            "--target",
            "demo",
            "--json-output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0
    assert "Endpoint Priorities" in result.output
    assert "/api/accounts/123/users/{id}/permissions" in result.output
    assert "critical" in result.output
    assert output_file.exists()

    data = json.loads(output_file.read_text())

    assert "endpoint_priorities" in data
    assert data["endpoint_priorities"][0]["endpoint"] == "/api/accounts/123/users/{id}/permissions"
    assert data["endpoint_priorities"][0]["planning_only"] is True
    assert data["endpoint_priorities"][0]["signals"]


def test_priority_table_helper_handles_empty_list(capsys):
    from bugintel.cli import _print_endpoint_priority_table

    _print_endpoint_priority_table([])

    captured = capsys.readouterr()
    assert captured.out == ""
