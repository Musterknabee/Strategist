import pandas as pd
import pytest

from strategy_validator.data_spine.joins.as_of import AsOfJoinEngine


def test_future_leakage_is_blocked_by_available_at_gate() -> None:
    decisions = pd.DataFrame(
        {"symbol": ["A"], "decision_at": [pd.Timestamp("2024-01-01T10:00:00Z")]}
    )
    features = pd.DataFrame(
        {
            "symbol": ["A", "A"],
            "available_at": [
                pd.Timestamp("2024-01-01T09:59:00Z"),
                pd.Timestamp("2024-01-01T10:00:01Z"),
            ],
            "feature_value": [10.0, 999.0],
        }
    )
    out, _ = AsOfJoinEngine(
        decision_time_col="decision_at",
        available_at_col="available_at",
        group_keys=["symbol"],
    ).execute(decisions, features)
    assert float(out.iloc[0]["feature_value"]) == 10.0


def test_deterministic_revision_selection_latest() -> None:
    decisions = pd.DataFrame(
        {"symbol": ["A"], "decision_at": [pd.Timestamp("2024-01-01T10:00:00Z")]}
    )
    features = pd.DataFrame(
        {
            "symbol": ["A", "A"],
            "available_at": [
                pd.Timestamp("2024-01-01T09:59:00Z"),
                pd.Timestamp("2024-01-01T09:59:00Z"),
            ],
            "revision": [1, 2],
            "feature_value": [10.0, 20.0],
        }
    )
    out, _ = AsOfJoinEngine(
        decision_time_col="decision_at",
        available_at_col="available_at",
        group_keys=["symbol"],
        revision_col="revision",
        revision_selection="latest_revision",
    ).execute(decisions, features)
    assert float(out.iloc[0]["feature_value"]) == 20.0


def test_deterministic_revision_selection_earliest() -> None:
    decisions = pd.DataFrame(
        {"symbol": ["A"], "decision_at": [pd.Timestamp("2024-01-01T10:00:00Z")]}
    )
    features = pd.DataFrame(
        {
            "symbol": ["A", "A"],
            "available_at": [
                pd.Timestamp("2024-01-01T09:59:00Z"),
                pd.Timestamp("2024-01-01T09:59:00Z"),
            ],
            "revision": [1, 2],
            "feature_value": [10.0, 20.0],
        }
    )
    out, _ = AsOfJoinEngine(
        decision_time_col="decision_at",
        available_at_col="available_at",
        group_keys=["symbol"],
        revision_col="revision",
        revision_selection="earliest_revision",
    ).execute(decisions, features)
    assert float(out.iloc[0]["feature_value"]) == 10.0


def test_revision_tie_requires_explicit_policy() -> None:
    decisions = pd.DataFrame(
        {"symbol": ["A"], "decision_at": [pd.Timestamp("2024-01-01T10:00:00Z")]}
    )
    features = pd.DataFrame(
        {
            "symbol": ["A", "A"],
            "available_at": [
                pd.Timestamp("2024-01-01T09:59:00Z"),
                pd.Timestamp("2024-01-01T09:59:00Z"),
            ],
            "feature_value": [1.0, 2.0],
        }
    )
    with pytest.raises(ValueError, match="Revision ties detected"):
        AsOfJoinEngine(
            decision_time_col="decision_at",
            available_at_col="available_at",
            group_keys=["symbol"],
        ).execute(decisions, features)


def test_timezone_must_be_explicit_utc() -> None:
    decisions = pd.DataFrame({"symbol": ["A"], "decision_at": [pd.Timestamp("2024-01-01 10:00:00")]})
    features = pd.DataFrame(
        {"symbol": ["A"], "available_at": [pd.Timestamp("2024-01-01T09:59:00Z")], "feature_value": [1.0]}
    )
    with pytest.raises(ValueError, match="naive datetimes are rejected"):
        AsOfJoinEngine(
            decision_time_col="decision_at",
            available_at_col="available_at",
            group_keys=["symbol"],
        ).execute(decisions, features)


