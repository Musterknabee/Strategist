from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.application.daily_operator_run_projection import build_ui_daily_operator_run_payload
from strategy_validator.application.paper_execution_cockpit import build_ui_paper_execution_cockpit_payload
from strategy_validator.application.paper_execution_intent_selection import write_paper_execution_intent_selection_artifact
from strategy_validator.application.paper_execution_journal import write_paper_order_dry_run_artifact
from strategy_validator.application.paper_execution_reconciliation import write_paper_account_position_snapshot_artifact
from strategy_validator.application.paper_execution_submission_guard import (
    build_paper_submission_guard_snapshot,
    write_paper_order_submission_artifact,
)
from strategy_validator.contracts.paper_broker import (
    PaperBrokerAccountStatus,
    PaperBrokerOrderIntent,
    PaperBrokerOrderResult,
    PaperBrokerPolicyStatus,
    PaperBrokerPositionSnapshot,
)


def _paper_env() -> dict[str, str]:
    return {
        "ALPACA_TRADING_MODE": "paper",
        "ALPACA_BASE_URL": "https://paper-api.alpaca.markets",
        "ALPACA_API_KEY": "paper-key",
        "ALPACA_API_SECRET": "paper-secret",
    }


def _materialize_guarded_submission(tmp_path: Path, *, status: str = "filled") -> tuple[Path, PaperBrokerOrderIntent]:
    now = datetime.now(timezone.utc)
    artifacts = tmp_path / "artifacts"
    output_root = artifacts / "paper_broker"
    intent = PaperBrokerOrderIntent(tracking_id="track-reconcile", symbol="SPY", side="buy", qty=1.0)
    _, _, selection = write_paper_execution_intent_selection_artifact(intent, output_root=output_root, generated_at_utc=now)
    write_paper_order_dry_run_artifact(
        intent,
        PaperBrokerOrderResult(ok=True, policy_status=PaperBrokerPolicyStatus.PAPER_READY, dry_run=True, retrieved_at_utc=now),
        output_root=output_root,
        generated_at_utc=now,
        source_selection_artifact_sha256=selection.artifact_sha256,
    )
    guard = build_paper_submission_guard_snapshot(intent=intent, env=_paper_env(), output_root=output_root, evaluated_at_utc=now)
    write_paper_order_submission_artifact(
        intent=intent,
        result=PaperBrokerOrderResult(
            ok=True,
            policy_status=PaperBrokerPolicyStatus.PAPER_READY,
            dry_run=False,
            broker_order_id="paper-order-reconcile-1",
            status=status,
            filled_qty=1.0 if status == "filled" else None,
            retrieved_at_utc=now,
        ),
        guard_snapshot=guard,
        output_root=output_root,
        generated_at_utc=now,
    )
    return output_root, intent


def test_paper_execution_cockpit_reconciles_guarded_submission_to_position_snapshot(monkeypatch, tmp_path: Path) -> None:
    now = datetime.now(timezone.utc)
    artifacts = tmp_path / "artifacts"
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(artifacts))
    monkeypatch.setenv("ALPACA_TRADING_MODE", "paper")
    monkeypatch.setenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
    monkeypatch.setenv("ALPACA_API_KEY", "paper-key")
    monkeypatch.setenv("ALPACA_API_SECRET", "paper-secret")
    output_root, _ = _materialize_guarded_submission(tmp_path, status="filled")

    write_paper_account_position_snapshot_artifact(
        account_status=PaperBrokerAccountStatus(
            policy_status=PaperBrokerPolicyStatus.PAPER_READY,
            account_id="paper-account-1",
            equity=10000.0,
            buying_power=9000.0,
            currency="USD",
            paper_endpoint_verified=True,
            retrieved_at_utc=now,
        ),
        positions=[PaperBrokerPositionSnapshot(symbol="SPY", qty=1.0, market_value=500.0, avg_entry_price=500.0)],
        notes=["test snapshot"],
        output_root=output_root,
        generated_at_utc=now,
    )

    payload = build_ui_paper_execution_cockpit_payload(repo_root=tmp_path)

    assert payload["summary"]["position_snapshot_count"] == 1
    assert payload["summary"]["position_reconciliation_status"] == "RECONCILED"
    assert payload["summary"]["position_reconciliation_blocker_count"] == 0
    assert payload["summary"]["latest_reconciled_symbol"] == "SPY"
    assert payload["summary"]["latest_reconciled_position_qty"] == 1.0
    reconciliation = payload["position_reconciliation"]
    assert reconciliation["status"] == "RECONCILED"
    assert reconciliation["observed_position_qty"] == 1.0
    assert reconciliation["expected_position_delta_qty"] == 1.0
    assert payload["account_position_snapshot"]["position_count"] == 1


def test_daily_operator_run_blocks_submission_without_position_snapshot(monkeypatch, tmp_path: Path) -> None:
    artifacts = tmp_path / "artifacts"
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(artifacts))
    monkeypatch.setenv("STRATEGY_VALIDATOR_STRATEGY_INTAKE_ROOT", str(tmp_path / "intake"))
    monkeypatch.setenv("STRATEGY_VALIDATOR_STRATEGY_BATCH_OUTPUT_ROOT", str(tmp_path / "batches"))
    monkeypatch.setenv("STRATEGY_VALIDATOR_STRATEGY_MEMORY_ROOT", str(tmp_path / "memory"))
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB", str(tmp_path / "ledger.sqlite3"))
    monkeypatch.setenv("ALPACA_TRADING_MODE", "paper")
    monkeypatch.setenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
    monkeypatch.setenv("ALPACA_API_KEY", "paper-key")
    monkeypatch.setenv("ALPACA_API_SECRET", "paper-secret")
    _materialize_guarded_submission(tmp_path, status="filled")

    payload = build_ui_daily_operator_run_payload(repo_root=tmp_path, database_path=str(tmp_path / "ledger.sqlite3"))
    paper = next(component for component in payload["components"] if component["component_id"] == "paper_execution")

    assert paper["summary"]["submission_receipt_count"] == 1
    assert paper["summary"]["position_reconciliation_status"] == "NO_POSITION_SNAPSHOT"
    assert "PAPER_EXECUTION_POSITION_SNAPSHOT_MISSING" in paper["blockers"]
    assert payload["summary"]["paper_execution_position_snapshot_count"] == 0
    assert payload["summary"]["paper_execution_position_reconciliation_blocker_count"] == 1
