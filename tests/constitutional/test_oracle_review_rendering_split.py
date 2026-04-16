from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ENGINE_PATH = REPO_ROOT / 'strategy_validator' / 'validator' / 'oracle_review_engine.py'
RENDERING_PATH = REPO_ROOT / 'strategy_validator' / 'validator' / 'oracle_review_rendering.py'


def test_oracle_review_engine_imports_renderers_from_dedicated_module() -> None:
    source = ENGINE_PATH.read_text(encoding='utf-8')
    assert 'from strategy_validator.validator.oracle_review_rendering import (' in source
    for name in [
        'render_oracle_state_transition_markdown',
        'render_oracle_memory_review_markdown',
        'render_oracle_memory_lane_summary_markdown',
        'render_oracle_weekly_digest_markdown',
    ]:
        assert name in source


def test_oracle_review_rendering_module_owns_render_functions() -> None:
    source = RENDERING_PATH.read_text(encoding='utf-8')
    for name in [
        'render_oracle_state_transition_markdown',
        'render_oracle_memory_review_markdown',
        'render_oracle_memory_lane_summary_markdown',
        'render_oracle_weekly_digest_markdown',
    ]:
        assert f'def {name}(' in source
