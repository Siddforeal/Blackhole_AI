"""
Brain chat validation step execution gate proposal.

This module turns an effective validation-step approval decision into a local
proposal for what a future execution gate would require. It does not create
an execution gate, execute tools, collect evidence, send requests, call
providers, mutate targets, submit reports, or confirm vulnerabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from bugintel.core.brain_chat_validation_step_approval_decision_importer import (
    BrainChatValidationStepApprovalDecision,
)


@dataclass(frozen=True)
class BrainChatValidationStepExecutionGateProposal:
    target_name: str
    focus_endpoint: str | None
    proposal_status: str
    decision: str
    effective_step_approval_granted: bool
    execution_gate_proposal_ready: bool
    runtime_execution_allowed: bool
    summary: str
    approved_steps: tuple[str, ...]
    proposed_execution_gate_requirements: tuple[str, ...]
    proposed_runtime_guards: tuple[str, ...]
    rejected_actions: tuple[str, ...]
    planning_only: bool = True
    execution_state: str = "not_executed"
    source: str = "brain-chat-validation-step-execution-gate-proposal"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "brain_chat_validation_step_execution_gate_proposal",
            "source": self.source,
            "target_name": self.target_name,
            "focus_endpoint": self.focus_endpoint,
            "proposal_status": self.proposal_status,
            "decision": self.decision,
            "effective_step_approval_granted": self.effective_step_approval_granted,
            "execution_gate_proposal_ready": self.execution_gate_proposal_ready,
            "runtime_execution_allowed": self.runtime_execution_allowed,
            "summary": self.summary,
            "approved_steps": list(self.approved_steps),
            "proposed_execution_gate_requirements": list(self.proposed_execution_gate_requirements),
            "proposed_runtime_guards": list(self.proposed_runtime_guards),
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

    def to_markdown(self, title: str = "Brain Chat Validation Step Execution Gate Proposal") -> str:
        lines = [
            f"# {title}",
            "",
            "## Proposal Status",
            "",
            f"- Target: `{self.target_name}`",
            f"- Focus endpoint: `{self.focus_endpoint or 'none'}`",
            f"- Proposal status: `{self.proposal_status}`",
            f"- Decision: `{self.decision}`",
            f"- Effective step approval granted: `{self.effective_step_approval_granted}`",
            f"- Execution gate proposal ready: `{self.execution_gate_proposal_ready}`",
            f"- Runtime execution allowed: `{self.runtime_execution_allowed}`",
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

        lines.extend(["", "## Proposed Execution Gate Requirements", ""])
        for item in self.proposed_execution_gate_requirements:
            lines.append(f"- {item}")

        lines.extend(["", "## Proposed Runtime Guards", ""])
        for item in self.proposed_runtime_guards:
            lines.append(f"- {item}")

        lines.extend(["", "## Rejected Actions", ""])
        for item in self.rejected_actions:
            lines.append(f"- {item}")

        lines.extend(
            [
                "",
                "## Safety",
                "",
                "- This is a proposal only.",
                "- It does not create an execution gate, execute validation, collect evidence, send requests, submit reports, or confirm vulnerabilities.",
                "",
            ]
        )

        return "\n".join(lines)


def build_validation_step_execution_gate_proposal(
    decision: BrainChatValidationStepApprovalDecision,
    source: str = "brain-chat-validation-step-execution-gate-proposal",
) -> BrainChatValidationStepExecutionGateProposal:
    if decision.effective_step_approval_granted and decision.approved_steps:
        proposal_status = "ready-for-human-execution-gate-design"
        execution_gate_proposal_ready = True
        summary = (
            "Effective validation-step approval is present. This packet can be used to design "
            "a future execution gate, but it does not create that gate and does not execute anything."
        )
        proposed_execution_gate_requirements = (
            "Require explicit human approval for the exact runtime command or browser action.",
            "Require scope, authorization, account, role, and object ownership confirmation immediately before runtime.",
            "Require a dry-run or preview mode when supported by the future executor.",
            "Require strict rate, volume, and non-destructive constraints.",
            "Require redaction and local evidence-storage configuration before any output capture.",
            "Require an abort condition for unexpected redirects, authentication changes, destructive responses, or out-of-scope hosts.",
        )
        proposed_runtime_guards = (
            "Runtime execution must remain disabled by default.",
            "Only approved steps may be converted into future runtime proposals.",
            "No scanner, brute force, high-volume, destructive, or mutation-heavy action may be proposed.",
            "Every future runtime proposal must produce a local audit artifact before execution.",
            "Every future runtime result must be reviewed before any vulnerability claim.",
        )
        rejected_actions = (
            "Do not execute approved steps from this proposal.",
            "Do not collect evidence from this proposal.",
            "Do not create an execution gate automatically.",
            "Do not submit a report from execution-gate proposal state alone.",
            "Do not claim vulnerability confirmation from execution-gate proposal state alone.",
        )
    else:
        proposal_status = "blocked-pending-effective-step-approval"
        execution_gate_proposal_ready = False
        summary = (
            "Effective validation-step approval is not granted or no approved steps exist. "
            "A future execution gate proposal remains blocked."
        )
        proposed_execution_gate_requirements = ()
        proposed_runtime_guards = (
            "Runtime execution remains disabled.",
            "No validation steps may be proposed for execution until effective step approval exists.",
            "A blocked or premature step decision must not be treated as runtime approval.",
        )
        rejected_actions = (
            "Do not execute network, browser, curl, Kali, shell, scanner, or target interaction steps.",
            "Do not collect new evidence from a target.",
            "Do not create or imply an execution gate.",
            "Do not submit a report.",
            "Do not claim vulnerability confirmation.",
        )

    return BrainChatValidationStepExecutionGateProposal(
        target_name=decision.target_name,
        focus_endpoint=decision.focus_endpoint,
        proposal_status=proposal_status,
        decision=decision.decision,
        effective_step_approval_granted=decision.effective_step_approval_granted,
        execution_gate_proposal_ready=execution_gate_proposal_ready,
        runtime_execution_allowed=False,
        summary=summary,
        approved_steps=tuple(decision.approved_steps),
        proposed_execution_gate_requirements=proposed_execution_gate_requirements,
        proposed_runtime_guards=proposed_runtime_guards,
        rejected_actions=rejected_actions,
        source=source,
    )
