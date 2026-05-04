from __future__ import annotations

from strategy_validator.application.ui_views import build_ui_workboard_payload


def test_ui_workboard_payload_uses_projection_read_model_surface(tmp_path) -> None:
    payload = build_ui_workboard_payload(search_root=tmp_path)
    assert payload['pack_workbench']['read_model_surface'] == 'application.ui_projection_surfaces'
    assert payload['pack_workbench']['source_projection_family'] == 'operator_pack_projection'


def test_ui_workboard_payload_defaults_search_root_from_artifact_env(monkeypatch, tmp_path) -> None:
    """Regression: GET /ui/workboard omits search_root; API uses STRATEGY_VALIDATOR_ARTIFACT_ROOT."""
    artifact = tmp_path / 'artifacts'
    artifact.mkdir()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('STRATEGY_VALIDATOR_ARTIFACT_ROOT', str(artifact))
    payload = build_ui_workboard_payload(board_label='operator', search_root=None)
    assert payload['schema_version'] == 'ui_workboard_dashboard/v1'
    assert payload['pack_workbench']['read_model_surface'] == 'application.ui_projection_surfaces'
    assert payload['pack_workbench']['source_projection_family'] == 'operator_pack_projection'
