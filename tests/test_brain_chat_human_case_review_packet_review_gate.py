from dataclasses import replace

from bugintel.core.brain_chat_case_intelligence_briefing_export import (
    build_case_intelligence_briefing_export,
)
from bugintel.core.brain_chat_case_intelligence_briefing_review_gate import (
    build_case_intelligence_briefing_review_gate,
)
from bugintel.core.brain_chat_case_intelligence_human_review_decision_gate import (
    build_case_intelligence_human_review_decision_gate,
)
from bugintel.core.brain_chat_case_intelligence_human_review_decision_importer import (
    import_case_intelligence_human_review_decision_data,
)
from bugintel.core.brain_chat_case_intelligence_human_review_request import (
    build_case_intelligence_human_review_request,
)
from bugintel.core.brain_chat_case_intelligence_status_summary import (
    BrainChatCaseIntelligenceStatusSummary,
    CaseChainPosition,
)
from bugintel.core.brain_chat_human_case_review_packet import (
    build_human_case_review_packet,
)
from bugintel.core.brain_chat_human_case_review_packet_review_gate import (
    build_human_case_review_packet_review_gate,
)


def _blocked_summary():
    return BrainChatCaseIntelligenceStatusSummary(
        target_name="demo.local",
        focus_endpoint="/api/accounts/123/users/{id}/permissions",
        current_stage="execution-gate-proposal-review",
        current_status="blocked-pending-effective-step-approval",
        blocked=True,
        validation_allowed=False,
        runtime_execution_allowed=False,
        report_submission_allowed=False,
        vulnerability_confirmation_allowed=False,
        safest_next_action="Collect or mark the missing local evidence items before requesting validation or approval.",
        blockers=("Effective approval is not granted.",),
        missing_evidence=("Redaction checklist",),
        chain_position=(CaseChainPosition("session", "not_executed", False),),
        evidence_counts={
            "total": 1,
            "missing": 1,
            "collected": 0,
            "review-needed": 0,
            "blocked": 0,
        },
    )


def _ready_summary():
    return BrainChatCaseIntelligenceStatusSummary(
        target_name="demo.local",
        focus_endpoint="/api/accounts/123/users/{id}/permissions",
        current_stage="case-intelligence-briefing-export",
        current_status="planning-only",
        blocked=False,
        validation_allowed=False,
        runtime_execution_allowed=False,
        report_submission_allowed=False,
        vulnerability_confirmation_allowed=False,
        safest_next_action="Continue with local human review only.",
        blockers=(),
        missing_evidence=(),
        chain_position=(
            CaseChainPosition("session", "loaded", True),
            CaseChainPosition("case-intelligence-briefing-export", "planning-only", True),
        ),
        evidence_counts={
            "total": 0,
            "missing": 0,
            "collected": 0,
            "review-needed": 0,
            "blocked": 0,
        },
    )


def _packet(summary, decision_value="approved-for-human-case-review"):
    briefing = build_case_intelligence_briefing_export(summary)
    review_gate = build_case_intelligence_briefing_review_gate(briefing)
    request = build_case_intelligence_human_review_request(review_gate)
    decision = import_case_intelligence_human_review_decision_data(
        request,
        {
            "decision": decision_value,
            "reason": "Local human review decision.",
            "reviewer": "local-reviewer",
        },
    )
    decision_gate = build_case_intelligence_human_review_decision_gate(decision)
    return build_human_case_review_packet(decision_gate)


def test_packet_review_gate_blocks_unready_packet():
    packet = _packet(_blocked_summary(), "approved-for-human-case-review")
    gate = build_human_case_review_packet_review_gate(packet)
    data = gate.to_dict()

    assert data["kind"] == "brain_chat_human_case_review_packet_review_gate"
    assert data["packet_review_status"] == "blocked-pending-human-case-review-packet"
    assert data["human_case_review_ready"] is False
    assert data["effective_human_review_approval_granted"] is False
    assert data["approval_granted"] is False
    assert any("not ready" in item for item in data["packet_blockers"])
    assert any("Decision blockers remain" in item for item in data["packet_blockers"])
    assert data["validation_allowed"] is False
    assert data["runtime_execution_allowed"] is False
    assert data["report_submission_allowed"] is False
    assert data["vulnerability_confirmation_allowed"] is False
    assert data["safety"]["human_approval_side_effects"] is False
    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["evidence_collection"] is False
    assert data["safety"]["validation_execution"] is False
    assert data["safety"]["report_submission"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_packet_review_gate_ready_for_human_case_review_when_packet_ready():
    packet = _packet(_ready_summary(), "approved-for-human-case-review")
    gate = build_human_case_review_packet_review_gate(packet)
    data = gate.to_dict()

    assert data["packet_review_status"] == "ready-for-human-case-review"
    assert data["human_case_review_ready"] is True
    assert data["effective_human_review_approval_granted"] is True
    assert data["approval_granted"] is True
    assert data["packet_blockers"] == []
    assert any("Begin local human case review" in item for item in data["allowed_local_next_steps"])
    assert data["safety"]["validation_execution"] is False
    assert data["safety"]["report_submission"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_packet_review_gate_changes_requested():
    packet = _packet(_ready_summary(), "changes-requested")
    gate = build_human_case_review_packet_review_gate(packet)
    data = gate.to_dict()

    assert data["packet_review_status"] == "changes-requested"
    assert data["human_case_review_ready"] is False
    assert any("changes requested" in item.lower() for item in data["packet_blockers"])


def test_packet_review_gate_rejected():
    packet = _packet(_ready_summary(), "rejected")
    gate = build_human_case_review_packet_review_gate(packet)
    data = gate.to_dict()

    assert data["packet_review_status"] == "rejected"
    assert data["human_case_review_ready"] is False
    assert any("rejected" in item.lower() for item in data["packet_blockers"])


def test_packet_review_gate_blocks_unsafe_ready_packet():
    packet = _packet(_ready_summary(), "approved-for-human-case-review")
    unsafe = replace(packet, runtime_execution_allowed=True)

    gate = build_human_case_review_packet_review_gate(unsafe)
    data = gate.to_dict()

    assert data["packet_review_status"] == "blocked-pending-human-case-review-packet"
    assert data["human_case_review_ready"] is False
    assert any("Runtime execution is unexpectedly allowed" in item for item in data["packet_blockers"])


def test_packet_review_gate_markdown_is_readable():
    packet = _packet(_blocked_summary(), "approved-for-human-case-review")
    gate = build_human_case_review_packet_review_gate(packet)
    markdown = gate.to_markdown()

    assert "# Brain Chat Human Case Review Packet Review Gate" in markdown
    assert "Review Gate State" in markdown
    assert "Packet Blockers" in markdown
    assert "Review Scope" in markdown
    assert "Human Review Tasks" in markdown
    assert "Decision Blockers" in markdown
    assert "Missing Evidence Checklist" in markdown
    assert "Blockers Checklist" in markdown
    assert "Required Human Checks" in markdown
    assert "Allowed Local Next Steps" in markdown
    assert "Rejected Actions" in markdown
    assert "Safety" in markdown
    assert "\\n" not in markdown
