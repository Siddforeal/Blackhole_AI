"""
Local safety scanner for LLM prompt packages.

This module does not call an LLM provider, does not read API keys, does not
perform network activity, and does not execute commands. It only scans prompt
package text for common sensitive patterns and risky instruction patterns.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any

from bugintel.core.llm_prompt import LLMPromptPackage


@dataclass(frozen=True)
class PromptSafetyFinding:
    """One local prompt safety finding."""

    category: str
    severity: str
    label: str
    evidence: str
    recommendation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LLMPromptSafetyReport:
    """Safety audit report for an LLM prompt package."""

    status: str
    finding_count: int
    high_count: int
    medium_count: int
    low_count: int
    findings: tuple[PromptSafetyFinding, ...]
    safety_notes: tuple[str, ...] = (
        "This report is generated locally and does not call an LLM provider.",
        "Review high and medium findings before sending prompts to any model.",
        "Treat a clean scan as a helper signal, not a formal data-loss guarantee.",
    )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["findings"] = [finding.to_dict() for finding in self.findings]
        return data


_SENSITIVE_PATTERNS: tuple[tuple[str, str, str, re.Pattern[str]], ...] = (
    (
        "sensitive-data",
        "medium",
        "Email address present",
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    ),
    (
        "sensitive-data",
        "high",
        "JWT-like token present",
        re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
    ),
    (
        "sensitive-data",
        "high",
        "AWS access key ID present",
        re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    ),
    (
        "sensitive-data",
        "high",
        "Secret assignment present",
        re.compile(r"(?i)\b(api[_-]?key|secret|password|token)\s*[:=]\s*['\"]?[^'\"\s,}]+"),
    ),
    (
        "sensitive-data",
        "high",
        "Bearer token present",
        re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{12,}"),
    ),
)

_RISKY_INSTRUCTION_PATTERNS: tuple[tuple[str, str, str, re.Pattern[str]], ...] = (
    (
        "risky-instruction",
        "medium",
        "Prompt-injection style instruction",
        re.compile(r"(?i)\b(ignore|disregard|override)\s+(all\s+)?(previous|prior|system)\s+instructions?\b"),
    ),
    (
        "risky-instruction",
        "medium",
        "Safety-bypass instruction",
        re.compile(r"(?i)\b(bypass|disable|ignore)\s+(safety|guardrails|policy|scope)\b"),
    ),
    (
        "risky-instruction",
        "high",
        "Credential theft instruction",
        re.compile(r"(?i)\b(steal|dump|extract|exfiltrate)\s+(credentials?|passwords?|tokens?|secrets?|cookies?)\b"),
    ),
    (
        "risky-instruction",
        "high",
        "Destructive action instruction",
        re.compile(r"(?i)\b(delete|wipe|destroy|drop)\s+(database|tables?|files?|records?)\b"),
    ),
)


def _mask_evidence(value: str, max_length: int = 80) -> str:
    value = value.replace("\n", "\\n")

    if len(value) <= max_length:
        return value

    return value[: max_length - 3] + "..."


def _scan_patterns(
    text: str,
    patterns: tuple[tuple[str, str, str, re.Pattern[str]], ...],
    recommendation: str,
) -> list[PromptSafetyFinding]:
    findings: list[PromptSafetyFinding] = []

    for category, severity, label, pattern in patterns:
        for match in pattern.finditer(text):
            findings.append(
                PromptSafetyFinding(
                    category=category,
                    severity=severity,
                    label=label,
                    evidence=_mask_evidence(match.group(0)),
                    recommendation=recommendation,
                )
            )

    return findings


def audit_llm_prompt_package(package: LLMPromptPackage) -> LLMPromptSafetyReport:
    """Audit a prompt package locally for sensitive and risky patterns."""
    text = "\n\n".join(
        (
            package.system_prompt,
            package.user_prompt,
            "\n".join(package.safety_notes),
        )
    )

    findings = []
    findings.extend(
        _scan_patterns(
            text,
            _SENSITIVE_PATTERNS,
            "Remove or redact sensitive values before provider use.",
        )
    )
    findings.extend(
        _scan_patterns(
            text,
            _RISKY_INSTRUCTION_PATTERNS,
            "Review the prompt for prompt injection or unsafe instructions before provider use.",
        )
    )

    high_count = sum(1 for finding in findings if finding.severity == "high")
    medium_count = sum(1 for finding in findings if finding.severity == "medium")
    low_count = sum(1 for finding in findings if finding.severity == "low")

    status = "blocked" if high_count else "review" if medium_count else "pass"

    return LLMPromptSafetyReport(
        status=status,
        finding_count=len(findings),
        high_count=high_count,
        medium_count=medium_count,
        low_count=low_count,
        findings=tuple(findings),
    )


def render_llm_prompt_safety_markdown(report: LLMPromptSafetyReport) -> str:
    """Render a prompt safety report as Markdown."""
    lines = [
        "# LLM Prompt Safety Audit",
        "",
        "## Summary",
        "",
        f"- Status: {report.status}",
        f"- Findings: {report.finding_count}",
        f"- High: {report.high_count}",
        f"- Medium: {report.medium_count}",
        f"- Low: {report.low_count}",
        "",
        "## Safety Notes",
        "",
    ]

    for note in report.safety_notes:
        lines.append(f"- {note}")

    lines.extend(["", "## Findings", ""])

    if not report.findings:
        lines.append("No local prompt safety findings were detected.")
    else:
        for index, finding in enumerate(report.findings, 1):
            lines.extend(
                [
                    f"### {index}. {finding.label}",
                    "",
                    f"- Category: {finding.category}",
                    f"- Severity: {finding.severity}",
                    f"- Evidence: `{finding.evidence}`",
                    f"- Recommendation: {finding.recommendation}",
                    "",
                ]
            )

    return "\n".join(lines).rstrip() + "\n"
