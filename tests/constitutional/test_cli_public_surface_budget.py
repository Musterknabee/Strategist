from __future__ import annotations

from pathlib import Path

from strategy_validator.cli.public_surface import check_cli_public_surface_budgets


def test_cli_public_surface_budget_freezes_sprawl() -> None:
    report = check_cli_public_surface_budgets(Path(__file__).resolve().parents[2])

    assert report["schema_version"] == "cli_public_surface_budget/v1"
    assert report["ok"] is True
    assert report["violations"] == []
    assert report["inventory"]["compatibility_file_count"] <= report["budgets"]["compatibility_file_count"]
    assert report["inventory"]["runtime_command_file_count"] <= report["budgets"]["runtime_command_file_count"]
