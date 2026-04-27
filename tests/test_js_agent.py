from bugintel.agents import js_agent
from bugintel.agents.js_agent import collect_js_sources
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


def test_collect_js_sources_fetches_scripts_and_mines_endpoints(monkeypatch):
    scope = make_scope()

    html = """
    <html>
      <head>
        <script src="/static/app.js"></script>
      </head>
    </html>
    """

    def fake_fetch(scope, url, timeout):
        assert url == "https://demo.example.com/static/app.js"
        return WebFetchResult(
            allowed=True,
            reason="Allowed by scope",
            url=url,
            final_url=url,
            status_code=200,
            headers={"content-type": "application/javascript"},
            text='fetch("/api/users/me"); fetch("/api/projects/123");',
            error=None,
        )

    monkeypatch.setattr(js_agent, "fetch_web_page", fake_fetch)

    result = collect_js_sources(
        scope=scope,
        page_url="https://demo.example.com/",
        html=html,
    )

    assert result.script_count == 1
    assert len(result.sources) == 1
    assert result.sources[0].allowed is True
    assert "/api/users/me" in result.all_endpoints
    assert "/api/projects/123" in result.all_endpoints


def test_collect_js_sources_records_blocked_script(monkeypatch):
    scope = make_scope()

    html = """
    <html>
      <head>
        <script src="https://evil.example.net/app.js"></script>
      </head>
    </html>
    """

    def fake_fetch(scope, url, timeout):
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

    monkeypatch.setattr(js_agent, "fetch_web_page", fake_fetch)

    result = collect_js_sources(
        scope=scope,
        page_url="https://demo.example.com/",
        html=html,
    )

    assert result.script_count == 1
    assert result.sources[0].allowed is False
    assert "Domain not in scope" in result.sources[0].reason


def test_collect_js_sources_empty_page():
    scope = make_scope()

    result = collect_js_sources(
        scope=scope,
        page_url="https://demo.example.com/",
        html="<html></html>",
    )

    assert result.script_count == 0
    assert result.sources == []
    assert result.all_endpoints == []
