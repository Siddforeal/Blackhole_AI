"""
Brain chat research hypothesis packet.

This module turns a local research source packet into deterministic research
hypotheses. It does not browse the web, call providers, execute tools, generate
commands, send requests, collect evidence, validate findings, submit reports, or
confirm vulnerabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from bugintel.core.brain_chat_research_source_packet import BrainChatResearchSourcePacket


@dataclass(frozen=True)
class ResearchHypothesisItem:
    hypothesis_id: str
    title: str
    attack_surface: str
    hypothesis_type: str
    rationale: str
    local_review_questions: tuple[str, ...]
    evidence_needed: tuple[str, ...]
    allowed_local_checks: tuple[str, ...]
    rejected_actions: tuple[str, ...]
    priority: str
    confidence: str
    tags: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "hypothesis_id": self.hypothesis_id,
            "title": self.title,
            "attack_surface": self.attack_surface,
            "hypothesis_type": self.hypothesis_type,
            "rationale": self.rationale,
            "local_review_questions": list(self.local_review_questions),
            "evidence_needed": list(self.evidence_needed),
            "allowed_local_checks": list(self.allowed_local_checks),
            "rejected_actions": list(self.rejected_actions),
            "priority": self.priority,
            "confidence": self.confidence,
            "tags": list(self.tags),
        }


@dataclass(frozen=True)
class BrainChatResearchHypothesisPacket:
    target_name: str
    packet_status: str
    source_packet_status: str
    hypothesis_count: int
    hypotheses: tuple[ResearchHypothesisItem, ...]
    source_gaps: tuple[str, ...]
    hypothesis_gaps: tuple[str, ...]
    allowed_local_next_steps: tuple[str, ...]
    rejected_actions: tuple[str, ...]
    planning_only: bool = True
    execution_state: str = "not_executed"
    source: str = "brain-chat-research-hypothesis-packet"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "brain_chat_research_hypothesis_packet",
            "source": self.source,
            "target_name": self.target_name,
            "packet_status": self.packet_status,
            "source_packet_status": self.source_packet_status,
            "hypothesis_count": self.hypothesis_count,
            "hypotheses": [item.to_dict() for item in self.hypotheses],
            "source_gaps": list(self.source_gaps),
            "hypothesis_gaps": list(self.hypothesis_gaps),
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
                "command_generation": False,
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

    def to_markdown(self, title: str = "Brain Chat Research Hypothesis Packet") -> str:
        lines = [
            f"# {title}",
            "",
            "## Packet State",
            "",
            f"- Target name: `{self.target_name}`",
            f"- Packet status: `{self.packet_status}`",
            f"- Source packet status: `{self.source_packet_status}`",
            f"- Hypothesis count: `{self.hypothesis_count}`",
            "",
            "## Hypotheses",
            "",
        ]

        if self.hypotheses:
            for item in self.hypotheses:
                lines.extend(
                    [
                        f"### {item.hypothesis_id}: {item.title}",
                        "",
                        f"- Attack surface: `{item.attack_surface}`",
                        f"- Type: `{item.hypothesis_type}`",
                        f"- Priority: `{item.priority}`",
                        f"- Confidence: `{item.confidence}`",
                        f"- Rationale: {item.rationale}",
                        "- Local review questions:",
                    ]
                )
                for question in item.local_review_questions:
                    lines.append(f"  - {question}")

                lines.append("- Evidence needed:")
                for evidence in item.evidence_needed:
                    lines.append(f"  - {evidence}")

                lines.append("- Allowed local checks:")
                for check in item.allowed_local_checks:
                    lines.append(f"  - {check}")

                lines.append("- Rejected actions:")
                for action in item.rejected_actions:
                    lines.append(f"  - {action}")

                lines.append("- Tags:")
                for tag in item.tags:
                    lines.append(f"  - `{tag}`")

                lines.append("")
        else:
            lines.append("- none")
            lines.append("")

        lines.extend(["## Source Gaps", ""])
        if self.source_gaps:
            for item in self.source_gaps:
                lines.append(f"- {item}")
        else:
            lines.append("- none")

        lines.extend(["", "## Hypothesis Gaps", ""])
        if self.hypothesis_gaps:
            for item in self.hypothesis_gaps:
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
                "- It does not browse, generate commands, execute tools, collect evidence, validate, submit reports, or confirm vulnerabilities.",
                "",
            ]
        )

        return "\n".join(lines)


def build_research_hypothesis_packet(
    source_packet: BrainChatResearchSourcePacket,
    source: str = "brain-chat-research-hypothesis-packet",
) -> BrainChatResearchHypothesisPacket:
    source_data = source_packet.to_dict()
    source_status = str(source_data.get("packet_status") or "unknown")
    target_name = str(source_data.get("target_name") or "unknown-target")
    source_gaps = tuple(_string_list(source_data.get("source_gaps")))

    if source_status != "ready-for-research-review":
        packet_status = "blocked-pending-ready-research-source-packet"
        hypotheses: tuple[ResearchHypothesisItem, ...] = ()
        hypothesis_gaps = (
            f"Research source packet is not ready: {source_status}.",
            "Resolve source gaps before deriving hypotheses.",
        )
    else:
        hypotheses = tuple(_derive_hypotheses(source_data))
        hypothesis_gaps = tuple(_derive_hypothesis_gaps(hypotheses))
        packet_status = "ready-for-hypothesis-review" if hypotheses and not hypothesis_gaps else "review-needed-hypothesis-gaps"

    return BrainChatResearchHypothesisPacket(
        target_name=target_name,
        packet_status=packet_status,
        source_packet_status=source_status,
        hypothesis_count=len(hypotheses),
        hypotheses=hypotheses,
        source_gaps=source_gaps,
        hypothesis_gaps=hypothesis_gaps,
        allowed_local_next_steps=tuple(_allowed_local_next_steps(packet_status)),
        rejected_actions=tuple(_rejected_actions()),
        source=source,
    )


def _derive_hypotheses(source_data: dict[str, Any]) -> list[ResearchHypothesisItem]:
    attack_surfaces = _string_list(source_data.get("likely_attack_surfaces"))
    research_questions = _string_list(source_data.get("research_questions"))
    sources = source_data.get("sources") if isinstance(source_data.get("sources"), list) else []

    hypotheses: list[ResearchHypothesisItem] = []

    for index, surface in enumerate(attack_surfaces, start=1):
        profile = _surface_profile(surface)
        priority = _priority_for_surface(surface)
        confidence = _confidence_for_surface(surface, sources)

        hypotheses.append(
            ResearchHypothesisItem(
                hypothesis_id=f"HYP-{index:03d}",
                title=f"Review {surface} for trust-boundary weaknesses",
                attack_surface=surface,
                hypothesis_type=profile["hypothesis_type"],
                rationale=profile["rationale"],
                local_review_questions=tuple(_local_review_questions(surface, research_questions)),
                evidence_needed=tuple(profile["evidence_needed"]),
                allowed_local_checks=tuple(profile["allowed_local_checks"]),
                rejected_actions=tuple(_hypothesis_rejected_actions()),
                priority=priority,
                confidence=confidence,
                tags=tuple(profile["tags"]),
            )
        )

    return hypotheses


def _surface_profile(surface: str) -> dict[str, Any]:
    lowered = surface.lower()

    if "archive" in lowered or "package" in lowered or "import" in lowered or "restore" in lowered:
        return {
            "hypothesis_type": "input-to-filesystem-trust-boundary",
            "rationale": "Import, restore, archive, and package flows often transform attacker-controlled names or entries into filesystem writes.",
            "evidence_needed": [
                "Local source path from parser/import entrypoint to extraction or write primitive.",
                "Canonicalization and root-boundary checks around output paths.",
                "A local-only proof showing whether traversal, overwrite, or unsafe extraction is possible.",
            ],
            "allowed_local_checks": [
                "Review local source code for archive entry handling and path normalization.",
                "Map parser entrypoints to filesystem write calls without target interaction.",
                "Prepare non-executed local PoC design notes only.",
            ],
            "tags": ["archive", "filesystem", "parser", "path-boundary"],
        }

    if "api" in lowered or "webhook" in lowered:
        return {
            "hypothesis_type": "api-authentication-authorization-boundary",
            "rationale": "API and webhook surfaces can expose object access, signature validation, token handling, and role enforcement mistakes.",
            "evidence_needed": [
                "Local endpoint inventory from documentation or source.",
                "Authentication and authorization decision points for each sensitive endpoint.",
                "A local matrix of object owner, role, and tenant boundaries.",
            ],
            "allowed_local_checks": [
                "Review local API route definitions and middleware order.",
                "Map documented endpoints to auth and authorization checks.",
                "Draft safe validation criteria without generating live requests.",
            ],
            "tags": ["api", "webhook", "authz", "token"],
        }

    if "auth" in lowered or "session" in lowered:
        return {
            "hypothesis_type": "authentication-session-trust-boundary",
            "rationale": "Authentication/session code can fail around token validation, refresh flows, audience checks, and session binding.",
            "evidence_needed": [
                "Local token/session lifecycle map.",
                "Validation checks for issuer, audience, expiry, tenant, and session binding.",
                "Source evidence for refresh and logout invalidation behavior.",
            ],
            "allowed_local_checks": [
                "Review local authentication middleware and token validation helpers.",
                "Map session creation, refresh, and invalidation flows.",
                "Identify missing checks before any runtime validation is proposed.",
            ],
            "tags": ["authentication", "session", "jwt", "token"],
        }

    if "authorization" in lowered or "admin" in lowered or "access control" in lowered:
        return {
            "hypothesis_type": "authorization-admin-boundary",
            "rationale": "Administrative and authorization boundaries can fail when role checks are missing, inconsistent, or applied after object lookup.",
            "evidence_needed": [
                "Local role and permission model.",
                "Object ownership and tenant boundary checks.",
                "Sensitive admin operations and required roles.",
            ],
            "allowed_local_checks": [
                "Review local permission checks and role mapping.",
                "Build a local-only access-control matrix.",
                "Identify endpoints that require differential validation later.",
            ],
            "tags": ["authorization", "admin", "rbac", "tenant"],
        }

    if "agent" in lowered or "runner" in lowered or "worker" in lowered or "deployment" in lowered:
        return {
            "hypothesis_type": "worker-execution-trust-boundary",
            "rationale": "Agent, runner, worker, and deployment flows can bridge low-trust configuration or package data into privileged execution contexts.",
            "evidence_needed": [
                "Local dataflow from user-controlled configuration/package fields into worker execution.",
                "Boundary between controller/server and worker/agent trust levels.",
                "Evidence of sanitization, allowlists, and execution policy checks.",
            ],
            "allowed_local_checks": [
                "Review local worker job deserialization and execution planning code.",
                "Map package/configuration fields to worker command or script construction.",
                "Keep all execution proof planning non-executed until later gates.",
            ],
            "tags": ["worker", "agent", "deployment", "execution-boundary"],
        }

    if "parser" in lowered or "template" in lowered or "serialization" in lowered:
        return {
            "hypothesis_type": "parser-template-serialization-boundary",
            "rationale": "Parser, template, and serialization surfaces can fail through unsafe deserialization, injection, or confused data interpretation.",
            "evidence_needed": [
                "Local parser/template entrypoints and accepted formats.",
                "Dangerous sinks such as eval, template rendering, XML/YAML loaders, or object deserialization.",
                "Input constraints and safe parser configuration evidence.",
            ],
            "allowed_local_checks": [
                "Review local parser configuration and dangerous sink usage.",
                "Map accepted file/data formats to parser libraries.",
                "Prepare safe local test cases only after a later validation gate.",
            ],
            "tags": ["parser", "template", "serialization", "injection"],
        }

    return {
        "hypothesis_type": "general-trust-boundary",
        "rationale": "The collected sources imply a trust boundary that needs local source and documentation review before any validation.",
        "evidence_needed": [
            "Local source or documentation evidence defining the boundary.",
            "Potential attacker-controlled inputs and privileged sinks.",
            "Safety constraints for any future validation.",
        ],
        "allowed_local_checks": [
            "Review local sources and documentation.",
            "Map inputs, trust boundaries, and sinks.",
            "Do not generate commands or interact with targets from this packet.",
        ],
        "tags": ["trust-boundary", "local-review"],
    }


def _local_review_questions(surface: str, research_questions: list[str]) -> list[str]:
    selected = [
        question for question in research_questions
        if surface.lower() in question.lower() or "trust boundaries" in question.lower()
    ]

    selected.extend(
        [
            f"Where does attacker-controlled input enter the {surface.lower()}?",
            f"What privileged sink or security decision does the {surface.lower()} influence?",
            f"What local evidence would disprove this hypothesis before any validation is proposed?",
        ]
    )

    return _unique_nonempty(selected)[:6]


def _derive_hypothesis_gaps(hypotheses: tuple[ResearchHypothesisItem, ...]) -> list[str]:
    gaps: list[str] = []

    if not hypotheses:
        gaps.append("No hypotheses were derived from the research source packet.")

    if not any(item.priority == "high" for item in hypotheses):
        gaps.append("No high-priority hypothesis was derived.")

    if not any("filesystem" in item.tags or "authz" in item.tags or "execution-boundary" in item.tags for item in hypotheses):
        gaps.append("No filesystem, authorization, or execution-boundary hypothesis was derived.")

    return gaps


def _allowed_local_next_steps(packet_status: str) -> list[str]:
    if packet_status == "ready-for-hypothesis-review":
        return [
            "Review hypotheses and select one local-only hypothesis for deeper planning.",
            "Keep command generation, validation, evidence collection, reporting, and vulnerability confirmation behind later gates.",
        ]

    if packet_status == "review-needed-hypothesis-gaps":
        return [
            "Review hypothesis gaps and improve local source coverage before selecting a hypothesis.",
        ]

    return [
        "Resolve the research source packet before deriving or reviewing hypotheses.",
    ]


def _rejected_actions() -> list[str]:
    return [
        "Do not browse the web from this hypothesis packet.",
        "Do not generate curl, Kali, browser, scanner, shell, or target interaction commands from this hypothesis packet.",
        "Do not execute tools or collect evidence from a target from this hypothesis packet.",
        "Do not submit a report from research hypothesis packet state alone.",
        "Do not claim vulnerability confirmation from research hypothesis packet state alone.",
        "Do not treat this hypothesis packet as validation or runtime execution approval.",
    ]


def _hypothesis_rejected_actions() -> list[str]:
    return [
        "Do not execute this hypothesis.",
        "Do not generate live target commands from this hypothesis.",
        "Do not collect target evidence from this hypothesis.",
        "Do not claim the hypothesis is a vulnerability without later validation gates.",
    ]


def _priority_for_surface(surface: str) -> str:
    lowered = surface.lower()
    if any(word in lowered for word in ("archive", "package", "restore", "worker", "agent", "deployment", "authorization", "admin")):
        return "high"
    if any(word in lowered for word in ("api", "webhook", "auth", "session", "parser", "template", "serialization")):
        return "medium"
    return "low"


def _confidence_for_surface(surface: str, sources: list[Any]) -> str:
    lowered = surface.lower()
    supporting_sources = 0

    for raw in sources:
        if not isinstance(raw, dict):
            continue
        text = " ".join(
            str(raw.get(key, ""))
            for key in ("title", "source_type", "summary")
        ).lower()
        text += " " + " ".join(_string_list(raw.get("observations"))).lower()
        text += " " + " ".join(_string_list(raw.get("attack_surfaces"))).lower()
        text += " " + " ".join(_string_list(raw.get("keywords"))).lower()

        if any(token in text for token in lowered.replace("/", " ").replace(",", " ").split()):
            supporting_sources += 1

    if supporting_sources >= 2:
        return "high"
    if supporting_sources == 1:
        return "medium"
    return "low"


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _unique_nonempty(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        cleaned = str(item).strip()
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(cleaned)
    return result
