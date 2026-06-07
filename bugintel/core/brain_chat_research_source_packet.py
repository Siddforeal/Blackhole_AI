"""
Brain chat research source packet.

This module turns local, user-provided research sources into a deterministic
research packet. It does not browse the web, call LLM providers, execute tools,
send requests, collect target evidence, mutate targets, submit reports, or
confirm vulnerabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


KNOWN_SOURCE_TYPES = frozenset(
    {
        "vendor-docs",
        "security-advisory",
        "cve",
        "research-paper",
        "source-code",
        "repository",
        "bug-bounty-scope",
        "release-notes",
        "api-docs",
        "blog-post",
        "local-notes",
        "unknown",
    }
)


@dataclass(frozen=True)
class ResearchSourceItem:
    source_id: str
    title: str
    source_type: str
    url: str | None
    summary: str
    observations: tuple[str, ...]
    attack_surfaces: tuple[str, ...]
    keywords: tuple[str, ...]
    confidence: str
    local_only: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "title": self.title,
            "source_type": self.source_type,
            "url": self.url,
            "summary": self.summary,
            "observations": list(self.observations),
            "attack_surfaces": list(self.attack_surfaces),
            "keywords": list(self.keywords),
            "confidence": self.confidence,
            "local_only": self.local_only,
        }


@dataclass(frozen=True)
class BrainChatResearchSourcePacket:
    target_name: str
    packet_status: str
    source_count: int
    source_types: tuple[str, ...]
    sources: tuple[ResearchSourceItem, ...]
    research_questions: tuple[str, ...]
    likely_attack_surfaces: tuple[str, ...]
    source_gaps: tuple[str, ...]
    allowed_local_next_steps: tuple[str, ...]
    rejected_actions: tuple[str, ...]
    planning_only: bool = True
    execution_state: str = "not_executed"
    source: str = "brain-chat-research-source-packet"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "brain_chat_research_source_packet",
            "source": self.source,
            "target_name": self.target_name,
            "packet_status": self.packet_status,
            "source_count": self.source_count,
            "source_types": list(self.source_types),
            "sources": [item.to_dict() for item in self.sources],
            "research_questions": list(self.research_questions),
            "likely_attack_surfaces": list(self.likely_attack_surfaces),
            "source_gaps": list(self.source_gaps),
            "allowed_local_next_steps": list(self.allowed_local_next_steps),
            "rejected_actions": list(self.rejected_actions),
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
            "safety": {
                "local_only": True,
                "deterministic": True,
                "planning_only": True,
                "web_browsing": False,
                "network_interaction": False,
                "target_mutation": False,
                "tool_execution": False,
                "browser_execution": False,
                "curl_execution": False,
                "kali_execution": False,
                "llm_provider_calls": False,
                "provider_execution": False,
                "evidence_collection": False,
                "validation_execution": False,
                "runtime_execution_allowed": False,
                "report_submission": False,
                "vulnerability_confirmation": False,
            },
        }

    def to_markdown(self, title: str = "Brain Chat Research Source Packet") -> str:
        lines = [
            f"# {title}",
            "",
            "## Packet State",
            "",
            f"- Target name: `{self.target_name}`",
            f"- Packet status: `{self.packet_status}`",
            f"- Source count: `{self.source_count}`",
            f"- Source types: `{', '.join(self.source_types) if self.source_types else 'none'}`",
            "",
            "## Sources",
            "",
        ]

        if self.sources:
            for item in self.sources:
                lines.extend(
                    [
                        f"### {item.source_id}: {item.title}",
                        "",
                        f"- Type: `{item.source_type}`",
                        f"- URL: {item.url or 'none'}",
                        f"- Confidence: `{item.confidence}`",
                        f"- Summary: {item.summary or 'none'}",
                        "- Observations:",
                    ]
                )
                if item.observations:
                    for obs in item.observations:
                        lines.append(f"  - {obs}")
                else:
                    lines.append("  - none")

                lines.append("- Attack surfaces:")
                if item.attack_surfaces:
                    for surface in item.attack_surfaces:
                        lines.append(f"  - {surface}")
                else:
                    lines.append("  - none")

                lines.append("- Keywords:")
                if item.keywords:
                    for keyword in item.keywords:
                        lines.append(f"  - `{keyword}`")
                else:
                    lines.append("  - none")

                lines.append("")
        else:
            lines.append("- none")
            lines.append("")

        lines.extend(["## Research Questions", ""])
        if self.research_questions:
            for item in self.research_questions:
                lines.append(f"- {item}")
        else:
            lines.append("- none")

        lines.extend(["", "## Likely Attack Surfaces", ""])
        if self.likely_attack_surfaces:
            for item in self.likely_attack_surfaces:
                lines.append(f"- {item}")
        else:
            lines.append("- none")

        lines.extend(["", "## Source Gaps", ""])
        if self.source_gaps:
            for item in self.source_gaps:
                lines.append(f"- {item}")
        else:
            lines.append("- none")

        lines.extend(["", "## Allowed Local Next Steps", ""])
        for item in self.allowed_local_next_steps:
            lines.append(f"- {item}")

        lines.extend(["", "## Rejected Actions", ""])
        for item in self.rejected_actions:
            lines.append(f"- {item}")

        lines.extend(
            [
                "",
                "## Safety",
                "",
                "- This packet is local, deterministic, and planning-only.",
                "- It does not browse the web, call providers, execute commands, collect evidence, submit reports, or confirm vulnerabilities.",
                "",
            ]
        )

        return "\n".join(lines)


def build_research_source_packet(
    raw_sources: list[dict[str, Any]] | None,
    target_name: str = "unknown-target",
    source: str = "brain-chat-research-source-packet",
) -> BrainChatResearchSourcePacket:
    sources = tuple(_normalize_source(item, index) for index, item in enumerate(raw_sources or [], start=1))
    source_types = tuple(sorted({item.source_type for item in sources}))
    likely_attack_surfaces = tuple(_derive_attack_surfaces(sources))
    research_questions = tuple(_derive_research_questions(sources, likely_attack_surfaces))
    source_gaps = tuple(_derive_source_gaps(sources, source_types))
    packet_status = _packet_status(sources, source_gaps)

    return BrainChatResearchSourcePacket(
        target_name=_clean_string(target_name) or "unknown-target",
        packet_status=packet_status,
        source_count=len(sources),
        source_types=source_types,
        sources=sources,
        research_questions=research_questions,
        likely_attack_surfaces=likely_attack_surfaces,
        source_gaps=source_gaps,
        allowed_local_next_steps=tuple(_allowed_local_next_steps(packet_status)),
        rejected_actions=tuple(_rejected_actions()),
        source=source,
    )


def _normalize_source(raw: dict[str, Any], index: int) -> ResearchSourceItem:
    if not isinstance(raw, dict):
        raw = {}

    source_type = _clean_string(raw.get("source_type") or raw.get("type") or "unknown").lower()
    if source_type not in KNOWN_SOURCE_TYPES:
        source_type = "unknown"

    title = _clean_string(raw.get("title") or f"Research source {index}")
    source_id = _clean_string(raw.get("source_id") or raw.get("id") or f"source-{index}")
    url = _clean_string(raw.get("url"))
    summary = _clean_string(raw.get("summary") or raw.get("description") or "")
    observations = tuple(_string_list(raw.get("observations")))
    attack_surfaces = tuple(_string_list(raw.get("attack_surfaces")))
    keywords = tuple(_string_list(raw.get("keywords")))
    confidence = _clean_string(raw.get("confidence") or "medium").lower()
    if confidence not in {"low", "medium", "high"}:
        confidence = "medium"

    return ResearchSourceItem(
        source_id=source_id,
        title=title,
        source_type=source_type,
        url=url or None,
        summary=summary,
        observations=observations,
        attack_surfaces=attack_surfaces,
        keywords=keywords,
        confidence=confidence,
    )


def _derive_attack_surfaces(sources: tuple[ResearchSourceItem, ...]) -> list[str]:
    surfaces: list[str] = []

    for item in sources:
        surfaces.extend(item.attack_surfaces)

        text = " ".join(
            [
                item.title,
                item.summary,
                " ".join(item.observations),
                " ".join(item.keywords),
            ]
        ).lower()

        if any(word in text for word in ("upload", "import", "export", "backup", "restore", "zip", "archive", "package")):
            surfaces.append("Import/export/archive/package handling")
        if any(word in text for word in ("api", "graphql", "rest", "endpoint", "webhook")):
            surfaces.append("API and webhook surface")
        if any(word in text for word in ("auth", "oauth", "saml", "jwt", "token", "session")):
            surfaces.append("Authentication and session boundary")
        if any(word in text for word in ("admin", "role", "permission", "authorization", "access control")):
            surfaces.append("Authorization and administrative access control")
        if any(word in text for word in ("agent", "runner", "worker", "executor", "deployment")):
            surfaces.append("Agent, runner, worker, or deployment trust boundary")
        if any(word in text for word in ("template", "parser", "render", "deserialize", "yaml", "xml")):
            surfaces.append("Parser, template, and serialization surface")

    return _unique_nonempty(surfaces)


def _derive_research_questions(
    sources: tuple[ResearchSourceItem, ...],
    attack_surfaces: tuple[str, ...] | list[str],
) -> list[str]:
    questions: list[str] = []

    if not sources:
        return [
            "What official scope, documentation, source code, or release notes should be added before planning tests?",
        ]

    questions.append("What trust boundaries are documented or implied by the collected sources?")
    questions.append("Which components process attacker-controlled input, files, URLs, tokens, or configuration?")

    for surface in attack_surfaces:
        questions.append(f"What safe local checks can validate the {surface.lower()} without target interaction?")

    questions.append("Which findings require only local/source review before any live validation is considered?")
    questions.append("What evidence is still missing before proposing commands or target interaction?")

    return _unique_nonempty(questions)


def _derive_source_gaps(
    sources: tuple[ResearchSourceItem, ...],
    source_types: tuple[str, ...],
) -> list[str]:
    gaps: list[str] = []

    if not sources:
        return [
            "No local research sources were provided.",
            "Add official scope, vendor documentation, source code, release notes, advisories, or local notes.",
        ]

    if "bug-bounty-scope" not in source_types:
        gaps.append("Bug bounty scope source is missing.")
    if "vendor-docs" not in source_types and "api-docs" not in source_types:
        gaps.append("Vendor/API documentation source is missing.")
    if "source-code" not in source_types and "repository" not in source_types:
        gaps.append("Source code or repository source is missing.")
    if "security-advisory" not in source_types and "cve" not in source_types:
        gaps.append("Advisory/CVE background source is missing.")

    return gaps


def _packet_status(
    sources: tuple[ResearchSourceItem, ...],
    source_gaps: tuple[str, ...] | list[str],
) -> str:
    if not sources:
        return "blocked-pending-research-sources"
    if source_gaps:
        return "review-needed-source-gaps"
    return "ready-for-research-review"


def _allowed_local_next_steps(packet_status: str) -> list[str]:
    if packet_status == "ready-for-research-review":
        return [
            "Review the local research packet and decide which hypotheses should be planned next.",
            "Keep command generation, browsing, target interaction, and evidence collection behind later gates.",
        ]

    if packet_status == "review-needed-source-gaps":
        return [
            "Review source gaps and add missing local sources before hypothesis planning.",
            "Use only local notes or manually collected sources at this stage.",
        ]

    return [
        "Add local research sources before building hypotheses or commands.",
    ]


def _rejected_actions() -> list[str]:
    return [
        "Do not browse the web from this source packet.",
        "Do not execute network, browser, curl, Kali, shell, scanner, or target interaction steps from this source packet.",
        "Do not collect new evidence from a target from this source packet.",
        "Do not submit a report from research source packet state alone.",
        "Do not claim vulnerability confirmation from research source packet state alone.",
        "Do not treat this source packet as validation or runtime execution approval.",
    ]


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _clean_string(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _unique_nonempty(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        cleaned = _clean_string(item)
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(cleaned)
    return result
