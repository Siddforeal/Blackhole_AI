from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from bugintel.brain.knowledge_store import (
    BrainKnowledgeStoreSnapshot,
    BrainKnowledgeRecord,
    build_brain_knowledge_store_snapshot,
)
from bugintel.brain.models import BrainEntity, BrainHypothesis, BrainRelationship, BrainSafety
from bugintel.brain.pattern_library import (
    BrainPattern,
    BrainPatternLibrarySnapshot,
    build_brain_pattern_library_snapshot,
)


@dataclass(frozen=True)
class BrainPatternKnowledgeExport:
    export_id: str
    version: str
    status: str
    pattern_library: BrainPatternLibrarySnapshot
    knowledge_store: BrainKnowledgeStoreSnapshot
    safety: BrainSafety = field(default_factory=BrainSafety)

    def to_dict(self) -> dict[str, Any]:
        pattern_data = self.pattern_library.to_dict()
        store_data = self.knowledge_store.to_dict()

        return {
            "kind": "blackhole_brain_pattern_knowledge_export",
            "export_id": self.export_id,
            "version": self.version,
            "status": self.status,
            "pattern_library_id": self.pattern_library.library_id,
            "pattern_library_version": self.pattern_library.version,
            "knowledge_store_id": self.knowledge_store.store_id,
            "knowledge_store_version": self.knowledge_store.version,
            "pattern_count": pattern_data["pattern_count"],
            "record_count": store_data["record_count"],
            "entity_count": store_data["entity_count"],
            "relationship_count": store_data["relationship_count"],
            "hypothesis_count": store_data["hypothesis_count"],
            "pattern_library": pattern_data,
            "knowledge_store": store_data,
            **self.safety.to_dict(),
        }

    def to_markdown(self) -> str:
        data = self.to_dict()

        lines = [
            "# Blackhole Brain Pattern Knowledge Export",
            "",
            f"- Export ID: `{self.export_id}`",
            f"- Version: `{self.version}`",
            f"- Status: `{self.status}`",
            f"- Pattern library: `{self.pattern_library.library_id}`",
            f"- Knowledge store: `{self.knowledge_store.store_id}`",
            f"- Patterns: `{data['pattern_count']}`",
            f"- Records: `{data['record_count']}`",
            f"- Entities: `{data['entity_count']}`",
            f"- Relationships: `{data['relationship_count']}`",
            f"- Hypotheses: `{data['hypothesis_count']}`",
            "",
            "## Exported Patterns",
            "",
        ]

        for pattern in self.pattern_library.patterns:
            lines.append(f"- `{pattern.vulnerability_class}` / `{pattern.severity_hint}` — {pattern.name}")

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


def build_brain_pattern_knowledge_export(
    pattern_library: BrainPatternLibrarySnapshot | None = None,
) -> BrainPatternKnowledgeExport:
    library = pattern_library or build_brain_pattern_library_snapshot()
    patterns = library.patterns

    knowledge_store = build_brain_knowledge_store_snapshot(
        records=tuple(_record_from_pattern(pattern) for pattern in patterns),
        entities=tuple(_entities_from_patterns(patterns)),
        relationships=tuple(_relationships_from_patterns(patterns)),
        hypotheses=tuple(_hypothesis_from_pattern(pattern) for pattern in patterns),
    )

    return BrainPatternKnowledgeExport(
        export_id="BLACKHOLE-BRAIN-PATTERN-KNOWLEDGE-EXPORT-v1.80.0",
        version="1.80.0",
        status="pattern-knowledge-export-local-only",
        pattern_library=library,
        knowledge_store=knowledge_store,
    )


def _record_from_pattern(pattern: BrainPattern) -> BrainKnowledgeRecord:
    return BrainKnowledgeRecord(
        record_id=f"knowledge-{pattern.pattern_id}",
        record_type="vulnerability-pattern",
        title=pattern.name,
        summary=pattern.summary,
        source=pattern.pattern_id,
        tags=tuple(sorted(set(pattern.tags + (pattern.vulnerability_class, pattern.severity_hint)))),
        confidence=pattern.confidence_hint,
    )


def _entities_from_patterns(patterns: tuple[BrainPattern, ...]) -> list[BrainEntity]:
    entities: list[BrainEntity] = []

    for pattern in patterns:
        entities.append(
            BrainEntity(
                entity_id=pattern.pattern_id,
                entity_type="Pattern",
                title=pattern.name,
                summary=pattern.summary,
                tags=tuple(sorted(set(pattern.tags + (pattern.vulnerability_class,)))),
            )
        )

        for indicator in pattern.indicators:
            indicator_id = _child_id(pattern.pattern_id, "indicator", indicator.name)
            entities.append(
                BrainEntity(
                    entity_id=indicator_id,
                    entity_type="PatternIndicator",
                    title=indicator.name,
                    summary=indicator.description,
                    tags=(indicator.signal_type,),
                )
            )

        for requirement in pattern.evidence_requirements:
            requirement_id = _child_id(pattern.pattern_id, "evidence", requirement.name)
            entities.append(
                BrainEntity(
                    entity_id=requirement_id,
                    entity_type="EvidenceRequirement",
                    title=requirement.name,
                    summary=requirement.description,
                    tags=("human-approval" if requirement.human_approval_required else "local-review",),
                )
            )

    return entities


def _relationships_from_patterns(patterns: tuple[BrainPattern, ...]) -> list[BrainRelationship]:
    relationships: list[BrainRelationship] = []

    for pattern in patterns:
        for indicator in pattern.indicators:
            relationships.append(
                BrainRelationship(
                    source_id=pattern.pattern_id,
                    relationship_type="has_indicator",
                    target_id=_child_id(pattern.pattern_id, "indicator", indicator.name),
                    confidence=indicator.weight,
                    rationale=indicator.description,
                )
            )

        for requirement in pattern.evidence_requirements:
            relationships.append(
                BrainRelationship(
                    source_id=pattern.pattern_id,
                    relationship_type="requires_evidence",
                    target_id=_child_id(pattern.pattern_id, "evidence", requirement.name),
                    confidence=1.0,
                    rationale=requirement.description,
                )
            )

    return relationships


def _hypothesis_from_pattern(pattern: BrainPattern) -> BrainHypothesis:
    return BrainHypothesis(
        hypothesis_id=f"hypothesis-{pattern.pattern_id}",
        title=f"{pattern.name} hypothesis",
        description=pattern.summary,
        vulnerability_class=pattern.vulnerability_class,
        confidence=pattern.confidence_hint,
        priority=pattern.severity_hint,
        required_next_evidence=tuple(requirement.name for requirement in pattern.evidence_requirements),
    )


def _child_id(pattern_id: str, child_type: str, name: str) -> str:
    slug = "".join(char.lower() if char.isalnum() else "-" for char in name)
    slug = "-".join(part for part in slug.split("-") if part)
    return f"{pattern_id}-{child_type}-{slug}"
