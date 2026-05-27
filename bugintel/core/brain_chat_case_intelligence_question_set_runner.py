"""
Brain chat case intelligence question set runner.

This module runs a deterministic local set of case-intelligence questions
against a case intelligence status summary. It does not call LLM providers,
execute tools, collect evidence, send requests, mutate targets, submit
reports, or confirm vulnerabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from bugintel.core.brain_chat_case_intelligence_question_answerer import (
    BrainChatCaseIntelligenceAnswer,
    answer_case_intelligence_question,
)
from bugintel.core.brain_chat_case_intelligence_status_summary import (
    BrainChatCaseIntelligenceStatusSummary,
)


DEFAULT_CASE_INTELLIGENCE_QUESTIONS: tuple[str, ...] = (
    "What is the current status?",
    "What is blocking this case?",
    "What evidence is missing?",
    "What should I do next?",
    "Is validation allowed?",
    "Why is runtime execution blocked?",
    "Can I submit a report?",
    "Is this vulnerability confirmed?",
    "Where am I in the chain?",
    "Is it safe?",
)


@dataclass(frozen=True)
class BrainChatCaseIntelligenceQuestionSet:
    target_name: str
    focus_endpoint: str | None
    current_stage: str
    current_status: str
    blocked: bool
    validation_allowed: bool
    runtime_execution_allowed: bool
    report_submission_allowed: bool
    vulnerability_confirmation_allowed: bool
    question_count: int
    answers: tuple[BrainChatCaseIntelligenceAnswer, ...]
    planning_only: bool = True
    execution_state: str = "not_executed"
    source: str = "brain-chat-case-intelligence-question-set-runner"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "brain_chat_case_intelligence_question_set",
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
            "question_count": self.question_count,
            "answers": [answer.to_dict() for answer in self.answers],
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

    def to_markdown(self, title: str = "Brain Chat Case Intelligence Question Set") -> str:
        lines = [
            f"# {title}",
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
            f"- Questions answered: `{self.question_count}`",
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
                "- This question set is local, deterministic, and planning-only.",
                "- It does not call providers, execute validation, collect evidence, send requests, submit reports, or confirm vulnerabilities.",
                "",
            ]
        )

        return "\n".join(lines)


def run_case_intelligence_question_set(
    summary: BrainChatCaseIntelligenceStatusSummary,
    questions: tuple[str, ...] | list[str] | None = None,
    source: str = "brain-chat-case-intelligence-question-set-runner",
) -> BrainChatCaseIntelligenceQuestionSet:
    selected_questions = tuple(q for q in (questions or DEFAULT_CASE_INTELLIGENCE_QUESTIONS) if q.strip())

    answers = tuple(
        answer_case_intelligence_question(summary, question)
        for question in selected_questions
    )

    return BrainChatCaseIntelligenceQuestionSet(
        target_name=summary.target_name,
        focus_endpoint=summary.focus_endpoint,
        current_stage=summary.current_stage,
        current_status=summary.current_status,
        blocked=summary.blocked,
        validation_allowed=summary.validation_allowed,
        runtime_execution_allowed=summary.runtime_execution_allowed,
        report_submission_allowed=summary.report_submission_allowed,
        vulnerability_confirmation_allowed=summary.vulnerability_confirmation_allowed,
        question_count=len(answers),
        answers=answers,
        source=source,
    )
