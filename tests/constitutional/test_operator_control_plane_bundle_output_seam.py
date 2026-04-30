from pathlib import Path


def test_operator_control_plane_bundle_persists_outputs_outside_section_materialization() -> None:
    sections_source = Path("strategy_validator/control_plane/operator_control_plane_bundle_sections.py").read_text(encoding="utf-8")
    root_source = Path("strategy_validator/control_plane/operator_control_plane_bundle.py").read_text(encoding="utf-8")
    output_source = Path("strategy_validator/control_plane/operator_control_plane_bundle_output.py").read_text(encoding="utf-8")

    assert "write_text(" not in sections_source
    assert "persist_operator_control_plane_bundle" in root_source
    assert "write_text(" in output_source
    assert "render_operator_control_plane_bundle_markdown_document" in output_source
