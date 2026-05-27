"""
Brain chat case intelligence question answerer.

This module answers local deterministic questions from a case intelligence
status summary. It does not call LLM providers, execute tools, collect
evidence, send requests, mutate targets, submit reports, or confirm
vulnerabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from bugintel.core.brain_chat_case_intelligence_status_summary import (
    BrainChatCaseIntelligenceStatusSummary,
)


@dataclass(frozen=True)
class BrainChatCaseIntelligenceAnswer:
    question: str
    route: str
    answer: str
    target_name: str
    focus_endpoint: str | None
    current_stage: str
    current_status: str
    blocked: bool
    validation_allowed: bool
    runtime_execution_allowed: bool
    report_submission_allowed: bool
    vulnerability_confirmation_allowed: bool
    supporting_points: tuple[str, ...]
    recommended_next_action: str
    planning_only: bool = True
    execution_state: str = "not_executed"
    source: str = "brain-chat-case-intelligence-question-answerer"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "brain_chat_case_intelligence_answer",
            "source": self.source,
            "question": self.question,
            "route": self.route,
            "answer": self.answer,
            "target_name": self.target_name,
            "focus_endpoint": self.focus_endpoint,
            "current_stage": self.current_stage,
            "current_status": self.current_status,
            "blocked": self.blocked,
            "validation_allowed": self.validation_allowed,
            "runtime_execution_allowed": self.runtime_execution_allowed,
            "report_submission_allowed": self.report_submission_allowed,
            "vulnerability_confirmation_allowed": self.vulnerability_confirmation_allowed,
            "supporting_points": list(self.supporting_points),
            "recommended_next_action": self.recommended_next_action,
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

    def to_markdown(self, title: str = "Brain Chat Case Intelligence Answer") -> str:
        lines = [
            f"# {title}",
            "",
            "## Question",
            "",
            self.question,
            "",
            "## Answer",
            "",
            self.answer,
            "",
            "## Case State",
            "",
            f"- Target: `{self.target_name}`",
            f"- Focus endpoint: `{self.focus_endpoint or 'none'}`",
            f"- Current stage: `{self.current_stage}`",
            f"- Current status: `{self.current_status}`",
            f"- Blocked: `{self.blocked}`",
            f"- Validation allowed: `{self.validation_allowed}`",
            f"- Runtime execution allowed: `{self.runtime_execution_allowed}`",
            f"- Report submission allowed: `{self.report_submission_allowed}`",
            f"- Vulnerability confirmation allowed: `{self.vulnerability_confirmation_allowed}`",
            "",
            "## Supporting Points",
            "",
        ]

        if self.supporting_points:
            for item in self.supporting_points:
                lines.append(f"- {item}")
        else:
            lines.append("- none")

        lines.extend(
            [
                "",
                "## Recommended Next Action",
                "",
                self.recommended_next_action,
                "",
                "## Safety",
                "",
                "- This answer is local, deterministic, and planning-only.",
                "- It does not execute validation, collect evidence, send requests, submit reports, or confirm vulnerabilities.",
                "",
            ]
        )

        return "\n".join(lines)


def answer_case_intelligence_question(
    summary: BrainChatCaseIntelligenceStatusSummary,
    question: str,
    source: str = "brain-chat-case-intelligence-question-answerer",
) -> BrainChatCaseIntelligenceAnswer:
    normalized = _normalize(question)
    route = _route_question(normalized)
    answer, supporting_points = _answer_for_route(summary, route)

    return BrainChatCaseIntelligenceAnswer(
        question=question.strip(),
        route=route,
        answer=answer,
        target_name=summary.target_name,
        focus_endpoint=summary.focus_endpoint,
        current_stage=summary.current_stage,
        current_status=summary.current_status,
        blocked=summary.blocked,
        validation_allowed=summary.validation_allowed,
        runtime_execution_allowed=summary.runtime_execution_allowed,
        report_submission_allowed=summary.report_submission_allowed,
        vulnerability_confirmation_allowed=summary.vulnerability_confirmation_allowed,
        supporting_points=tuple(supporting_points),
        recommended_next_action=summary.safest_next_action,
        source=source,
    )


def _normalize(question: str) -> str:
    return " ".join(question.strip().lower().replace("_", " ").replace("-", " ").split())


def _route_question(normalized: str) -> str:
    if not normalized:
        return "status"

    if any(term in normalized for term in ("missing evidence", "evidence missing", "what evidence", "evidence do we need")):
        return "missing-evidence"

    if any(term in normalized for term in ("next", "do now", "what should i do", "safest", "continue")):
        return "next-action"

    if "validation" in normalized or "validate" in normalized:
        return "validation"

    if any(term in normalized for term in ("runtime", "execution", "execute", "kali", "curl", "browser")):
        return "runtime-execution"

    if any(term in normalized for term in ("report", "submit", "submission")):
        return "report-submission"

    if any(term in normalized for term in ("vulnerability", "confirmed", "confirmation", "reportable")):
        return "vulnerability-confirmation"

    if any(term in normalized for term in ("chain", "stage", "where am i", "position")):
        return "chain-position"

    if "safe" in normalized or "safety" in normalized:
        return "safety"

    if any(term in normalized for term in ("block", "blocking", "blocked", "why stuck", "stuck")):
        return "blockers"

    return "status"


def _answer_for_route(
    summary: BrainChatCaseIntelligenceStatusSummary,
    route: str,
) -> tuple[str, list[str]]:
    if route == "blockers":
        if summary.blockers:
            return (
                f"The case is blocked at `{summary.current_stage}` with status `{summary.current_status}`.",
                list(summary.blockers),
            )
        if summary.blocked:
            return (
                f"The case is blocked at `{summary.current_stage}` with status `{summary.current_status}`.",
                ["No detailed blockers were recorded, but the current status is blocked or incomplete."],
            )
        return (
            f"The case is not currently blocked. The latest stage is `{summary.current_stage}`.",
            ["No blockers are recorded."],
        )

    if route == "missing-evidence":
        if summary.missing_evidence:
            return (
                f"{len(summary.missing_evidence)} evidence item(s) are missing.",
                list(summary.missing_evidence),
            )
        return (
            "No missing evidence items are recorded in the local summary.",
            [f"Evidence counts: {summary.evidence_counts}"],
        )

    if route == "next-action":
        return (
            summary.safest_next_action,
            [
                f"Current stage: {summary.current_stage}",
                f"Current status: {summary.current_status}",
                f"Blocked: {summary.blocked}",
            ],
        )

    if route == "validation":
        if summary.validation_allowed:
            return (
                "Validation is marked as allowed by the local summary, but this answerer still does not execute validation.",
                ["Separate explicit runtime approval is still required before any target interaction."],
            )
        return (
            "Validation is not allowed right now.",
            _negative_reason_points(summary, "validation"),
        )

    if route == "runtime-execution":
        return (
            "Runtime execution is not allowed right now.",
            [
                "Runtime execution is always false in this local question-answering layer.",
                f"Current stage: {summary.current_stage}",
                f"Current status: {summary.current_status}",
                *list(summary.blockers[:5]),
            ],
        )

    if route == "report-submission":
        return (
            "Report submission is not allowed right now.",
            [
                "This summary does not confirm a vulnerability.",
                "This summary does not submit reports.",
                f"Current status: {summary.current_status}",
            ],
        )

    if route == "vulnerability-confirmation":
        return (
            "Vulnerability confirmation is not allowed from this local summary.",
            [
                "The chain has not produced validated vulnerability evidence.",
                "The answerer does not confirm vulnerabilities.",
                f"Current status: {summary.current_status}",
            ],
        )

    if route == "chain-position":
        points = [
            f"{item.stage}: {item.status} ready={item.ready}"
            for item in summary.chain_position
        ]
        return (
            f"The latest chain stage is `{summary.current_stage}` with status `{summary.current_status}`.",
            points,
        )

    if route == "safety":
        return (
            "The current case-intelligence answer is local, deterministic, and planning-only.",
            [
                "Tool execution: false",
                "Evidence collection: false",
                "Validation execution: false",
                "Runtime execution allowed: false",
                "Report submission: false",
                "Vulnerability confirmation: false",
            ],
        )

    return (
        f"The current case status is `{summary.current_status}` at stage `{summary.current_stage}`.",
        [
            f"Blocked: {summary.blocked}",
            f"Validation allowed: {summary.validation_allowed}",
            f"Runtime execution allowed: {summary.runtime_execution_allowed}",
            f"Missing evidence: {len(summary.missing_evidence)}",
        ],
    )


def _negative_reason_points(
    summary: BrainChatCaseIntelligenceStatusSummary,
    label: str,
) -> list[str]:
    points = [
        f"Current stage: {summary.current_stage}",
        f"Current status: {summary.current_status}",
    ]

    if summary.missing_evidence:
        points.append(f"{len(summary.missing_evidence)} evidence item(s) are missing.")

    if summary.blockers:
        points.extend(summary.blockers[:5])

    if len(points) == 2:
        points.append(f"No local approval state currently allows {label}.")

    return points
