from __future__ import annotations

import json

from typer.testing import CliRunner

from bugintel.cli import app

runner = CliRunner()


def test_brain_knowledge_store_cli_writes_json_and_markdown(tmp_path) -> None:
    output_json = tmp_path / "brain-knowledge-store.json"
    output_md = tmp_path / "brain-knowledge-store.md"

    result = runner.invoke(
        app,
        [
            "brain-knowledge-store",
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

    assert data["kind"] == "blackhole_brain_knowledge_store"
    assert data["store_id"] == "BLACKHOLE-BRAIN-KNOWLEDGE-STORE-v1.78.0"
    assert data["version"] == "1.78.0"
    assert data["status"] == "knowledge-store-local-only"
    assert data["record_count"] == 1
    assert data["network_requests_allowed"] is False
    assert data["evidence_collection_allowed"] is False
    assert data["target_mutation_allowed"] is False
    assert data["vulnerability_confirmation_allowed"] is False
    assert "# Blackhole Brain Knowledge Store" in markdown
    assert "Saved Brain Knowledge Store JSON" in normalized_stdout
    assert "Saved Brain Knowledge Store Markdown" in normalized_stdout
