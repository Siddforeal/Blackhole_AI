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
from bugintel.core.brain_chat_human_case_review_decision_request import (
    build_human_case_review_decision_request,
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


def _packet_review_gate(summary, decision_value="approved-for-human-case-review"):
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
    packet = build_human_case_review_packet(decision_gate)
    return build_human_case_review_packet_review_gate(packet)


def test_decision_request_blocks_when_packet_review_gate_blocked():
    gate = _packet_review_gate(_blocked_summary(), "approved-for-human-case-review")
    request = build_human_case_review_decision_request(gate)
    data = request.to_dict()

    assert data["kind"] == "brain_chat_human_case_review_decision_request"
    assert data["decision_request_status"] == "blocked-pending-packet-review-gate"
    assert data["human_case_review_decision_ready"] is False
    assert data["human_case_review_ready"] is False
    assert data["effective_human_review_approval_granted"] is False
    assert data["approval_granted"] is False
    assert "rejected" in data["requested_human_decision_options"]
    assert "changes-requested" in data["requested_human_decision_options"]
    assert any("Do not approve" in item for item in data["reviewer_instructions"])
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


def test_decision_request_ready_when_packet_review_gate_ready():
    gate = _packet_review_gate(_ready_summary(), "approved-for-human-case-review")
    request = build_human_case_review_decision_request(gate)
    data = request.to_dict()

    assert data["decision_request_status"] == "ready-for-human-case-review-decision"
    assert data["human_case_review_decision_ready"] is True
    assert data["human_case_review_ready"] is True
    assert data["effective_human_review_approval_granted"] is True
    assert data["approval_granted"] is True
    assert "approved-for-next-local-planning-gate" in data["requested_human_decision_options"]
    assert any("Create or import" in item for item in data["allowed_local_next_steps"])
    assert data["safety"]["validation_execution"] is False
    assert data["safety"]["report_submission"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_decision_request_changes_requested():
    gate = _packet_review_gate(_ready_summary(), "changes-requested")
    request = build_human_case_review_decision_request(gate)
    data = request.to_dict()

    assert data["decision_request_status"] == "changes-requested"
    assert data["human_case_review_decision_ready"] is False
    assert "changes-requested" in data["requested_human_decision_options"]


def test_decision_request_rejected():
    gate = _packet_review_gate(_ready_summary(), "rejected")
    request = build_human_case_review_decision_request(gate)
    data = request.to_dict()

    assert data["decision_request_status"] == "rejected"
    assert data["human_case_review_decision_ready"] is False
    assert data["requested_human_decision_options"] == ["rejected", "changes-requested"]


def test_decision_request_blocks_unsafe_packet_review_gate():
    gate = _packet_review_gate(_ready_summary(), "approved-for-human-case-review")
    unsafe = replace(gate, runtime_execution_allowed=True)

    request = build_human_case_review_decision_request(unsafe)
    data = request.to_dict()

    assert data["decision_request_status"] == "blocked-pending-safe-packet-review-gate"
    assert data["human_case_review_decision_ready"] is False
    assert any("Runtime execution is unexpectedly allowed" in item for item in data["packet_blockers"])


def test_decision_request_markdown_is_readable():
    gate = _packet_review_gate(_blocked_summary(), "approved-for-human-case-review")
    request = build_human_case_review_decision_request(gate)
    markdown = request.to_markdown()

    assert "# Brain Chat Human Case Review Decision Request" in markdown
    assert "Request State" in markdown
    assert "Requested Human Decision Options" in markdown
    assert "Reviewer Instructions" in markdown
    assert "Required Human Checks" in markdown
    assert "Packet Blockers" in markdown
    assert "Decision Blockers" in markdown
    assert "Missing Evidence Checklist" in markdown
    assert "Blockers Checklist" in markdown
    assert "Allowed Local Next Steps" in markdown
    assert "Rejected Actions" in markdown
    assert "Safety" in markdown
    assert "\\n" not in markdown
