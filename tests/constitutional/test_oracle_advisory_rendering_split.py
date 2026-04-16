from pathlib import Path


def test_oracle_advisory_imports_renderer_from_dedicated_module() -> None:
    advisory = Path("strategy_validator/validator/oracle_advisory.py").read_text(encoding="utf-8")
    assert "from strategy_validator.validator.oracle_advisory_rendering import render_oracle_morning_attestation_markdown" in advisory
    assert "def render_oracle_morning_attestation_markdown(" not in advisory


def test_oracle_advisory_rendering_module_owns_renderer() -> None:
    rendering = Path("strategy_validator/validator/oracle_advisory_rendering.py").read_text(encoding="utf-8")
    assert "def render_oracle_morning_attestation_markdown(" in rendering
