from bugintel.core.brain_chat_research_source_packet import build_research_source_packet


def test_research_source_packet_blocks_without_sources():
    packet = build_research_source_packet([], target_name="demo.local")
    data = packet.to_dict()

    assert data["kind"] == "brain_chat_research_source_packet"
    assert data["target_name"] == "demo.local"
    assert data["packet_status"] == "blocked-pending-research-sources"
    assert data["source_count"] == 0
    assert "No local research sources were provided." in data["source_gaps"]
    assert data["safety"]["web_browsing"] is False
    assert data["safety"]["network_interaction"] is False
    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["evidence_collection"] is False
    assert data["safety"]["validation_execution"] is False
    assert data["safety"]["report_submission"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_research_source_packet_builds_from_local_sources():
    packet = build_research_source_packet(
        [
            {
                "source_id": "scope",
                "title": "Program scope",
                "source_type": "bug-bounty-scope",
                "url": "https://example.test/scope",
                "summary": "Self-hosted product is in scope.",
                "observations": ["Only test owned instances."],
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
        target_name="demo.local",
    )
    data = packet.to_dict()

    assert data["packet_status"] == "review-needed-source-gaps"
    assert data["source_count"] == 2
    assert "bug-bounty-scope" in data["source_types"]
    assert "source-code" in data["source_types"]
    assert "Import/export/archive/package handling" in data["likely_attack_surfaces"]
    assert "Self-hosted admin console" in data["likely_attack_surfaces"]
    assert any("trust boundaries" in item for item in data["research_questions"])
    assert data["safety"]["curl_execution"] is False
    assert data["safety"]["kali_execution"] is False


def test_research_source_packet_ready_when_core_source_types_present():
    packet = build_research_source_packet(
        [
            {"title": "Scope", "source_type": "bug-bounty-scope", "summary": "Authorized lab only."},
            {"title": "Vendor docs", "source_type": "vendor-docs", "summary": "Admin import API docs."},
            {"title": "Source", "source_type": "source-code", "summary": "Package upload parser code."},
            {"title": "Advisory", "source_type": "security-advisory", "summary": "Historical archive traversal issue."},
        ],
        target_name="demo.local",
    )
    data = packet.to_dict()

    assert data["packet_status"] == "ready-for-research-review"
    assert data["source_gaps"] == []
    assert any("Review the local research packet" in item for item in data["allowed_local_next_steps"])


def test_research_source_packet_normalizes_unknown_values():
    packet = build_research_source_packet(
        [
            {
                "title": "Odd source",
                "source_type": "weird-type",
                "confidence": "certain",
                "observations": "single observation",
                "keywords": "token",
                "summary": "OAuth token session behavior.",
            }
        ],
        target_name="demo.local",
    )
    data = packet.to_dict()
    source = data["sources"][0]

    assert source["source_type"] == "unknown"
    assert source["confidence"] == "medium"
    assert source["observations"] == ["single observation"]
    assert source["keywords"] == ["token"]
    assert "Authentication and session boundary" in data["likely_attack_surfaces"]


def test_research_source_packet_markdown_is_readable():
    packet = build_research_source_packet(
        [
            {
                "title": "API docs",
                "source_type": "api-docs",
                "summary": "Webhook and REST API endpoint documentation.",
                "observations": ["Webhook signing is documented."],
                "keywords": ["webhook", "api"],
            }
        ],
        target_name="demo.local",
    )
    markdown = packet.to_markdown()

    assert "# Brain Chat Research Source Packet" in markdown
    assert "Packet State" in markdown
    assert "Sources" in markdown
    assert "Research Questions" in markdown
    assert "Likely Attack Surfaces" in markdown
    assert "Source Gaps" in markdown
    assert "Allowed Local Next Steps" in markdown
    assert "Rejected Actions" in markdown
    assert "Safety" in markdown
    assert "\\n" not in markdown
