from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.application.paper_execution_cockpit import build_ui_paper_execution_cockpit_payload
from strategy_validator.application.paper_execution_intent_selection import (
    read_latest_paper_execution_intent_selection,
    write_paper_execution_intent_selection_artifact,
)
from strategy_validator.contracts.paper_broker import PaperBrokerOrderIntent


def test_write_paper_execution_intent_selection_creates_latest_and_history(tmp_path: Path) -> None:
    intent = PaperBrokerOrderIntent(tracking_id="track-select1", symbol="qqq", side="sell", qty=0.5)

    latest, history, artifact = write_paper_execution_intent_selection_artifact(
        intent,
        strategy_id="strategy-qqq",
        selected_by="jp",
        selection_reason="prepare next paper dry-run",
        output_root=tmp_path / "paper_broker",
    )

    assert latest.name == "paper_execution_intent_selection.json"
    assert history.parent.name == "intent_selections"
    assert latest.exists()
    assert history.exists()
    payload = json.loads(latest.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "paper_execution_intent_selection/v1"
    assert payload["tracking_id"] == "track-select1"
    assert payload["selected_intent"]["symbol"] == "QQQ"
    assert payload["selected_intent"]["side"] == "sell"
    assert payload["selection_authority"] == "CLI_ARTIFACT_ONLY"
    assert payload["no_order_submitted"] is True
    assert payload["artifact_sha256"] == artifact.artifact_sha256
    assert "strategy-validator-paper-broker dry-run-order" in payload["dry_run_command_hint"]


def test_cockpit_prefers_selected_intent_over_inferred_latest(monkeypatch, tmp_path: Path) -> None:
    art = tmp_path / "artifacts"
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(art))
    monkeypatch.delenv("ALPACA_API_KEY", raising=False)
    monkeypatch.delenv("ALPACA_API_SECRET", raising=False)

    tdir = art / "paper_tracking" / "track-select1"
    tdir.mkdir(parents=True)
    (tdir / "paper_tracking_manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "paper_tracking_manifest/v1",
                "tracking_id": "track-select1",
                "batch_run_dir": "batch/demo",
                "candidate": {
                    "strategy_id": "strategy-spy",
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
            indent=2,
        ),
        encoding="utf-8",
    )
    (tdir / "snapshots" / "signals").mkdir(parents=True)
    (tdir / "snapshots" / "signals" / "2026-01-02.json").write_text(
        json.dumps(
            {
                "schema_version": "paper_daily_signal/v1",
                "tracking_id": "track-select1",
                "strategy_id": "strategy-spy",
                "observation_date_utc": "2026-01-02",
                "signal_exposure": 1.0,
                "signal_metadata": {"symbol": "SPY"},
                "evidence_sha256": "sig-sha",
            }
        ),
        encoding="utf-8",
    )
    write_paper_execution_intent_selection_artifact(
        PaperBrokerOrderIntent(tracking_id="track-select1", symbol="QQQ", side="sell", qty=0.25),
        strategy_id="strategy-qqq",
        output_root=art / "paper_broker",
    )

    path, latest, count = read_latest_paper_execution_intent_selection(repo_root=tmp_path)
    assert path is not None
    assert latest is not None
    assert count == 1

    payload = build_ui_paper_execution_cockpit_payload(repo_root=tmp_path)

    assert payload["summary"]["selected_intent_count"] == 1
    assert payload["summary"]["latest_selected_tracking_id"] == "track-select1"
    assert payload["selected_intent"]["selected_intent"]["symbol"] == "QQQ"
    assert payload["candidate_intents"][0]["source"] == "selected_intent_artifact"
    assert payload["candidate_intents"][0]["symbol"] == "QQQ"
    assert payload["dry_run_results"][0]["intent"]["symbol"] == "QQQ"
    assert "select-intent" not in "\n".join(payload["recommended_actions"])
