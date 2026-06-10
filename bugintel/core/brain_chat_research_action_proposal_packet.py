"""Research action proposal packet.

This module converts a reviewed research investigation plan into deterministic,
human-reviewable action proposals.

It does not generate executable commands, install software, execute tools,
launch browsers, interact with Burp Suite, send requests, collect evidence,
validate findings, mutate state, submit reports, or confirm vulnerabilities.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PLAN_KIND = "brain_chat_research_investigation_plan_packet"
REVIEW_KIND = "brain_chat_research_investigation_plan_review_gate"


@dataclass(frozen=True)
class ResearchActionProposalItem:
    action_id: str
    hypothesis_id: str
    hypothesis_type: str
    action_type: str
    title: str
    purpose: str
    manual_order: int
    proposed_tool_family: str
    expected_artifact: str
    requires_human_approval: bool
    requires_scope_confirmation: bool
    execution_allowed: bool
    runtime_execution_allowed: bool
    command_generated: bool
    target_interaction_allowed: bool
    evidence_collection_allowed: bool
    validation_allowed: bool
    blocked_by: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "hypothesis_id": self.hypothesis_id,
            "hypothesis_type": self.hypothesis_type,
            "action_type": self.action_type,
            "title": self.title,
            "purpose": self.purpose,
            "manual_order": self.manual_order,
            "proposed_tool_family": self.proposed_tool_family,
            "expected_artifact": self.expected_artifact,
            "requires_human_approval": self.requires_human_approval,
            "requires_scope_confirmation": self.requires_scope_confirmation,
            "execution_allowed": self.execution_allowed,
            "runtime_execution_allowed": self.runtime_execution_allowed,
            "command_generated": self.command_generated,
            "target_interaction_allowed": self.target_interaction_allowed,
            "evidence_collection_allowed": self.evidence_collection_allowed,
            "validation_allowed": self.validation_allowed,
            "blocked_by": list(self.blocked_by),
        }


@dataclass(frozen=True)
class ResearchActionProposalPacket:
    target_name: str
    proposal_status: str
    review_status: str
    review_ready: bool
    action_proposal_ready: bool
    summary: str
    plan_count: int
    proposal_count: int
    proposals: tuple[ResearchActionProposalItem, ...]
    blockers: tuple[str, ...]
    human_review_items: tuple[str, ...]
    rejected_actions: tuple[str, ...]
    source: str = "brain-chat-research-action-proposal-packet"
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "brain_chat_research_action_proposal_packet",
            "source": self.source,
            "target_name": self.target_name,
            "proposal_status": self.proposal_status,
            "review_status": self.review_status,
            "review_ready": self.review_ready,
            "action_proposal_ready": self.action_proposal_ready,
            "summary": self.summary,
            "plan_count": self.plan_count,
            "proposal_count": self.proposal_count,
            "proposals": [item.to_dict() for item in self.proposals],
            "blockers": list(self.blockers),
            "human_review_items": list(self.human_review_items),
            "rejected_actions": list(self.rejected_actions),
            "execution_allowed": False,
            "runtime_execution_allowed": False,
            "command_generation_allowed": False,
            "target_interaction_allowed": False,
            "evidence_collection_allowed": False,
            "validation_allowed": False,
            "report_submission_allowed": False,
            "vulnerability_confirmation_allowed": False,
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
            "safety": {
                "local_only": True,
                "planning_only": True,
                "human_approval_required": True,
                "network_interaction": False,
                "target_mutation": False,
                "command_generation": False,
                "tool_execution": False,
                "browser_execution": False,
                "curl_execution": False,
                "kali_execution": False,
                "burp_execution": False,
                "provider_execution": False,
                "package_installation": False,
                "target_interaction": False,
                "evidence_collection": False,
                "validation_execution": False,
                "runtime_execution_allowed": False,
                "state_mutation": False,
                "report_submission": False,
                "vulnerability_confirmation": False,
            },
        }

    def to_markdown(self) -> str:
        lines = [
            "# Research Action Proposal Packet",
            "",
            "## Proposal Status",
            "",
            f"- Target: `{self.target_name}`",
            f"- Proposal status: `{self.proposal_status}`",
            f"- Review status: `{self.review_status}`",
            f"- Review ready: `{self.review_ready}`",
            f"- Action proposal ready: `{self.action_proposal_ready}`",
            f"- Plan count: `{self.plan_count}`",
            f"- Proposal count: `{self.proposal_count}`",
            "- Execution allowed: `false`",
            "- Runtime execution allowed: `false`",
            "- Command generation allowed: `false`",
            "- Target interaction allowed: `false`",
            "- Evidence collection allowed: `false`",
            "- Validation allowed: `false`",
            "",
            "## Summary",
            "",
            self.summary,
            "",
            "## Proposed Actions",
            "",
        ]

        if self.proposals:
            for item in self.proposals:
                lines.extend(
                    [
                        f"### {item.action_id} - {item.action_type}",
                        "",
                        f"- Hypothesis: `{item.hypothesis_id}`",
                        f"- Hypothesis type: `{item.hypothesis_type}`",
                        f"- Title: {item.title}",
                        f"- Purpose: {item.purpose}",
                        f"- Manual order: `{item.manual_order}`",
                        f"- Proposed tool family: `{item.proposed_tool_family}`",
                        f"- Expected artifact: `{item.expected_artifact}`",
                        f"- Requires human approval: `{item.requires_human_approval}`",
                        f"- Requires scope confirmation: `{item.requires_scope_confirmation}`",
                        f"- Execution allowed: `{item.execution_allowed}`",
                        f"- Command generated: `{item.command_generated}`",
                        "",
                        "#### Blocked By",
                        "",
                    ]
                )
                for blocker in item.blocked_by:
                    lines.append(f"- {blocker}")
                lines.append("")
        else:
            lines.append("- none")

        lines.extend(["", "## Blockers", ""])
        if self.blockers:
            for blocker in self.blockers:
                lines.append(f"- {blocker}")
        else:
            lines.append("- none")

        lines.extend(["", "## Human Review Items", ""])
        if self.human_review_items:
            for item in self.human_review_items:
                lines.append(f"- [ ] {item}")
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
                "- This packet contains proposals only.",
                "- It does not generate executable commands or install software.",
                "- It does not execute shell, browser, curl, Kali, Burp, scanner, or network actions.",
                "- It does not collect evidence, validate findings, mutate state, submit reports, or confirm vulnerabilities.",
                "",
            ]
        )

        return "\n".join(lines)


def build_research_action_proposal_packet(
    plan_packet: dict[str, Any],
    review_gate: dict[str, Any],
    source: str = "brain-chat-research-action-proposal-packet",
) -> ResearchActionProposalPacket:
    """Build deterministic research action proposals from a plan and its review gate."""

    blockers = _packet_blockers(plan_packet, review_gate)
    plans = _object_list(plan_packet.get("plans"))

    if blockers:
        proposal_status = _blocked_status(blockers)
        action_proposal_ready = False
        proposals: tuple[ResearchActionProposalItem, ...] = ()
        summary = "Research action proposal generation is blocked until the input plan and review gate are aligned and review-ready."
    elif not plans:
        proposal_status = "blocked-no-investigation-plans"
        action_proposal_ready = False
        proposals = ()
        summary = "No investigation plans are available for action proposal generation."
    else:
        proposal_status = "ready-for-action-proposal-review"
        action_proposal_ready = True
        proposals = tuple(_build_proposals(plans))
        summary = (
            "Deterministic research action proposals were prepared for human review. "
            "No command, tool execution, target interaction, evidence collection, or validation was performed."
        )

    return ResearchActionProposalPacket(
        target_name=_text(plan_packet.get("target_name"), "unknown-target"),
        proposal_status=proposal_status,
        review_status=_text(review_gate.get("review_status"), "unknown"),
        review_ready=bool(review_gate.get("review_ready")),
        action_proposal_ready=action_proposal_ready,
        summary=summary,
        plan_count=len(plans),
        proposal_count=len(proposals),
        proposals=proposals,
        blockers=tuple(blockers),
        human_review_items=tuple(_human_review_items(proposals, blockers)),
        rejected_actions=(
            "Do not generate executable shell, curl, browser, Burp, Kali, scanner, or exploitation commands from this packet.",
            "Do not install packages or modify the local environment from this packet.",
            "Do not execute any proposed action from this packet.",
            "Do not send requests or interact with a target from this packet.",
            "Do not collect evidence from this packet.",
            "Do not validate or confirm a vulnerability from this packet.",
            "Do not mutate case memory or research state from this packet.",
            "Do not submit or prepare a confirmed report from this packet.",
        ),
        source=source,
    )


def build_packet_from_files(
    plan_file: str | Path,
    review_file: str | Path,
    output_file: str | Path | None = None,
    json_output: str | Path | None = None,
) -> ResearchActionProposalPacket:
    """Load plan/review JSON files and optionally write Markdown and JSON outputs."""

    plan_packet = load_json(plan_file)
    review_gate = load_json(review_file)

    packet = build_research_action_proposal_packet(plan_packet, review_gate)

    if output_file is not None:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(packet.to_markdown(), encoding="utf-8")

    if json_output is not None:
        json_path = Path(json_output)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(
            json.dumps(packet.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    return packet


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in {path}")

    return data


def _packet_blockers(
    plan_packet: dict[str, Any],
    review_gate: dict[str, Any],
) -> list[str]:
    blockers: list[str] = []

    if plan_packet.get("kind") != PLAN_KIND:
        blockers.append("invalid-investigation-plan-kind")

    if review_gate.get("kind") != REVIEW_KIND:
        blockers.append("invalid-review-gate-kind")

    plan_target = _text(plan_packet.get("target_name"))
    review_target = _text(review_gate.get("target_name"))
    if plan_target and review_target and plan_target != review_target:
        blockers.append("plan-review-target-mismatch")

    plans = _object_list(plan_packet.get("plans"))
    review_plan_count = _int(review_gate.get("plan_count"))
    if review_plan_count != len(plans):
        blockers.append("plan-review-count-mismatch")

    if _text(review_gate.get("review_status")) != "needs-human-review":
        blockers.append("review-status-not-human-reviewable")

    if bool(review_gate.get("review_ready")) is not True:
        blockers.append("review-gate-not-ready")

    if bool(review_gate.get("runtime_execution_allowed")):
        blockers.append("review-gate-runtime-execution-enabled")

    if bool(review_gate.get("validation_allowed")):
        blockers.append("review-gate-validation-enabled")

    if bool(review_gate.get("evidence_collection_allowed")):
        blockers.append("review-gate-evidence-collection-enabled")

    return _dedupe(blockers)


def _blocked_status(blockers: list[str]) -> str:
    if "invalid-investigation-plan-kind" in blockers:
        return "blocked-invalid-investigation-plan"

    if "invalid-review-gate-kind" in blockers:
        return "blocked-invalid-review-gate"

    if any("mismatch" in blocker for blocker in blockers):
        return "blocked-plan-review-mismatch"

    return "blocked-pending-review-ready-plan"


def _build_proposals(
    plans: list[dict[str, Any]],
) -> list[ResearchActionProposalItem]:
    proposals: list[ResearchActionProposalItem] = []
    order = 1

    for plan_index, plan in enumerate(plans, start=1):
        hypothesis_id = _text(plan.get("hypothesis_id"), f"HYP-{plan_index:03d}")
        hypothesis_type = _text(plan.get("hypothesis_type"), "generic-research-hypothesis")
        focus = _text(plan.get("focus"), _text(plan.get("title"), "Review selected hypothesis."))

        proposal_specs = (
            (
                "local-source-review",
                "Review local source and documentation",
                f"Trace the selected trust boundary using local source, documentation, and existing artifacts. Focus: {focus}",
                "local-file-analysis",
                "local-source-review-note",
                False,
                ("human-review", "local-artifacts-only"),
            ),
            (
                "local-artifact-review",
                "Review existing local artifacts",
                "Inspect existing HAR, HTTP, browser, source, mobile, or evidence artifacts without sending new requests.",
                "local-artifact-analysis",
                "local-artifact-review-note",
                False,
                ("human-review", "existing-artifacts-only"),
            ),
            (
                "scope-confirmation-preparation",
                "Prepare scope confirmation",
                "Prepare the scope, authorization, asset, role, account, and object questions required before future active validation.",
                "scope",
                "scope-confirmation-checklist",
                True,
                ("scope-confirmation", "human-approval"),
            ),
            (
                "controlled-account-preparation",
                "Prepare controlled test-account requirements",
                "List controlled accounts, roles, tenants, projects, objects, or files needed for later non-destructive validation.",
                "test-controls",
                "controlled-account-matrix",
                True,
                ("controlled-assets", "human-approval"),
            ),
            (
                "browser-observation-proposal",
                "Prepare browser observation proposal",
                "Describe what a future approved browser session should observe in the DOM, console, and network without executing it now.",
                "browser",
                "browser-observation-proposal",
                True,
                ("scope-confirmation", "human-approval", "browser-execution-gate"),
            ),
            (
                "burp-request-review-proposal",
                "Prepare Burp request review proposal",
                "Describe which existing request and response artifacts should be reviewed or later replayed after separate approval.",
                "burp",
                "burp-request-review-proposal",
                True,
                ("scope-confirmation", "human-approval", "burp-execution-gate"),
            ),
            (
                "command-proposal-preparation",
                "Prepare command-review requirements",
                "Define the purpose, inputs, expected output, safety limits, and approval requirements for a future command proposal without generating a command.",
                "shell-review",
                "command-review-requirements",
                True,
                ("command-safety-review", "human-approval", "runtime-execution-gate"),
            ),
            (
                "evidence-plan-preparation",
                "Prepare evidence requirements",
                "Convert the investigation plan evidence requirements into a human-reviewable checklist without collecting evidence.",
                "evidence-planning",
                "evidence-requirements-checklist",
                True,
                ("human-approval", "evidence-collection-gate"),
            ),
        )

        for spec_index, spec in enumerate(proposal_specs, start=1):
            (
                action_type,
                title,
                purpose,
                tool_family,
                expected_artifact,
                requires_scope,
                blocked_by,
            ) = spec

            proposals.append(
                ResearchActionProposalItem(
                    action_id=f"ACT-{hypothesis_id}-{spec_index:03d}",
                    hypothesis_id=hypothesis_id,
                    hypothesis_type=hypothesis_type,
                    action_type=action_type,
                    title=title,
                    purpose=purpose,
                    manual_order=order,
                    proposed_tool_family=tool_family,
                    expected_artifact=expected_artifact,
                    requires_human_approval=True,
                    requires_scope_confirmation=requires_scope,
                    execution_allowed=False,
                    runtime_execution_allowed=False,
                    command_generated=False,
                    target_interaction_allowed=False,
                    evidence_collection_allowed=False,
                    validation_allowed=False,
                    blocked_by=tuple(blocked_by),
                )
            )
            order += 1

    return proposals


def _human_review_items(
    proposals: tuple[ResearchActionProposalItem, ...],
    blockers: list[str],
) -> list[str]:
    if blockers:
        return [
            "Resolve every packet blocker before using action proposals.",
            "Confirm the plan and review gate were generated for the same target and plan set.",
            "Keep all execution, target interaction, evidence collection, and validation disabled.",
        ]

    items = [
        "Review each proposed action for relevance to the selected hypothesis.",
        "Confirm local-only actions use existing files and artifacts only.",
        "Confirm active browser, Burp, shell, curl, Kali, scanner, or network actions remain blocked.",
        "Confirm scope and authorization before any later active validation proposal.",
        "Confirm controlled accounts, roles, tenants, objects, projects, or files before later testing.",
        "Confirm no executable command was generated by this packet.",
        "Confirm evidence collection and validation require separate approval gates.",
    ]

    if proposals:
        items.append("Select, reject, or revise each action proposal before the next workflow stage.")

    return items


def _object_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _text(value: Any, default: str = "") -> str:
    text = str(value or "").strip()
    return text or default


def _int(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


__all__ = [
    "ResearchActionProposalItem",
    "ResearchActionProposalPacket",
    "build_packet_from_files",
    "build_research_action_proposal_packet",
    "load_json",
]
