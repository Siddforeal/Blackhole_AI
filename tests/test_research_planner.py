from bugintel.core.research_planner import (
    EvidenceReference,
    ResearchHypothesis,
    ResearchPlan,
    ResearchRecommendation,
    build_research_plan_from_browser_evidence,
)


def test_research_plan_models_serialize_to_dict():
    ref = EvidenceReference(
        evidence_type="browser",
        source="capture dashboard",
        locator="network_events[0]",
        summary="GET /api/accounts/123/users",
        tags=("api", "account"),
    )

    hypothesis = ResearchHypothesis(
        title="Account users route may need authorization review",
        category="api-authorization",
        rationale="The route exposes account-scoped users.",
        confidence="medium",
        evidence=(ref,),
        suggested_tests=("Compare own-account and foreign-account responses.",),
        tags=("bac",),
    )

    recommendation = ResearchRecommendation(
        priority=1,
        title="Prioritize account-scoped read routes",
        reason="They are high-impact if authorization is missing.",
        next_actions=("Build read-only checks.",),
        related_hypotheses=(hypothesis.title,),
    )

    plan = ResearchPlan(
        target_name="demo-lab",
        source_evidence_type="browser",
        hypotheses=(hypothesis,),
        recommendations=(recommendation,),
    )

    data = plan.to_dict()

    assert data["target_name"] == "demo-lab"
    assert data["source_evidence_type"] == "browser"
    assert data["generated_by"] == "deterministic"
    assert data["hypotheses"][0]["title"] == hypothesis.title
    assert data["hypotheses"][0]["evidence"][0]["locator"] == "network_events[0]"
    assert data["recommendations"][0]["priority"] == 1
    assert "Scope Guard" in " ".join(data["safety_notes"])


def test_build_research_plan_from_browser_evidence_detects_api_and_object_routes():
    evidence = {
        "target_name": "demo-lab",
        "task_name": "capture dashboard",
        "evidence_type": "browser",
        "network_events": [
            {
                "method": "GET",
                "url": "https://demo.example.com/api/accounts/123/users",
                "status_code": 200,
                "resource_type": "fetch",
            },
            {
                "method": "GET",
                "url": "https://demo.example.com/static/app.js",
                "status_code": 200,
                "resource_type": "script",
            },
        ],
        "screenshots": [
            {
                "path": "artifacts/browser/demo/screenshot.png",
                "sha256": "a" * 64,
            }
        ],
        "html_snapshots": [
            {
                "url": "https://demo.example.com/dashboard",
                "html_sha256": "b" * 64,
            }
        ],
    }

    plan = build_research_plan_from_browser_evidence(evidence)
    data = plan.to_dict()

    titles = [
        hypothesis["title"]
        for hypothesis in data["hypotheses"]
    ]

    assert data["target_name"] == "demo-lab"
    assert data["source_evidence_type"] == "browser"
    assert any("API surface" in title for title in titles)
    assert any("Identifier-bearing" in title for title in titles)
    assert any("Browser artifacts" in title for title in titles)

    recommendation = data["recommendations"][0]

    assert recommendation["priority"] == 1
    assert "Review browser-observed API routes" in recommendation["title"]
    assert recommendation["safety_notes"]


def test_build_research_plan_from_browser_evidence_detects_sensitive_and_error_routes():
    evidence = {
        "target_name": "admin-lab",
        "task_name": "admin workflow",
        "evidence_type": "browser",
        "network_events": [
            {
                "method": "GET",
                "url": "https://demo.example.com/api/admin/users",
                "status_code": 403,
                "resource_type": "fetch",
            },
            {
                "method": "GET",
                "url": "https://demo.example.com/api/export/jobs",
                "status_code": 500,
                "resource_type": "fetch",
            },
        ],
    }

    plan = build_research_plan_from_browser_evidence(evidence)
    categories = {
        hypothesis.category
        for hypothesis in plan.hypotheses
    }

    assert "sensitive-surface-review" in categories
    assert "error-handling" in categories


def test_build_research_plan_from_low_signal_evidence_recommends_more_collection():
    evidence = {
        "target_name": "static-lab",
        "task_name": "static page",
        "evidence_type": "browser",
        "network_events": [
            {
                "method": "GET",
                "url": "https://demo.example.com/assets/app.js",
                "status_code": 200,
            }
        ],
    }

    plan = build_research_plan_from_browser_evidence(evidence)

    assert plan.hypotheses == ()
    assert plan.recommendations[0].priority == 1
    assert "Collect more evidence" in plan.recommendations[0].title
