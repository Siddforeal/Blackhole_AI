"""
Brain review / reasoning draft builder for Blackhole AI Workbench.

This module converts a brain-prompt package into a planning-only reasoning
review. It does not call LLM providers, send requests, execute shell commands,
launch browsers, use Kali tools, mutate targets, or bypass authorization.

This is the first deterministic reasoning-output layer after the prompt package.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class BrainReviewSection:
    title: str
    content: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BrainReview:
    target_name: str
    focus_endpoint: str | None
    sections: tuple[BrainReviewSection, ...]
    safety_gates: tuple[str, ...]
    provider_execution_enabled: bool = False
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_name": self.target_name,
            "focus_endpoint": self.focus_endpoint,
            "sections": [section.to_dict() for section in self.sections],
            "safety_gates": list(self.safety_gates),
            "provider_execution_enabled": self.provider_execution_enabled,
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
            "markdown": render_brain_review_markdown(self),
        }


@dataclass(frozen=True)
class _FocusContext:
    endpoint: str | None
    priority: str
    triage: str
    reason: str
    hypotheses: tuple[str, ...]
    artifacts: tuple[str, ...]
    next_actions: tuple[str, ...]
    approval_actions: tuple[str, ...]


def build_brain_review(prompt_package_data: dict[str, Any]) -> BrainReview:
    """Build a deterministic planning-only reasoning review from prompt package JSON."""
    target_name = str(prompt_package_data.get("target_name") or "unknown-target")
    focus_endpoint = prompt_package_data.get("focus_endpoint")
    focus_endpoint = str(focus_endpoint) if focus_endpoint else None

    safety_gates = tuple(str(item) for item in prompt_package_data.get("safety_gates") or [])
    messages = list(prompt_package_data.get("messages") or [])
    user_context = _message_content(messages, "user")

    focus = _extract_focus_context(user_context, focus_endpoint)

    sections = (
        BrainReviewSection(
            title="Recommended Focus Endpoint",
            content=_recommended_focus_section(focus),
        ),
        BrainReviewSection(
            title="Why This Endpoint Is Highest Signal",
            content=_why_high_signal_section(focus),
        ),
        BrainReviewSection(
            title="Open Hypotheses To Review",
            content=_list_section(focus.hypotheses, empty="No hypotheses were extracted from the prompt package."),
        ),
        BrainReviewSection(
            title="Evidence Artifacts Needed",
            content=_list_section(focus.artifacts, empty="No required artifacts were extracted from the prompt package."),
        ),
        BrainReviewSection(
            title="Human Approvals Required",
            content=_approval_section(focus),
        ),
        BrainReviewSection(
            title="Safety Gates Still Blocking Execution",
            content=_list_section(safety_gates, empty="No safety gates were supplied."),
        ),
        BrainReviewSection(
            title="Next Manual Validation Step",
            content=_next_step_section(focus),
        ),
        BrainReviewSection(
            title="Stop Conditions",
            content=_stop_conditions_section(),
        ),
        BrainReviewSection(
            title="Research State Updates After Validation",
            content=_state_updates_section(focus),
        ),
    )

    return BrainReview(
        target_name=target_name,
        focus_endpoint=focus.endpoint,
        sections=sections,
        safety_gates=safety_gates,
    )


def render_brain_review_markdown(review: BrainReview) -> str:
    """Render the brain review as Markdown."""
    lines = [
        f"# Blackhole Brain Review: {review.target_name}",
        "",
        "> Planning-only reasoning review. No LLM provider, browser, curl, Kali, shell, or network execution is performed.",
        "",
        f"- Target: `{review.target_name}`",
        f"- Focus endpoint: `{review.focus_endpoint or 'none'}`",
        f"- Provider execution enabled: `{review.provider_execution_enabled}`",
        f"- Execution state: `{review.execution_state}`",
        "",
    ]

    for section in review.sections:
        lines.append(f"## {section.title}")
        lines.append("")
        lines.append(section.content.rstrip())
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _message_content(messages: list[dict[str, Any]], role: str) -> str:
    for message in messages:
        if message.get("role") == role:
            return str(message.get("content") or "")
    return ""


def _extract_focus_context(user_context: str, focus_endpoint: str | None) -> _FocusContext:
    blocks = _extract_endpoint_blocks(user_context)

    block = ""
    endpoint = focus_endpoint

    if focus_endpoint and focus_endpoint in blocks:
        block = blocks[focus_endpoint]
    elif blocks:
        endpoint, block = next(iter(blocks.items()))

    priority = _extract_prefixed_value(block, "Priority:")
    triage = _extract_prefixed_value(block, "Triage:")
    reason = _extract_prefixed_value(block, "Reason:")

    hypotheses = tuple(_extract_list_after_header(block, "Hypotheses:"))
    artifacts = tuple(_extract_list_after_header(block, "Required artifacts:"))
    next_actions = tuple(_extract_list_after_header(block, "Next actions:"))
    approval_actions = tuple(action for action in next_actions if "approval=yes" in action)

    return _FocusContext(
        endpoint=endpoint,
        priority=priority or "unknown",
        triage=triage or "unknown",
        reason=reason or "No reason was extracted from the prompt package.",
        hypotheses=hypotheses,
        artifacts=artifacts,
        next_actions=next_actions,
        approval_actions=approval_actions,
    )


def _extract_endpoint_blocks(user_context: str) -> dict[str, str]:
    lines = user_context.splitlines()
    blocks: dict[str, list[str]] = {}
    current_endpoint: str | None = None

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("Global actions:"):
            current_endpoint = None
            continue

        if ". Endpoint:" in stripped:
            endpoint = stripped.split(". Endpoint:", 1)[1].strip()
            current_endpoint = endpoint
            blocks[current_endpoint] = [line]
            continue

        if current_endpoint:
            blocks[current_endpoint].append(line)

    return {endpoint: "\n".join(block_lines) for endpoint, block_lines in blocks.items()}


def _extract_prefixed_value(block: str, prefix: str) -> str:
    for line in block.splitlines():
        stripped = line.strip()
        if stripped.startswith(prefix):
            return stripped[len(prefix):].strip()
    return ""


def _extract_list_after_header(block: str, header: str) -> list[str]:
    lines = block.splitlines()
    values: list[str] = []
    active = False

    for line in lines:
        stripped = line.strip()

        if stripped == header:
            active = True
            continue

        if active and stripped.endswith(":") and not stripped.startswith("-"):
            break

        if active and stripped.startswith("- "):
            values.append(stripped[2:].strip())

    return values


def _recommended_focus_section(focus: _FocusContext) -> str:
    if not focus.endpoint:
        return "No focus endpoint was available in the prompt package."

    return "\n".join(
        [
            f"Recommended focus endpoint: `{focus.endpoint}`",
            "",
            f"- Priority: `{focus.priority}`",
            f"- Triage state: `{focus.triage}`",
            "",
            "This endpoint should be reviewed first only after scope, account ownership, and redaction requirements are confirmed.",
        ]
    )


def _why_high_signal_section(focus: _FocusContext) -> str:
    return "\n".join(
        [
            focus.reason,
            "",
            "High-signal status is not a confirmed vulnerability. It only means this endpoint should be reviewed before lower-signal routes.",
        ]
    )


def _approval_section(focus: _FocusContext) -> str:
    if not focus.approval_actions:
        return "No approval-gated actions were extracted. Continue to require human review before any active validation."

    lines = ["The following planned actions require approval:"]
    lines.append("")

    for action in focus.approval_actions:
        lines.append(f"- {action}")

    lines.append("")
    lines.append("Do not collect these artifacts until the human researcher confirms scope, authorization, and redaction handling.")

    return "\n".join(lines)


def _next_step_section(focus: _FocusContext) -> str:
    if not focus.next_actions:
        return "Next step: review the research state manually and confirm scope before doing anything active."

    return "\n".join(
        [
            "Recommended next manual step:",
            "",
            f"- {focus.next_actions[0]}",
            "",
            "This is still planning-only. Do not execute requests, browser actions, shell commands, or provider calls from this review.",
        ]
    )


def _stop_conditions_section() -> str:
    return "\n".join(
        [
            "- Stop if the target or endpoint is out of scope.",
            "- Stop if controlled test accounts are not available.",
            "- Stop if live secrets, cookies, tokens, API keys, or private customer data appear.",
            "- Stop if an action could mutate data, trigger payments, change settings, or affect real users.",
            "- Stop if the evidence cannot be redacted safely.",
            "- Stop if authorization is unclear.",
        ]
    )


def _state_updates_section(focus: _FocusContext) -> str:
    endpoint = focus.endpoint or "the focus endpoint"

    return "\n".join(
        [
            f"After manual validation of `{endpoint}`, update research state with:",
            "",
            "- hypothesis status: open, supported, rejected, or needs-more-evidence",
            "- artifact status: planned, collected, redacted, rejected, or attached-to-report",
            "- triage state: ready-for-manual-validation, queued, watchlist, deprioritized, or report-candidate",
            "- validation decision and rationale",
            "- remaining safety blockers",
        ]
    )


def _list_section(values: tuple[str, ...], empty: str) -> str:
    if not values:
        return empty
    return "\n".join(f"- `{value}`" for value in values)
