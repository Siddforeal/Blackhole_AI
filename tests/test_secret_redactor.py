from bugintel.analyzers.secret_redactor import redact_dict, redact_text


def test_redacts_email():
    text = "Reporter email is sidd@example.com"
    assert "<email>" in redact_text(text)
    assert "sidd@example.com" not in redact_text(text)


def test_redacts_bearer_token():
    text = "Authorization: Bearer abc.def.ghi"
    clean = redact_text(text)
    assert "Authorization: Bearer <redacted>" in clean
    assert "abc.def.ghi" not in clean


def test_redacts_cookie():
    text = "Cookie: sessionid=abc123; csrftoken=xyz"
    clean = redact_text(text)
    assert clean == "Cookie: <redacted>"


def test_redacts_api_key():
    text = "x-api-key: ABCDEFGH123456789"
    clean = redact_text(text)
    assert "<redacted>" in clean
    assert "ABCDEFGH123456789" not in clean


def test_redacts_nested_dict():
    data = {
        "url": "https://demo.example.com/api",
        "headers": {
            "Authorization": "Bearer abc.def.ghi",
            "Cookie": "sessionid=abc123",
        },
        "notes": ["contact sidd@example.com"],
    }

    clean = redact_dict(data)

    assert clean["headers"]["Authorization"] == "Bearer <redacted>"
    assert clean["headers"]["Cookie"] == "sessionid=abc123"
    assert clean["notes"][0] == "contact <email>"
