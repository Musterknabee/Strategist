from __future__ import annotations

from pathlib import Path


def test_architecture_health_reports_application_public_surface_budget() -> None:
    source = Path("scripts/architecture_health_report.py").read_text(encoding="utf-8")
    assert "application_public_surface_budget" in source
    assert "strategy_validator/application/_exports.py" in source
    assert "export_budget" in source
