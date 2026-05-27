"""
Brain chat case intelligence briefing export.

This module exports a deterministic local briefing packet from a case
intelligence status summary and question set. It does not call LLM providers,
execute tools, collect evidence, send requests, mutate targets, submit
reports, or confirm vulnerabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from bugintel.core.brain_chat_case_intelligence_question_set_runner import (
    BrainChatCaseIntelligenceQuestionSet,
    run_case_intelligence_question_set,
)
from bugintel.core.brain_chat_case_intelligence_status_summary import (
    BrainChatCaseIntelligenceStatusSummary,
)


@dataclass(frozen=True)
class BrainChatCaseIntelligenceBriefingExport:
    target_name: str
    focus_endpoint: str | None
    current_stage: str
    current_status: str
    blocked: bool
    validation_allowed: bool
    runtime_execution_allowed: bool
    report_submission_allowed: bool
    vulnerability_confirmation_allowed: bool
    safest_next_action: str
    blockers: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    chain_position: tuple[dict[str, Any], ...]
    evidence_counts: dict[str, int]
    question_set: BrainChatCaseIntelligenceQuestionSet
    briefing_status: str
    briefing_summary: str
    planning_only: bool = True
    execution_state: str = "not_executed"
    source: str = "brain-chat-case-intelligence-briefing-export"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "brain_chat_case_intelligence_briefing_export",
            "source": self.source,
            "target_name": self.target_name,
            "focus_endpoint": self.focus_endpoint,
            "current_stage": self.current_stage,
            "current_status": self.current_status,
            "blocked": self.blocked,
            "validation_allowed": self.validation_allowed,
            "runtime_execution_allowed": self.runtime_execution_allowed,
            "report_submission_allowed": self.report_submission_allowed,
            "vulnerability_confirmation_allowed": self.vulnerability_confirmation_allowed,
            "safest_next_action": self.safest_next_action,
            "briefing_status": self.briefing_status,
            "briefing_summary": self.briefing_summary,
            "blockers": list(self.blockers),
            "missing_evidence": list(self.missing_evidence),
            "chain_position": list(self.chain_position),
            "evidence_counts": dict(self.evidence_counts),
            "question_set": self.question_set.to_dict(),
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
            "safety": {
                "local_only": True,
                "deterministic": True,
                "planning_only": True,
                "network_interaction": False,
                "target_mutation": False,
                "tool_execution": False,
                "browser_execution": False,
                "llm_provider_calls": False,
                "provider_execution": False,
                "evidence_collection": False,
                "validation_execution": False,
                "runtime_execution_allowed": False,
                "report_submission": False,
                "vulnerability_confirmation": False,
            },
        }

    def to_markdown(self, title: str = "Brain Chat Case Intelligence Briefing Export") -> str:
        lines = [
            f"# {title}",
            "",
            "## Briefing Summary",
            "",
            self.briefing_summary,
            "",
            "## Case State",
            "",
            f"- Target: `{self.target_name}`",
            f"- Focus endpoint: `{self.focus_endpoint or 'none'}`",
            f"- Current stage: `{self.current_stage}`",
            f"- Current status: `{self.current_status}`",
            f"- Briefing status: `{self.briefing_status}`",
            f"- Blocked: `{self.blocked}`",
            f"- Validation allowed: `{self.validation_allowed}`",
            f"- Runtime execution allowed: `{self.runtime_execution_allowed}`",
            f"- Report submission allowed: `{self.report_submission_allowed}`",
            f"- Vulnerability confirmation allowed: `{self.vulnerability_confirmation_allowed}`",
            "",
            "## Safest Next Action",
            "",
            self.safest_next_action,
            "",
            "## Missing Evidence",
            "",
        ]

        if self.missing_evidence:
            for item in self.missing_evidence:
                lines.append(f"- {item}")
        else:
            lines.append("- none")

        lines.extend(["", "## Blockers", ""])
        if self.blockers:
            for item in self.blockers:
                lines.append(f"- {item}")
        else:
            lines.append("- none")

        lines.extend(["", "## Chain Position", ""])
        if self.chain_position:
            for item in self.chain_position:
                stage = item.get("stage", "unknown")
                status = item.get("status", "unknown")
                ready = item.get("ready", False)
                lines.append(f"- {stage}: `{status}` ready=`{ready}`")
        else:
            lines.append("- none")

        lines.extend(["", "## Evidence Counts", ""])
        for key, value in sorted(self.evidence_counts.items()):
            lines.append(f"- {key}: `{value}`")

        lines.extend(["", "## Question Set Answers", ""])
        for index, answer in enumerate(self.question_set.answers, start=1):
            lines.extend(
                [
                    f"### {index}. {answer.question}",
                    "",
                    f"- Route: `{answer.route}`",
                    f"- Answer: {answer.answer}",
                    "",
                    "Supporting points:",
                ]
            )

            if answer.supporting_points:
                for item in answer.supporting_points:
                    lines.append(f"- {item}")
            else:
                lines.append("- none")

            lines.extend(
                [
                    "",
                    f"Recommended next action: {answer.recommended_next_action}",
                    "",
                ]
            )

        lines.extend(
            [
                "## Safety",
                "",
                "- This briefing export is local, deterministic, and planning-only.",
                "- It does not call providers, execute validation, collect evidence, send requests, submit reports, or confirm vulnerabilities.",
                "",
            ]
        )

        return "\n".join(lines)


def build_case_intelligence_briefing_export(
    summary: BrainChatCaseIntelligenceStatusSummary,
    question_set: BrainChatCaseIntelligenceQuestionSet | None = None,
    source: str = "brain-chat-case-intelligence-briefing-export",
) -> BrainChatCaseIntelligenceBriefingExport:
    resolved_question_set = question_set or run_case_intelligence_question_set(summary)
    chain_position = tuple(item.to_dict() for item in summary.chain_position)

    briefing_status = _briefing_status(summary)
    briefing_summary = _briefing_summary(summary, resolved_question_set, briefing_status)

    return BrainChatCaseIntelligenceBriefingExport(
        target_name=summary.target_name,
        focus_endpoint=summary.focus_endpoint,
        current_stage=summary.current_stage,
        current_status=summary.current_status,
        blocked=summary.blocked,
        validation_allowed=summary.validation_allowed,
        runtime_execution_allowed=summary.runtime_execution_allowed,
        report_submission_allowed=summary.report_submission_allowed,
        vulnerability_confirmation_allowed=summary.vulnerability_confirmation_allowed,
        safest_next_action=summary.safest_next_action,
        blockers=tuple(summary.blockers),
        missing_evidence=tuple(summary.missing_evidence),
        chain_position=chain_position,
        evidence_counts=dict(summary.evidence_counts),
        question_set=resolved_question_set,
        briefing_status=briefing_status,
        briefing_summary=briefing_summary,
        source=source,
    )


def _briefing_status(summary: BrainChatCaseIntelligenceStatusSummary) -> str:
    if summary.runtime_execution_allowed:
        return "invalid-runtime-execution-enabled"

    if summary.report_submission_allowed:
        return "invalid-report-submission-enabled"

    if summary.vulnerability_confirmation_allowed:
        return "invalid-vulnerability-confirmation-enabled"

    if summary.blocked:
        return "blocked"

    if summary.validation_allowed:
        return "ready-for-human-validation-review"

    return "planning-only"


def _briefing_summary(
    summary: BrainChatCaseIntelligenceStatusSummary,
    question_set: BrainChatCaseIntelligenceQuestionSet,
    briefing_status: str,
) -> str:
    if briefing_status == "blocked":
        return (
            f"The case is blocked at `{summary.current_stage}` with status `{summary.current_status}`. "
            f"{len(summary.missing_evidence)} evidence item(s) are missing, "
            f"{len(summary.blockers)} blocker(s) are recorded, and {question_set.question_count} local question(s) were answered. "
            "The safest next action is to resolve local evidence and blocker state before validation or reporting."
        )

    if briefing_status == "ready-for-human-validation-review":
        return (
            f"The case is not blocked and validation is locally marked as allowed at `{summary.current_stage}`. "
            "This briefing still does not execute validation; every runtime step needs separate human review."
        )

    return (
        f"The case is in planning-only state at `{summary.current_stage}` with status `{summary.current_status}`. "
        "No runtime execution, evidence collection, report submission, or vulnerability confirmation is allowed by this briefing."
    )
