from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from bugintel.brain.models import BrainSafety


@dataclass(frozen=True)
class BrainPatternIndicator:
    name: str
    description: str
    signal_type: str
    weight: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "signal_type": self.signal_type,
            "weight": self.weight,
        }


@dataclass(frozen=True)
class BrainEvidenceRequirement:
    name: str
    description: str
    required: bool = True
    human_approval_required: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "required": self.required,
            "human_approval_required": self.human_approval_required,
        }


@dataclass(frozen=True)
class BrainPattern:
    pattern_id: str
    name: str
    vulnerability_class: str
    summary: str
    severity_hint: str
    indicators: tuple[BrainPatternIndicator, ...] = field(default_factory=tuple)
    evidence_requirements: tuple[BrainEvidenceRequirement, ...] = field(default_factory=tuple)
    tags: tuple[str, ...] = field(default_factory=tuple)
    confidence_hint: float = 0.5

    def to_dict(self) -> dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "name": self.name,
            "vulnerability_class": self.vulnerability_class,
            "summary": self.summary,
            "severity_hint": self.severity_hint,
            "indicators": [indicator.to_dict() for indicator in self.indicators],
            "evidence_requirements": [requirement.to_dict() for requirement in self.evidence_requirements],
            "tags": list(self.tags),
            "confidence_hint": self.confidence_hint,
        }


@dataclass(frozen=True)
class BrainPatternLibrarySnapshot:
    library_id: str
    version: str
    status: str
    patterns: tuple[BrainPattern, ...]
    safety: BrainSafety = field(default_factory=BrainSafety)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "blackhole_brain_pattern_library",
            "library_id": self.library_id,
            "version": self.version,
            "status": self.status,
            "pattern_count": len(self.patterns),
            "patterns": [pattern.to_dict() for pattern in self.patterns],
            "vulnerability_classes": sorted({pattern.vulnerability_class for pattern in self.patterns}),
            "severity_hints": sorted({pattern.severity_hint for pattern in self.patterns}),
            **self.safety.to_dict(),
        }

    def to_markdown(self) -> str:
        lines = [
            "# Blackhole Brain Pattern Library",
            "",
            f"- Library ID: `{self.library_id}`",
            f"- Version: `{self.version}`",
            f"- Status: `{self.status}`",
            f"- Patterns: `{len(self.patterns)}`",
            "",
            "## Patterns",
            "",
        ]

        if not self.patterns:
            lines.append("- none")
        else:
            for pattern in self.patterns:
                lines.append(f"- `{pattern.vulnerability_class}` / `{pattern.severity_hint}` — {pattern.name}")
                lines.append(f"  - Indicators: `{len(pattern.indicators)}`")
                lines.append(f"  - Evidence requirements: `{len(pattern.evidence_requirements)}`")

        lines.extend(
            [
                "",
                "## Safety",
                "",
                "- adapter_execution_state: `not_executed`",
                "- execution_allowed: `false`",
                "- network_requests_allowed: `false`",
                "- evidence_collection_allowed: `false`",
                "- target_mutation_allowed: `false`",
                "- report_submission_allowed: `false`",
                "- vulnerability_confirmation_allowed: `false`",
                "",
            ]
        )

        return "\n".join(lines)


def build_brain_pattern_library_snapshot(
    patterns: tuple[BrainPattern, ...] | None = None,
) -> BrainPatternLibrarySnapshot:
    selected_patterns = patterns if patterns is not None else default_brain_patterns()
    return BrainPatternLibrarySnapshot(
        library_id="BLACKHOLE-BRAIN-PATTERN-LIBRARY-v1.79.0",
        version="1.79.0",
        status="pattern-library-local-only",
        patterns=tuple(_dedupe_patterns(selected_patterns)),
    )


def default_brain_patterns() -> tuple[BrainPattern, ...]:
    return (
        BrainPattern(
            pattern_id="pattern-authorization-boundary",
            name="Authorization boundary weakness",
            vulnerability_class="authorization",
            summary="User, role, tenant, project, or account boundary behavior may be inconsistent.",
            severity_hint="P2",
            tags=("authorization", "rbac", "idor", "tenant-boundary"),
            confidence_hint=0.75,
            indicators=(
                BrainPatternIndicator("object identifier in route", "Endpoint contains user, account, project, tenant, or object identifiers.", "endpoint"),
                BrainPatternIndicator("privileged operation", "Endpoint appears to read, write, deploy, invite, export, or administer scoped resources.", "behavior"),
            ),
            evidence_requirements=(
                BrainEvidenceRequirement("authorized scope proof", "Show the tested identity and its allowed scope.", True, False),
                BrainEvidenceRequirement("boundary comparison", "Compare behavior across two users, roles, tenants, projects, or accounts.", True, True),
            ),
        ),
        BrainPattern(
            pattern_id="pattern-secret-exposure",
            name="Sensitive data exposure",
            vulnerability_class="information-disclosure",
            summary="A response, artifact, log, export, or workflow may reveal secrets or sensitive values.",
            severity_hint="P2",
            tags=("secret", "token", "credential", "exposure"),
            confidence_hint=0.7,
            indicators=(
                BrainPatternIndicator("secret-like value", "Observed value resembles a token, key, password, credential, cookie, or signed secret.", "evidence"),
                BrainPatternIndicator("unexpected disclosure path", "Disclosure occurs through a low-privilege or indirect workflow.", "behavior"),
            ),
            evidence_requirements=(
                BrainEvidenceRequirement("redacted sample", "Keep only a safely redacted sample of the sensitive value.", True, False),
                BrainEvidenceRequirement("access-path explanation", "Explain why the actor should not receive the value.", True, False),
            ),
        ),
        BrainPattern(
            pattern_id="pattern-server-side-request",
            name="Server-side request behavior",
            vulnerability_class="ssrf",
            summary="A server-side fetch, webhook, import, preview, or integration feature may request attacker-controlled URLs.",
            severity_hint="P2",
            tags=("ssrf", "webhook", "import", "callback"),
            confidence_hint=0.65,
            indicators=(
                BrainPatternIndicator("url parameter", "Input accepts a URL, callback, webhook, feed, import, or preview target.", "input"),
                BrainPatternIndicator("outbound interaction signal", "Evidence suggests server-side outbound interaction.", "behavior"),
            ),
            evidence_requirements=(
                BrainEvidenceRequirement("safe external interaction proof", "Use only authorized, non-invasive interaction evidence.", True, True),
                BrainEvidenceRequirement("impact boundary", "Document reachable metadata, internal service, or callback impact without exploitation.", True, True),
            ),
        ),
    )


def _dedupe_patterns(patterns: tuple[BrainPattern, ...]) -> list[BrainPattern]:
    seen: set[str] = set()
    output: list[BrainPattern] = []

    for pattern in patterns:
        if pattern.pattern_id not in seen:
            seen.add(pattern.pattern_id)
            output.append(pattern)

    return output
