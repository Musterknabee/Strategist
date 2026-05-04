from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from strategy_validator.application.paper_execution_intent_selection import write_paper_execution_intent_selection_artifact
from strategy_validator.application.paper_execution_journal import write_paper_order_dry_run_artifact
from strategy_validator.application.paper_execution_submission_guard import build_paper_submission_guard_snapshot
from strategy_validator.contracts.paper_broker import PaperBrokerOrderIntent, PaperBrokerOrderResult, PaperBrokerPolicyStatus


def _paper_env() -> dict[str, str]:
    return {
        "ALPACA_TRADING_MODE": "paper",
        "ALPACA_BASE_URL": "https://paper-api.alpaca.markets",
        "ALPACA_API_KEY": "paper-key",
        "ALPACA_API_SECRET": "paper-secret",
    }


def test_paper_submission_guard_passes_for_fresh_matching_selected_dry_run(tmp_path: Path) -> None:
    now = datetime.now(timezone.utc)
    out_root = tmp_path / "paper_broker"
    intent = PaperBrokerOrderIntent(tracking_id="track-submit-pass", symbol="SPY", side="buy", qty=1.0)
    _, _, selection = write_paper_execution_intent_selection_artifact(
        intent,
        output_root=out_root,
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
        output_root=out_root,
        generated_at_utc=now,
        source_selection_artifact_sha256=selection.artifact_sha256,
    )

    guard = build_paper_submission_guard_snapshot(intent=intent, env=_paper_env(), output_root=out_root, evaluated_at_utc=now)

    assert guard.status == "PASS"
    assert guard.evidence_freshness_status == "FRESH"
    assert guard.submission_intent_matches_selection is True
    assert guard.linked_dry_run_matches_selection is True
    assert guard.linked_dry_run_ok is True
    assert guard.blockers == []


def test_paper_submission_guard_blocks_stale_or_mismatched_evidence(tmp_path: Path) -> None:
    now = datetime.now(timezone.utc)
    out_root = tmp_path / "paper_broker"
    selected = PaperBrokerOrderIntent(tracking_id="track-submit-block", symbol="QQQ", side="sell", qty=0.5)
    submitted = PaperBrokerOrderIntent(tracking_id="track-submit-block", symbol="SPY", side="sell", qty=0.5)
    _, _, selection = write_paper_execution_intent_selection_artifact(
        selected,
        output_root=out_root,
        generated_at_utc=now - timedelta(hours=30),
    )
    result = PaperBrokerOrderResult(
        ok=True,
        policy_status=PaperBrokerPolicyStatus.PAPER_READY,
        dry_run=True,
        retrieved_at_utc=now - timedelta(hours=13),
    )
    write_paper_order_dry_run_artifact(
        selected,
        result,
        output_root=out_root,
        generated_at_utc=now - timedelta(hours=13),
        source_selection_artifact_sha256=selection.artifact_sha256,
    )

    guard = build_paper_submission_guard_snapshot(intent=submitted, env=_paper_env(), output_root=out_root, evaluated_at_utc=now)

    assert guard.status == "BLOCKED"
    assert guard.evidence_freshness_status == "STALE"
    assert "SUBMISSION_INTENT_MISMATCH_SELECTED_INTENT" in guard.blockers
    assert "SELECTED_INTENT_STALE" in guard.blockers
    assert "LINKED_DRY_RUN_STALE" in guard.blockers
