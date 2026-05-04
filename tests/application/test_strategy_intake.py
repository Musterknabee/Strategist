from __future__ import annotations

from pathlib import Path

from strategy_validator.application.strategy_intake import (
    build_ui_strategy_intake_latest_payload,
    strategy_intake_root_directory,
    submit_strategy_intake,
)
from strategy_validator.contracts.strategy_intake import StrategyIntakeRequest


def test_strategy_intake_writes_artifact_and_index(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(tmp_path / "artifacts"))

    receipt = submit_strategy_intake(
        StrategyIntakeRequest(
            strategy_name="Opening Range Breakout",
            thesis="Trade post-open expansion only after provider freshness is verified.",
            target_universe="DAX futures",
            intended_horizon="intraday",
            expected_edge="Volatility expansion after compressed open range.",
            data_dependencies=("minute_bars", "calendar"),
            falsification_rules=("kill if slippage doubles expected edge",),
            risk_assumptions=("single position per symbol",),
            tags=("family:breakout", "paper-first"),
            idempotency_key="intake-1",
        )
    )

    assert receipt.accepted is True
    assert receipt.authority_boundary == "ADVISORY_ARTIFACT_ONLY"
    assert receipt.promotion_authority == "NONE"
    assert Path(receipt.artifact_path).is_file()
    assert Path(receipt.index_path).is_file()

    payload = build_ui_strategy_intake_latest_payload()
    assert payload["schema_version"] == "ui_strategy_intake/v1"
    assert payload["latest"]["intake_count"] == 1
    entry = payload["latest"]["entries"][0]
    assert entry["proposal_id"] == receipt.proposal_id
    assert entry["strategy_name"] == "Opening Range Breakout"


def test_strategy_intake_idempotency_replays_existing_artifact(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    request = StrategyIntakeRequest(
        strategy_name="Mean Reversion",
        thesis="Fade stretched basket moves after PIT-safe signal confirmation.",
        target_universe="SP500",
        intended_horizon="swing",
        expected_edge="Temporary flow dislocation normalizes within two sessions.",
        idempotency_key="same-intake",
    )

    first = submit_strategy_intake(request)
    second = submit_strategy_intake(request)

    assert first.idempotency_status == "RECORDED"
    assert second.idempotency_status == "REPLAYED"
    assert second.intake_id == first.intake_id
    assert second.artifact_sha256 == first.artifact_sha256
    assert strategy_intake_root_directory().is_dir()
