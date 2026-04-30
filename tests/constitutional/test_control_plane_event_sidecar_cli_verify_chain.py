from __future__ import annotations

from pathlib import Path


def test_control_plane_event_sidecar_cli_exposes_reconcile_chain_verification() -> None:
    source = (Path(__file__).resolve().parents[2] / "strategy_validator/cli/control_plane_event_sidecars.py").read_text(
        encoding="utf-8"
    )
    pyproject = (Path(__file__).resolve().parents[2] / "pyproject.toml").read_text(encoding="utf-8")

    assert "--verify-operator-chain" in source
    assert "operator_journal_chain_verified" in source
    assert "strategy-validator-control-plane-event-sidecars" in pyproject


def test_control_plane_event_sidecar_reconciliation_projection_reports_chain_status() -> None:
    source = (Path(__file__).resolve().parents[2] / "strategy_validator/projections/control_plane_event_sidecars.py").read_text(
        encoding="utf-8"
    )

    assert "operator_journal_chain_ok" in source
    assert "operator_journal_chain_issue_count" in source
    assert "verify_operator_action_event_chain" in source
