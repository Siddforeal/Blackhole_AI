from __future__ import annotations

import json

from typer.testing import CliRunner

from bugintel.cli import app

runner = CliRunner()


def test_brain_pattern_library_cli_writes_json_and_markdown(tmp_path) -> None:
    output_json = tmp_path / "brain-pattern-library.json"
    output_md = tmp_path / "brain-pattern-library.md"

    result = runner.invoke(
        app,
        [
            "brain-pattern-library",
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

    assert data["kind"] == "blackhole_brain_pattern_library"
    assert data["library_id"] == "BLACKHOLE-BRAIN-PATTERN-LIBRARY-v1.79.0"
    assert data["version"] == "1.79.0"
    assert data["status"] == "pattern-library-local-only"
    assert data["pattern_count"] == 3
    assert data["vulnerability_classes"] == [
        "authorization",
        "information-disclosure",
        "ssrf",
    ]
    assert data["network_requests_allowed"] is False
    assert data["evidence_collection_allowed"] is False
    assert data["target_mutation_allowed"] is False
    assert data["vulnerability_confirmation_allowed"] is False
    assert "# Blackhole Brain Pattern Library" in markdown
    assert "Saved Brain Pattern Library JSON" in normalized_stdout
    assert "Saved Brain Pattern Library Markdown" in normalized_stdout
