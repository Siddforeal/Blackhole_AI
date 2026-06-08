import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def _ready_sources():
    return {
        "target_name": "demo-self-hosted-product",
        "sources": [
            {
                "source_id": "scope",
                "title": "Bug bounty scope notes",
                "source_type": "bug-bounty-scope",
                "summary": "Self-hosted product testing is authorized only in an owned local lab.",
                "attack_surfaces": ["Self-hosted admin console"],
                "keywords": ["scope", "self-hosted", "owned-lab"],
                "confidence": "high",
            },
            {
                "source_id": "repo-importer",
                "title": "Repository importer notes",
                "source_type": "source-code",
                "summary": "Package import, zip archive extraction, backup restore, and deployment worker code.",
                "observations": ["Archive extraction code exists."],
                "keywords": ["zip", "archive", "import", "restore", "package", "worker", "deployment"],
                "confidence": "high",
            },
            {
                "source_id": "api-docs",
                "title": "API documentation notes",
                "source_type": "api-docs",
                "summary": "Admin REST API and webhook documentation mention token authentication, roles, and permissions.",
                "keywords": ["api", "rest", "webhook", "token", "auth", "role", "permission"],
                "confidence": "medium",
            },
            {
                "source_id": "advisory",
                "title": "Historical advisory notes",
                "source_type": "security-advisory",
                "summary": "Similar products had archive traversal and parser trust-boundary failures.",
                "keywords": ["advisory", "zip slip", "parser", "restore"],
                "confidence": "medium",
            },
        ],
    }


def test_research_hypothesis_packet_cli_builds_from_sources(tmp_path):
    sources_file = tmp_path / "research-sources.json"
    sources_file.write_text(json.dumps(_ready_sources()), encoding="utf-8")
    json_output = tmp_path / "research-hypothesis-packet.json"
    markdown_output = tmp_path / "research-hypothesis-packet.md"

    result = runner.invoke(
        app,
        [
            "brain-chat-research-hypothesis-packet",
            "--sources-file",
            str(sources_file),
            "--json-output",
            str(json_output),
            "--output-file",
            str(markdown_output),
        ],
    )

    assert result.exit_code == 0
    assert "Brain Chat Research Hypothesis Packet" in result.output
    assert "ready-for-hypothesis-review" in result.output
    assert json_output.exists()
    assert markdown_output.exists()

    data = json.loads(json_output.read_text())
    assert data["kind"] == "brain_chat_research_hypothesis_packet"
    assert data["target_name"] == "demo-self-hosted-product"
    assert data["packet_status"] == "ready-for-hypothesis-review"
    assert data["source_packet_status"] == "ready-for-research-review"
    assert data["hypothesis_count"] >= 6
    assert any(item["priority"] == "high" for item in data["hypotheses"])
    assert any(item["hypothesis_type"] == "input-to-filesystem-trust-boundary" for item in data["hypotheses"])
    assert data["safety"]["web_browsing"] is False
    assert data["safety"]["command_generation"] is False
    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["evidence_collection"] is False
    assert data["safety"]["validation_execution"] is False
    assert data["safety"]["report_submission"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_research_hypothesis_packet_cli_blocks_when_sources_not_ready(tmp_path):
    sources_file = tmp_path / "research-sources.json"
    sources_file.write_text(json.dumps({"target_name": "demo.local", "sources": []}), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-hypothesis-packet",
            "--sources-file",
            str(sources_file),
        ],
    )

    assert result.exit_code == 0
    assert "blocked-pending-ready-research-source-packet" in result.output


def test_research_hypothesis_packet_cli_missing_file_errors(tmp_path):
    result = runner.invoke(
        app,
        [
            "brain-chat-research-hypothesis-packet",
            "--sources-file",
            str(tmp_path / "missing-sources.json"),
        ],
    )

    assert result.exit_code == 1
    assert "Research sources JSON not found" in result.output


def test_research_hypothesis_packet_cli_invalid_sources_shape_errors(tmp_path):
    sources_file = tmp_path / "research-sources.json"
    sources_file.write_text(json.dumps({"sources": {"not": "a-list"}}), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-hypothesis-packet",
            "--sources-file",
            str(sources_file),
        ],
    )

    assert result.exit_code == 1
    assert "Research sources JSON must be a list" in result.output


def test_research_hypothesis_packet_cli_rejects_non_object_sources(tmp_path):
    sources_file = tmp_path / "research-sources.json"
    sources_file.write_text(json.dumps(["not-an-object"]), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-hypothesis-packet",
            "--sources-file",
            str(sources_file),
        ],
    )

    assert result.exit_code == 1
    assert "Each research source must be a JSON object" in result.output
