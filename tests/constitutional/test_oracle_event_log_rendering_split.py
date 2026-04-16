from __future__ import annotations

from pathlib import Path


def test_oracle_event_log_rendering_split() -> None:
    source = Path("strategy_validator/validator/oracle_event_log.py").read_text(encoding="utf-8")
    rendering = Path("strategy_validator/validator/oracle_event_log_rendering.py").read_text(encoding="utf-8")

    assert "from strategy_validator.validator.oracle_event_log_rendering import (" in source
    assert "render_oracle_rolling_review_markdown" in source
    assert "render_oracle_derived_view_markdown" in source
    assert "render_oracle_event_checkpoint_markdown" in source

    assert "def render_oracle_rolling_review_markdown(" not in source
    assert "def render_oracle_derived_view_markdown(" not in source
    assert "def render_oracle_event_checkpoint_markdown(" not in source

    assert "def render_oracle_rolling_review_markdown(" in rendering
    assert "def render_oracle_derived_view_markdown(" in rendering
    assert "def render_oracle_event_checkpoint_markdown(" in rendering
