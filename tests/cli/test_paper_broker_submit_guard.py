from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.cli import paper_broker
from strategy_validator.cli.paper_broker import main
from strategy_validator.contracts.paper_broker import PaperBrokerOrderResult, PaperBrokerPolicyStatus


def _set_paper_env(monkeypatch) -> None:
    monkeypatch.setenv("ALPACA_TRADING_MODE", "paper")
    monkeypatch.setenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
    monkeypatch.setenv("ALPACA_API_KEY", "paper-key")
    monkeypatch.setenv("ALPACA_API_SECRET", "paper-secret")
    monkeypatch.delenv("PERSONAL_LIVE_APPROVED", raising=False)


def test_submit_paper_order_requires_selected_intent_replay_evidence(monkeypatch, tmp_path: Path, capsys) -> None:
    _set_paper_env(monkeypatch)
    out_root = tmp_path / "paper_broker"

    rc = main(
        [
            "submit-paper-order",
            "--tracking-id",
            "track-no-evidence",
            "--symbol",
            "SPY",
            "--side",
            "buy",
            "--qty",
            "1",
            "--confirm-paper",
            "--output-root",
            str(out_root),
        ]
    )

    assert rc == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert "SELECTED_INTENT_ARTIFACT_NOT_FOUND" in payload["blocked"]
    assert payload["submission_guard"]["status"] == "BLOCKED"


def test_submit_paper_order_writes_guarded_submission_artifact(monkeypatch, tmp_path: Path, capsys) -> None:
    _set_paper_env(monkeypatch)
    out_root = tmp_path / "paper_broker"

    assert main([
        "select-intent",
        "--tracking-id",
        "track-submit-ok",
        "--symbol",
        "SPY",
        "--side",
        "buy",
        "--qty",
        "1",
        "--output-root",
        str(out_root),
    ]) == 0
    capsys.readouterr()
    assert main([
        "dry-run-selected-intent",
        "--tracking-id",
        "track-submit-ok",
        "--output-root",
        str(out_root),
    ]) == 0
    replay = json.loads(capsys.readouterr().out)

    def fake_submit(intent, env):
        return PaperBrokerOrderResult(
            ok=True,
            policy_status=PaperBrokerPolicyStatus.PAPER_READY,
            dry_run=False,
            broker_order_id="paper-order-1",
            status="accepted",
            retrieved_at_utc=datetime.now(timezone.utc),
        )

    monkeypatch.setattr(paper_broker, "submit_paper_order", fake_submit)

    rc = main(
        [
            "submit-paper-order",
            "--tracking-id",
            "track-submit-ok",
            "--symbol",
            "SPY",
            "--side",
            "buy",
            "--qty",
            "1",
            "--confirm-paper",
            "--output-root",
            str(out_root),
        ]
    )

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["submission_guard"]["status"] == "PASS"
    assert payload["submission_guard"]["evidence_freshness_status"] == "FRESH"
    assert payload["submission_guard"]["selected_intent_artifact_sha256"] == replay["selected_intent_sha256"]
    artifact = json.loads(Path(payload["artifact"]).read_text(encoding="utf-8"))
    assert artifact["schema_version"] == "paper_execution_submission_artifact/v1"
    assert artifact["result"]["broker_order_id"] == "paper-order-1"
    assert artifact["submission_guard"]["status"] == "PASS"
    assert Path(payload["history_artifact"]).exists()
