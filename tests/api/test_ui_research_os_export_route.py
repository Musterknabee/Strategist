from __future__ import annotations

from strategy_validator.api.routes.ui_routes_detail_runtime import get_research_os_export_latest


def test_ui_research_os_export_route_empty_root_degraded() -> None:
    payload = get_research_os_export_latest()
    assert payload["schema_version"] == "ui_research_os_export/v1"
    assert payload["read_plane_only"] is True
    assert payload["no_live_trading"] is True
