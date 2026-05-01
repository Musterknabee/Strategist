from __future__ import annotations

from datetime import datetime, timezone

import pytest

from strategy_validator.contracts.strategy_data_snapshot import (
    StrategyBar,
    StrategyDataSnapshot,
    StrategyDataSnapshotManifest,
    StrategyDataSourceClassification,
    StrategyPitSnapshotStatus,
    snapshot_data_gates_promotion,
    snapshot_promotion_eligible_data_plane,
)
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256


def _snap(**over) -> StrategyDataSnapshot:
    base = dict(
        strategy_id="s",
        batch_id="b",
        universe="U",
        timeframe="1d",
        as_of_utc=datetime(2026, 5, 1, tzinfo=timezone.utc),
        lookback_start_utc=datetime(2026, 1, 1, tzinfo=timezone.utc),
        lookback_end_utc=datetime(2026, 5, 1, tzinfo=timezone.utc),
        pit_status=StrategyPitSnapshotStatus.PIT_VERIFIED,
        retrieved_at_utc=datetime(2026, 5, 1, tzinfo=timezone.utc),
        published_at_utc=datetime(2026, 5, 1, tzinfo=timezone.utc),
        bars_path="tests/fixtures/x.csv",
        bars_sha256="abc",
        row_count=10,
        symbol_count=1,
        warnings=[],
        blockers=[],
        may_gate_live_promotion=False,
    )
    base.update(over)
    return StrategyDataSnapshot(**base)


def test_strategy_bar_rejects_naive_timestamp() -> None:
    with pytest.raises(ValueError):
        StrategyBar(
            symbol="D",
            timestamp_utc=datetime(2026, 1, 1),
            open=1,
            high=1,
            low=1,
            close=1,
        )


def test_manifest_roundtrip_json_keys() -> None:
    snap = _snap()
    m = StrategyDataSnapshotManifest(strategy_id="s", batch_id="b", run_id="r", snapshot=snap)
    raw = m.model_dump(mode="json")
    m2 = StrategyDataSnapshotManifest.model_validate(raw)
    assert m2.snapshot.bars_sha256 == snap.bars_sha256


def test_digest_stable_for_snapshot_payload() -> None:
    s1 = _snap(bars_sha256="deadbeef")
    s2 = _snap(bars_sha256="deadbeef")
    assert s1.model_dump(mode="json") == s2.model_dump(mode="json")
    assert canonical_json_sha256(s1.model_dump(mode="json")) == canonical_json_sha256(s2.model_dump(mode="json"))


def test_missing_pit_blocks_promotion() -> None:
    s = _snap(pit_status=StrategyPitSnapshotStatus.BLOCKED_NO_PIT, blockers=["NO_PIT"])
    assert snapshot_data_gates_promotion(s) is True
    assert snapshot_promotion_eligible_data_plane(s) is False


def test_synthetic_not_promotable() -> None:
    s = _snap(pit_status=StrategyPitSnapshotStatus.SYNTHETIC_DEMO)
    assert snapshot_data_gates_promotion(s) is True
    assert snapshot_promotion_eligible_data_plane(s) is False


def test_verified_clean_eligible_data_plane() -> None:
    s = _snap(
        pit_status=StrategyPitSnapshotStatus.PIT_VERIFIED,
        warnings=[],
        blockers=[],
        source_classification=StrategyDataSourceClassification.LOCAL_GOVERNED_BARS,
    )
    s = s.model_copy(update={"may_gate_live_promotion": snapshot_data_gates_promotion(s)})
    assert snapshot_promotion_eligible_data_plane(s) is True


def test_verified_with_warnings_not_eligible() -> None:
    s = _snap(pit_status=StrategyPitSnapshotStatus.PIT_VERIFIED, warnings=["W"])
    assert snapshot_data_gates_promotion(s) is True
    assert snapshot_promotion_eligible_data_plane(s) is False
