from pathlib import Path


def test_oracle_diagnostics_imports_pack_line_helpers_from_bounded_module() -> None:
    source = Path('strategy_validator/validator/oracle_diagnostics.py').read_text(encoding='utf-8')
    assert 'from strategy_validator.validator.oracle_diagnostics_pack_lines import (' in source
    assert 'def _operator_pack_dashboard_lines(' not in source
    assert 'def _operator_pack_terminal_record_lines(' not in source
    assert 'def _closure_section(' not in source


def test_oracle_diagnostics_pack_lines_module_owns_moved_definitions() -> None:
    source = Path('strategy_validator/validator/oracle_diagnostics_pack_lines.py').read_text(encoding='utf-8')
    assert 'def _operator_pack_dashboard_lines(' in source
    assert 'def _operator_pack_terminal_record_lines(' in source
    assert 'def _closure_section(' in source


def test_pack_rendering_prefers_bounded_pack_lines_module() -> None:
    source = Path('strategy_validator/validator/oracle_diagnostics_pack_rendering.py').read_text(encoding='utf-8')
    assert 'from strategy_validator.validator import oracle_diagnostics_pack_lines as _lines' in source
    assert 'from strategy_validator.validator import oracle_diagnostics as _engine' not in source
