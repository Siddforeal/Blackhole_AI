import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def _ready_sources():
    return {
        "target_name": "demo-self-hosted-product",
        "sources": [
            {"title": "Scope", "source_type": "bug-bounty-scope", "summary": "Authorized owned lab."},
            {
                "title": "Source",
                "source_type": "source-code",
                "summary": "Package import, zip archive extraction, backup restore, and deployment worker code.",
                "keywords": ["zip", "archive", "import", "restore", "package", "worker", "deployment"],
            },
            {
                "title": "API docs",
                "source_type": "api-docs",
                "summary": "Admin REST API and webhook documentation mention token authentication, roles, and permissions.",
                "keywords": ["api", "webhook", "token", "role", "permission"],
            },
            {
                "title": "Advisory",
                "source_type": "security-advisory",
                "summary": "Historical archive traversal and admin access-control weakness.",
                "keywords": ["archive", "admin", "authorization"],
            },
        ],
    }


def test_research_hypothesis_selection_packet_cli_builds_from_sources(tmp_path):
    sources_file = tmp_path / "research-sources.json"
    sources_file.write_text(json.dumps(_ready_sources()), encoding="utf-8")
    json_output = tmp_path / "research-hypothesis-selection-packet.json"
    markdown_output = tmp_path / "research-hypothesis-selection-packet.md"

    result = runner.invoke(
        app,
        [
            "brain-chat-research-hypothesis-selection-packet",
            "--sources-file",
            str(sources_file),
            "--json-output",
            str(json_output),
            "--output-file",
            str(markdown_output),
        ],
    )

    assert result.exit_code == 0
    assert "Brain Chat Research Hypothesis Selection Packet" in result.output
    assert "ready-for-local-investigation-planning" in result.output
    assert json_output.exists()
    assert markdown_output.exists()

    data = json.loads(json_output.read_text())
    assert data["kind"] == "brain_chat_research_hypothesis_selection_packet"
    assert data["target_name"] == "demo-self-hosted-product"
    assert data["selection_status"] == "ready-for-local-investigation-planning"
    assert data["selected_count"] == 3
    assert data["primary_hypothesis_id"]
    assert data["selection_gaps"] == []

    selected_types = {item["hypothesis_type"] for item in data["selected_hypotheses"]}
    assert "worker-execution-trust-boundary" in selected_types
    assert "input-to-filesystem-trust-boundary" in selected_types
    assert "authorization-admin-boundary" in selected_types

    assert data["safety"]["web_browsing"] is False
    assert data["safety"]["command_generation"] is False
    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["evidence_collection"] is False
    assert data["safety"]["validation_execution"] is False
    assert data["safety"]["report_submission"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_research_hypothesis_selection_packet_cli_respects_max_selected(tmp_path):
    sources_file = tmp_path / "research-sources.json"
    sources_file.write_text(json.dumps(_ready_sources()), encoding="utf-8")
    json_output = tmp_path / "selection.json"

    result = runner.invoke(
        app,
        [
            "brain-chat-research-hypothesis-selection-packet",
            "--sources-file",
            str(sources_file),
            "--max-selected",
            "1",
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0
    data = json.loads(json_output.read_text())
    assert data["selected_count"] == 1
    assert len(data["selected_hypotheses"]) == 1
    assert data["primary_hypothesis_id"] == data["selected_hypotheses"][0]["hypothesis_id"]


def test_research_hypothesis_selection_packet_cli_blocks_when_sources_not_ready(tmp_path):
    sources_file = tmp_path / "research-sources.json"
    sources_file.write_text(json.dumps({"target_name": "demo.local", "sources": []}), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-hypothesis-selection-packet",
            "--sources-file",
            str(sources_file),
        ],
    )

    assert result.exit_code == 0
    assert "blocked-pending-ready-hypothesis-packet" in result.output


def test_research_hypothesis_selection_packet_cli_missing_file_errors(tmp_path):
    result = runner.invoke(
        app,
        [
            "brain-chat-research-hypothesis-selection-packet",
            "--sources-file",
            str(tmp_path / "missing-sources.json"),
        ],
    )

    assert result.exit_code == 1
    assert "Research sources JSON not found" in result.output


def test_research_hypothesis_selection_packet_cli_invalid_sources_shape_errors(tmp_path):
    sources_file = tmp_path / "research-sources.json"
    sources_file.write_text(json.dumps({"sources": {"not": "a-list"}}), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-hypothesis-selection-packet",
            "--sources-file",
            str(sources_file),
        ],
    )

    assert result.exit_code == 1
    assert "Research sources JSON must be a list" in result.output


def test_research_hypothesis_selection_packet_cli_rejects_non_object_sources(tmp_path):
    sources_file = tmp_path / "research-sources.json"
    sources_file.write_text(json.dumps(["not-an-object"]), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-research-hypothesis-selection-packet",
            "--sources-file",
            str(sources_file),
        ],
    )

    assert result.exit_code == 1
    assert "Each research source must be a JSON object" in result.output
