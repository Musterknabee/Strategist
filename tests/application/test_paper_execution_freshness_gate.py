from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from strategy_validator.application.daily_operator_run_projection import build_ui_daily_operator_run_payload
from strategy_validator.application.paper_execution_cockpit import build_ui_paper_execution_cockpit_payload
from strategy_validator.application.paper_execution_intent_selection import write_paper_execution_intent_selection_artifact
from strategy_validator.application.paper_execution_journal import write_paper_order_dry_run_artifact
from strategy_validator.contracts.paper_broker import PaperBrokerOrderIntent, PaperBrokerOrderResult, PaperBrokerPolicyStatus


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _tracking_bundle(root: Path, *, tracking_id: str, strategy_id: str, generated_at: datetime) -> None:
    tdir = root / "paper_tracking" / tracking_id
    _write(
        tdir / "paper_tracking_manifest.json",
        {
            "schema_version": "paper_tracking_manifest/v1",
            "tracking_id": tracking_id,
            "batch_run_dir": "batch/freshness",
            "candidate": {
                "strategy_id": strategy_id,
                "strategy_type": "mean_reversion",
                "batch_id": "batch-1",
                "run_id": "run-1",
                "enrolled_at_utc": generated_at.isoformat(),
                "promotion_eligible_at_enrollment": False,
                "synthetic_demo": False,
                "paper_posture": "RESEARCH_PAPER_TRACKING",
                "data_plane_at_enrollment": "PROVIDER_PAPER",
                "gauntlet_gate_snapshot": {},
            },
            "kill_rules": [],
            "manifest_sha256": "manifest-sha",
            "created_at_utc": generated_at.isoformat(),
            "enrollment_notes": [],
        },
    )
    _write(
        tdir / "snapshots" / "signals" / "latest.json",
        {
            "schema_version": "paper_daily_signal/v1",
            "tracking_id": tracking_id,
            "strategy_id": strategy_id,
            "observation_date_utc": generated_at.date().isoformat(),
            "generated_at_utc": generated_at.isoformat(),
            "signal_exposure": 0.25,
            "signal_metadata": {"symbol": "SPY"},
            "evidence_sha256": "sig-sha",
        },
    )


def test_paper_execution_freshness_gate_marks_matched_recent_evidence_fresh(monkeypatch, tmp_path: Path) -> None:
    now = datetime.now(timezone.utc)
    art = tmp_path / "artifacts"
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(art))
    _tracking_bundle(art, tracking_id="track-fresh", strategy_id="strategy-fresh", generated_at=now)
    intent = PaperBrokerOrderIntent(tracking_id="track-fresh", symbol="SPY", side="buy", qty=0.25)
    _, _, selection = write_paper_execution_intent_selection_artifact(
        intent,
        strategy_id="strategy-fresh",
        output_root=art / "paper_broker",
        generated_at_utc=now,
    )
    result = PaperBrokerOrderResult(
        ok=True,
        policy_status=PaperBrokerPolicyStatus.PAPER_READY,
        dry_run=True,
        retrieved_at_utc=now,
    )
    write_paper_order_dry_run_artifact(
        intent,
        result,
        output_root=art / "paper_broker",
        generated_at_utc=now,
        source_selection_artifact_sha256=selection.artifact_sha256,
    )

    payload = build_ui_paper_execution_cockpit_payload(repo_root=tmp_path)

    assert payload["summary"]["selected_intent_dry_run_status"] == "MATCHED"
    assert payload["summary"]["evidence_freshness_status"] == "FRESH"
    assert payload["summary"]["evidence_freshness_blocker_count"] == 0
    assert payload["freshness_gate"]["status"] == "FRESH"
    assert payload["freshness_gate"]["blockers"] == []


def test_paper_execution_freshness_gate_blocks_stale_selected_and_dry_run(monkeypatch, tmp_path: Path) -> None:
    now = datetime.now(timezone.utc)
    old_selection = now - timedelta(hours=30)
    old_dry_run = now - timedelta(hours=13)
    art = tmp_path / "artifacts"
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(art))
    _tracking_bundle(art, tracking_id="track-stale", strategy_id="strategy-stale", generated_at=now)
    intent = PaperBrokerOrderIntent(tracking_id="track-stale", symbol="SPY", side="buy", qty=0.25)
    _, _, selection = write_paper_execution_intent_selection_artifact(
        intent,
        strategy_id="strategy-stale",
        output_root=art / "paper_broker",
        generated_at_utc=old_selection,
    )
    result = PaperBrokerOrderResult(
        ok=True,
        policy_status=PaperBrokerPolicyStatus.PAPER_READY,
        dry_run=True,
        retrieved_at_utc=old_dry_run,
    )
    write_paper_order_dry_run_artifact(
        intent,
        result,
        output_root=art / "paper_broker",
        generated_at_utc=old_dry_run,
        source_selection_artifact_sha256=selection.artifact_sha256,
    )

    payload = build_ui_paper_execution_cockpit_payload(repo_root=tmp_path)

    assert payload["summary"]["selected_intent_dry_run_status"] == "MATCHED"
    assert payload["summary"]["evidence_freshness_status"] == "STALE"
    assert payload["summary"]["evidence_freshness_blocker_count"] >= 2
    assert "SELECTED_INTENT_STALE" in payload["freshness_gate"]["blockers"]
    assert "LINKED_DRY_RUN_STALE" in payload["freshness_gate"]["blockers"]
    assert "Refresh stale paper execution evidence" in "\n".join(payload["recommended_actions"])


def test_daily_operator_run_propagates_paper_execution_freshness_blocker(monkeypatch, tmp_path: Path) -> None:
    now = datetime.now(timezone.utc)
    art = tmp_path / "artifacts"
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(art))
    monkeypatch.setenv("STRATEGY_VALIDATOR_STRATEGY_INTAKE_ROOT", str(tmp_path / "intake"))
    monkeypatch.setenv("STRATEGY_VALIDATOR_STRATEGY_BATCH_OUTPUT_ROOT", str(tmp_path / "batches"))
    monkeypatch.setenv("STRATEGY_VALIDATOR_STRATEGY_MEMORY_ROOT", str(tmp_path / "memory"))
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB", str(tmp_path / "ledger.sqlite3"))
    _tracking_bundle(art, tracking_id="track-daily-stale", strategy_id="strategy-daily", generated_at=now)
    intent = PaperBrokerOrderIntent(tracking_id="track-daily-stale", symbol="SPY", side="buy", qty=0.25)
    _, _, selection = write_paper_execution_intent_selection_artifact(
        intent,
        output_root=art / "paper_broker",
        generated_at_utc=now - timedelta(hours=30),
    )
    result = PaperBrokerOrderResult(ok=True, policy_status=PaperBrokerPolicyStatus.PAPER_READY, dry_run=True, retrieved_at_utc=now - timedelta(hours=13))
    write_paper_order_dry_run_artifact(
        intent,
        result,
        output_root=art / "paper_broker",
        generated_at_utc=now - timedelta(hours=13),
        source_selection_artifact_sha256=selection.artifact_sha256,
    )

    payload = build_ui_daily_operator_run_payload(repo_root=tmp_path, database_path=str(tmp_path / "ledger.sqlite3"))
    paper = next(c for c in payload["components"] if c["component_id"] == "paper_execution")

    assert paper["summary"]["evidence_freshness_status"] == "STALE"
    assert paper["summary"]["evidence_freshness_blocker_count"] >= 2
    assert payload["summary"]["paper_execution_freshness_blocker_count"] >= 2
    assert "paper_execution:PAPER_EXECUTION_EVIDENCE_STALE" in payload["blockers"]
