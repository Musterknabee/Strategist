from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.brokers import alpaca_paper
from strategy_validator.cli import paper_broker
from strategy_validator.contracts.paper_broker import PaperBrokerAccountStatus, PaperBrokerPolicyStatus, PaperBrokerPositionSnapshot


def _set_paper_env(monkeypatch) -> None:
    monkeypatch.setenv("ALPACA_TRADING_MODE", "paper")
    monkeypatch.setenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
    monkeypatch.setenv("ALPACA_API_KEY", "paper-key")
    monkeypatch.setenv("ALPACA_API_SECRET", "paper-secret")
    monkeypatch.delenv("PERSONAL_LIVE_APPROVED", raising=False)


def test_snapshot_account_positions_writes_secret_free_artifact(monkeypatch, tmp_path: Path, capsys) -> None:
    _set_paper_env(monkeypatch)
    out_root = tmp_path / "paper_broker"

    def fake_account(env, *, allow_network=True):
        return PaperBrokerAccountStatus(
            policy_status=PaperBrokerPolicyStatus.PAPER_READY,
            account_id="paper-account-cli",
            equity=12000.0,
            buying_power=8000.0,
            currency="USD",
            paper_endpoint_verified=True,
            retrieved_at_utc=datetime.now(timezone.utc),
        )

    def fake_positions(env):
        return PaperBrokerPolicyStatus.PAPER_READY, [PaperBrokerPositionSnapshot(symbol="SPY", qty=2.0)], ["MOCK_POSITIONS"]

    monkeypatch.setattr(paper_broker, "get_alpaca_paper_account", fake_account)
    monkeypatch.setattr(paper_broker, "list_alpaca_paper_positions", fake_positions)

    rc = paper_broker.main([
        "snapshot-account-positions",
        "--allow-network",
        "--output-root",
        str(out_root),
    ])

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["position_count"] == 1
    artifact = json.loads(Path(payload["artifact"]).read_text(encoding="utf-8"))
    assert artifact["schema_version"] == "paper_execution_account_position_snapshot/v1"
    assert artifact["position_count"] == 1
    assert artifact["positions"][0]["symbol"] == "SPY"
    assert "paper-secret" not in Path(payload["artifact"]).read_text(encoding="utf-8")
    assert Path(payload["history_artifact"]).exists()
