from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from strategy_validator.application.daily_operator_run_projection import build_ui_daily_operator_run_payload
from strategy_validator.application.paper_execution_cockpit import build_ui_paper_execution_cockpit_payload
from strategy_validator.application.paper_execution_evidence_bundle import write_paper_execution_evidence_bundle_artifact
from strategy_validator.application.paper_execution_intent_selection import write_paper_execution_intent_selection_artifact
from strategy_validator.application.paper_execution_journal import write_paper_order_dry_run_artifact
from strategy_validator.application.paper_execution_order_status import write_paper_order_status_artifact
from strategy_validator.application.paper_execution_reconciliation import write_paper_account_position_snapshot_artifact
from strategy_validator.application.paper_execution_submission_guard import build_paper_submission_guard_snapshot, write_paper_order_submission_artifact
from strategy_validator.contracts.paper_broker import (
    PaperBrokerAccountStatus,
    PaperBrokerOrderIntent,
    PaperBrokerOrderResult,
    PaperBrokerPolicyStatus,
    PaperBrokerPositionSnapshot,
)
from strategy_validator.contracts.paper_execution import PaperExecutionTimelineEntry, PaperExecutionTimelineSummary


def _paper_env() -> dict[str, str]:
    return {
        "ALPACA_TRADING_MODE": "paper",
        "ALPACA_BASE_URL": "https://paper-api.alpaca.markets",
        "ALPACA_API_KEY": "paper-key",
        "ALPACA_API_SECRET": "paper-secret",
    }


def _materialize_complete_loop(tmp_path: Path) -> Path:
    output_root = tmp_path / "artifacts" / "paper_broker"
    t0 = datetime.now(timezone.utc).replace(microsecond=0) - timedelta(minutes=5)
    intent = PaperBrokerOrderIntent(tracking_id="track-bundle", symbol="SPY", side="buy", qty=1.0)
    _, _, selection = write_paper_execution_intent_selection_artifact(intent, output_root=output_root, generated_at_utc=t0)
    _, _, dry = write_paper_order_dry_run_artifact(
        intent,
        PaperBrokerOrderResult(ok=True, policy_status=PaperBrokerPolicyStatus.PAPER_READY, dry_run=True, retrieved_at_utc=t0 + timedelta(minutes=1)),
        output_root=output_root,
        generated_at_utc=t0 + timedelta(minutes=1),
        source_selection_artifact_sha256=selection.artifact_sha256,
    )
    guard = build_paper_submission_guard_snapshot(intent=intent, env=_paper_env(), output_root=output_root, evaluated_at_utc=t0 + timedelta(minutes=2))
    assert guard.status == "PASS"
    _, _, submission = write_paper_order_submission_artifact(
        intent=intent,
        result=PaperBrokerOrderResult(
            ok=True,
            policy_status=PaperBrokerPolicyStatus.PAPER_READY,
            dry_run=False,
            broker_order_id="paper-order-bundle",
            status="accepted",
            retrieved_at_utc=t0 + timedelta(minutes=2),
        ),
        guard_snapshot=guard,
        output_root=output_root,
        generated_at_utc=t0 + timedelta(minutes=2),
    )
    assert submission.submission_guard.linked_dry_run_artifact_sha256 == dry.artifact_sha256
    write_paper_order_status_artifact(
        tracking_id="track-bundle",
        broker_order_id="paper-order-bundle",
        result=PaperBrokerOrderResult(
            ok=True,
            policy_status=PaperBrokerPolicyStatus.PAPER_READY,
            dry_run=False,
            broker_order_id="paper-order-bundle",
            status="filled",
            filled_qty=1.0,
            evidence_redacted={"id": "paper-order-bundle", "status": "filled", "symbol": "SPY", "side": "buy"},
            retrieved_at_utc=t0 + timedelta(minutes=3),
        ),
        source_submission_artifact_path=str(output_root / "track-bundle" / "paper_order_submission.json"),
        source_submission_artifact_sha256=submission.artifact_sha256,
        output_root=output_root,
        generated_at_utc=t0 + timedelta(minutes=3),
    )
    write_paper_account_position_snapshot_artifact(
        account_status=PaperBrokerAccountStatus(
            policy_status=PaperBrokerPolicyStatus.PAPER_READY,
            account_id="paper-account-bundle",
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
    return output_root


def test_evidence_bundle_seals_complete_paper_timeline(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    monkeypatch.setenv("ALPACA_TRADING_MODE", "paper")
    monkeypatch.setenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
    monkeypatch.setenv("ALPACA_API_KEY", "paper-key")
    monkeypatch.setenv("ALPACA_API_SECRET", "paper-secret")
    output_root = _materialize_complete_loop(tmp_path)
    cockpit = build_ui_paper_execution_cockpit_payload(repo_root=tmp_path)
    assert cockpit["execution_timeline_summary"]["sequence_status"] == "COMPLETE"

    timeline = [PaperExecutionTimelineEntry.model_validate(row) for row in cockpit["execution_timeline"]]
    timeline_summary = PaperExecutionTimelineSummary.model_validate(cockpit["execution_timeline_summary"])
    latest_path, history_path, bundle = write_paper_execution_evidence_bundle_artifact(
        timeline=timeline,
        timeline_summary=timeline_summary,
        output_root=output_root,
    )

    assert latest_path.exists()
    assert history_path.exists()
    assert bundle.trust_banner == "TRUSTED"
    assert bundle.bundle_status == "SEALED"
    assert bundle.timeline_event_count == 6
    assert bundle.source_artifact_count >= 6
    assert bundle.bundle_sha256

    refreshed = build_ui_paper_execution_cockpit_payload(repo_root=tmp_path)
    assert refreshed["summary"]["evidence_bundle_count"] == 1
    assert refreshed["summary"]["latest_evidence_bundle_trust_banner"] == "TRUSTED"
    assert refreshed["latest_evidence_bundle"]["bundle_sha256"] == bundle.bundle_sha256


def test_daily_operator_run_summarizes_evidence_bundle(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB", str(tmp_path / "ledger.sqlite3"))
    monkeypatch.setenv("ALPACA_TRADING_MODE", "paper")
    monkeypatch.setenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
    monkeypatch.setenv("ALPACA_API_KEY", "paper-key")
    monkeypatch.setenv("ALPACA_API_SECRET", "paper-secret")
    output_root = _materialize_complete_loop(tmp_path)
    cockpit = build_ui_paper_execution_cockpit_payload(repo_root=tmp_path)
    write_paper_execution_evidence_bundle_artifact(
        timeline=[PaperExecutionTimelineEntry.model_validate(row) for row in cockpit["execution_timeline"]],
        timeline_summary=PaperExecutionTimelineSummary.model_validate(cockpit["execution_timeline_summary"]),
        output_root=output_root,
    )

    payload = build_ui_daily_operator_run_payload(repo_root=tmp_path, database_path=str(tmp_path / "ledger.sqlite3"))
    paper = next(component for component in payload["components"] if component["component_id"] == "paper_execution")

    assert paper["summary"]["evidence_bundle_count"] == 1
    assert paper["summary"]["latest_evidence_bundle_trust_banner"] == "TRUSTED"
    assert payload["summary"]["paper_execution_evidence_bundle_count"] == 1
    assert payload["summary"]["paper_execution_latest_bundle_trusted_count"] == 1
