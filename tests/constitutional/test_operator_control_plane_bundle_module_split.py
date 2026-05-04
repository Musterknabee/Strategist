from pathlib import Path


def test_operator_control_plane_bundle_delegates_to_bounded_helper_modules() -> None:
    source = Path("strategy_validator/control_plane/operator_control_plane_bundle.py").read_text(encoding="utf-8")
    assert "operator_control_plane_bundle_sections" in source
    assert "operator_control_plane_bundle_rendering" in source
    assert "materialize_operator_control_plane_bundle_sections" in source
    assert "render_operator_control_plane_bundle_markdown_lines" in source


def test_operator_control_plane_bundle_delegates_output_persistence_to_helper_module() -> None:
    source = Path("strategy_validator/control_plane/operator_control_plane_bundle.py").read_text(encoding="utf-8")
    assert "operator_control_plane_bundle_output" in source
    assert "persist_operator_control_plane_bundle" in source
