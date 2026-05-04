from __future__ import annotations

from pathlib import Path

from strategy_validator.application.paper_execution_cockpit import build_ui_paper_execution_cockpit_payload
from strategy_validator.application.paper_execution_intent_selection import write_paper_execution_intent_selection_artifact
from strategy_validator.application.paper_execution_journal import write_paper_order_dry_run_artifact
from strategy_validator.contracts.paper_broker import PaperBrokerOrderIntent, PaperBrokerOrderResult, PaperBrokerPolicyStatus


def test_cockpit_marks_selected_intent_dry_run_replay_match(monkeypatch, tmp_path: Path) -> None:
    art = tmp_path / "artifacts"
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(art))
    intent = PaperBrokerOrderIntent(tracking_id="track-replay1", symbol="QQQ", side="sell", qty=0.5)
    _, _, selection = write_paper_execution_intent_selection_artifact(
        intent,
        strategy_id="strategy-qqq",
        output_root=art / "paper_broker",
    )
    result = PaperBrokerOrderResult(
        ok=False,
        policy_status=PaperBrokerPolicyStatus.PENDING_KEY,
        dry_run=True,
        blockers=["ALPACA_KEYS_MISSING"],
    )
    write_paper_order_dry_run_artifact(
        intent,
        result,
        output_root=art / "paper_broker",
        source_selection_artifact_sha256=selection.artifact_sha256,
    )

    payload = build_ui_paper_execution_cockpit_payload(repo_root=tmp_path)

    assert payload["summary"]["selected_intent_dry_run_status"] == "MATCHED"
    assert payload["summary"]["selected_intent_dry_run_match"] is True
    assert payload["summary"]["latest_dry_run_source_selection_sha256"] == selection.artifact_sha256
    assert payload["journal_entries"][0]["source_selection_artifact_sha256"] == selection.artifact_sha256
    assert "dry-run-selected-intent" not in "\n".join(payload["recommended_actions"])


def test_cockpit_flags_selected_intent_without_linked_replay(monkeypatch, tmp_path: Path) -> None:
    art = tmp_path / "artifacts"
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(art))
    intent = PaperBrokerOrderIntent(tracking_id="track-replay2", symbol="SPY", side="buy", qty=1.0)
    write_paper_execution_intent_selection_artifact(intent, output_root=art / "paper_broker")

    payload = build_ui_paper_execution_cockpit_payload(repo_root=tmp_path)

    assert payload["summary"]["selected_intent_dry_run_status"] == "NO_DRY_RUN"
    assert payload["summary"]["selected_intent_dry_run_match"] is None
    assert "dry-run-selected-intent" in "\n".join(payload["recommended_actions"])
