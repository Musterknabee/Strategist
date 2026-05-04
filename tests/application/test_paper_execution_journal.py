from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.application.paper_execution_cockpit import build_ui_paper_execution_cockpit_payload
from strategy_validator.application.paper_execution_journal import write_paper_order_dry_run_artifact
from strategy_validator.contracts.paper_broker import PaperBrokerOrderIntent, PaperBrokerOrderResult, PaperBrokerPolicyStatus


def test_write_paper_order_dry_run_artifact_creates_latest_and_history(tmp_path: Path) -> None:
    intent = PaperBrokerOrderIntent(tracking_id="track-abc12345", symbol="SPY", side="buy", qty=1.0)
    result = PaperBrokerOrderResult(
        ok=False,
        policy_status=PaperBrokerPolicyStatus.PENDING_KEY,
        dry_run=True,
        blockers=["ALPACA_KEYS_MISSING"],
    )

    latest, history, artifact = write_paper_order_dry_run_artifact(intent, result, output_root=tmp_path / "paper_broker")

    assert latest.name == "paper_order_dry_run.json"
    assert history.parent.name == "dry_runs"
    assert latest.exists()
    assert history.exists()
    payload = json.loads(latest.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "paper_execution_dry_run_artifact/v1"
    assert payload["tracking_id"] == "track-abc12345"
    assert payload["no_order_submitted"] is True
    assert payload["execution_authority"] == "NONE"
    assert payload["artifact_sha256"] == artifact.artifact_sha256


def test_cockpit_reads_dry_run_artifact_history(monkeypatch, tmp_path: Path) -> None:
    art = tmp_path / "artifacts"
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(art))
    intent = PaperBrokerOrderIntent(tracking_id="track-abc12345", symbol="SPY", side="buy", qty=1.0)
    result = PaperBrokerOrderResult(
        ok=False,
        policy_status=PaperBrokerPolicyStatus.PENDING_KEY,
        dry_run=True,
        blockers=["ALPACA_KEYS_MISSING"],
    )
    write_paper_order_dry_run_artifact(intent, result, output_root=art / "paper_broker")

    payload = build_ui_paper_execution_cockpit_payload(repo_root=tmp_path)

    assert payload["summary"]["dry_run_artifact_count"] == 1
    assert payload["summary"]["submission_artifact_count"] == 0
    assert payload["summary"]["journal_entry_count"] == 1
    assert payload["journal_entries"][0]["artifact_kind"] == "DRY_RUN"
    assert payload["journal_entries"][0]["status"] == "dry_run_blocked"
