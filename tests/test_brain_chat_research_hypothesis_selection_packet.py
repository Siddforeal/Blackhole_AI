from bugintel.core.brain_chat_research_hypothesis_packet import build_research_hypothesis_packet
from bugintel.core.brain_chat_research_hypothesis_selection_packet import (
    build_research_hypothesis_selection_packet,
)
from bugintel.core.brain_chat_research_source_packet import build_research_source_packet


def _ready_hypothesis_packet():
    source_packet = build_research_source_packet(
        [
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
        target_name="demo-self-hosted-product",
    )
    return build_research_hypothesis_packet(source_packet)


def test_selection_packet_blocks_when_hypothesis_packet_not_ready():
    source_packet = build_research_source_packet([], target_name="demo.local")
    hypothesis_packet = build_research_hypothesis_packet(source_packet)

    packet = build_research_hypothesis_selection_packet(hypothesis_packet)
    data = packet.to_dict()

    assert data["kind"] == "brain_chat_research_hypothesis_selection_packet"
    assert data["selection_status"] == "blocked-pending-ready-hypothesis-packet"
    assert data["selected_count"] == 0
    assert data["primary_hypothesis_id"] is None
    assert data["selection_gaps"]
    assert data["safety"]["command_generation"] is False
    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["evidence_collection"] is False
    assert data["safety"]["validation_execution"] is False
    assert data["safety"]["report_submission"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_selection_packet_selects_top_local_hypotheses():
    packet = build_research_hypothesis_selection_packet(_ready_hypothesis_packet())
    data = packet.to_dict()

    assert data["selection_status"] == "ready-for-local-investigation-planning"
    assert data["selected_count"] == 3
    assert data["primary_hypothesis_id"] is not None
    assert data["selection_gaps"] == []

    selected_types = {item["hypothesis_type"] for item in data["selected_hypotheses"]}
    assert "worker-execution-trust-boundary" in selected_types
    assert "input-to-filesystem-trust-boundary" in selected_types
    assert "authorization-admin-boundary" in selected_types

    scores = [item["selection_score"] for item in data["selected_hypotheses"]]
    assert scores == sorted(scores, reverse=True)


def test_selection_packet_can_limit_selected_count():
    packet = build_research_hypothesis_selection_packet(_ready_hypothesis_packet(), max_selected=1)
    data = packet.to_dict()

    assert data["selection_status"] == "ready-for-local-investigation-planning"
    assert data["selected_count"] == 1
    assert len(data["selected_hypotheses"]) == 1
    assert data["primary_hypothesis_id"] == data["selected_hypotheses"][0]["hypothesis_id"]


def test_selected_hypothesis_contains_investigation_planning_material():
    packet = build_research_hypothesis_selection_packet(_ready_hypothesis_packet())
    data = packet.to_dict()
    primary = data["selected_hypotheses"][0]

    assert primary["hypothesis_id"].startswith("HYP-")
    assert primary["selection_rank"] == 1
    assert primary["selection_score"] > 0
    assert "Selected because" in primary["selection_reason"]
    assert primary["evidence_needed"]
    assert primary["allowed_local_checks"]
    assert primary["tags"]


def test_selection_packet_markdown_is_readable():
    packet = build_research_hypothesis_selection_packet(_ready_hypothesis_packet())
    markdown = packet.to_markdown()

    assert "# Brain Chat Research Hypothesis Selection Packet" in markdown
    assert "Packet State" in markdown
    assert "Selected Hypotheses" in markdown
    assert "Selection Gaps" in markdown
    assert "Allowed Local Next Steps" in markdown
    assert "Rejected Actions" in markdown
    assert "Safety" in markdown
    assert "\\n" not in markdown
