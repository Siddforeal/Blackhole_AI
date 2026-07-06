from __future__ import annotations

import json

from typer.testing import CliRunner

from bugintel.cli import app

runner = CliRunner()


def test_blackhole_brain_architecture_cli_writes_json_and_markdown(tmp_path) -> None:
    output_json = tmp_path / "brain-architecture.json"
    output_md = tmp_path / "brain-architecture.md"

    result = runner.invoke(
        app,
        [
            "blackhole-brain-architecture",
            "--json-output",
            str(output_json),
            "--output-file",
            str(output_md),
        ],
    )

    assert result.exit_code == 0
    assert output_json.exists()
    assert output_md.exists()

    data = json.loads(output_json.read_text())
    markdown = output_md.read_text()
    normalized_stdout = " ".join(result.stdout.split())

    assert data["kind"] == "blackhole_brain_architecture_spec"
    assert data["version"] == "1.77.0"
    assert data["status"] == "architecture-foundation-local-only"
    assert len(data["entities"]) == 12
    assert len(data["pipeline"]) == 9
    assert len(data["service_contracts"]) == 7
    assert data["network_requests_allowed"] is False
    assert data["tool_execution_allowed"] is False
    assert data["evidence_collection_allowed"] is False
    assert "# Blackhole Brain Architecture" in markdown
    assert "Saved Blackhole Brain architecture JSON" in normalized_stdout
    assert "Saved Blackhole Brain architecture Markdown" in normalized_stdout
