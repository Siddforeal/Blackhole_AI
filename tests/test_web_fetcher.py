import httpx

from bugintel.core.scope_guard import TargetScope
from bugintel.integrations.web_fetcher import fetch_web_page


def make_scope():
    return TargetScope(
        target_name="demo-lab",
        allowed_domains=["demo.example.com", "127.0.0.1", "localhost"],
        allowed_schemes=["https", "http"],
        allowed_methods=["GET", "HEAD", "OPTIONS"],
        forbidden_paths=["/logout", "/delete*"],
        human_approval_required=True,
    )


def test_fetch_web_page_blocks_out_of_scope():
    scope = make_scope()

    result = fetch_web_page(scope, "https://evil.example.net")

    assert result.allowed is False
    assert "Domain not in scope" in result.reason
    assert result.text == ""


def test_fetch_web_page_uses_httpx_for_allowed_url(monkeypatch):
    scope = make_scope()

    class FakeResponse:
        url = "https://demo.example.com/"
        status_code = 200
        headers = {"content-type": "text/html"}
        text = "<html><body>hello</body></html>"

    def fake_get(url, headers, follow_redirects, timeout):
        assert url == "https://demo.example.com/"
        assert follow_redirects is True
        assert timeout == 15
        assert "User-Agent" in headers
        return FakeResponse()

    monkeypatch.setattr(httpx, "get", fake_get)

    result = fetch_web_page(scope, "https://demo.example.com/")

    assert result.allowed is True
    assert result.status_code == 200
    assert result.headers["content-type"] == "text/html"
    assert "hello" in result.text


def test_fetch_web_page_handles_http_error(monkeypatch):
    scope = make_scope()

    def fake_get(url, headers, follow_redirects, timeout):
        raise httpx.ConnectError("connection failed")

    monkeypatch.setattr(httpx, "get", fake_get)

    result = fetch_web_page(scope, "https://demo.example.com/")

    assert result.allowed is True
    assert result.status_code is None
    assert result.text == ""
    assert "connection failed" in result.error
