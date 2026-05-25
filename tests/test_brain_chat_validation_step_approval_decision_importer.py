import json
from dataclasses import replace

import pytest

from bugintel.core.brain_chat import BrainChatReply
from bugintel.core.brain_chat_evidence_approval_decision_importer import (
    import_evidence_approval_decision_data,
)
from bugintel.core.brain_chat_evidence_approval_request import (
    build_evidence_approval_request,
)
from bugintel.core.brain_chat_evidence_approved_validation_plan import (
    build_evidence_approved_validation_plan,
)
from bugintel.core.brain_chat_evidence_checklist import build_brain_chat_evidence_checklist
from bugintel.core.brain_chat_evidence_checklist_review_gate import (
    build_evidence_checklist_review_gate,
)
from bugintel.core.brain_chat_session import BrainChatSession, append_brain_chat_turn
from bugintel.core.brain_chat_validation_plan_step_review_gate import (
    build_validation_plan_step_review_gate,
)
from bugintel.core.brain_chat_validation_step_approval_decision_importer import (
    import_validation_step_approval_decision_data,
    import_validation_step_approval_decision_file,
)
from bugintel.core.brain_chat_validation_step_approval_request import (
    build_validation_step_approval_request,
)


LABELS = (
    "Scope and authorization proof for `/api/accounts/123/users/{id}/permissions`",
    "Baseline request/response sample",
    "Redaction checklist",
    "Controlled account / role / object matrix",
    "Authorization decision diff",
    "Identifier source map",
    "Owned / foreign / random response matrix",
)


def _reply(question="What evidence do we need?"):
    return BrainChatReply(
        question=question,
        answer="Evidence planning answer.",
        target_name="demo.local",
        focus_endpoint="/api/accounts/123/users/{id}/permissions",
        decision="blocked-pending-scope-and-controls",
        approval_status="blocked-pending-approval",
        execution_gate="blocked-manifest-execution-disabled",
        execution_allowed=False,
    )


def _session():
    session = BrainChatSession()
    session = append_brain_chat_turn(session, _reply("What should I test first?"))
    session = append_brain_chat_turn(session, _reply("What evidence do we need?"))
    return session


def _step_approval_request(statuses, approval_decision_data, planned_steps=None):
    checklist = build_brain_chat_evidence_checklist(
        _session(),
        item_statuses=statuses,
    )
    gate = build_evidence_checklist_review_gate(checklist)
    approval_request = build_evidence_approval_request(gate)
    approval_decision = import_evidence_approval_decision_data(
        approval_request,
        approval_decision_data,
    )
    plan = build_evidence_approved_validation_plan(approval_decision)
    if planned_steps is not None:
        plan = replace(plan, planned_validation_steps=planned_steps)
    step_gate = build_validation_plan_step_review_gate(plan)
    return build_validation_step_approval_request(step_gate)


