from __future__ import annotations

from strategy_validator.api.routes.ui_routes_detail_runtime import get_research_os_release_readiness_latest


def test_release_readiness_route_empty_degrades() -> None:
    payload = get_research_os_release_readiness_latest()
    assert payload["schema_version"] == "ui_research_os_release_readiness/v1"
    assert payload["read_plane_only"] is True
    assert payload["no_live_trading"] is True
