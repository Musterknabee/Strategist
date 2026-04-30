from pathlib import Path


def test_ui_workboard_intelligence_item_facade_is_thin_reexport_surface() -> None:
    text = Path("strategy_validator/application/ui_workboard_intelligence_items.py").read_text(encoding="utf-8")
    assert "ui_workboard_intelligence_foundations" in text
    assert "ui_workboard_intelligence_policy" in text
    assert "def _build_policy_recommendation(" not in text
    assert "def _linked_pack_for_entry(" not in text


def test_ui_workboard_intelligence_runtime_imports_canonical_modules() -> None:
    intelligence_text = Path("strategy_validator/application/ui_workboard_intelligence.py").read_text(encoding="utf-8")
    assert "strategy_validator.application.ui_workboard_intelligence_foundations" in intelligence_text
    assert "strategy_validator.application.ui_workboard_intelligence_policy" in intelligence_text
    assert "strategy_validator.application.ui_workboard_intelligence_items" not in intelligence_text
