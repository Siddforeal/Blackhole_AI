"""
Brain handoff question-set runner.

This module is local, deterministic, and planning-only. It does not send
requests, execute tools, launch browsers, call LLM providers, collect evidence,
mutate targets, submit reports, or confirm vulnerabilities.

It runs the standard brain questions over a case_intake_brain_handoff artifact
and returns one combined JSON/Markdown artifact.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from bugintel.core.case_intake_brain_handoff_answerer import (
    CaseIntakeBrainHandoffAnswer,
    answer_case_intake_brain_handoff_question,
)


DEFAULT_CASE_INTAKE_BRAIN_HANDOFF_QUESTIONS: tuple[str, ...] = (
    "What should I test first?",
    "Which endpoint has strongest P1/P2 potential?",
    "What evidence is missing?",
    "What should I ignore or defer?",
    "What safe manual tests are possible with controlled accounts?",
)


@dataclass(frozen=True)
class CaseIntakeBrainHandoffQuestionSet:
    target_name: str
    handoff_status: str
    questions: tuple[str, ...]
    answers: tuple[CaseIntakeBrainHandoffAnswer, ...]
    blocked: bool
    focus_endpoint_count: int
    deferred_endpoint_count: int
    evidence_gap_count: int
    validation_allowed: bool = False
    runtime_execution_allowed: bool = False
    report_submission_allowed: bool = False
    vulnerability_confirmation_allowed: bool = False
    planning_only: bool = True
    execution_state: str = "not_executed"
    source: str = "case-intake-brain-handoff-question-set-runner"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "case_intake_brain_handoff_question_set",
            "source": self.source,
            "target_name": self.target_name,
            "handoff_status": self.handoff_status,
            "questions": list(self.questions),
            "answers": [answer.to_dict() for answer in self.answers],
            "answer_count": len(self.answers),
            "blocked": self.blocked,
            "focus_endpoint_count": self.focus_endpoint_count,
            "deferred_endpoint_count": self.deferred_endpoint_count,
            "evidence_gap_count": self.evidence_gap_count,
            "validation_allowed": self.validation_allowed,
            "runtime_execution_allowed": self.runtime_execution_allowed,
            "report_submission_allowed": self.report_submission_allowed,
            "vulnerability_confirmation_allowed": self.vulnerability_confirmation_allowed,
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
            "safety": _safety_metadata(),
        }

    def to_markdown(self, title: str = "Case Intake Brain Handoff Question Set") -> str:
        lines = [
            f"# {title}",
            "",
            "## Summary",
            "",
            f"- Target: `{self.target_name}`",
            f"- Handoff status: `{self.handoff_status}`",
            f"- Questions answered: `{len(self.answers)}`",
            f"- Focus endpoints: `{self.focus_endpoint_count}`",
            f"- Deferred endpoints: `{self.deferred_endpoint_count}`",
            f"- Evidence gaps: `{self.evidence_gap_count}`",
            f"- Planning only: `{self.planning_only}`",
            f"- Execution state: `{self.execution_state}`",
            "",
            "## Safety",
            "",
            "- No network requests",
            "- No tool execution",
            "- No browser execution",
            "- No provider calls",
            "- No evidence collection",
            "- No target mutation",
            "- No report submission",
            "- No vulnerability confirmation",
            "",
            "## Answers",
            "",
        ]

        for index, answer in enumerate(self.answers, start=1):
            lines.extend(
                [
                    f"### {index}. {answer.question}",
                    "",
                    f"- Route: `{answer.route}`",
                    f"- Focus endpoint: `{answer.focus_endpoint or 'none'}`",
                    f"- Blocked: `{answer.blocked}`",
                    "",
                    answer.answer,
                    "",
                    "Supporting points:",
                    "",
                ]
            )
            if answer.supporting_points:
                lines.extend(f"- {point}" for point in answer.supporting_points)
            else:
                lines.append("- None")
            lines.extend(
                [
                    "",
                    "Recommended next action:",
                    "",
                    answer.recommended_next_action,
                    "",
                ]
            )

        return "\n".join(lines).rstrip() + "\n"


def run_case_intake_brain_handoff_question_set(
    handoff: dict[str, Any],
    questions: tuple[str, ...] | list[str] | None = None,
) -> CaseIntakeBrainHandoffQuestionSet:
    selected_questions = tuple(questions or DEFAULT_CASE_INTAKE_BRAIN_HANDOFF_QUESTIONS)
    answers = tuple(
        answer_case_intake_brain_handoff_question(handoff, question)
        for question in selected_questions
    )

    first = answers[0] if answers else answer_case_intake_brain_handoff_question(
        handoff, "What should I test first?"
    )

    return CaseIntakeBrainHandoffQuestionSet(
        target_name=first.target_name,
        handoff_status=first.handoff_status,
        questions=selected_questions,
        answers=answers,
        blocked=any(answer.blocked for answer in answers),
        focus_endpoint_count=first.focus_endpoint_count,
        deferred_endpoint_count=first.deferred_endpoint_count,
        evidence_gap_count=first.evidence_gap_count,
        validation_allowed=False,
        runtime_execution_allowed=False,
        report_submission_allowed=False,
        vulnerability_confirmation_allowed=False,
    )


def _safety_metadata() -> dict[str, bool]:
    return {
        "local_only": True,
        "deterministic": True,
        "planning_only": True,
        "network_requests": False,
        "tool_execution": False,
        "browser_execution": False,
        "llm_provider_calls": False,
        "provider_execution": False,
        "target_mutation": False,
        "evidence_collection": False,
        "validation_execution": False,
        "report_submission": False,
        "vulnerability_confirmation": False,
        "requires_human_authorization_before_testing": True,
    }
