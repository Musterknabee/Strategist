from pathlib import Path


def test_operator_control_plane_bundle_sections_delegate_to_stage_builders() -> None:
    source = Path('strategy_validator/control_plane/operator_control_plane_bundle_sections.py').read_text(encoding='utf-8')
    assert 'operator_control_plane_bundle_stage_core' in source
    assert 'operator_control_plane_bundle_stage_reentry' in source
    assert 'operator_control_plane_bundle_stage_recurrence' in source
    assert 'materialize_operator_control_plane_bundle_core_stage' in source
    assert 'materialize_operator_control_plane_bundle_reentry_stage' in source
    assert 'materialize_operator_control_plane_bundle_recurrence_stage' in source
