from bugintel.core.attack_surface import (
    build_attack_surface_map,
    classify_attack_surface_groups,
    default_attack_surface_group_specs,
)


def test_classify_attack_surface_groups_identity_and_object_reference():
    groups = classify_attack_surface_groups("/api/accounts/123/users/{id}/permissions")

    assert "identity-access" in groups
    assert "object-reference" in groups


def test_classify_attack_surface_groups_file_surface():
    groups = classify_attack_surface_groups("/api/files/{id}/download")

    assert "file-surface" in groups
    assert "object-reference" in groups


def test_classify_attack_surface_groups_low_signal():
    groups = classify_attack_surface_groups("/api/status")

    assert groups == ("low-signal",)


def test_classify_attack_surface_groups_general_api_fallback():
    groups = classify_attack_surface_groups("/api/catalog")

    assert groups == ("general-api",)


def test_default_attack_surface_group_specs_contains_expected_groups():
    specs = default_attack_surface_group_specs()

    assert "identity-access" in specs
    assert "tenant-project-boundary" in specs
    assert "file-surface" in specs
    assert "auth-flow" in specs
    assert "billing-money" in specs
    assert "integration-webhook" in specs
    assert "secret-token-key" in specs
    assert "low-signal" in specs


def test_build_attack_surface_map_groups_and_sorts_by_priority():
    surface = build_attack_surface_map(
        [
            "/api/status",
            "/api/accounts/123/users/{id}/permissions",
            "/api/files/{id}/download",
            "/api/integrations/webhooks",
        ]
    )

    data = surface.to_dict()
    group_names = [group["name"] for group in data["groups"]]

    assert data["endpoint_count"] == 4
    assert data["planning_only"] is True
    assert data["execution_state"] == "not_executed"
    assert "identity-access" in group_names
    assert "file-surface" in group_names
    assert "integration-webhook" in group_names
    assert "low-signal" in group_names

    identity = next(group for group in data["groups"] if group["name"] == "identity-access")
    assert identity["max_score"] >= 75
    assert identity["endpoints"][0]["endpoint"] == "/api/accounts/123/users/{id}/permissions"


def test_attack_surface_map_to_dict_contains_endpoint_priority_results():
    surface = build_attack_surface_map(["/api/projects/{projectId}/exports"])
    data = surface.to_dict()

    assert data["groups"]
    assert data["groups"][0]["endpoints"][0]["planning_only"] is True
    assert data["groups"][0]["endpoints"][0]["signals"]
