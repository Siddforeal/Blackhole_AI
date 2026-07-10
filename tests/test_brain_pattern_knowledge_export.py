from __future__ import annotations

from bugintel.brain import (
    BrainPatternKnowledgeExport,
    build_brain_pattern_knowledge_export,
)


def test_brain_pattern_knowledge_export_connects_patterns_to_knowledge_store() -> None:
    export = build_brain_pattern_knowledge_export()
    data = export.to_dict()

    assert isinstance(export, BrainPatternKnowledgeExport)
    assert data["kind"] == "blackhole_brain_pattern_knowledge_export"
    assert data["export_id"] == "BLACKHOLE-BRAIN-PATTERN-KNOWLEDGE-EXPORT-v1.80.0"
    assert data["version"] == "1.80.0"
    assert data["status"] == "pattern-knowledge-export-local-only"

    assert data["pattern_library_id"] == "BLACKHOLE-BRAIN-PATTERN-LIBRARY-v1.79.0"
    assert data["knowledge_store_id"] == "BLACKHOLE-BRAIN-KNOWLEDGE-STORE-v1.78.0"

    assert data["pattern_count"] == 3
    assert data["record_count"] == 3
    assert data["entity_count"] == 15
    assert data["relationship_count"] == 12
    assert data["hypothesis_count"] == 3


def test_brain_pattern_knowledge_export_creates_vulnerability_pattern_records() -> None:
    data = build_brain_pattern_knowledge_export().to_dict()
    records = data["knowledge_store"]["records"]

    assert {record["record_type"] for record in records} == {"vulnerability-pattern"}
    assert {record["record_id"] for record in records} == {
        "knowledge-pattern-authorization-boundary",
        "knowledge-pattern-secret-exposure",
        "knowledge-pattern-server-side-request",
    }
    assert {record["title"] for record in records} == {
        "Authorization boundary weakness",
        "Sensitive data exposure",
        "Server-side request behavior",
    }


def test_brain_pattern_knowledge_export_creates_entities_and_relationships() -> None:
    data = build_brain_pattern_knowledge_export().to_dict()

    entities = data["knowledge_store"]["entities"]
    relationships = data["knowledge_store"]["relationships"]

    entity_types = {entity["entity_type"] for entity in entities}
    relationship_types = {relationship["relationship_type"] for relationship in relationships}

    assert entity_types == {
        "EvidenceRequirement",
        "Pattern",
        "PatternIndicator",
    }
    assert relationship_types == {
        "has_indicator",
        "requires_evidence",
    }

    assert len([entity for entity in entities if entity["entity_type"] == "Pattern"]) == 3
    assert len([entity for entity in entities if entity["entity_type"] == "PatternIndicator"]) == 6
    assert len([entity for entity in entities if entity["entity_type"] == "EvidenceRequirement"]) == 6


def test_brain_pattern_knowledge_export_creates_hypotheses_from_patterns() -> None:
    data = build_brain_pattern_knowledge_export().to_dict()
    hypotheses = data["knowledge_store"]["hypotheses"]

    assert {hypothesis["priority"] for hypothesis in hypotheses} == {"P2"}
    assert {hypothesis["vulnerability_class"] for hypothesis in hypotheses} == {
        "authorization",
        "information-disclosure",
        "ssrf",
    }

    for hypothesis in hypotheses:
        assert hypothesis["hypothesis_id"].startswith("hypothesis-pattern-")
        assert hypothesis["required_next_evidence"]


def test_brain_pattern_knowledge_export_preserves_no_execution_safety() -> None:
    data = build_brain_pattern_knowledge_export().to_dict()

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


def test_brain_pattern_knowledge_export_markdown_is_human_readable() -> None:
    markdown = build_brain_pattern_knowledge_export().to_markdown()

    assert "# Blackhole Brain Pattern Knowledge Export" in markdown
    assert "BLACKHOLE-BRAIN-PATTERN-LIBRARY-v1.79.0" in markdown
    assert "BLACKHOLE-BRAIN-KNOWLEDGE-STORE-v1.78.0" in markdown
    assert "Authorization boundary weakness" in markdown
    assert "Sensitive data exposure" in markdown
    assert "Server-side request behavior" in markdown
    assert "network_requests_allowed: `false`" in markdown
    assert "vulnerability_confirmation_allowed: `false`" in markdown
