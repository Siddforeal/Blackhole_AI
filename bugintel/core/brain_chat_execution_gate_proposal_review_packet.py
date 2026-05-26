"""
Brain chat execution gate proposal review packet.

This module reviews a validation step execution-gate proposal before any future
execution-gate design work. It does not create an execution gate, execute
tools, collect evidence, send requests, call providers, mutate targets,
submit reports, or confirm vulnerabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from bugintel.core.brain_chat_validation_step_execution_gate_proposal import (
    BrainChatValidationStepExecutionGateProposal,
)


@dataclass(frozen=True)
class BrainChatExecutionGateProposalReviewPacket:
    target_name: str
    focus_endpoint: str | None
    review_status: str
    proposal_status: str
    effective_step_approval_granted: bool
    execution_gate_proposal_ready: bool
    runtime_execution_allowed: bool
    design_review_ready: bool
    summary: str
    approved_steps: tuple[str, ...]
    proposal_requirements: tuple[str, ...]
    runtime_guards: tuple[str, ...]
    blockers: tuple[str, ...]
    human_review_items: tuple[str, ...]
    rejected_actions: tuple[str, ...]
    planning_only: bool = True
    execution_state: str = "not_executed"
    source: str = "brain-chat-execution-gate-proposal-review-packet"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "brain_chat_execution_gate_proposal_review_packet",
            "source": self.source,
            "target_name": self.target_name,
            "focus_endpoint": self.focus_endpoint,
            "review_status": self.review_status,
            "proposal_status": self.proposal_status,
            "effective_step_approval_granted": self.effective_step_approval_granted,
            "execution_gate_proposal_ready": self.execution_gate_proposal_ready,
            "runtime_execution_allowed": self.runtime_execution_allowed,
            "design_review_ready": self.design_review_ready,
            "summary": self.summary,
            "approved_steps": list(self.approved_steps),
            "proposal_requirements": list(self.proposal_requirements),
            "runtime_guards": list(self.runtime_guards),
            "blockers": list(self.blockers),
            "human_review_items": list(self.human_review_items),
            "rejected_actions": list(self.rejected_actions),
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
            "safety": {
                "local_only": True,
                "planning_only": True,
                "network_interaction": False,
                "target_mutation": False,
                "tool_execution": False,
                "browser_execution": False,
                "llm_provider_calls": False,
                "provider_execution": False,
                "evidence_collection": False,
                "validation_execution": False,
                "execution_gate_created": False,
                "runtime_execution_allowed": False,
                "report_submission": False,
                "vulnerability_confirmation": False,
            },
        }

    def to_markdown(self, title: str = "Brain Chat Execution Gate Proposal Review Packet") -> str:
        lines = [
            f"# {title}",
            "",
            "## Review Status",
            "",
            f"- Target: `{self.target_name}`",
            f"- Focus endpoint: `{self.focus_endpoint or 'none'}`",
            f"- Review status: `{self.review_status}`",
            f"- Proposal status: `{self.proposal_status}`",
            f"- Effective step approval granted: `{self.effective_step_approval_granted}`",
            f"- Execution gate proposal ready: `{self.execution_gate_proposal_ready}`",
            f"- Runtime execution allowed: `{self.runtime_execution_allowed}`",
            f"- Design review ready: `{self.design_review_ready}`",
            "",
            "## Summary",
            "",
            self.summary,
            "",
            "## Approved Steps",
            "",
        ]

        if self.approved_steps:
            for item in self.approved_steps:
                lines.append(f"- {item}")
        else:
            lines.append("- none")

        lines.extend(["", "## Proposal Requirements", ""])
        if self.proposal_requirements:
            for item in self.proposal_requirements:
                lines.append(f"- {item}")
        else:
            lines.append("- none")

        lines.extend(["", "## Runtime Guards", ""])
        if self.runtime_guards:
            for item in self.runtime_guards:
                lines.append(f"- {item}")
        else:
            lines.append("- none")

        lines.extend(["", "## Blockers", ""])
        if self.blockers:
            for item in self.blockers:
                lines.append(f"- {item}")
        else:
            lines.append("- none")

        lines.extend(["", "## Human Review Items", ""])
        if self.human_review_items:
            for item in self.human_review_items:
                lines.append(f"- {item}")
        else:
            lines.append("- none")

        lines.extend(["", "## Rejected Actions", ""])
        for item in self.rejected_actions:
            lines.append(f"- {item}")

        lines.extend(
            [
                "",
                "## Safety",
                "",
                "- This review packet is local and planning-only.",
                "- It does not create an execution gate, execute validation, collect evidence, send requests, submit reports, or confirm vulnerabilities.",
                "",
            ]
        )

        return "\n".join(lines)


def build_execution_gate_proposal_review_packet(
    proposal: BrainChatValidationStepExecutionGateProposal,
    source: str = "brain-chat-execution-gate-proposal-review-packet",
) -> BrainChatExecutionGateProposalReviewPacket:
    blockers = _blockers(proposal)
    human_review_items = _human_review_items(proposal)

    if blockers:
        review_status = "blocked-pending-effective-step-approval"
        design_review_ready = False
        summary = (
            "The execution-gate proposal is blocked. Effective validation-step approval, "
            "approved steps, and complete proposal requirements are needed before design review."
        )
    elif human_review_items:
        review_status = "needs-human-review"
        design_review_ready = False
        summary = (
            "The execution-gate proposal has enough structure to review, but it still needs "
            "human review of safeguards before it can be treated as ready for design review."
        )
    else:
        review_status = "ready-for-execution-gate-design-review"
        design_review_ready = True
        summary = (
            "The execution-gate proposal is ready for human design review. This is still only "
            "a review packet and does not create or run an execution gate."
        )

    return BrainChatExecutionGateProposalReviewPacket(
        target_name=proposal.target_name,
        focus_endpoint=proposal.focus_endpoint,
        review_status=review_status,
        proposal_status=proposal.proposal_status,
        effective_step_approval_granted=proposal.effective_step_approval_granted,
        execution_gate_proposal_ready=proposal.execution_gate_proposal_ready,
        runtime_execution_allowed=proposal.runtime_execution_allowed,
        design_review_ready=design_review_ready,
        summary=summary,
        approved_steps=tuple(proposal.approved_steps),
        proposal_requirements=tuple(proposal.proposed_execution_gate_requirements),
        runtime_guards=tuple(proposal.proposed_runtime_guards),
        blockers=tuple(blockers),
        human_review_items=tuple(human_review_items),
        rejected_actions=(
            "Do not create an execution gate from this review packet.",
            "Do not execute approved steps from this review packet.",
            "Do not run browser, curl, Kali, shell, scanner, or target interaction from this review packet.",
            "Do not collect evidence from a target from this review packet.",
            "Do not submit a report from execution-gate proposal review state alone.",
            "Do not claim vulnerability confirmation from execution-gate proposal review state alone.",
        ),
        source=source,
    )


def _blockers(proposal: BrainChatValidationStepExecutionGateProposal) -> list[str]:
    blockers: list[str] = []

    if not proposal.effective_step_approval_granted:
        blockers.append("Effective validation-step approval is not granted.")

    if not proposal.execution_gate_proposal_ready:
        blockers.append("Execution-gate proposal is not ready.")

    if proposal.proposal_status == "blocked-pending-effective-step-approval":
        blockers.append("Proposal is blocked pending effective step approval.")

    if proposal.runtime_execution_allowed:
        blockers.append("Runtime execution must not be allowed by a proposal packet.")

    if not proposal.approved_steps:
        blockers.append("No approved validation steps are available for execution-gate design review.")

    if not proposal.proposed_execution_gate_requirements:
        blockers.append("No proposed execution-gate requirements are available for review.")

    if not proposal.proposed_runtime_guards:
        blockers.append("No proposed runtime guards are available for review.")

    return list(dict.fromkeys(blockers))


def _human_review_items(proposal: BrainChatValidationStepExecutionGateProposal) -> list[str]:
    if not proposal.execution_gate_proposal_ready:
        return []

    items = [
        "Human reviewer must confirm the future execution gate remains opt-in and disabled by default.",
        "Human reviewer must confirm every proposed step remains in authorized scope.",
        "Human reviewer must confirm future runtime commands or browser actions are not generated by this packet.",
        "Human reviewer must confirm evidence redaction and storage requirements before any future execution layer.",
    ]

    required_keywords = (
        "explicit human approval",
        "scope",
        "dry-run",
        "non-destructive",
        "redaction",
        "abort condition",
    )
    requirement_text = "\n".join(proposal.proposed_execution_gate_requirements).lower()

    missing = [keyword for keyword in required_keywords if keyword not in requirement_text]
    if missing:
        items.append("Proposal requirements need reviewer attention for missing safeguards: " + ", ".join(missing) + ".")

    # If all required keywords are present, no additional human-review blocker is needed.
    return () if len(items) == 4 and not missing else items
