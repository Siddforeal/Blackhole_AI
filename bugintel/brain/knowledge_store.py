from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from bugintel.brain.models import (
    BrainEntity,
    BrainHypothesis,
    BrainRelationship,
    BrainSafety,
)


@dataclass(frozen=True)
class BrainKnowledgeRecord:
    record_id: str
    record_type: str
    title: str
    summary: str
    source: str
    tags: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "record_type": self.record_type,
            "title": self.title,
            "summary": self.summary,
            "source": self.source,
            "tags": list(self.tags),
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class BrainKnowledgeStoreSnapshot:
    store_id: str
    version: str
    status: str
    records: tuple[BrainKnowledgeRecord, ...]
    entities: tuple[BrainEntity, ...]
    relationships: tuple[BrainRelationship, ...]
    hypotheses: tuple[BrainHypothesis, ...]
    safety: BrainSafety = field(default_factory=BrainSafety)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "blackhole_brain_knowledge_store",
            "store_id": self.store_id,
            "version": self.version,
            "status": self.status,
            "record_count": len(self.records),
            "entity_count": len(self.entities),
            "relationship_count": len(self.relationships),
            "hypothesis_count": len(self.hypotheses),
            "records": [record.to_dict() for record in self.records],
            "entities": [entity.to_dict() for entity in self.entities],
            "relationships": [relationship.to_dict() for relationship in self.relationships],
            "hypotheses": [hypothesis.to_dict() for hypothesis in self.hypotheses],
            **self.safety.to_dict(),
        }

    def to_markdown(self) -> str:
        lines = [
            "# Blackhole Brain Knowledge Store",
            "",
            f"- Store ID: `{self.store_id}`",
            f"- Version: `{self.version}`",
            f"- Status: `{self.status}`",
            f"- Records: `{len(self.records)}`",
            f"- Entities: `{len(self.entities)}`",
            f"- Relationships: `{len(self.relationships)}`",
            f"- Hypotheses: `{len(self.hypotheses)}`",
            "",
            "## Knowledge Records",
            "",
        ]

        if not self.records:
            lines.append("- none")
        else:
            for record in self.records:
                lines.append(f"- `{record.record_type}` / `{record.confidence}` — {record.title}")

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


def build_brain_knowledge_store_snapshot(
    records: tuple[BrainKnowledgeRecord, ...] = (),
    entities: tuple[BrainEntity, ...] = (),
    relationships: tuple[BrainRelationship, ...] = (),
    hypotheses: tuple[BrainHypothesis, ...] = (),
) -> BrainKnowledgeStoreSnapshot:
    return BrainKnowledgeStoreSnapshot(
        store_id="BLACKHOLE-BRAIN-KNOWLEDGE-STORE-v1.78.0",
        version="1.78.0",
        status="knowledge-store-local-only",
        records=tuple(_dedupe_records(records)),
        entities=tuple(_dedupe_entities(entities)),
        relationships=tuple(_dedupe_relationships(relationships)),
        hypotheses=tuple(_dedupe_hypotheses(hypotheses)),
    )


def _dedupe_records(records: tuple[BrainKnowledgeRecord, ...]) -> list[BrainKnowledgeRecord]:
    seen: set[str] = set()
    output: list[BrainKnowledgeRecord] = []
    for record in records:
        if record.record_id not in seen:
            seen.add(record.record_id)
            output.append(record)
    return output


def _dedupe_entities(entities: tuple[BrainEntity, ...]) -> list[BrainEntity]:
    seen: set[str] = set()
    output: list[BrainEntity] = []
    for entity in entities:
        if entity.entity_id not in seen:
            seen.add(entity.entity_id)
            output.append(entity)
    return output


def _dedupe_relationships(relationships: tuple[BrainRelationship, ...]) -> list[BrainRelationship]:
    seen: set[tuple[str, str, str]] = set()
    output: list[BrainRelationship] = []
    for relationship in relationships:
        key = (relationship.source_id, relationship.relationship_type, relationship.target_id)
        if key not in seen:
            seen.add(key)
            output.append(relationship)
    return output


def _dedupe_hypotheses(hypotheses: tuple[BrainHypothesis, ...]) -> list[BrainHypothesis]:
    seen: set[str] = set()
    output: list[BrainHypothesis] = []
    for hypothesis in hypotheses:
        if hypothesis.hypothesis_id not in seen:
            seen.add(hypothesis.hypothesis_id)
            output.append(hypothesis)
    return output
