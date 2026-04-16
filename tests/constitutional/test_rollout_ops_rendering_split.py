from pathlib import Path


def test_rollout_ops_imports_renderers_from_bounded_module() -> None:
    source = Path('strategy_validator/validator/rollout_ops.py').read_text(encoding='utf-8')
    assert 'from strategy_validator.validator.rollout_ops_rendering import (' in source
    assert 'render_governed_exception_markdown' in source
    assert 'render_final_release_signoff_markdown' in source
    assert 'render_decision_reconciliation_markdown' in source


def test_rollout_ops_no_longer_defines_renderers_inline() -> None:
    source = Path('strategy_validator/validator/rollout_ops.py').read_text(encoding='utf-8')
    assert 'def render_governed_exception_markdown(' not in source
    assert 'def render_final_release_signoff_markdown(' not in source
    assert 'def render_decision_reconciliation_markdown(' not in source


def test_rollout_ops_rendering_module_owns_moved_renderers() -> None:
    source = Path('strategy_validator/validator/rollout_ops_rendering.py').read_text(encoding='utf-8')
    assert 'def render_governed_exception_markdown(' in source
    assert 'def render_final_release_signoff_markdown(' in source
    assert 'def render_decision_reconciliation_markdown(' in source
