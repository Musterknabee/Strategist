from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from strategy_validator.application.daily_operator_run_projection import build_ui_daily_operator_run_payload
from strategy_validator.application.paper_execution_cockpit import build_ui_paper_execution_cockpit_payload
from strategy_validator.application.paper_execution_intent_selection import write_paper_execution_intent_selection_artifact
from strategy_validator.application.paper_execution_journal import write_paper_order_dry_run_artifact
from strategy_validator.application.paper_execution_order_status import write_paper_order_status_artifact
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


def _materialize_full_timeline(tmp_path: Path) -> None:
    output_root = tmp_path / "artifacts" / "paper_broker"
    t0 = datetime.now(timezone.utc).replace(microsecond=0) - timedelta(minutes=5)
    intent = PaperBrokerOrderIntent(tracking_id="track-timeline", symbol="SPY", side="buy", qty=1.0)
    _, _, selection = write_paper_execution_intent_selection_artifact(
        intent,
        output_root=output_root,
        generated_at_utc=t0,
    )
    _, _, dry = write_paper_order_dry_run_artifact(
        intent,
        PaperBrokerOrderResult(
            ok=True,
            policy_status=PaperBrokerPolicyStatus.PAPER_READY,
            dry_run=True,
            retrieved_at_utc=t0 + timedelta(minutes=1),
        ),
        output_root=output_root,
        generated_at_utc=t0 + timedelta(minutes=1),
        source_selection_artifact_sha256=selection.artifact_sha256,
    )
    guard = build_paper_submission_guard_snapshot(
        intent=intent,
        env=_paper_env(),
        output_root=output_root,
        evaluated_at_utc=t0 + timedelta(minutes=2),
    )
    assert guard.status == "PASS"
    _, _, submission = write_paper_order_submission_artifact(
        intent=intent,
        result=PaperBrokerOrderResult(
            ok=True,
            policy_status=PaperBrokerPolicyStatus.PAPER_READY,
            dry_run=False,
            broker_order_id="paper-order-timeline",
            status="accepted",
            retrieved_at_utc=t0 + timedelta(minutes=2),
        ),
        guard_snapshot=guard,
        output_root=output_root,
        generated_at_utc=t0 + timedelta(minutes=2),
    )
    assert submission.submission_guard.linked_dry_run_artifact_sha256 == dry.artifact_sha256
    write_paper_order_status_artifact(
        tracking_id="track-timeline",
        broker_order_id="paper-order-timeline",
        result=PaperBrokerOrderResult(
            ok=True,
            policy_status=PaperBrokerPolicyStatus.PAPER_READY,
            dry_run=False,
            broker_order_id="paper-order-timeline",
            status="filled",
            filled_qty=1.0,
            evidence_redacted={"id": "paper-order-timeline", "status": "filled", "symbol": "SPY", "side": "buy"},
            retrieved_at_utc=t0 + timedelta(minutes=3),
        ),
        source_submission_artifact_path=str(output_root / "track-timeline" / "paper_order_submission.json"),
        source_submission_artifact_sha256=submission.artifact_sha256,
        output_root=output_root,
        generated_at_utc=t0 + timedelta(minutes=3),
    )
    write_paper_account_position_snapshot_artifact(
        account_status=PaperBrokerAccountStatus(
            policy_status=PaperBrokerPolicyStatus.PAPER_READY,
            account_id="paper-account-timeline",
            equity=10000.0,
            buying_power=9000.0,
            currency="USD",
            paper_endpoint_verified=True,
            retrieved_at_utc=t0 + timedelta(minutes=4),
        ),
        positions=[PaperBrokerPositionSnapshot(symbol="SPY", qty=1.0)],
        output_root=output_root,
        generated_at_utc=t0 + timedelta(minutes=4),
    )


def test_paper_execution_cockpit_builds_chronological_timeline(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    monkeypatch.setenv("ALPACA_TRADING_MODE", "paper")
    monkeypatch.setenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
    monkeypatch.setenv("ALPACA_API_KEY", "paper-key")
    monkeypatch.setenv("ALPACA_API_SECRET", "paper-secret")
    _materialize_full_timeline(tmp_path)

    payload = build_ui_paper_execution_cockpit_payload(repo_root=tmp_path)

    stages = [event["stage"] for event in payload["execution_timeline"]]
    assert stages == [
        "SELECTED_INTENT",
        "DRY_RUN",
        "SUBMISSION",
        "ORDER_STATUS",
        "POSITION_SNAPSHOT",
        "POSITION_RECONCILIATION",
    ]
    assert payload["execution_timeline_summary"]["sequence_status"] == "COMPLETE"
    assert payload["summary"]["timeline_sequence_status"] == "COMPLETE"
    assert payload["summary"]["timeline_event_count"] == 6
    assert payload["summary"]["timeline_blocker_count"] == 0
    assert payload["position_reconciliation"]["status"] == "RECONCILED"


def test_daily_operator_run_summarizes_paper_execution_timeline(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    monkeypatch.setenv("STRATEGY_VALIDATOR_STRATEGY_INTAKE_ROOT", str(tmp_path / "intake"))
    monkeypatch.setenv("STRATEGY_VALIDATOR_STRATEGY_BATCH_OUTPUT_ROOT", str(tmp_path / "batches"))
    monkeypatch.setenv("STRATEGY_VALIDATOR_STRATEGY_MEMORY_ROOT", str(tmp_path / "memory"))
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB", str(tmp_path / "ledger.sqlite3"))
    monkeypatch.setenv("ALPACA_TRADING_MODE", "paper")
    monkeypatch.setenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
    monkeypatch.setenv("ALPACA_API_KEY", "paper-key")
    monkeypatch.setenv("ALPACA_API_SECRET", "paper-secret")
    _materialize_full_timeline(tmp_path)

    payload = build_ui_daily_operator_run_payload(repo_root=tmp_path, database_path=str(tmp_path / "ledger.sqlite3"))
    paper = next(component for component in payload["components"] if component["component_id"] == "paper_execution")

    assert paper["summary"]["timeline_sequence_status"] == "COMPLETE"
    assert paper["summary"]["timeline_event_count"] == 6
    assert payload["summary"]["paper_execution_timeline_event_count"] == 6
    assert payload["summary"]["paper_execution_timeline_complete_count"] == 1