def test_non_utc_timezone_is_rejected() -> None:
    decisions = pd.DataFrame({"symbol": ["A"], "decision_at": [pd.Timestamp("2024-01-01T10:00:00", tz="Europe/Berlin")]})
    features = pd.DataFrame(
        {
            "symbol": ["A"],
            "available_at": [pd.Timestamp("2024-01-01T09:59:00Z")],
            "feature_value": [1.0],
        }
    )
    with pytest.raises(ValueError, match="only UTC storage is allowed"):
        AsOfJoinEngine(
            decision_time_col="decision_at",
            available_at_col="available_at",
            group_keys=["symbol"],
        ).execute(decisions, features)


def test_non_utc_available_at_is_rejected() -> None:
    decisions = pd.DataFrame({"symbol": ["A"], "decision_at": [pd.Timestamp("2024-01-01T10:00:00Z")]})
    features = pd.DataFrame(
        {
            "symbol": ["A"],
            "available_at": [pd.Timestamp("2024-01-01T09:59:00", tz="Europe/Berlin")],
            "feature_value": [1.0],
        }
    )
    with pytest.raises(ValueError, match="only UTC storage is allowed"):
        AsOfJoinEngine(
            decision_time_col="decision_at",
            available_at_col="available_at",
            group_keys=["symbol"],
        ).execute(decisions, features)


def test_macro_embargo_blocks_recent_macro_release() -> None:
    decisions = pd.DataFrame(
        {"symbol": ["A"], "decision_at": [pd.Timestamp("2024-01-01T10:00:00Z")]}
    )
    features = pd.DataFrame(
        {
            "symbol": ["A", "A"],
            "available_at": [
                pd.Timestamp("2024-01-01T09:59:30Z"),
                pd.Timestamp("2024-01-01T09:58:00Z"),
            ],
            "feature_value": [99.0, 1.0],
        }
    )
    out, _ = AsOfJoinEngine(
        decision_time_col="decision_at",
        available_at_col="available_at",
        group_keys=["symbol"],
        feature_kind="macro",
        macro_embargo_ms=120000,
    ).execute(decisions, features)
    assert float(out.iloc[0]["feature_value"]) == 1.0


def test_latency_buffer_blocks_nearby_available_feature() -> None:
    decisions = pd.DataFrame(
        {"symbol": ["A"], "decision_at": [pd.Timestamp("2024-01-01T10:00:00Z")]}
    )
    features = pd.DataFrame(
        {
            "symbol": ["A", "A"],
            "available_at": [
                pd.Timestamp("2024-01-01T09:59:45Z"),
                pd.Timestamp("2024-01-01T09:59:20Z"),
            ],
            "feature_value": [9.0, 1.0],
        }
    )
    out, _ = AsOfJoinEngine(
        decision_time_col="decision_at",
        available_at_col="available_at",
        group_keys=["symbol"],
        latency_buffer_ms=30000,
    ).execute(decisions, features)
    assert float(out.iloc[0]["feature_value"]) == 1.0


def test_macro_embargo_is_ignored_for_standard_features() -> None:
    decisions = pd.DataFrame(
        {"symbol": ["A"], "decision_at": [pd.Timestamp("2024-01-01T10:00:00Z")]}
    )
    features = pd.DataFrame(
        {
            "symbol": ["A"],
            "available_at": [pd.Timestamp("2024-01-01T09:59:30Z")],
            "feature_value": [7.0],
        }
    )
    out, _ = AsOfJoinEngine(
        decision_time_col="decision_at",
        available_at_col="available_at",
        group_keys=["symbol"],
        feature_kind="standard",
        macro_embargo_ms=120000,
    ).execute(decisions, features)
    assert float(out.iloc[0]["feature_value"]) == 7.0


def test_pit_purges_target_rows_without_eligible_feature() -> None:
    decisions = pd.DataFrame(
        {"symbol": ["A", "B"], "decision_at": [pd.Timestamp("2024-01-01T10:00:00Z"), pd.Timestamp("2024-01-01T10:00:00Z")]}
    )
    features = pd.DataFrame(
        {
            "symbol": ["A", "B"],
            "available_at": [pd.Timestamp("2024-01-01T09:59:00Z"), pd.Timestamp("2024-01-01T10:01:00Z")],
            "feature_value": [1.0, 2.0],
        }
    )
    out, _ = AsOfJoinEngine(
        decision_time_col="decision_at",
        available_at_col="available_at",
        group_keys=["symbol"],
    ).execute(decisions, features)
    assert len(out) == 1
    assert out.iloc[0]["symbol"] == "A"


