from __future__ import annotations

from pathlib import Path


def test_compatibility_deprecation_catalog_exists_and_names_current_sinks() -> None:
    path = Path("docs/architecture/COMPATIBILITY_DEPRECATION_CATALOG.md")
    source = path.read_text(encoding="utf-8")

    assert "strategy_validator.application.__init__" in source
    assert "strategy_validator.cli" in source
    assert "strategy_validator.api.routes.research" in source
    assert "research_handoff.py" in source
    assert "Removal condition" in source
    assert "must not accumulate new behavior" in source
