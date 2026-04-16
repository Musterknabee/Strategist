from pathlib import Path


def test_oracle_briefing_uses_bounded_io_module() -> None:
    briefing = Path("strategy_validator/validator/oracle_briefing.py").read_text(encoding="utf-8")
    io_module = Path("strategy_validator/validator/oracle_briefing_io.py").read_text(encoding="utf-8")

    assert "from strategy_validator.validator.oracle_briefing_io import (" in briefing
    assert "emit_oracle_briefing_pack_projection_registry" in briefing
    assert "_briefing_pack_projection_inputs" in briefing
    assert "def emit_oracle_briefing_pack_projection_registry(" in io_module
    assert "def _briefing_pack_projection_inputs(" in io_module
    assert "def _load_strategic_briefing(" in io_module
    assert "def _load_scenario_lab(" in io_module

    assert "def emit_oracle_briefing_pack_projection_registry(" not in briefing
    assert "def _briefing_pack_projection_inputs(" not in briefing
    assert "def _load_strategic_briefing(" not in briefing
    assert "def _load_scenario_lab(" not in briefing