def test_negative_latency_buffer_is_rejected() -> None:
    decisions = pd.DataFrame({"symbol": ["A"], "decision_at": [pd.Timestamp("2024-01-01T10:00:00Z")]})
    features = pd.DataFrame(
        {"symbol": ["A"], "available_at": [pd.Timestamp("2024-01-01T09:59:00Z")], "feature_value": [1.0]}
    )
    with pytest.raises(ValueError, match="non-negative"):
        AsOfJoinEngine(
            decision_time_col="decision_at",
            available_at_col="available_at",
            group_keys=["symbol"],
            latency_buffer_ms=-1,
        ).execute(decisions, features)


def test_invalid_feature_kind_is_rejected() -> None:
    decisions = pd.DataFrame({"symbol": ["A"], "decision_at": [pd.Timestamp("2024-01-01T10:00:00Z")]})
    features = pd.DataFrame(
        {"symbol": ["A"], "available_at": [pd.Timestamp("2024-01-01T09:59:00Z")], "feature_value": [1.0]}
    )
    with pytest.raises(ValueError, match="feature_kind must be"):
        AsOfJoinEngine(
            decision_time_col="decision_at",
            available_at_col="available_at",
            group_keys=["symbol"],
            feature_kind="invalid",  # type: ignore[arg-type]
        ).execute(decisions, features)


def test_missing_required_column_is_rejected() -> None:
    decisions = pd.DataFrame({"symbol": ["A"], "decision_at": [pd.Timestamp("2024-01-01T10:00:00Z")]})
    features = pd.DataFrame({"symbol": ["A"], "feature_value": [1.0]})
    with pytest.raises(KeyError, match="missing required columns"):
        AsOfJoinEngine(
            decision_time_col="decision_at",
            available_at_col="available_at",
            group_keys=["symbol"],
        ).execute(decisions, features)





def test_empty_group_keys_are_rejected() -> None:
    decisions = pd.DataFrame({"decision_at": [pd.Timestamp("2024-01-01T10:00:00Z")]})
    features = pd.DataFrame(
        {
            "available_at": [pd.Timestamp("2024-01-01T09:59:00Z")],
            "feature_value": [5.0],
        }
    )
    with pytest.raises(ValueError, match="group_keys must not be empty"):
        AsOfJoinEngine(
            decision_time_col="decision_at",
            available_at_col="available_at",
            group_keys=[],
        ).execute(decisions, features)


def test_duplicate_group_keys_are_rejected() -> None:
    decisions = pd.DataFrame(
        {"symbol": ["A"], "decision_at": [pd.Timestamp("2024-01-01T10:00:00Z")]}
    )
    features = pd.DataFrame(
        {
            "symbol": ["A"],
            "available_at": [pd.Timestamp("2024-01-01T09:59:00Z")],
            "feature_value": [5.0],
        }
    )
    with pytest.raises(ValueError, match="duplicates"):
        AsOfJoinEngine(
            decision_time_col="decision_at",
            available_at_col="available_at",
            group_keys=["symbol", "symbol"],
        ).execute(decisions, features)


def test_revision_selection_requires_revision_column_when_ties_exist() -> None:
    decisions = pd.DataFrame(
        {"symbol": ["A"], "decision_at": [pd.Timestamp("2024-01-01T10:00:00Z")]}
    )
    features = pd.DataFrame(
        {
            "symbol": ["A", "A"],
            "available_at": [pd.Timestamp("2024-01-01T09:59:00Z"), pd.Timestamp("2024-01-01T09:59:00Z")],
            "feature_value": [1.0, 2.0],
        }
    )
    with pytest.raises(ValueError, match="Revision ties detected"):
        AsOfJoinEngine(
            decision_time_col="decision_at",
            available_at_col="available_at",
            group_keys=["symbol"],
            revision_selection="earliest_revision",
        ).execute(decisions, features)
