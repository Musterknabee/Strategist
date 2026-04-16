from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ENGINE_PATH = REPO_ROOT / "strategy_validator" / "validator" / "oracle_doctrine_engine.py"
RENDERING_PATH = REPO_ROOT / "strategy_validator" / "validator" / "oracle_doctrine_rendering.py"


def test_oracle_doctrine_engine_imports_renderers_from_dedicated_module() -> None:
    source = ENGINE_PATH.read_text(encoding="utf-8")
    assert "from strategy_validator.validator.oracle_doctrine_rendering import (" in source
    assert "render_oracle_monthly_digest_markdown" in source
    assert "render_oracle_constitutional_digest_markdown" in source


def test_oracle_doctrine_rendering_module_owns_render_functions() -> None:
    source = RENDERING_PATH.read_text(encoding="utf-8")
    for name in [
        "render_oracle_doctrine_drift_markdown",
        "render_oracle_monthly_digest_markdown",
        "render_oracle_quarterly_review_markdown",
        "render_oracle_semiannual_audit_markdown",
        "render_oracle_annual_review_markdown",
        "render_oracle_constitutional_digest_markdown",
    ]:
        assert f"def {name}(" in source
