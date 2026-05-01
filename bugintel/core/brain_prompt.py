"""
LLM brain prompt package builder for Blackhole AI Workbench.

This module converts an AI brain plan into a provider-ready prompt package,
but it does not call LLM providers, send requests, execute shell commands,
launch browsers, use Kali tools, mutate targets, or bypass authorization.

It is a safe bridge between deterministic planning and future provider-gated
LLM reasoning.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class BrainPromptMessage:
    role: str
    content: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BrainPromptPackage:
    target_name: str
    message_count: int
    messages: tuple[BrainPromptMessage, ...]
    safety_gates: tuple[str, ...]
    focus_endpoint: str | None
    provider_execution_enabled: bool = False
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_name": self.target_name,
            "message_count": self.message_count,
            "messages": [message.to_dict() for message in self.messages],
            "safety_gates": list(self.safety_gates),
            "focus_endpoint": self.focus_endpoint,
            "provider_execution_enabled": self.provider_execution_enabled,
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
            "markdown": render_brain_prompt_package_markdown(self),
        }


def build_brain_prompt_package(ai_brain_plan_data: dict[str, Any]) -> BrainPromptPackage:
    """Build a planning-only LLM prompt package from AI brain plan JSON."""
    target_name = str(ai_brain_plan_data.get("target_name") or "unknown-target")
    focus_queue = list(ai_brain_plan_data.get("focus_queue") or [])
    global_actions = list(ai_brain_plan_data.get("global_actions") or [])
    safety_gates = tuple(str(item) for item in ai_brain_plan_data.get("safety_gates") or [])

    focus_endpoint = None
    if focus_queue:
        focus_endpoint = str(focus_queue[0].get("endpoint") or "unknown-endpoint")

    messages = (
        BrainPromptMessage(
            role="system",
            content=_system_prompt(),
        ),
        BrainPromptMessage(
            role="developer",
            content=_developer_safety_prompt(safety_gates),
        ),
        BrainPromptMessage(
            role="user",
            content=_user_context_prompt(target_name, focus_queue, global_actions),
        ),
        BrainPromptMessage(
            role="assistant_task",
            content=_assistant_task_prompt(),
        ),
    )

    return BrainPromptPackage(
        target_name=target_name,
        message_count=len(messages),
        messages=messages,
        safety_gates=safety_gates,
        focus_endpoint=focus_endpoint,
    )


def render_brain_prompt_package_markdown(package: BrainPromptPackage) -> str:
    """Render the prompt package as Markdown for review."""
    lines = [
        f"# Blackhole LLM Brain Prompt Package: {package.target_name}",
        "",
        "> Planning-only prompt package. Provider execution is disabled.",
        "",
        f"- Target: `{package.target_name}`",
        f"- Focus endpoint: `{package.focus_endpoint or 'none'}`",
        f"- Messages: `{package.message_count}`",
        f"- Provider execution enabled: `{package.provider_execution_enabled}`",
        f"- Execution state: `{package.execution_state}`",
        "",
        "## Safety Gates",
        "",
    ]

    for gate in package.safety_gates:
        lines.append(f"- `{gate}`")

    lines.append("")

    for index, message in enumerate(package.messages, start=1):
        lines.append(f"## Message {index}: `{message.role}`")
        lines.append("")
        lines.append(message.content.rstrip())
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _system_prompt() -> str:
    return "\n".join(
        [
            "You are the Blackhole AI security research planning brain.",
            "",
            "You help a human researcher reason about authorized bug bounty work.",
            "You do not execute commands, send requests, call tools, use a browser, use Kali, mutate targets, or bypass authorization.",
            "You only produce safe planning guidance from the structured case memory provided.",
        ]
    )


def _developer_safety_prompt(safety_gates: tuple[str, ...]) -> str:
    gates = "\n".join(f"- {gate}" for gate in safety_gates) or "- no safety gates supplied"

    return "\n".join(
        [
            "Safety requirements:",
            "",
            "- Treat the work as planning-only.",
            "- Require confirmed scope and authorization before any active validation.",
            "- Prefer controlled accounts and synthetic test data.",
            "- Require redaction for cookies, tokens, API keys, emails, IDs, screenshots, and private data.",
            "- Do not provide credential theft, persistence, evasion, destructive, or unauthorized exploitation instructions.",
            "- Do not suggest running commands or browser actions directly; produce human-reviewable plans only.",
            "- Stop if real customer data, live secrets, or out-of-scope systems appear.",
            "",
            "Active safety gates:",
            "",
            gates,
        ]
    )


def _user_context_prompt(
    target_name: str,
    focus_queue: list[dict[str, Any]],
    global_actions: list[dict[str, Any]],
) -> str:
    lines = [
        f"Target: {target_name}",
        "",
        "AI brain focus queue:",
        "",
    ]

    if not focus_queue:
        lines.append("- No focus items were supplied.")
    else:
        for index, item in enumerate(focus_queue, start=1):
            lines.append(f"{index}. Endpoint: {item.get('endpoint', 'unknown-endpoint')}")
            lines.append(f"   Priority: {item.get('priority_band', 'info')} / {item.get('priority_score', 0)}")
            lines.append(f"   Triage: {item.get('triage_state', 'unknown')}")
            lines.append(f"   Reason: {item.get('reason', 'none')}")
            lines.append("   Hypotheses:")
            for hypothesis in item.get("hypotheses") or []:
                lines.append(f"   - {hypothesis}")
            lines.append("   Required artifacts:")
            for artifact in item.get("required_artifacts") or []:
                lines.append(f"   - {artifact}")
            lines.append("   Next actions:")
            for action in item.get("next_actions") or []:
                approval = "yes" if action.get("human_approval_required") else "no"
                blocked_by = ", ".join(action.get("blocked_by") or []) or "none"
                lines.append(
                    f"   - {action.get('phase', 'phase')} / {action.get('name', 'action')} "
                    f"(approval={approval}, blocked_by={blocked_by})"
                )
            lines.append("")

    lines.append("Global actions:")
    if not global_actions:
        lines.append("- No global actions were supplied.")
    else:
        for action in global_actions:
            approval = "yes" if action.get("human_approval_required") else "no"
            blocked_by = ", ".join(action.get("blocked_by") or []) or "none"
            lines.append(
                f"- {action.get('phase', 'phase')} / {action.get('name', 'action')} "
                f"(approval={approval}, blocked_by={blocked_by}): {action.get('rationale', '')}"
            )

    return "\n".join(lines)


def _assistant_task_prompt() -> str:
    return "\n".join(
        [
            "Produce a planning-only reasoning response with these sections:",
            "",
            "1. Recommended focus endpoint",
            "2. Why this endpoint is highest signal",
            "3. Open hypotheses to review",
            "4. Evidence artifacts needed",
            "5. Human approvals required",
            "6. Safety gates still blocking execution",
            "7. Next manual validation step",
            "8. Stop conditions",
            "9. Research state updates to make after validation",
            "",
            "Do not write executable exploit code.",
            "Do not claim a vulnerability is confirmed without evidence.",
            "Do not suggest unauthorized testing.",
            "Do not request live secrets or private data.",
        ]
    )
