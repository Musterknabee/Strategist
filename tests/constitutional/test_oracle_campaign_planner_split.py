from pathlib import Path


def test_oracle_campaign_planner_imports_bounded_rendering_and_io() -> None:
    planner = Path("strategy_validator/validator/oracle_campaign_planner.py").read_text(encoding="utf-8")
    assert "from strategy_validator.validator.oracle_campaign_planner_rendering import (" not in planner
    assert "from strategy_validator.validator.oracle_campaign_planner_rendering import render_oracle_strategic_campaign_markdown" in planner
    assert "from strategy_validator.validator.oracle_campaign_planner_io import load_strategic_campaign_report" in planner
    assert "def render_oracle_strategic_campaign_markdown(" not in planner
    assert "def load_strategic_campaign_report(" not in planner


def test_oracle_campaign_planner_bounded_modules_own_moved_definitions() -> None:
    rendering = Path("strategy_validator/validator/oracle_campaign_planner_rendering.py").read_text(encoding="utf-8")
    io_text = Path("strategy_validator/validator/oracle_campaign_planner_io.py").read_text(encoding="utf-8")
    assert "def render_oracle_strategic_campaign_markdown(" in rendering
    assert "def load_strategic_campaign_report(" in io_text
