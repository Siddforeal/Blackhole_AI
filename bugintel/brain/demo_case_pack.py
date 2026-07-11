from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from bugintel.brain.models import BrainSafety
from bugintel.brain.pattern_knowledge_export import (
    BrainPatternKnowledgeExport,
    build_brain_pattern_knowledge_export,
)


@dataclass(frozen=True)
class BlackholeDemoObservation:
    observation_id: str
    title: str
    summary: str
    signal_type: str
    related_pattern_ids: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "title": self.title,
            "summary": self.summary,
            "signal_type": self.signal_type,
            "related_pattern_ids": list(self.related_pattern_ids),
        }


@dataclass(frozen=True)
class BlackholeDemoMatchedPattern:
    pattern_id: str
    name: str
    vulnerability_class: str
    severity_hint: str
    confidence: float
    rationale: str
    required_next_evidence: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "name": self.name,
            "vulnerability_class": self.vulnerability_class,
            "severity_hint": self.severity_hint,
            "confidence": self.confidence,
            "rationale": self.rationale,
            "required_next_evidence": list(self.required_next_evidence),
        }


@dataclass(frozen=True)
class BlackholeDemoCasePack:
    demo_id: str
    version: str
    product_version: str
    demo_schema_version: str
    status: str
    case_title: str
    case_summary: str
    target_label: str
    endpoint: str
    actor_context: str
    observations: tuple[BlackholeDemoObservation, ...]
    matched_patterns: tuple[BlackholeDemoMatchedPattern, ...]
    knowledge_record_titles: tuple[str, ...]
    hypothesis_titles: tuple[str, ...]
    next_investigation_plan: tuple[str, ...]
    report_ready_summary: str
    pattern_knowledge_export: BrainPatternKnowledgeExport
    safety: BrainSafety = field(default_factory=BrainSafety)

    def to_dict(self) -> dict[str, Any]:
        export_data = self.pattern_knowledge_export.to_dict()

        return {
            "kind": "blackhole_demo_case_pack",
            "demo_id": self.demo_id,
            "version": self.version,
            "product_version": self.product_version,
            "demo_schema_version": self.demo_schema_version,
            "status": self.status,
            "case_title": self.case_title,
            "case_summary": self.case_summary,
            "target_label": self.target_label,
            "endpoint": self.endpoint,
            "actor_context": self.actor_context,
            "observation_count": len(self.observations),
            "matched_pattern_count": len(self.matched_patterns),
            "knowledge_record_count": export_data["record_count"],
            "hypothesis_count": export_data["hypothesis_count"],
            "next_step_count": len(self.next_investigation_plan),
            "observations": [observation.to_dict() for observation in self.observations],
            "matched_patterns": [pattern.to_dict() for pattern in self.matched_patterns],
            "knowledge_record_titles": list(self.knowledge_record_titles),
            "hypothesis_titles": list(self.hypothesis_titles),
            "next_investigation_plan": list(self.next_investigation_plan),
            "report_ready_summary": self.report_ready_summary,
            "pattern_knowledge_export": export_data,
            **self.safety.to_dict(),
        }

    def to_markdown(self) -> str:
        lines = [
            "# Blackhole Demo Case Pack",
            "",
            f"- Demo ID: `{self.demo_id}`",
            f"- Product version: `{self.product_version}`",
            f"- Demo schema version: `{self.demo_schema_version}`",
            f"- Legacy version alias: `{self.version}`",
            f"- Status: `{self.status}`",
            f"- Case: {self.case_title}",
            f"- Target label: `{self.target_label}`",
            f"- Endpoint: `{self.endpoint}`",
            f"- Actor context: {self.actor_context}",
            "",
            "## Case Summary",
            "",
            self.case_summary,
            "",
            "## Observations",
            "",
        ]

        for observation in self.observations:
            lines.append(f"- `{observation.signal_type}` — {observation.title}")
            lines.append(f"  - {observation.summary}")

        lines.extend(["", "## Matched Patterns", ""])

        for pattern in self.matched_patterns:
            lines.append(
                f"- `{pattern.vulnerability_class}` / `{pattern.severity_hint}` / `{pattern.confidence}` — {pattern.name}"
            )
            lines.append(f"  - Rationale: {pattern.rationale}")
            lines.append(f"  - Required next evidence: {', '.join(pattern.required_next_evidence)}")

        lines.extend(["", "## Next Investigation Plan", ""])

        for index, step in enumerate(self.next_investigation_plan, start=1):
            lines.append(f"{index}. {step}")

        lines.extend(
            [
                "",
                "## Report-Ready Summary",
                "",
                self.report_ready_summary,
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


def build_blackhole_demo_case_pack(
    pattern_knowledge_export: BrainPatternKnowledgeExport | None = None,
) -> BlackholeDemoCasePack:
    export = pattern_knowledge_export or build_brain_pattern_knowledge_export()
    export_data = export.to_dict()

    patterns_by_id = {
        pattern["pattern_id"]: pattern
        for pattern in export_data["pattern_library"]["patterns"]
    }
    records = export_data["knowledge_store"]["records"]
    hypotheses = export_data["knowledge_store"]["hypotheses"]

    observations = (
        BlackholeDemoObservation(
            observation_id="demo-observation-account-id-route",
            title="Account identifier appears in export route",
            summary="Synthetic demo endpoint contains an account identifier and an export operation that should be scoped to the active user or tenant.",
            signal_type="endpoint",
            related_pattern_ids=("pattern-authorization-boundary",),
        ),
        BlackholeDemoObservation(
            observation_id="demo-observation-redacted-export-url",
            title="Response may contain a redacted signed export URL",
            summary="Demo notes include a placeholder signed URL value only. No real secret, token, or live response is stored.",
            signal_type="evidence",
            related_pattern_ids=("pattern-secret-exposure",),
        ),
        BlackholeDemoObservation(
            observation_id="demo-observation-callback-url-input",
            title="Export flow accepts a callback URL parameter",
            summary="Demo input models a callback URL field for planning only. No callback is sent and no outbound interaction is attempted.",
            signal_type="input",
            related_pattern_ids=("pattern-server-side-request",),
        ),
    )

    matched_patterns = tuple(
        _matched_pattern(
            pattern=patterns_by_id[pattern_id],
            confidence=confidence,
            rationale=rationale,
        )
        for pattern_id, confidence, rationale in (
            (
                "pattern-authorization-boundary",
                0.86,
                "The demo case contains an account-scoped object identifier and an export/read operation that should require boundary comparison.",
            ),
            (
                "pattern-secret-exposure",
                0.68,
                "The demo case models a redacted signed export URL, so the next safe step is to prove whether sensitive values are disclosed to the wrong actor.",
            ),
            (
                "pattern-server-side-request",
                0.61,
                "The demo case includes a callback URL input, so the next safe step is to review whether any server-side request behavior is possible inside scope.",
            ),
        )
    )

    return BlackholeDemoCasePack(
        demo_id="BLACKHOLE-DEMO-CASE-PACK-v1.81.0",
        version="1.81.0",
        product_version="1.84.1",
        demo_schema_version="1.81.0",
        status="demo-case-pack-local-only",
        case_title="Synthetic account export boundary review",
        case_summary=(
            "A synthetic local-only case showing how Blackhole turns observations into matched patterns, "
            "knowledge records, hypotheses, next evidence requirements, and a report-readiness summary."
        ),
        target_label="local-demo-api",
        endpoint="/api/v1/accounts/{account_id}/exports?callback_url=https://researcher.invalid/sink",
        actor_context="low-privilege viewer account in a synthetic local demo",
        observations=observations,
        matched_patterns=matched_patterns,
        knowledge_record_titles=tuple(record["title"] for record in records),
        hypothesis_titles=tuple(hypothesis["title"] for hypothesis in hypotheses),
        next_investigation_plan=(
            "Confirm the tested role, account, tenant, and exact allowed scope before any live testing.",
            "Perform a controlled two-account comparison only in an authorized environment.",
            "Keep any sensitive value samples redacted and store only local placeholder evidence.",
            "Review callback URL handling without triggering live outbound requests unless scope and human approval explicitly allow it.",
            "Do not mark the case report-ready until authorization, impact boundary, and safe evidence are reviewed.",
        ),
        report_ready_summary=(
            "Not report-ready. The demo shows a plausible research path, but it intentionally does not confirm a vulnerability. "
            "A human researcher still needs authorized boundary comparison, redacted evidence, and impact review."
        ),
        pattern_knowledge_export=export,
    )


def _matched_pattern(
    pattern: dict[str, Any],
    confidence: float,
    rationale: str,
) -> BlackholeDemoMatchedPattern:
    return BlackholeDemoMatchedPattern(
        pattern_id=pattern["pattern_id"],
        name=pattern["name"],
        vulnerability_class=pattern["vulnerability_class"],
        severity_hint=pattern["severity_hint"],
        confidence=confidence,
        rationale=rationale,
        required_next_evidence=tuple(
            requirement["name"]
            for requirement in pattern["evidence_requirements"]
            if requirement["required"]
        ),
    )
