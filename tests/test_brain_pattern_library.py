from __future__ import annotations

from bugintel.brain import (
    BrainEvidenceRequirement,
    BrainPattern,
    BrainPatternIndicator,
    BrainPatternLibrarySnapshot,
    build_brain_pattern_library_snapshot,
    default_brain_patterns,
)


def test_brain_pattern_library_default_snapshot() -> None:
    snapshot = build_brain_pattern_library_snapshot()
    data = snapshot.to_dict()

    assert isinstance(snapshot, BrainPatternLibrarySnapshot)
    assert data["kind"] == "blackhole_brain_pattern_library"
    assert data["library_id"] == "BLACKHOLE-BRAIN-PATTERN-LIBRARY-v1.79.0"
    assert data["version"] == "1.79.0"
    assert data["status"] == "pattern-library-local-only"
    assert data["pattern_count"] == 3
    assert data["vulnerability_classes"] == [
        "authorization",
        "information-disclosure",
        "ssrf",
    ]
    assert data["severity_hints"] == ["P2"]


def test_brain_pattern_library_patterns_have_indicators_and_evidence_requirements() -> None:
    patterns = default_brain_patterns()

    assert len(patterns) == 3

    for pattern in patterns:
        assert pattern.pattern_id
        assert pattern.name
        assert pattern.vulnerability_class
        assert pattern.severity_hint == "P2"
        assert pattern.indicators
        assert pattern.evidence_requirements
        assert 0.0 <= pattern.confidence_hint <= 1.0


def test_brain_pattern_library_accepts_custom_patterns_and_dedupes() -> None:
    pattern = BrainPattern(
        pattern_id="pattern-custom-rbac",
        name="Custom RBAC pattern",
        vulnerability_class="authorization",
        summary="Custom authorization-boundary pattern.",
        severity_hint="P2",
        tags=("rbac", "custom"),
        confidence_hint=0.8,
        indicators=(
            BrainPatternIndicator(
                name="role-sensitive endpoint",
                description="Endpoint appears role-sensitive.",
                signal_type="endpoint",
                weight=1.0,
            ),
        ),
        evidence_requirements=(
            BrainEvidenceRequirement(
                name="role comparison",
                description="Compare two roles under authorized conditions.",
                required=True,
                human_approval_required=True,
            ),
        ),
    )

    snapshot = build_brain_pattern_library_snapshot(patterns=(pattern, pattern))
    data = snapshot.to_dict()

    assert data["pattern_count"] == 1
    assert data["patterns"][0]["pattern_id"] == "pattern-custom-rbac"
    assert data["patterns"][0]["indicators"][0]["name"] == "role-sensitive endpoint"
    assert data["patterns"][0]["evidence_requirements"][0]["human_approval_required"] is True


def test_brain_pattern_library_preserves_no_execution_safety() -> None:
    data = build_brain_pattern_library_snapshot().to_dict()

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


def test_brain_pattern_library_markdown_is_human_readable() -> None:
    markdown = build_brain_pattern_library_snapshot().to_markdown()

    assert "# Blackhole Brain Pattern Library" in markdown
    assert "Authorization boundary weakness" in markdown
    assert "Sensitive data exposure" in markdown
    assert "Server-side request behavior" in markdown
    assert "network_requests_allowed: `false`" in markdown
    assert "vulnerability_confirmation_allowed: `false`" in markdown
