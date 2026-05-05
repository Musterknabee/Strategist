"""Runtime UI payload exposes read-plane mutation safety posture (no secrets)."""

from strategy_validator.application.ui_detail_views import build_ui_runtime_status_payload


def test_ui_runtime_payload_includes_mutation_safety_shape() -> None:
    payload = build_ui_runtime_status_payload(role="operator")
    assert "mutation_safety" in payload
    ms = payload["mutation_safety"]
    assert isinstance(ms, dict)
    for key in ("runtime_mode", "authorization_mode", "token_configured", "mutation_routes_safe", "detail_code"):
        assert key in ms
