from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.application.paper_execution_cockpit import build_ui_paper_execution_cockpit_payload


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_paper_execution_cockpit_is_read_plane_without_tracking(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    monkeypatch.delenv("ALPACA_API_KEY", raising=False)
    monkeypatch.delenv("ALPACA_API_SECRET", raising=False)

    payload = build_ui_paper_execution_cockpit_payload(repo_root=tmp_path)

    assert payload["schema_version"] == "ui_paper_execution_cockpit/v1"
    assert payload["read_plane_only"] is True
    assert payload["no_browser_orders"] is True
    assert payload["no_live_trading"] is True
    assert payload["mutation_authority"] == "NONE"
    assert payload["execution_authority"] == "NONE"
    assert payload["paper_submission_authority"] == "CLI_ONLY"
    assert payload["summary"]["tracking_present"] is False
    assert "NO_PAPER_TRACKING_BUNDLE" in payload["degraded"]
    assert payload["recommended_actions"]


def test_paper_execution_derives_intent_and_reads_journal(monkeypatch, tmp_path: Path) -> None:
    art = tmp_path / "artifacts"
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(art))
    monkeypatch.setenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
    monkeypatch.delenv("ALPACA_API_KEY", raising=False)
    monkeypatch.delenv("ALPACA_API_SECRET", raising=False)

    tdir = art / "paper_tracking" / "track-12345678"
    _write(
        tdir / "paper_tracking_manifest.json",
        {
            "schema_version": "paper_tracking_manifest/v1",
            "tracking_id": "track-12345678",
            "batch_run_dir": "batch/demo",
            "candidate": {
                "strategy_id": "provider-mr-qqq",
                "strategy_type": "mean_reversion",
                "batch_id": "batch-1",
                "run_id": "run-1",
                "enrolled_at_utc": "2026-01-01T00:00:00+00:00",
                "promotion_eligible_at_enrollment": False,
                "synthetic_demo": False,
                "paper_posture": "RESEARCH_PAPER_TRACKING",
                "data_plane_at_enrollment": "PROVIDER_PAPER",
                "gauntlet_gate_snapshot": {},
            },
            "kill_rules": [],
            "manifest_sha256": "manifest-sha",
            "created_at_utc": "2026-01-01T00:00:00+00:00",
            "enrollment_notes": [],
        },
    )
    _write(
        tdir / "snapshots" / "signals" / "2026-01-02.json",
        {
            "schema_version": "paper_daily_signal/v1",
            "tracking_id": "track-12345678",
            "strategy_id": "provider-mr-qqq",
            "observation_date_utc": "2026-01-02",
            "signal_exposure": -0.42,
            "signal_metadata": {},
            "evidence_sha256": "sig-sha",
        },
    )
    _write(
        art / "paper_broker" / "track-12345678" / "paper_order_submission.json",
        {
            "schema_version": "paper_broker_order_result/v1",
            "ok": True,
            "policy_status": "PAPER_READY",
            "dry_run": False,
            "broker_order_id": "paper-order-1",
            "status": "accepted",
            "warnings": [],
            "blockers": [],
            "retrieved_at_utc": "2026-01-02T12:00:00+00:00",
        },
    )

    payload = build_ui_paper_execution_cockpit_payload(repo_root=tmp_path)

    assert payload["summary"]["tracking_present"] is True
    assert payload["summary"]["candidate_intent_count"] == 1
    assert payload["summary"]["dry_run_blocked_count"] == 1
    assert payload["summary"]["journal_entry_count"] == 1
    intent = payload["candidate_intents"][0]
    assert intent["symbol"] == "QQQ"
    assert intent["side"] == "sell"
    assert intent["qty"] == 0.42
    assert payload["dry_run_results"][0]["submission_route"] == "CLI_ONLY"
    assert payload["journal_entries"][0]["broker_order_id"] == "paper-order-1"
