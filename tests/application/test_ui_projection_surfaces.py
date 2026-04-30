from __future__ import annotations

from strategy_validator.application.ui_views import build_ui_workboard_payload


def test_ui_workboard_payload_uses_projection_read_model_surface(tmp_path) -> None:
    payload = build_ui_workboard_payload(search_root=tmp_path)
    assert payload['pack_workbench']['read_model_surface'] == 'application.ui_projection_surfaces'
    assert payload['pack_workbench']['source_projection_family'] == 'operator_pack_projection'
