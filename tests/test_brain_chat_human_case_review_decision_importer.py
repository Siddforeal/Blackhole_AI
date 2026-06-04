from dataclasses import replace
from pathlib import Path

import pytest

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
from bugintel.core.brain_chat_human_case_review_decision_importer import (
    import_human_case_review_decision_data,
    import_human_case_review_decision_file,
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


def _decision_request(summary, decision_value="approved-for-human-case-review"):
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
    packet_review_gate = build_human_case_review_packet_review_gate(packet)
    return build_human_case_review_decision_request(packet_review_gate)


def test_importer_rejects_invalid_decision():
    request = _decision_request(_blocked_summary())

    with pytest.raises(ValueError, match="Invalid human case review decision"):
        import_human_case_review_decision_data(request, {"decision": "approved"})


def test_importer_rejects_approval_when_request_blocked():
    request = _decision_request(_blocked_summary())

    with pytest.raises(ValueError, match="Allowed decisions"):
        import_human_case_review_decision_data(
            request,
            {
                "decision": "approved-for-next-local-planning-gate",
                "reason": "Premature approval.",
                "reviewer": "local-reviewer",
            },
        )


def test_importer_allows_changes_requested_when_request_blocked():
    request = _decision_request(_blocked_summary())
    imported = import_human_case_review_decision_data(
        request,
        {
            "decision": "changes-requested",
            "reason": "Need more evidence.",
            "reviewer": "local-reviewer",
        },
    )
    data = imported.to_dict()

    assert data["kind"] == "brain_chat_human_case_review_decision_import"
    assert data["decision"] == "changes-requested"
    assert data["decision_import_status"] == "changes-requested"
    assert data["decision_effective"] is True
    assert data["approval_granted"] is False
    assert data["effective_next_local_planning_approval_granted"] is False
    assert data["safety"]["human_approval_side_effects"] is False
    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["evidence_collection"] is False
    assert data["safety"]["validation_execution"] is False
    assert data["safety"]["report_submission"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_importer_allows_rejected_when_request_blocked():
    request = _decision_request(_blocked_summary())
    imported = import_human_case_review_decision_data(
        request,
        {
            "decision": "rejected",
            "reason": "Stop this path.",
            "reviewer": "local-reviewer",
        },
    )
    data = imported.to_dict()

    assert data["decision"] == "rejected"
    assert data["decision_import_status"] == "rejected"
    assert data["decision_effective"] is True
    assert data["approval_granted"] is False


def test_importer_approval_effective_only_when_request_ready():
    request = _decision_request(_ready_summary())
    imported = import_human_case_review_decision_data(
        request,
        {
            "decision": "approved-for-next-local-planning-gate",
            "reason": "Ready for next local planning gate.",
            "reviewer": "local-reviewer",
        },
    )
    data = imported.to_dict()

    assert data["decision_import_status"] == "approved-for-next-local-planning-gate"
    assert data["decision_effective"] is True
    assert data["approval_granted"] is True
    assert data["effective_next_local_planning_approval_granted"] is True
    assert any("Proceed to the next local planning gate" in item for item in data["allowed_local_next_steps"])
    assert data["safety"]["validation_execution"] is False
    assert data["safety"]["report_submission"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_importer_blocks_unsafe_ready_request():
    request = _decision_request(_ready_summary())
    unsafe = replace(request, runtime_execution_allowed=True)

    imported = import_human_case_review_decision_data(
        unsafe,
        {
            "decision": "approved-for-next-local-planning-gate",
            "reason": "Unsafe approval should not become effective.",
            "reviewer": "local-reviewer",
        },
    )
    data = imported.to_dict()

    assert data["decision_import_status"] == "blocked-pending-safe-decision-request"
    assert data["approval_granted"] is False
    assert data["effective_next_local_planning_approval_granted"] is False


def test_importer_reads_file(tmp_path):
    request = _decision_request(_blocked_summary())
    path = tmp_path / "human-case-review-decision.json"
    path.write_text(
        '{"decision":"changes-requested","reason":"Needs edits","reviewer":"local-reviewer"}',
        encoding="utf-8",
    )

    imported = import_human_case_review_decision_file(request, path)

    assert imported.decision == "changes-requested"
    assert imported.reason == "Needs edits"


def test_importer_markdown_is_readable():
    request = _decision_request(_blocked_summary())
    imported = import_human_case_review_decision_data(
        request,
        {
            "decision": "changes-requested",
            "reason": "Need more evidence.",
            "reviewer": "local-reviewer",
        },
    )
    markdown = imported.to_markdown()

    assert "# Brain Chat Human Case Review Decision Import" in markdown
    assert "Decision State" in markdown
    assert "Requested Human Decision Options" in markdown
    assert "Reviewer Instructions" in markdown
    assert "Required Human Checks" in markdown
    assert "Packet Blockers" in markdown
    assert "Decision Blockers" in markdown
    assert "Missing Evidence Checklist" in markdown
    assert "Blockers Checklist" in markdown
    assert "Allowed Local Next Steps" in markdown
    assert "Rejected Next Steps" in markdown
    assert "Safety" in markdown
    assert "\\n" not in markdown
