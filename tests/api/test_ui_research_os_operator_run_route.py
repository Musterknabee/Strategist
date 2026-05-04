from strategy_validator.api.routes.ui_routes_detail_runtime import get_research_os_operator_run_latest


def test_research_os_operator_run_route_returns_payload() -> None:
    payload = get_research_os_operator_run_latest()
    assert payload["schema_version"] == "ui_research_os_operator_run/v1"
    assert payload["read_plane_only"] is True
    assert payload["no_live_trading"] is True
    assert payload["no_broker_orders"] is True
