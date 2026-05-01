import json

from typer.testing import CliRunner

from bugintel.cli import app
from bugintel.core.orchestrator import create_orchestration_plan


runner = CliRunner()


def test_evidence_workspace_cli_dry_run(tmp_path):
    plan = create_orchestration_plan(
        target_name="demo",
        endpoints=["/api/accounts/123/users/{id}/permissions"],
    )

    orchestration_file = tmp_path / "orchestration.json"
    output_dir = tmp_path / "case-demo"
    orchestration_file.write_text(json.dumps(plan.to_dict()))

    result = runner.invoke(
        app,
        [
            "evidence-workspace",
            str(orchestration_file),
            "--output-dir",
            str(output_dir),
            "--dry-run",
        ],
    )

    assert result.exit_code == 0
    assert "Evidence Workspace" in result.output
    assert "Workspace Files" in result.output
    assert "dry-run" in result.output
    assert "manifest.json" in result.output
    assert not (output_dir / "manifest.json").exists()


def test_evidence_workspace_cli_creates_workspace(tmp_path):
    plan = create_orchestration_plan(
        target_name="demo",
        endpoints=["/api/accounts/123/users/{id}/permissions"],
    )

    orchestration_file = tmp_path / "orchestration.json"
    output_dir = tmp_path / "case-demo"
    orchestration_file.write_text(json.dumps(plan.to_dict()))

    result = runner.invoke(
        app,
        [
            "evidence-workspace",
            str(orchestration_file),
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0
    assert "Evidence workspace created" in result.output

    manifest_file = output_dir / "manifest.json"
    assert manifest_file.exists()

    data = json.loads(manifest_file.read_text())
    endpoint_slug = data["endpoints"][0]["slug"]

    assert data["planning_only"] is True
    assert data["execution_state"] == "not_executed"
    assert (output_dir / "README.md").exists()
    assert (output_dir / "redaction-checklist.md").exists()
    assert (output_dir / "report-notes.md").exists()
    assert (output_dir / "endpoints" / endpoint_slug / "README.md").exists()
    assert (output_dir / "endpoints" / endpoint_slug / "checklist.md").exists()
    assert (output_dir / "endpoints" / endpoint_slug / "requests" / ".gitkeep").exists()


def test_evidence_workspace_cli_missing_file_exits_nonzero(tmp_path):
    missing = tmp_path / "missing.json"

    result = runner.invoke(
        app,
        [
            "evidence-workspace",
            str(missing),
            "--output-dir",
            str(tmp_path / "case"),
        ],
    )

    assert result.exit_code == 1
    assert "Orchestration JSON not found" in result.output


def test_evidence_workspace_cli_invalid_json_exits_nonzero(tmp_path):
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{not json")

    result = runner.invoke(
        app,
        [
            "evidence-workspace",
            str(bad_file),
            "--output-dir",
            str(tmp_path / "case"),
        ],
    )

    assert result.exit_code == 2
    assert "Invalid orchestration JSON" in result.output
