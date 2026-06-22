import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def test_bug_bounty_case_intake_cli_writes_json(tmp_path):
    input_file = tmp_path / "case.txt"
    output_file = tmp_path / "intake.json"

    input_file.write_text(
        "\\n".join(
            [
                "GET /api/status",
                "GET /api/admin/users/{id}/permissions",
                "POST /api/billing/invoices/{invoiceId}",
                "/api/files/{id}/download",
            ]
        )
        + "\\n"
    )

    result = runner.invoke(
        app,
        [
            "bug-bounty-case-intake",
            str(input_file),
            "--target",
            "demo-program",
            "--top",
            "3",
            "--json-output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0
    assert "Bug Bounty Case Intake" in result.output
    assert "P1/P2-Focused Endpoint Plan" in result.output
    assert "planning-only" in result.output
    assert output_file.exists()

    data = json.loads(output_file.read_text())

    assert data["target_name"] == "demo-program"
    assert data["endpoint_count"] == 4
    assert data["selected_endpoint_count"] == 3
    assert data["top_endpoints"]
    assert data["safety"]["network_requests"] is False
    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_bug_bounty_case_intake_cli_missing_file_exits_nonzero(tmp_path):
    missing = tmp_path / "missing.txt"

    result = runner.invoke(app, ["bug-bounty-case-intake", str(missing)])

    assert result.exit_code == 1
    assert "Input file not found" in result.output
