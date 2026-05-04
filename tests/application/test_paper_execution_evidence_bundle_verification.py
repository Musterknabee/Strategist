from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from strategy_validator.application.daily_operator_run_projection import build_ui_daily_operator_run_payload
from strategy_validator.application.paper_execution_cockpit import build_ui_paper_execution_cockpit_payload
from strategy_validator.application.paper_execution_evidence_bundle import write_paper_execution_evidence_bundle_artifact
from strategy_validator.application.paper_execution_evidence_bundle_verification import write_paper_execution_evidence_bundle_verification_artifact
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


def _materialize_complete_loop(tmp_path: Path) -> tuple[Path, Path]:
    output_root = tmp_path / "artifacts" / "paper_broker"
    t0 = datetime.now(timezone.utc).replace(microsecond=0) - timedelta(minutes=5)
    intent = PaperBrokerOrderIntent(tracking_id="track-verify", symbol="SPY", side="buy", qty=1.0)
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
            broker_order_id="paper-order-verify",
            status="accepted",
            retrieved_at_utc=t0 + timedelta(minutes=2),
        ),
        guard_snapshot=guard,
        output_root=output_root,
        generated_at_utc=t0 + timedelta(minutes=2),
    )
    assert submission.submission_guard.linked_dry_run_artifact_sha256 == dry.artifact_sha256
    write_paper_order_status_artifact(
        tracking_id="track-verify",
        broker_order_id="paper-order-verify",
        result=PaperBrokerOrderResult(
            ok=True,
            policy_status=PaperBrokerPolicyStatus.PAPER_READY,
            dry_run=False,
            broker_order_id="paper-order-verify",
            status="filled",
            filled_qty=1.0,
            evidence_redacted={"id": "paper-order-verify", "status": "filled", "symbol": "SPY", "side": "buy"},
            retrieved_at_utc=t0 + timedelta(minutes=3),
        ),
        source_submission_artifact_sha256=submission.artifact_sha256,
        output_root=output_root,
        generated_at_utc=t0 + timedelta(minutes=3),
    )
    write_paper_account_position_snapshot_artifact(
        account_status=PaperBrokerAccountStatus(
            policy_status=PaperBrokerPolicyStatus.PAPER_READY,
            account_id="paper-account-verify",
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
    cockpit = build_ui_paper_execution_cockpit_payload(repo_root=tmp_path)
    latest_path, _, _ = write_paper_execution_evidence_bundle_artifact(
        timeline=[PaperExecutionTimelineEntry.model_validate(row) for row in cockpit["execution_timeline"]],
        timeline_summary=PaperExecutionTimelineSummary.model_validate(cockpit["execution_timeline_summary"]),
        output_root=output_root,
    )
    return output_root, latest_path


def test_bundle_verification_passes_and_surfaces_in_cockpit_and_daily(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB", str(tmp_path / "ledger.sqlite3"))
    for key, value in _paper_env().items():
        monkeypatch.setenv(key, value)
    output_root, bundle_path = _materialize_complete_loop(tmp_path)

    latest_path, history_path, verification = write_paper_execution_evidence_bundle_verification_artifact(
        bundle_artifact_path=bundle_path,
        output_root=output_root,
    )

    assert latest_path.exists()
    assert history_path.exists()
    assert verification.verification_status == "PASS"
    assert verification.trust_banner == "TRUSTED"
    assert verification.bundle_hash_valid is True
    assert verification.timeline_source_link_valid is True
    assert verification.verified_source_artifact_count == verification.source_artifact_count
    assert verification.artifact_sha256

    cockpit = build_ui_paper_execution_cockpit_payload(repo_root=tmp_path)
    assert cockpit["summary"]["evidence_bundle_verification_count"] == 1
    assert cockpit["summary"]["latest_evidence_bundle_verification_status"] == "PASS"
    assert cockpit["latest_evidence_bundle_verification"]["artifact_sha256"] == verification.artifact_sha256

    daily = build_ui_daily_operator_run_payload(repo_root=tmp_path, database_path=str(tmp_path / "ledger.sqlite3"))
    assert daily["summary"]["paper_execution_evidence_bundle_verification_count"] == 1
    assert daily["summary"]["paper_execution_latest_bundle_verified_count"] == 1


def test_bundle_verification_fails_when_source_artifact_is_tampered(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    for key, value in _paper_env().items():
        monkeypatch.setenv(key, value)
    output_root, bundle_path = _materialize_complete_loop(tmp_path)
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    dry_source = next(src for src in bundle["source_artifacts"] if src["stage"] == "DRY_RUN")
    dry_path = Path(dry_source["artifact_path"])
    raw = json.loads(dry_path.read_text(encoding="utf-8"))
    raw["tampered_after_bundle"] = True
    dry_path.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    _, _, verification = write_paper_execution_evidence_bundle_verification_artifact(
        bundle_artifact_path=bundle_path,
        output_root=output_root,
    )

    assert verification.verification_status == "FAIL"
    assert verification.trust_banner == "UNTRUSTED"
    assert "SOURCE_ARTIFACTS_SHA256_MISMATCHED" in verification.blockers
    assert verification.mismatched_source_artifact_count >= 1
