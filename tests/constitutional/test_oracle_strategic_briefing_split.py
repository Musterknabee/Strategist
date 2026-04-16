from pathlib import Path


def test_oracle_strategic_briefing_uses_bounded_rendering_and_io_modules() -> None:
    briefing = Path("strategy_validator/validator/oracle_strategic_briefing.py").read_text(encoding="utf-8")
    rendering = Path("strategy_validator/validator/oracle_strategic_briefing_rendering.py").read_text(encoding="utf-8")
    io_module = Path("strategy_validator/validator/oracle_strategic_briefing_io.py").read_text(encoding="utf-8")

    assert "from strategy_validator.validator.oracle_strategic_briefing_rendering import render_oracle_strategic_briefing_markdown" in briefing
    assert "from strategy_validator.validator.oracle_strategic_briefing_io import load_fusion_report, load_strategic_briefing_report" in briefing

    assert "def render_oracle_strategic_briefing_markdown(" in rendering
    assert "def load_fusion_report(" in io_module
    assert "def load_strategic_briefing_report(" in io_module

    assert "def render_oracle_strategic_briefing_markdown(" not in briefing
    assert "def load_fusion_report(" not in briefing
    assert "def load_strategic_briefing_report(" not in briefing
