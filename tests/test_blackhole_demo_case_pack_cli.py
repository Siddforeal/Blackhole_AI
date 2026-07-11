from __future__ import annotations

import json

from typer.testing import CliRunner

from bugintel.cli import app

runner = CliRunner()


def test_blackhole_demo_case_pack_cli_writes_json_and_markdown(tmp_path) -> None:
    output_json = tmp_path / "blackhole-demo-case-pack.json"
    output_md = tmp_path / "blackhole-demo-case-pack.md"

    result = runner.invoke(
        app,
        [
            "blackhole-demo-case-pack",
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

    assert data["kind"] == "blackhole_demo_case_pack"
    assert data["demo_id"] == "BLACKHOLE-DEMO-CASE-PACK-v1.81.0"
    assert data["version"] == "1.81.0"
    assert data["product_version"] == "1.84.1"
    assert data["demo_schema_version"] == "1.81.0"
    assert data["status"] == "demo-case-pack-local-only"
    assert data["observation_count"] == 3
    assert data["matched_pattern_count"] == 3
    assert data["knowledge_record_count"] == 3
    assert data["hypothesis_count"] == 3
    assert data["next_step_count"] == 5
    assert data["network_requests_allowed"] is False
    assert data["evidence_collection_allowed"] is False
    assert data["target_mutation_allowed"] is False
    assert data["vulnerability_confirmation_allowed"] is False

    assert "# Blackhole Demo Case Pack" in markdown
    assert "Synthetic account export boundary review" in markdown
    assert "Product version" in normalized_stdout
    assert "Demo schema version" in normalized_stdout
    assert "Saved Blackhole Demo Case Pack JSON" in normalized_stdout
    assert "Saved Blackhole Demo Case Pack Markdown" in normalized_stdout