def test_step_decision_importer_approves_only_ready_step_request():
    request = _step_approval_request(
        {label: "collected" for label in LABELS},
        {
            "decision": "approved",
            "reason": "Ready.",
        },
        planned_steps=("Prepare a minimal non-destructive validation checklist.",),
    )

    decision = import_validation_step_approval_decision_data(
        request,
        {
            "decision": "approved",
            "reason": "Step approval granted for manual plan.",
            "reviewer": "local-reviewer",
        },
    )
    data = decision.to_dict()

    assert data["kind"] == "brain_chat_validation_step_approval_decision"
    assert data["decision"] == "approved"
    assert data["request_status"] == "ready-for-human-step-approval"
    assert data["gate_status"] == "ready-for-manual-step-review"
    assert data["step_review_ready"] is True
    assert data["validation_allowed"] is True
    assert data["effective_step_approval_granted"] is True
    assert data["approved_steps"] == ["Prepare a minimal non-destructive validation checklist."]
    assert "Prepare a separate runtime execution gate proposal" in data["allowed_next_steps"][0]
    assert data["safety"]["step_approval_side_effects"] is False
    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["evidence_collection"] is False
    assert data["safety"]["validation_execution"] is False
    assert data["safety"]["report_submission"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_step_decision_importer_does_not_approve_blocked_request():
    request = _step_approval_request(
        {},
        {
            "decision": "approved",
            "reason": "Premature approval attempt.",
        },
    )

    decision = import_validation_step_approval_decision_data(
        request,
        {
            "decision": "approved",
            "reason": "Premature step approval attempt.",
        },
    )
    data = decision.to_dict()

    assert data["decision"] == "approved"
    assert data["request_status"] == "blocked-pending-step-review-gate"
    assert data["effective_step_approval_granted"] is False
    assert data["approved_steps"] == []
    assert "Do not treat this decision as runtime execution approval." in data["rejected_next_steps"]


def test_step_decision_importer_tracks_changes_requested():
    request = _step_approval_request(
        {label: "collected" for label in LABELS},
        {
            "decision": "approved",
            "reason": "Ready.",
        },
        planned_steps=("Prepare a minimal non-destructive validation checklist.",),
    )

    decision = import_validation_step_approval_decision_data(
        request,
        {
            "decision": "changes_requested",
            "reason": "Clarify account ownership.",
            "reviewer": "analyst",
        },
    )
    data = decision.to_dict()

    assert data["decision"] == "changes-requested"
    assert data["effective_step_approval_granted"] is False
    assert data["reviewer"] == "analyst"
    assert "Update validation step review state and reviewer notes." in data["allowed_next_steps"]


def test_step_decision_importer_tracks_rejection():
    request = _step_approval_request(
        {label: "collected" for label in LABELS},
        {
            "decision": "approved",
            "reason": "Ready.",
        },
        planned_steps=("Prepare a minimal non-destructive validation checklist.",),
    )

    decision = import_validation_step_approval_decision_data(
        request,
        {
            "decision": "rejected",
            "reason": "Step is not allowed.",
        },
    )
    data = decision.to_dict()

    assert data["decision"] == "rejected"
    assert data["effective_step_approval_granted"] is False
    assert data["approved_steps"] == []


def test_step_decision_importer_reads_local_json_file(tmp_path):
    request = _step_approval_request(
        {label: "collected" for label in LABELS},
        {
            "decision": "approved",
            "reason": "Ready.",
        },
        planned_steps=("Prepare a minimal non-destructive validation checklist.",),
    )
    decision_file = tmp_path / "validation-step-decision.json"
    decision_file.write_text(
        json.dumps(
            {
                "decision": "approved",
                "reason": "Ready.",
                "reviewer": "local",
            }
        ),
        encoding="utf-8",
    )

    decision = import_validation_step_approval_decision_file(request, decision_file)
    data = decision.to_dict()

    assert data["source_file"] == str(decision_file)
    assert data["effective_step_approval_granted"] is True


def test_step_decision_importer_missing_file_errors(tmp_path):
    request = _step_approval_request(
        {label: "collected" for label in LABELS},
        {
            "decision": "approved",
            "reason": "Ready.",
        },
        planned_steps=("Prepare a minimal non-destructive validation checklist.",),
    )

    with pytest.raises(FileNotFoundError):
        import_validation_step_approval_decision_file(request, tmp_path / "missing.json")


def test_step_decision_importer_invalid_decision_raises():
    request = _step_approval_request(
        {label: "collected" for label in LABELS},
        {
            "decision": "approved",
            "reason": "Ready.",
        },
        planned_steps=("Prepare a minimal non-destructive validation checklist.",),
    )

    with pytest.raises(ValueError, match="Invalid validation step approval decision"):
        import_validation_step_approval_decision_data(
            request,
            {"decision": "maybe"},
        )


def test_step_decision_importer_markdown_is_readable():
    request = _step_approval_request(
        {},
        {
            "decision": "approved",
            "reason": "Premature approval attempt.",
        },
    )
    decision = import_validation_step_approval_decision_data(
        request,
        {"decision": "rejected", "reason": "Not ready."},
    )
    markdown = decision.to_markdown()

    assert "# Brain Chat Validation Step Approval Decision" in markdown
    assert "Decision" in markdown
    assert "Approved Steps" in markdown
    assert "Rejected Next Steps" in markdown
    assert "Safety" in markdown
    assert "\\n" not in markdown
