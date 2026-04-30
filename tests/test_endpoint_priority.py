from bugintel.core.endpoint_priority import prioritize_endpoints, score_endpoint


def test_score_sensitive_account_endpoint_is_high_priority():
    result = score_endpoint("/api/accounts/123/users/{id}/permissions")

    signal_names = {signal.name for signal in result.signals}

    assert result.score >= 75
    assert result.band == "critical"
    assert "authorization-sensitive" in result.categories
    assert "object-reference" in result.categories
    assert "category:authorization-sensitive" in signal_names
    assert "category:object-reference" in signal_names
    assert any("authorization boundary" in step for step in result.recommended_next_steps)


def test_score_file_download_endpoint_gets_file_surface_signal():
    result = score_endpoint("/api/files/{id}/download")

    signal_names = {signal.name for signal in result.signals}

    assert result.score >= 50
    assert result.band in {"high", "critical"}
    assert "file-surface" in result.categories
    assert "category:file-surface" in signal_names
    assert any("file access" in step for step in result.recommended_next_steps)


def test_low_signal_status_endpoint_is_deprioritized():
    result = score_endpoint("/api/status")

    signal_names = {signal.name for signal in result.signals}

    assert result.score < 25
    assert result.band in {"info", "low"}
    assert "deprioritize:low-signal-route" in signal_names


def test_prioritize_endpoints_sorts_highest_score_first():
    results = prioritize_endpoints(
        [
            "/api/status",
            "/api/accounts/123/users/{id}/permissions",
            "/api/files/{id}/download",
        ]
    )

    assert results[0].endpoint == "/api/accounts/123/users/{id}/permissions"
    assert results[0].score >= results[1].score >= results[2].score
    assert results[-1].endpoint == "/api/status"


def test_priority_result_to_dict_is_planning_only():
    data = score_endpoint("/api/projects/{projectId}/exports").to_dict()

    assert data["planning_only"] is True
    assert data["execution_state"] == "not_executed"
    assert data["score"] > 0
    assert data["signals"]
    assert data["recommended_next_steps"]
