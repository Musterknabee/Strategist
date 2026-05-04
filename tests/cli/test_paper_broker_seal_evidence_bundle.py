from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from strategy_validator.cli import paper_broker
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


def _paper_env(monkeypatch) -> dict[str, str]:
    env = {
        "ALPACA_TRADING_MODE": "paper",
        "ALPACA_BASE_URL": "https://paper-api.alpaca.markets",
        "ALPACA_API_KEY": "paper-key",
        "ALPACA_API_SECRET": "paper-secret",
    }
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    return env


def _materialize_complete_loop(output_root: Path, env: dict[str, str]) -> None:
    t0 = datetime.now(timezone.utc).replace(microsecond=0) - timedelta(minutes=5)
    intent = PaperBrokerOrderIntent(tracking_id="track-cli-bundle", symbol="SPY", side="buy", qty=1.0)
    _, _, selection = write_paper_execution_intent_selection_artifact(intent, output_root=output_root, generated_at_utc=t0)
    _, _, dry = write_paper_order_dry_run_artifact(
        intent,
        PaperBrokerOrderResult(ok=True, policy_status=PaperBrokerPolicyStatus.PAPER_READY, dry_run=True, retrieved_at_utc=t0 + timedelta(minutes=1)),
        output_root=output_root,
        generated_at_utc=t0 + timedelta(minutes=1),
        source_selection_artifact_sha256=selection.artifact_sha256,
    )
    guard = build_paper_submission_guard_snapshot(intent=intent, env=env, output_root=output_root, evaluated_at_utc=t0 + timedelta(minutes=2))
    _, _, submission = write_paper_order_submission_artifact(
        intent=intent,
        result=PaperBrokerOrderResult(ok=True, policy_status=PaperBrokerPolicyStatus.PAPER_READY, dry_run=False, broker_order_id="paper-order-cli-bundle", status="accepted", retrieved_at_utc=t0 + timedelta(minutes=2)),
        guard_snapshot=guard,
        output_root=output_root,
        generated_at_utc=t0 + timedelta(minutes=2),
    )
    assert submission.submission_guard.linked_dry_run_artifact_sha256 == dry.artifact_sha256
    write_paper_order_status_artifact(
        tracking_id="track-cli-bundle",
        broker_order_id="paper-order-cli-bundle",
        result=PaperBrokerOrderResult(ok=True, policy_status=PaperBrokerPolicyStatus.PAPER_READY, dry_run=False, broker_order_id="paper-order-cli-bundle", status="filled", filled_qty=1.0, evidence_redacted={"id": "paper-order-cli-bundle", "status": "filled", "symbol": "SPY", "side": "buy"}, retrieved_at_utc=t0 + timedelta(minutes=3)),
        source_submission_artifact_sha256=submission.artifact_sha256,
        output_root=output_root,
        generated_at_utc=t0 + timedelta(minutes=3),
    )
    write_paper_account_position_snapshot_artifact(
        account_status=PaperBrokerAccountStatus(policy_status=PaperBrokerPolicyStatus.PAPER_READY, account_id="paper-account-cli-bundle", equity=10000.0, buying_power=9000.0, currency="USD", paper_endpoint_verified=True, retrieved_at_utc=t0 + timedelta(minutes=4)),
        positions=[PaperBrokerPositionSnapshot(symbol="SPY", qty=1.0)],
        output_root=output_root,
        generated_at_utc=t0 + timedelta(minutes=4),
    )


def test_seal_evidence_bundle_cli_writes_digest_bundle(monkeypatch, tmp_path: Path, capsys) -> None:
    env = _paper_env(monkeypatch)
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    output_root = tmp_path / "artifacts" / "paper_broker"
    _materialize_complete_loop(output_root, env)

    rc = paper_broker.main(["seal-evidence-bundle", "--output-root", str(output_root)])

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["trust_banner"] == "TRUSTED"
    assert payload["bundle_status"] == "SEALED"
    assert payload["timeline_sequence_status"] == "COMPLETE"
    artifact_path = Path(payload["artifact"])
    assert artifact_path.exists()
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert artifact["schema_version"] == "paper_execution_evidence_bundle/v1"
    assert artifact["bundle_sha256"] == payload["bundle_sha256"]
    assert artifact["source_artifact_count"] >= 6
    assert "paper-secret" not in artifact_path.read_text(encoding="utf-8")
    assert Path(payload["history_artifact"]).exists()
