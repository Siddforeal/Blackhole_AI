from bugintel.analyzers.response_diff import compare_responses, summarize_response


def test_summarize_json_response_extracts_keys_and_keywords():
    summary = summarize_response(
        200,
        {"content-type": "application/json"},
        '{"user":{"email":"sidd@example.com","role":"admin"},"account_id":123}',
    )

    assert summary.status_code == 200
    assert summary.is_json is True
    assert "user.email" in summary.json_keys
    assert "user.role" in summary.json_keys
    assert "email" in summary.interesting_keywords
    assert "role" in summary.interesting_keywords
    assert len(summary.body_sha256) == 64


def test_compare_successful_similar_json_is_interesting():
    baseline = summarize_response(
        200,
        {"content-type": "application/json"},
        '{"id":1,"email":"a@example.com","role":"user"}',
    )

    candidate = summarize_response(
        200,
        {"content-type": "application/json"},
        '{"id":2,"email":"b@example.com","role":"admin"}',
    )

    comparison = compare_responses(baseline, candidate)

    assert comparison.same_status is True
    assert comparison.json_key_overlap >= 0.6
    assert "similar_successful_json_structure" in comparison.signals
    assert comparison.verdict.startswith("interesting")


def test_compare_blocked_candidate_is_expected():
    baseline = summarize_response(
        200,
        {"content-type": "application/json"},
        '{"id":1,"email":"a@example.com"}',
    )

    candidate = summarize_response(
        403,
        {"content-type": "application/json"},
        '{"error":"Forbidden"}',
    )

    comparison = compare_responses(baseline, candidate)

    assert "candidate_blocked_or_not_found" in comparison.signals
    assert comparison.verdict == "expected: candidate appears blocked"


def test_compare_404_candidate_is_likely_safe():
    baseline = summarize_response(
        200,
        {"content-type": "application/json"},
        '{"id":1,"email":"a@example.com"}',
    )

    candidate = summarize_response(
        404,
        {"content-type": "application/json"},
        '{"error":"Not found"}',
    )

    comparison = compare_responses(baseline, candidate)

    assert comparison.verdict == "likely safe/blocked: candidate returned not found"
