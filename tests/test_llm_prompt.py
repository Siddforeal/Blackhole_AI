from bugintel.core.llm_prompt import (
    build_llm_prompt_package_from_research_plan,
    redact_prompt_text,
    render_llm_prompt_package_markdown,
)
from bugintel.core.research_planner import build_research_plan_from_browser_evidence


def test_redact_prompt_text_redacts_email_jwt_and_secret_like_values():
    text = (
        "email=sidd@example.com "
        "Authorization: Bearer eyJaaaaaaaaaa.bbbbbbbbbbbb.cccccccccccc "
        "api_key=secret-value "
        "password=hunter2 "
        "aws=AKIAABCDEFGHIJKLMNOP"
    )

    redacted, changed = redact_prompt_text(text)

    assert changed is True
    assert "sidd@example.com" not in redacted
    assert "<email>" in redacted
    assert "<jwt>" in redacted
    assert "secret-value" not in redacted
    assert "hunter2" not in redacted
    assert "<aws_access_key_id>" in redacted


def test_build_llm_prompt_package_from_research_plan_is_offline_and_redacted():
    evidence = {
        "target_name": "demo-lab",
        "task_name": "capture dashboard",
        "evidence_type": "browser",
        "network_events": [
            {
                "method": "GET",
                "url": "https://demo.example.com/api/accounts/123/users?email=sidd@example.com",
                "status_code": 200,
                "request_headers": {
                    "authorization": "Bearer eyJaaaaaaaaaa.bbbbbbbbbbbb.cccccccccccc"
                },
            }
        ],
    }

    plan = build_research_plan_from_browser_evidence(evidence)
    package = build_llm_prompt_package_from_research_plan(plan)
    data = package.to_dict()

    assert data["source"] == "research_plan"
    assert data["redaction_applied"] is False
    assert "cybersecurity research assistant" in data["system_prompt"]
    assert "Review this deterministic BugIntel research plan" in data["user_prompt"]
    assert "sidd@example.com" not in data["user_prompt"]
    assert "eyJaaaaaaaaaa.bbbbbbbbbbbb.cccccccccccc" not in data["user_prompt"]
    assert "Do not invent evidence" in data["user_prompt"]
    assert package.safety_notes


def test_render_llm_prompt_package_markdown_contains_reviewable_prompts():
    evidence = {
        "target_name": "demo-lab",
        "task_name": "capture dashboard",
        "evidence_type": "browser",
        "network_events": [
            {
                "method": "GET",
                "url": "https://demo.example.com/api/accounts/123/users",
                "status_code": 200,
            }
        ],
    }

    plan = build_research_plan_from_browser_evidence(evidence)
    package = build_llm_prompt_package_from_research_plan(plan)
    markdown = render_llm_prompt_package_markdown(package)

    assert "# LLM Prompt Package" in markdown
    assert "## Safety Notes" in markdown
    assert "## System Prompt" in markdown
    assert "## User Prompt" in markdown
    assert "Research plan JSON" in markdown
