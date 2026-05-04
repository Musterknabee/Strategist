from strategy_validator.api.routes.ui_routes_detail_runtime import get_research_os_handoff_latest


def test_ui_research_os_handoff_route_empty_degrades() -> None:
    payload = get_research_os_handoff_latest()
    assert payload["schema_version"] == "ui_research_os_handoff/v1"
    assert payload["read_plane_only"] is True
    assert payload["no_live_trading"] is True
