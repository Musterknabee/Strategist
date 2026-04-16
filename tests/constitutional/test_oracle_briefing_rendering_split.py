from pathlib import Path


def test_oracle_briefing_uses_rendering_shim() -> None:
    source = Path('strategy_validator/validator/oracle_briefing.py').read_text(encoding='utf-8')
    assert 'from strategy_validator.validator.oracle_briefing_rendering import (' in source
    assert 'def render_oracle_briefing_pack_markdown(' not in source
    assert 'def render_oracle_briefing_pack_html(' not in source


def test_oracle_briefing_rendering_module_owns_renderers() -> None:
    source = Path('strategy_validator/validator/oracle_briefing_rendering.py').read_text(encoding='utf-8')
    assert 'def render_oracle_briefing_pack_markdown(' in source
    assert 'def render_oracle_briefing_pack_html(' in source
