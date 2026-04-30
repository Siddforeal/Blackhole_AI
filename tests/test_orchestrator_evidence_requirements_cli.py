import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def test_orchestrate_prints_evidence_requirements(tmp_path):
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
    assert "Evidence Requirements" in result.output
    assert "/api/accounts/123/users/{id}/permissions" in result.output
    assert output_file.exists()

    data = json.loads(output_file.read_text())

    assert data["evidence_requirement_plan"]["planning_only"] is True
    assert data["evidence_requirement_plan"]["endpoint_plans"][0]["requirements"]


def test_evidence_requirements_table_helper_handles_none(capsys):
    from bugintel.cli import _print_evidence_requirements_table

    _print_evidence_requirements_table(None)

    captured = capsys.readouterr()
    assert captured.out == ""
