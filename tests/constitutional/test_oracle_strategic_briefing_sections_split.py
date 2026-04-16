from pathlib import Path


def test_oracle_strategic_briefing_uses_bounded_sections_module() -> None:
    briefing = Path("strategy_validator/validator/oracle_strategic_briefing.py").read_text(encoding="utf-8")
    sections = Path("strategy_validator/validator/oracle_strategic_briefing_sections.py").read_text(encoding="utf-8")

    assert "from strategy_validator.validator.oracle_strategic_briefing_sections import build_oracle_strategic_briefing" in briefing
    assert "def build_oracle_strategic_briefing(" in sections
    assert "def build_oracle_strategic_briefing(" not in briefing
