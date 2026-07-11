from __future__ import annotations

from bugintel.brain import (
    BlackholeDemoCasePack,
    build_blackhole_demo_case_pack,
)


def test_blackhole_demo_case_pack_builds_visible_demo_output() -> None:
    pack = build_blackhole_demo_case_pack()
    data = pack.to_dict()

    assert isinstance(pack, BlackholeDemoCasePack)
    assert data["kind"] == "blackhole_demo_case_pack"
    assert data["demo_id"] == "BLACKHOLE-DEMO-CASE-PACK-v1.81.0"
    assert data["version"] == "1.81.0"
    assert data["product_version"] == "1.84.1"
    assert data["demo_schema_version"] == "1.81.0"
    assert data["status"] == "demo-case-pack-local-only"

    assert data["case_title"] == "Synthetic account export boundary review"
    assert data["target_label"] == "local-demo-api"
    assert data["observation_count"] == 3
    assert data["matched_pattern_count"] == 3
    assert data["knowledge_record_count"] == 3
    assert data["hypothesis_count"] == 3
    assert data["next_step_count"] == 5


def test_blackhole_demo_case_pack_contains_human_readable_observations() -> None:
    data = build_blackhole_demo_case_pack().to_dict()
    observations = data["observations"]

    assert {observation["signal_type"] for observation in observations} == {
        "endpoint",
        "evidence",
        "input",
    }
    assert {observation["observation_id"] for observation in observations} == {
        "demo-observation-account-id-route",
        "demo-observation-redacted-export-url",
        "demo-observation-callback-url-input",
    }

    for observation in observations:
        assert observation["title"]
        assert observation["summary"]
        assert observation["related_pattern_ids"]


def test_blackhole_demo_case_pack_matches_core_patterns() -> None:
    data = build_blackhole_demo_case_pack().to_dict()
    matched_patterns = data["matched_patterns"]

    assert {pattern["pattern_id"] for pattern in matched_patterns} == {
        "pattern-authorization-boundary",
        "pattern-secret-exposure",
        "pattern-server-side-request",
    }
    assert {pattern["vulnerability_class"] for pattern in matched_patterns} == {
        "authorization",
        "information-disclosure",
        "ssrf",
    }
    assert {pattern["severity_hint"] for pattern in matched_patterns} == {"P2"}

    for pattern in matched_patterns:
        assert 0.0 <= pattern["confidence"] <= 1.0
        assert pattern["rationale"]
        assert pattern["required_next_evidence"]


def test_blackhole_demo_case_pack_includes_knowledge_and_hypothesis_titles() -> None:
    data = build_blackhole_demo_case_pack().to_dict()

    assert set(data["knowledge_record_titles"]) == {
        "Authorization boundary weakness",
        "Sensitive data exposure",
        "Server-side request behavior",
    }

    assert set(data["hypothesis_titles"]) == {
        "Authorization boundary weakness hypothesis",
        "Sensitive data exposure hypothesis",
        "Server-side request behavior hypothesis",
    }


def test_blackhole_demo_case_pack_contains_next_plan_and_report_readiness() -> None:
    data = build_blackhole_demo_case_pack().to_dict()

    assert len(data["next_investigation_plan"]) == 5
    assert data["report_ready_summary"].startswith("Not report-ready.")
    assert "does not confirm a vulnerability" in data["report_ready_summary"]

    joined_steps = " ".join(data["next_investigation_plan"]).lower()
    assert "authorized" in joined_steps
    assert "redacted" in joined_steps
    assert "human approval" in joined_steps


def test_blackhole_demo_case_pack_preserves_no_execution_safety() -> None:
    data = build_blackhole_demo_case_pack().to_dict()

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


def test_blackhole_demo_case_pack_markdown_is_product_visible() -> None:
    markdown = build_blackhole_demo_case_pack().to_markdown()

    assert "# Blackhole Demo Case Pack" in markdown
    assert "Product version: `1.84.1`" in markdown
    assert "Demo schema version: `1.81.0`" in markdown
    assert "Legacy version alias: `1.81.0`" in markdown
    assert "Synthetic account export boundary review" in markdown
    assert "## Observations" in markdown
    assert "## Matched Patterns" in markdown
    assert "## Next Investigation Plan" in markdown
    assert "## Report-Ready Summary" in markdown
    assert "Authorization boundary weakness" in markdown
    assert "Sensitive data exposure" in markdown
    assert "Server-side request behavior" in markdown
    assert "network_requests_allowed: `false`" in markdown
    assert "vulnerability_confirmation_allowed: `false`" in markdown
