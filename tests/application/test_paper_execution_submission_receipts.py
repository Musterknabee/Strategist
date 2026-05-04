from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.application.daily_operator_run_projection import build_ui_daily_operator_run_payload
from strategy_validator.application.paper_execution_cockpit import build_ui_paper_execution_cockpit_payload
from strategy_validator.application.paper_execution_intent_selection import write_paper_execution_intent_selection_artifact
from strategy_validator.application.paper_execution_journal import write_paper_order_dry_run_artifact
from strategy_validator.application.paper_execution_submission_guard import (
    build_paper_submission_guard_snapshot,
    write_paper_order_submission_artifact,
)
from strategy_validator.contracts.paper_broker import PaperBrokerOrderIntent, PaperBrokerOrderResult, PaperBrokerPolicyStatus


def _paper_env() -> dict[str, str]:
    return {
        "ALPACA_TRADING_MODE": "paper",
        "ALPACA_BASE_URL": "https://paper-api.alpaca.markets",
        "ALPACA_API_KEY": "paper-key",
        "ALPACA_API_SECRET": "paper-secret",
    }


def test_paper_execution_cockpit_surfaces_guarded_submission_receipt(monkeypatch, tmp_path: Path) -> None:
    now = datetime.now(timezone.utc)
    artifacts = tmp_path / "artifacts"
    output_root = artifacts / "paper_broker"
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(artifacts))
    monkeypatch.setenv("ALPACA_TRADING_MODE", "paper")
    monkeypatch.setenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
    monkeypatch.setenv("ALPACA_API_KEY", "paper-key")
    monkeypatch.setenv("ALPACA_API_SECRET", "paper-secret")

    intent = PaperBrokerOrderIntent(tracking_id="track-receipt", symbol="SPY", side="buy", qty=1.0)
    _, _, selection = write_paper_execution_intent_selection_artifact(
        intent,
        output_root=output_root,
        generated_at_utc=now,
    )
    dry_result = PaperBrokerOrderResult(
        ok=True,
        policy_status=PaperBrokerPolicyStatus.PAPER_READY,
        dry_run=True,
        retrieved_at_utc=now,
    )
    write_paper_order_dry_run_artifact(
        intent,
        dry_result,
        output_root=output_root,
        generated_at_utc=now,
        source_selection_artifact_sha256=selection.artifact_sha256,
    )
    guard = build_paper_submission_guard_snapshot(
        intent=intent,
        env=_paper_env(),
        output_root=output_root,
        evaluated_at_utc=now,
    )
    submission_result = PaperBrokerOrderResult(
        ok=True,
        policy_status=PaperBrokerPolicyStatus.PAPER_READY,
        dry_run=False,
        broker_order_id="paper-order-receipt-1",
        status="accepted",
        retrieved_at_utc=now,
    )
    write_paper_order_submission_artifact(
        intent=intent,
        result=submission_result,
        guard_snapshot=guard,
        output_root=output_root,
        generated_at_utc=now,
    )

    payload = build_ui_paper_execution_cockpit_payload(repo_root=tmp_path)

    assert payload["summary"]["submission_receipt_count"] == 1
    assert payload["summary"]["latest_submission_guard_status"] == "PASS"
    assert payload["summary"]["latest_submission_evidence_freshness_status"] == "FRESH"
    assert payload["summary"]["latest_submission_broker_order_id"] == "paper-order-receipt-1"
    assert payload["summary"]["submission_guard_blocker_count"] == 0
    receipt = payload["submission_receipts"][0]
    assert receipt["schema_version"] == "paper_execution_submission_receipt_view/v1"
    assert receipt["guard_status"] == "PASS"
    assert receipt["evidence_freshness_status"] == "FRESH"
    assert receipt["submission_intent_matches_selection"] is True
    assert receipt["linked_dry_run_matches_selection"] is True
    assert receipt["linked_dry_run_ok"] is True
    assert receipt["selected_intent_artifact_sha256"] == selection.artifact_sha256
    assert receipt["broker_order_id"] == "paper-order-receipt-1"
    journal_submission = next(row for row in payload["journal_entries"] if row["artifact_kind"] == "SUBMISSION")
    assert journal_submission["submission_guard_status"] == "PASS"
    assert journal_submission["evidence_freshness_status"] == "FRESH"
    assert journal_submission["linked_dry_run_ok"] is True


def test_daily_operator_run_includes_submission_receipt_status(monkeypatch, tmp_path: Path) -> None:
    now = datetime.now(timezone.utc)
    artifacts = tmp_path / "artifacts"
    output_root = artifacts / "paper_broker"
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(artifacts))
    monkeypatch.setenv("STRATEGY_VALIDATOR_STRATEGY_INTAKE_ROOT", str(tmp_path / "intake"))
    monkeypatch.setenv("STRATEGY_VALIDATOR_STRATEGY_BATCH_OUTPUT_ROOT", str(tmp_path / "batches"))
    monkeypatch.setenv("STRATEGY_VALIDATOR_STRATEGY_MEMORY_ROOT", str(tmp_path / "memory"))
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB", str(tmp_path / "ledger.sqlite3"))
    monkeypatch.setenv("ALPACA_TRADING_MODE", "paper")
    monkeypatch.setenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
    monkeypatch.setenv("ALPACA_API_KEY", "paper-key")
    monkeypatch.setenv("ALPACA_API_SECRET", "paper-secret")

    intent = PaperBrokerOrderIntent(tracking_id="track-daily-receipt", symbol="QQQ", side="sell", qty=0.5)
    _, _, selection = write_paper_execution_intent_selection_artifact(intent, output_root=output_root, generated_at_utc=now)
    dry_result = PaperBrokerOrderResult(ok=True, policy_status=PaperBrokerPolicyStatus.PAPER_READY, dry_run=True, retrieved_at_utc=now)
    write_paper_order_dry_run_artifact(
        intent,
        dry_result,
        output_root=output_root,
        generated_at_utc=now,
        source_selection_artifact_sha256=selection.artifact_sha256,
    )
    guard = build_paper_submission_guard_snapshot(intent=intent, env=_paper_env(), output_root=output_root, evaluated_at_utc=now)
    submission_result = PaperBrokerOrderResult(
        ok=True,
        policy_status=PaperBrokerPolicyStatus.PAPER_READY,
        dry_run=False,
        broker_order_id="paper-order-daily-1",
        status="accepted",
        retrieved_at_utc=now,
    )
    write_paper_order_submission_artifact(
        intent=intent,
        result=submission_result,
        guard_snapshot=guard,
        output_root=output_root,
        generated_at_utc=now,
    )

    payload = build_ui_daily_operator_run_payload(repo_root=tmp_path, database_path=str(tmp_path / "ledger.sqlite3"))
    paper = next(component for component in payload["components"] if component["component_id"] == "paper_execution")

    assert paper["summary"]["submission_receipt_count"] == 1
    assert paper["summary"]["latest_submission_guard_status"] == "PASS"
    assert paper["summary"]["latest_submission_evidence_freshness_status"] == "FRESH"
    assert payload["summary"]["paper_execution_submission_receipt_count"] == 1
    assert payload["summary"]["paper_execution_submission_guard_blocker_count"] == 0
    assert payload["summary"]["paper_execution_latest_submission_guard_passed_count"] == 1
