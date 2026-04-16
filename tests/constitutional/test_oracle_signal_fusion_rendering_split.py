from pathlib import Path


def test_oracle_signal_fusion_imports_renderer_from_dedicated_module() -> None:
    source = Path('strategy_validator/validator/oracle_signal_fusion.py').read_text(encoding='utf-8')
    assert 'from strategy_validator.validator.oracle_signal_fusion_rendering import (' in source
    assert 'def render_oracle_strategic_fusion_markdown(' not in source


def test_oracle_signal_fusion_rendering_module_owns_renderer() -> None:
    source = Path('strategy_validator/validator/oracle_signal_fusion_rendering.py').read_text(encoding='utf-8')
    assert 'def render_oracle_strategic_fusion_markdown(' in source
