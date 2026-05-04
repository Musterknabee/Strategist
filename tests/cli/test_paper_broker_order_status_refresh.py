from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.cli import paper_broker
from strategy_validator.application.paper_execution_intent_selection import write_paper_execution_intent_selection_artifact
from strategy_validator.application.paper_execution_journal import write_paper_order_dry_run_artifact
from strategy_validator.application.paper_execution_submission_guard import (
    build_paper_submission_guard_snapshot,
    write_paper_order_submission_artifact,
)
from strategy_validator.contracts.paper_broker import PaperBrokerOrderIntent, PaperBrokerOrderResult, PaperBrokerPolicyStatus


def _set_paper_env(monkeypatch) -> None:
    monkeypatch.setenv("ALPACA_TRADING_MODE", "paper")
    monkeypatch.setenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
    monkeypatch.setenv("ALPACA_API_KEY", "paper-key")
    monkeypatch.setenv("ALPACA_API_SECRET", "paper-secret")
    monkeypatch.delenv("PERSONAL_LIVE_APPROVED", raising=False)


def _materialize_submission(output_root: Path) -> None:
    now = datetime.now(timezone.utc)
    env = {
        "ALPACA_TRADING_MODE": "paper",
        "ALPACA_BASE_URL": "https://paper-api.alpaca.markets",
        "ALPACA_API_KEY": "paper-key",
        "ALPACA_API_SECRET": "paper-secret",
    }
    intent = PaperBrokerOrderIntent(tracking_id="track-cli-status", symbol="SPY", side="buy", qty=1.0)
    _, _, selection = write_paper_execution_intent_selection_artifact(intent, output_root=output_root, generated_at_utc=now)
    write_paper_order_dry_run_artifact(
        intent,
        PaperBrokerOrderResult(ok=True, policy_status=PaperBrokerPolicyStatus.PAPER_READY, dry_run=True, retrieved_at_utc=now),
        output_root=output_root,
        generated_at_utc=now,
        source_selection_artifact_sha256=selection.artifact_sha256,
    )
    guard = build_paper_submission_guard_snapshot(intent=intent, env=env, output_root=output_root, evaluated_at_utc=now)
    write_paper_order_submission_artifact(
        intent=intent,
        result=PaperBrokerOrderResult(
            ok=True,
            policy_status=PaperBrokerPolicyStatus.PAPER_READY,
            dry_run=False,
            broker_order_id="paper-order-cli-status",
            status="accepted",
            retrieved_at_utc=now,
        ),
        guard_snapshot=guard,
        output_root=output_root,
        generated_at_utc=now,
    )


def test_refresh_order_status_writes_secret_free_artifact(monkeypatch, tmp_path: Path, capsys) -> None:
    _set_paper_env(monkeypatch)
    out_root = tmp_path / "paper_broker"
    _materialize_submission(out_root)

    def fake_order_status(env, broker_order_id, *, transport=None, allow_network=True):
        assert allow_network is True
        return PaperBrokerOrderResult(
            ok=True,
            policy_status=PaperBrokerPolicyStatus.PAPER_READY,
            dry_run=False,
            broker_order_id=broker_order_id,
            status="filled",
            filled_qty=1.0,
            evidence_redacted={"id": broker_order_id, "status": "filled", "symbol": "SPY", "side": "buy"},
            retrieved_at_utc=datetime.now(timezone.utc),
        )

    monkeypatch.setattr(paper_broker, "get_alpaca_paper_order_status", fake_order_status)

    rc = paper_broker.main([
        "refresh-order-status",
        "--tracking-id",
        "track-cli-status",
        "--allow-network",
        "--output-root",
        str(out_root),
    ])

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["broker_order_id"] == "paper-order-cli-status"
    assert payload["status"] == "filled"
    artifact = json.loads(Path(payload["artifact"]).read_text(encoding="utf-8"))
    assert artifact["schema_version"] == "paper_execution_order_status_artifact/v1"
    assert artifact["no_new_order_submitted"] is True
    assert artifact["result"]["filled_qty"] == 1.0
    assert "paper-secret" not in Path(payload["artifact"]).read_text(encoding="utf-8")
    assert Path(payload["history_artifact"]).exists()
