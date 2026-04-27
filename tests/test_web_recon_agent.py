from bugintel.agents.js_agent import JSCollectionResult, JSSourceResult
from bugintel.agents.recon_agent import analyze_html
from bugintel.agents import web_recon_agent
from bugintel.agents.web_recon_agent import run_website_recon
from bugintel.core.scope_guard import TargetScope
from bugintel.integrations.web_fetcher import WebFetchResult


def make_scope():
    return TargetScope(
        target_name="demo-lab",
        allowed_domains=["demo.example.com"],
        allowed_schemes=["https"],
        allowed_methods=["GET", "HEAD", "OPTIONS"],
        forbidden_paths=[],
        human_approval_required=True,
    )


def test_run_website_recon_combines_html_and_js_endpoints(monkeypatch):
    scope = make_scope()

    html = """
    <html>
      <head>
        <script src="/static/app.js"></script>
      </head>
      <body>
        <a href="/dashboard">Dashboard</a>
        <script>
          fetch("/api/users/me");
        </script>
      </body>
    </html>
    """

    def fake_fetch_page(scope, url, timeout):
        return WebFetchResult(
            allowed=True,
            reason="Allowed by scope",
            url=url,
            final_url=url,
            status_code=200,
            headers={"content-type": "text/html"},
            text=html,
            error=None,
        )

    def fake_collect_js_sources(scope, page_url, html, timeout):
        return JSCollectionResult(
            page_url=page_url,
            script_count=1,
            sources=[
                JSSourceResult(
                    url="https://demo.example.com/static/app.js",
                    allowed=True,
                    status_code=200,
                    reason="Allowed by scope",
                    endpoints=[
                        "/api/projects/123",
                        "/api/admin/settings",
                    ],
                    error=None,
                )
            ],
        )

    monkeypatch.setattr(web_recon_agent, "fetch_web_page", fake_fetch_page)
    monkeypatch.setattr(web_recon_agent, "collect_js_sources", fake_collect_js_sources)

    result = run_website_recon(
        scope=scope,
        page_url="https://demo.example.com/",
    )

    assert result.allowed is True
    assert result.successful is True
    assert result.html_recon is not None
    assert result.js_recon is not None

    assert "/api/users/me" in result.endpoints
    assert "/api/projects/123" in result.endpoints
    assert "/api/admin/settings" in result.endpoints

    assert result.orchestration_plan is not None
    assert len(result.orchestration_plan.assignments) >= 6


def test_run_website_recon_returns_early_when_blocked(monkeypatch):
    scope = make_scope()

    def fake_fetch_page(scope, url, timeout):
        return WebFetchResult(
            allowed=False,
            reason="Domain not in scope: evil.example.net",
            url=url,
            final_url=None,
            status_code=None,
            headers={},
            text="",
            error=None,
        )

    monkeypatch.setattr(web_recon_agent, "fetch_web_page", fake_fetch_page)

    result = run_website_recon(
        scope=scope,
        page_url="https://evil.example.net/",
    )

    assert result.allowed is False
    assert result.html_recon is None
    assert result.js_recon is None
    assert result.orchestration_plan is None
    assert result.endpoints == []


def test_run_website_recon_returns_early_on_fetch_error(monkeypatch):
    scope = make_scope()

    def fake_fetch_page(scope, url, timeout):
        return WebFetchResult(
            allowed=True,
            reason="Allowed by scope",
            url=url,
            final_url=None,
            status_code=None,
            headers={},
            text="",
            error="connection failed",
        )

    monkeypatch.setattr(web_recon_agent, "fetch_web_page", fake_fetch_page)

    result = run_website_recon(
        scope=scope,
        page_url="https://demo.example.com/",
    )

    assert result.allowed is True
    assert result.successful is False
    assert result.html_recon is None
    assert result.js_recon is None
    assert result.orchestration_plan is None
