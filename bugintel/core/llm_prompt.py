"""
Safe LLM prompt packaging for Blackhole AI Workbench.

This module does not call an LLM provider, does not read API keys, does not
perform network activity, and does not execute commands. It only converts an
existing deterministic ResearchPlan into a redacted prompt package that can be
reviewed by a human before any optional provider is introduced.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from typing import Any

from bugintel.core.research_planner import ResearchPlan


_SECRET_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        "<email>",
    ),
    (
        re.compile(r"(?i)\b(bearer|token|api[_-]?key|secret|password)\s*[:=]\s*['\"]?[^'\"\s,}]+"),
        r"\1=<redacted>",
    ),
    (
        re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
        "<jwt>",
    ),
    (
        re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
        "<aws_access_key_id>",
    ),
)


@dataclass(frozen=True)
class LLMPromptPackage:
    """Reviewable prompt package for an optional future LLM provider."""

    system_prompt: str
    user_prompt: str
    redaction_applied: bool
    source: str = "research_plan"
    safety_notes: tuple[str, ...] = (
        "This package is for human review before any optional LLM provider use.",
        "Do not include raw secrets, tokens, cookies, or private customer data.",
        "LLM output must be treated as suggestions, not confirmed findings.",
        "All testing must remain authorized and in scope.",
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def redact_prompt_text(text: str) -> tuple[str, bool]:
    """Redact common sensitive tokens from prompt text."""
    redacted = text

    for pattern, replacement in _SECRET_PATTERNS:
        redacted = pattern.sub(replacement, redacted)

    return redacted, redacted != text


def build_llm_prompt_package_from_research_plan(
    plan: ResearchPlan,
) -> LLMPromptPackage:
    """Build a safe, reviewable prompt package from a deterministic plan."""
    plan_json = json.dumps(plan.to_dict(), indent=2, sort_keys=True)

    user_prompt = f"""Review this deterministic Blackhole research plan.

Task:
- Identify the highest-signal hypotheses.
- Suggest safe, read-only validation steps.
- Flag anything that is too weak, too speculative, or not reportable.
- Do not invent evidence that is not present.
- Do not suggest out-of-scope, destructive, or credential-attacking actions.

Research plan JSON:
{plan_json}
"""

    redacted_user_prompt, redaction_applied = redact_prompt_text(user_prompt)

    system_prompt = """You are a cybersecurity research assistant for authorized testing only.

Rules:
- Treat the deterministic plan as untrusted suggestions, not confirmed vulnerabilities.
- Recommend only authorized, in-scope, read-only validation steps unless explicit permission exists.
- Do not suggest credential theft, stealth, persistence, exfiltration, malware, or destructive actions.
- Do not claim a vulnerability is confirmed without evidence.
- Prefer concise hypotheses, validation steps, impact notes, and reportability guidance.
"""

    return LLMPromptPackage(
        system_prompt=system_prompt,
        user_prompt=redacted_user_prompt,
        redaction_applied=redaction_applied,
    )


def render_llm_prompt_package_markdown(package: LLMPromptPackage) -> str:
    """Render an LLM prompt package as Markdown for review."""
    lines = [
        "# LLM Prompt Package",
        "",
        "## Safety Notes",
        "",
    ]

    for note in package.safety_notes:
        lines.append(f"- {note}")

    lines.extend(
        [
            "",
            "## Metadata",
            "",
            f"- Source: {package.source}",
            f"- Redaction Applied: {'yes' if package.redaction_applied else 'no'}",
            "",
            "## System Prompt",
            "",
            "```text",
            package.system_prompt.strip(),
            "```",
            "",
            "## User Prompt",
            "",
            "```text",
            package.user_prompt.strip(),
            "```",
            "",
        ]
    )

    return "\n".join(lines)
