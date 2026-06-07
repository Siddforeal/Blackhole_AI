import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def test_research_source_packet_cli_blocks_without_sources(tmp_path):
    json_output = tmp_path / "research-source-packet.json"
    markdown_output = tmp_path / "research-source-packet.md"

    result = runner.invoke(
        app,
        [
            "brain-chat-research-source-packet",
            "--target-name",
            "demo.local",
            "--json-output",
            str(json_output),
            "--output-file",
            str(markdown_output),
        ],
    )

    assert result.exit_code == 0
    assert "Brain Chat Research Source Packet" in result.output
    assert "blocked-pending-research-sources" in result.output
    assert json_output.exists()
    assert markdown_output.exists()

    data = json.loads(json_output.read_text())
    assert data["kind"] == "brain_chat_research_source_packet"
    assert data["target_name"] == "demo.local"
    assert data["packet_status"] == "blocked-pending-research-sources"
    assert data["source_count"] == 0
    assert data["safety"]["web_browsing"] is False
    assert data["safety"]["network_interaction"] is False
    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["evidence_collection"] is False
    assert data["safety"]["validation_execution"] is False
    assert data["safety"]["report_submission"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_research_source_packet_cli_builds_from_object_sources(tmp_path):
    sources_file = tmp_path / "sources.json"
    sources_file.write_text(
        json.dumps(
            {
                "target_name": "demo.local",
                "sources": [
                    {
                        "source_id": "scope",
                        "title": "Program scope",
                        "source_type": "bug-bounty-scope",
                        "summary": "Authorized self-hosted lab testing only.",
                        "attack_surfaces": ["Self-hosted admin console"],
                        "keywords": ["scope", "self-hosted"],
                        "confidence": "high",
                    },
                    {
                        "source_id": "repo",
                        "title": "Repository notes",
                        "source_type": "source-code",
                        "summary": "Importer handles zip archive package upload and restore flows.",
                        "observations": ["Archive extraction code exists."],
                        "keywords": ["zip", "import", "restore", "package"],
                        "confidence": "high",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    json_output = tmp_path / "research-source-packet.json"

    result = runner.invoke(
        app,
        [
            "brain-chat-research-source-packet",
            "--sources-file",
            str(sources_file),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0
    assert "review-needed-source-gaps" in result.output
    assert "Import/export/archive/package handling" in result.output
    assert json_output.exists()

    data = json.loads(json_output.read_text())
    assert data["target_name"] == "demo.local"
    assert data["source_count"] == 2
    assert "bug-bounty-scope" in data["source_types"]
    assert "source-code" in data["source_types"]
    assert "Import/export/archive/package handling" in data["likely_attack_surfaces"]


def test_research_source_packet_cli_builds_from_list_sources(tmp_path):
    sources_file = tmp_path / "sources.json"
    sources_file.write_text(
        json.dumps(
            [
                {"title": "Scope", "source_type": "bug-bounty-scope", "summary": "Authorized lab only."},
                {"title": "Vendor docs", "source_type": "vendor-docs", "summary": "Admin import API docs."},
                {"title": "Source", "source_type": "source-code", "summary": "Package upload parser code."},
                {"title": "Advisory", "source_type": "security-advisory", "summary": "Historical archive traversal issue."},
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "brain-chat-research-source-packet",
            "--sources-file",
            str(sources_file),
            "--target-name",
            "demo.local",
        ],
    )

    assert result.exit_code == 0
    assert "ready-for-research-review" in result.output


def test_research_source_packet_cli_missing_file_errors(tmp_path):
    result = runner.invoke(
        app,
        [
            "brain-chat-research-source-packet",
            "--sources-file",
            str(tmp_path / "missing-sources.json"),
        ],
    )

    assert result.exit_code == 1
    assert "Research sources JSON not found" in result.output


def test_research_source_packet_cli_invalid_sources_shape_errors(tmp_path):
    sources_file = tmp_path / "sources.json"
    sources_file.write_text(json.dumps({"sources": {"not": "a-list"}}), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-source-packet",
            "--sources-file",
            str(sources_file),
        ],
    )

    assert result.exit_code == 1
    assert "Research sources JSON must be a list" in result.output


def test_research_source_packet_cli_rejects_non_object_sources(tmp_path):
    sources_file = tmp_path / "sources.json"
    sources_file.write_text(json.dumps(["not-an-object"]), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-source-packet",
            "--sources-file",
            str(sources_file),
        ],
    )

    assert result.exit_code == 1
    assert "Each research source must be a JSON object" in result.output
