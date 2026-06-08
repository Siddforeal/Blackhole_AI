from bugintel.core.brain_chat_research_hypothesis_packet import build_research_hypothesis_packet
from bugintel.core.brain_chat_research_source_packet import build_research_source_packet


def _ready_source_packet():
    return build_research_source_packet(
        [
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
        target_name="demo-self-hosted-product",
    )


def test_hypothesis_packet_blocks_when_source_packet_not_ready():
    source_packet = build_research_source_packet([], target_name="demo.local")
    packet = build_research_hypothesis_packet(source_packet)
    data = packet.to_dict()

    assert data["kind"] == "brain_chat_research_hypothesis_packet"
    assert data["packet_status"] == "blocked-pending-ready-research-source-packet"
    assert data["source_packet_status"] == "blocked-pending-research-sources"
    assert data["hypothesis_count"] == 0
    assert data["hypothesis_gaps"]
    assert data["safety"]["web_browsing"] is False
    assert data["safety"]["command_generation"] is False
    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["evidence_collection"] is False
    assert data["safety"]["validation_execution"] is False
    assert data["safety"]["report_submission"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_hypothesis_packet_derives_hypotheses_from_ready_source_packet():
    packet = build_research_hypothesis_packet(_ready_source_packet())
    data = packet.to_dict()

    assert data["packet_status"] == "ready-for-hypothesis-review"
    assert data["source_packet_status"] == "ready-for-research-review"
    assert data["target_name"] == "demo-self-hosted-product"
    assert data["hypothesis_count"] >= 6
    assert data["hypothesis_gaps"] == []
    assert any(item["priority"] == "high" for item in data["hypotheses"])
    assert any(item["hypothesis_type"] == "input-to-filesystem-trust-boundary" for item in data["hypotheses"])
    assert any(item["hypothesis_type"] == "worker-execution-trust-boundary" for item in data["hypotheses"])
    assert any(item["hypothesis_type"] == "authorization-admin-boundary" for item in data["hypotheses"])
    assert data["safety"]["command_generation"] is False
    assert data["safety"]["curl_execution"] is False
    assert data["safety"]["kali_execution"] is False


def test_hypothesis_items_include_local_review_material():
    packet = build_research_hypothesis_packet(_ready_source_packet())
    data = packet.to_dict()
    archive_hypothesis = next(
        item for item in data["hypotheses"]
        if item["hypothesis_type"] == "input-to-filesystem-trust-boundary"
    )

    assert archive_hypothesis["hypothesis_id"].startswith("HYP-")
    assert archive_hypothesis["local_review_questions"]
    assert archive_hypothesis["evidence_needed"]
    assert archive_hypothesis["allowed_local_checks"]
    assert archive_hypothesis["rejected_actions"]
    assert "filesystem" in archive_hypothesis["tags"]
    assert "path-boundary" in archive_hypothesis["tags"]


def test_hypothesis_packet_rejected_actions_are_safe():
    packet = build_research_hypothesis_packet(_ready_source_packet())
    data = packet.to_dict()

    assert any("Do not browse" in item for item in data["rejected_actions"])
    assert any("Do not generate curl" in item for item in data["rejected_actions"])
    assert any("Do not execute tools" in item for item in data["rejected_actions"])
    assert data["safety"]["network_interaction"] is False
    assert data["safety"]["browser_execution"] is False
    assert data["safety"]["runtime_execution_allowed"] is False


def test_hypothesis_packet_markdown_is_readable():
    packet = build_research_hypothesis_packet(_ready_source_packet())
    markdown = packet.to_markdown()

    assert "# Brain Chat Research Hypothesis Packet" in markdown
    assert "Packet State" in markdown
    assert "Hypotheses" in markdown
    assert "Source Gaps" in markdown
    assert "Hypothesis Gaps" in markdown
    assert "Allowed Local Next Steps" in markdown
    assert "Rejected Actions" in markdown
    assert "Safety" in markdown
    assert "\\n" not in markdown
