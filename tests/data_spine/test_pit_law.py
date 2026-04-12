import pytest
import pandas as pd
from datetime import datetime, timezone, timedelta
from strategy_validator.data_spine.joins.as_of import AsOfJoinEngine
from strategy_validator.contracts.data_spine import PITJoinProvenance

def test_pit_join_refuses_future_data():
    """
    PIT LAW: Joins must refuse data whose available_at is later than the cutoff.
    """
    now = datetime.now(timezone.utc).replace(microsecond=0)
    
    # Target: observations at T and T+1
    target_df = pd.DataFrame({
        "asset": ["AAPL", "AAPL"],
        "dt": [now, now + timedelta(minutes=1)]
    })
    
    # Features: T-based but one row is "available" ONLY at T+2 (Future Leakage)
    feature_df = pd.DataFrame({
        "asset": ["AAPL", "AAPL"],
        "price": [100.0, 105.0],
        "avail": [now - timedelta(minutes=1), now + timedelta(minutes=2)]
    })
    
    engine = AsOfJoinEngine(
        decision_time_col="dt",
        available_at_col="avail",
        group_keys=["asset"],
        latency_buffer_ms=0
    )
    
    # EXECUTE
    result, prov = engine.execute(target_df, feature_df, dataset_id="pricing_p50")
    
    # VERIFY
    # The first target (T) finds the T-1 price.
    # The second target (T+1) STILL only finds the T-1 price, because T+2 is forbidden.
    assert len(result) == 2
    assert all(result["price"] == 100.0)
    assert prov.row_count_before == 2
    assert prov.row_count_after == 2
    
    print(f"PIT Cutoff enforced: {prov.available_at_cutoff_utc}")

def test_revision_selection_is_deterministic():
    """
    REVISION LAW: Choosing 'earliest' vs 'latest' must be deterministic.
    """
    now = datetime.now(timezone.utc).replace(microsecond=0)
    target_df = pd.DataFrame({"asset": ["AAPL"], "dt": [now]})
    
    # Two revisions available at the same time
    feature_df = pd.DataFrame({
        "asset": ["AAPL", "AAPL"],
        "signal": [0.5, 0.8],
        "avail": [now - timedelta(minutes=1), now - timedelta(minutes=1)],
        "rev": [1, 2]
    })
    
    # Case A: Latest revision
    engine_latest = AsOfJoinEngine(
        decision_time_col="dt", available_at_col="avail", group_keys=["asset"],
        revision_col="rev", revision_selection="latest_revision"
    )
    res_latest, _ = engine_latest.execute(target_df, feature_df)
    assert res_latest.iloc[0]["signal"] == 0.8
    
    # Case B: Earliest revision
    engine_earliest = AsOfJoinEngine(
        decision_time_col="dt", available_at_col="avail", group_keys=["asset"],
        revision_col="rev", revision_selection="earliest_revision"
    )
    res_earliest, _ = engine_earliest.execute(target_df, feature_df)
    assert res_earliest.iloc[0]["signal"] == 0.5

def test_embargo_window_prevents_unlawful_inclusion():
    """
    EMBARGO LAW: Macro embargo ensures data is only available after a delay.
    """
    now = datetime.now(timezone.utc).replace(microsecond=0)
    target_df = pd.DataFrame({"asset": ["AAPL"], "dt": [now]})
    
    # Feature available at T-500ms
    feature_df = pd.DataFrame({
        "asset": ["AAPL"],
        "macro": [1.0],
        "avail": [now - timedelta(milliseconds=500)]
    })
    
    # Engine with 1000ms embargo
    engine = AsOfJoinEngine(
        decision_time_col="dt", available_at_col="avail", group_keys=["asset"],
        feature_kind="macro", macro_embargo_ms=1000
    )
    
    result, prov = engine.execute(target_df, feature_df)
    
    # Should find nothing because (now - 1000ms) < (now - 500ms)
    assert len(result) == 0
    assert prov.available_at_cutoff_utc < now

if __name__ == "__main__":
    pytest.main([__file__])
