from bugintel.agents.recon_agent import analyze_html


def test_analyze_html_extracts_links_scripts_forms_and_endpoints():
    html = """
    <html>
      <head>
        <script src="/static/app.js"></script>
      </head>
      <body>
        <a href="/dashboard">Dashboard</a>
        <a href="https://demo.example.com/settings">Settings</a>

        <form method="post" action="/api/login">
          <input name="email">
          <input name="password" type="password">
        </form>

        <script>
          fetch("/api/users/me");
          fetch("/api/projects/123");
        </script>
      </body>
    </html>
    """

    result = analyze_html("https://demo.example.com", html)

    assert "https://demo.example.com/dashboard" in result.links
    assert "https://demo.example.com/settings" in result.links
    assert "https://demo.example.com/static/app.js" in result.scripts

    assert len(result.forms) == 1
    assert result.forms[0].method == "POST"
    assert result.forms[0].action == "https://demo.example.com/api/login"
    assert "email" in result.forms[0].inputs
    assert "password" in result.forms[0].inputs

    assert "/api/users/me" in result.endpoints
    assert "/api/projects/123" in result.endpoints


def test_analyze_empty_html_returns_empty_lists():
    result = analyze_html("https://demo.example.com", "")

    assert result.links == []
    assert result.scripts == []
    assert result.forms == []
    assert result.endpoints == []
