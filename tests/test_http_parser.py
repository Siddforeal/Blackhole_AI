from bugintel.analyzers.http_parser import parse_http_response


def test_parse_http_1_response():
    raw = """HTTP/1.0 200 OK
Server: BaseHTTP/0.6 Python/3.13.12
content-type: application/json
content-length: 85

{"id":1,"email":"demo@example.com"}
"""

    parsed = parse_http_response(raw)

    assert parsed.status_code == 200
    assert parsed.headers["content-type"] == "application/json"
    assert parsed.body == '{"id":1,"email":"demo@example.com"}'


def test_parse_http_2_response():
    raw = """HTTP/2 403
content-type: application/json

{"error":"Forbidden"}
"""

    parsed = parse_http_response(raw)

    assert parsed.status_code == 403
    assert parsed.headers["content-type"] == "application/json"
    assert parsed.body == '{"error":"Forbidden"}'


def test_parse_raw_body_without_http_headers():
    raw = '{"ok":true}'

    parsed = parse_http_response(raw)

    assert parsed.status_code is None
    assert parsed.headers == {}
    assert parsed.body == '{"ok":true}'
