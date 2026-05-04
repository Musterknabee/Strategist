from __future__ import annotations


def test_ui_provider_setup_route_function_returns_secret_safe_console() -> None:
    from strategy_validator.api.routes.ui_routes_detail_runtime import get_provider_setup

    payload = get_provider_setup()
    assert payload["schema_version"] == "ui_provider_setup_console/v1"
    assert payload["read_plane_only"] is True
    assert payload["mutation_authority"] == "NONE"
    assert payload["execution_authority"] == "NONE"
    assert payload["no_secret_values"] is True
    assert "entries" in payload
