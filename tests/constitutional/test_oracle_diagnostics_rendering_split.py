from pathlib import Path


def test_oracle_diagnostics_imports_renderers_from_dedicated_module() -> None:
    source = Path('strategy_validator/validator/oracle_diagnostics.py').read_text(encoding='utf-8')
    assert 'from strategy_validator.validator.oracle_diagnostics_rendering import (' in source
    assert 'def render_oracle_operator_diagnostic_markdown(' not in source
    assert 'def render_oracle_status_pack_html(' not in source
    assert 'def render_oracle_incident_pack_html(' not in source


def test_oracle_diagnostics_rendering_module_owns_renderers() -> None:
    source = Path('strategy_validator/validator/oracle_diagnostics_rendering.py').read_text(encoding='utf-8')
    assert 'def render_oracle_operator_diagnostic_markdown(' in source
    assert 'def render_oracle_status_pack_html(' in source
    assert 'def render_oracle_incident_pack_html(' in source
