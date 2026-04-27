import json

from bugintel.integrations.har_importer import endpoint_from_url, import_har_from_dict, load_har


def sample_har():
    return {
        "log": {
            "version": "1.2",
            "entries": [
                {
                    "request": {
                        "method": "GET",
                        "url": "https://demo.example.com/api/users/me",
                    },
                    "response": {
                        "status": 200,
                        "content": {
                            "mimeType": "application/json",
                        },
                    },
                },
                {
                    "request": {
                        "method": "POST",
                        "url": "https://demo.example.com/api/projects/123/export?format=csv",
                    },
                    "response": {
                        "status": 202,
                        "content": {
                            "mimeType": "application/json",
                        },
                    },
                },
                {
                    "request": {
                        "method": "GET",
                        "url": "https://demo.example.com/static/app.js",
                    },
                    "response": {
                        "status": 200,
                        "content": {
                            "mimeType": "application/javascript",
                        },
                    },
                },
            ],
        }
    }


def test_endpoint_from_url_keeps_path_and_query():
    assert endpoint_from_url("https://demo.example.com/api/users/me") == "/api/users/me"
    assert endpoint_from_url("https://demo.example.com/api/export?format=csv") == "/api/export?format=csv"


def test_import_har_from_dict_extracts_entries_and_endpoints():
    result = import_har_from_dict(sample_har())

    assert len(result.entries) == 3
    assert "/api/users/me" in result.endpoints
    assert "/api/projects/123/export?format=csv" in result.endpoints

    first = result.entries[0]
    assert first.method == "GET"
    assert first.status_code == 200
    assert first.category == "user"


def test_import_har_from_dict_filters_api_entries():
    result = import_har_from_dict(sample_har())

    endpoints = [entry.endpoint for entry in result.api_entries]

    assert "/api/users/me" in endpoints
    assert "/api/projects/123/export?format=csv" in endpoints


def test_load_har_from_file(tmp_path):
    har_path = tmp_path / "traffic.har"
    har_path.write_text(json.dumps(sample_har()), encoding="utf-8")

    result = load_har(har_path)

    assert len(result.entries) == 3
    assert result.entries[1].method == "POST"
    assert result.entries[1].status_code == 202
