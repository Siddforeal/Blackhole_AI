from __future__ import annotations

from bugintel.brain import (
    BrainKnowledgeRecord,
    BrainKnowledgeStoreSnapshot,
    build_brain_knowledge_store_snapshot,
)
from bugintel.brain.models import BrainEntity, BrainHypothesis, BrainRelationship


def test_brain_knowledge_store_snapshot_defines_cross_case_store() -> None:
    snapshot = build_brain_knowledge_store_snapshot(
        records=(
            BrainKnowledgeRecord(
                record_id="record-rbac-001",
                record_type="pattern",
                title="RBAC boundary signal",
                summary="Reusable authorization-boundary knowledge.",
                source="unit-test",
                tags=("rbac", "authorization"),
                confidence=0.8,
            ),
        ),
        entities=(
            BrainEntity(
                entity_id="endpoint-admin-users",
                entity_type="Endpoint",
                title="/admin/users",
                summary="Admin user-management endpoint.",
                tags=("admin", "users"),
            ),
        ),
        relationships=(
            BrainRelationship(
                source_id="endpoint-admin-users",
                relationship_type="suggests",
                target_id="hypothesis-rbac-001",
                confidence=0.7,
                rationale="Admin endpoint suggests authorization boundary checks.",
            ),
        ),
        hypotheses=(
            BrainHypothesis(
                hypothesis_id="hypothesis-rbac-001",
                title="RBAC boundary hypothesis",
                description="Endpoint may expose role boundary behavior.",
                vulnerability_class="authorization",
                confidence=0.7,
                priority="P2",
            ),
        ),
    )

    data = snapshot.to_dict()

    assert isinstance(snapshot, BrainKnowledgeStoreSnapshot)
    assert data["kind"] == "blackhole_brain_knowledge_store"
    assert data["store_id"] == "BLACKHOLE-BRAIN-KNOWLEDGE-STORE-v1.78.0"
    assert data["version"] == "1.78.0"
    assert data["status"] == "knowledge-store-local-only"
    assert data["record_count"] == 1
    assert data["entity_count"] == 1
    assert data["relationship_count"] == 1
    assert data["hypothesis_count"] == 1
    assert data["records"][0]["record_type"] == "pattern"
    assert data["entities"][0]["entity_type"] == "Endpoint"
    assert data["hypotheses"][0]["priority"] == "P2"


def test_brain_knowledge_store_dedupes_records_entities_relationships_and_hypotheses() -> None:
    record = BrainKnowledgeRecord(
        record_id="duplicate-record",
        record_type="pattern",
        title="Duplicate pattern",
        summary="Should only appear once.",
        source="unit-test",
    )
    entity = BrainEntity("duplicate-entity", "Endpoint", "/api/test")
    relationship = BrainRelationship("duplicate-entity", "suggests", "duplicate-hypothesis")
    hypothesis = BrainHypothesis(
        hypothesis_id="duplicate-hypothesis",
        title="Duplicate hypothesis",
        description="Should only appear once.",
        vulnerability_class="authorization",
        confidence=0.5,
        priority="P2",
    )

    snapshot = build_brain_knowledge_store_snapshot(
        records=(record, record),
        entities=(entity, entity),
        relationships=(relationship, relationship),
        hypotheses=(hypothesis, hypothesis),
    )
    data = snapshot.to_dict()

    assert data["record_count"] == 1
    assert data["entity_count"] == 1
    assert data["relationship_count"] == 1
    assert data["hypothesis_count"] == 1


def test_brain_knowledge_store_preserves_no_execution_safety() -> None:
    data = build_brain_knowledge_store_snapshot().to_dict()

    assert data["adapter_execution_state"] == "not_executed"
    assert data["can_execute_now"] is False
    assert data["execution_allowed"] is False
    assert data["validation_allowed"] is False
    assert data["runtime_execution_allowed"] is False
    assert data["tool_execution_allowed"] is False
    assert data["browser_execution_allowed"] is False
    assert data["network_requests_allowed"] is False
    assert data["evidence_collection_allowed"] is False
    assert data["target_mutation_allowed"] is False
    assert data["report_submission_allowed"] is False
    assert data["vulnerability_confirmation_allowed"] is False
    assert data["planning_only"] is True
    assert data["dry_run_only"] is True


def test_brain_knowledge_store_markdown_is_human_readable() -> None:
    snapshot = build_brain_knowledge_store_snapshot(
        records=(
            BrainKnowledgeRecord(
                record_id="record-oauth-001",
                record_type="pattern",
                title="OAuth redirect signal",
                summary="Reusable OAuth redirect validation knowledge.",
                source="unit-test",
                tags=("oauth",),
                confidence=0.9,
            ),
        )
    )

    markdown = snapshot.to_markdown()

    assert "# Blackhole Brain Knowledge Store" in markdown
    assert "OAuth redirect signal" in markdown
    assert "## Knowledge Records" in markdown
    assert "network_requests_allowed: `false`" in markdown
    assert "vulnerability_confirmation_allowed: `false`" in markdown
