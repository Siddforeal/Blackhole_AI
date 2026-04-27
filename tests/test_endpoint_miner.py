from bugintel.analyzers.endpoint_miner import categorize_endpoint, mine_endpoints


def test_mines_quoted_api_paths():
    text = """
    fetch("/api/users/me")
    axios.get('/v1/projects/123')
    const uploadUrl = `/api/files/upload`;
    """

    endpoints = mine_endpoints(text)
    values = [e.value for e in endpoints]

    assert "/api/users/me" in values
    assert "/v1/projects/123" in values
    assert "/api/files/upload" in values


def test_mines_absolute_urls_as_paths():
    text = "Request URL: https://demo.example.com/api/admin/settings?debug=false"
    endpoints = mine_endpoints(text)

    assert endpoints[0].value == "/api/admin/settings?debug=false"
    assert endpoints[0].category == "admin"


def test_mines_method_path_format():
    text = """
    GET /api/accounts/1001/users HTTP/2
    POST /api/export/report HTTP/2
    """

    values = [e.value for e in mine_endpoints(text)]

    assert "/api/accounts/1001/users" in values
    assert "/api/export/report" in values


def test_categorizes_common_endpoint_types():
    assert categorize_endpoint("/graphql") == "graphql"
    assert categorize_endpoint("/api/oauth/token") == "auth"
    assert categorize_endpoint("/api/admin/users") == "admin"
    assert categorize_endpoint("/api/users/me") == "user"
    assert categorize_endpoint("/api/accounts/123") == "account"
    assert categorize_endpoint("/api/projects/123") == "project"
    assert categorize_endpoint("/api/integrations/slack") == "integration"
    assert categorize_endpoint("/api/files/upload") == "file"
    assert categorize_endpoint("/api/billing/invoices") == "billing"
