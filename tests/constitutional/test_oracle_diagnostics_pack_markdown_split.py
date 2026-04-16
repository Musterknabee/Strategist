from pathlib import Path


def test_oracle_diagnostics_imports_pack_markdown_from_dedicated_module() -> None:
    source = Path('strategy_validator/validator/oracle_diagnostics.py').read_text(encoding='utf-8')
    assert 'from strategy_validator.validator.oracle_diagnostics_pack_rendering import (' in source
    assert 'render_oracle_incident_pack_markdown' in source
    assert 'render_oracle_status_pack_markdown' in source


def test_dedicated_pack_markdown_module_owns_renderers() -> None:
    source = Path('strategy_validator/validator/oracle_diagnostics_pack_rendering.py').read_text(encoding='utf-8')
    assert 'def render_oracle_incident_pack_markdown(' in source
    assert 'def render_oracle_status_pack_markdown(' in source
