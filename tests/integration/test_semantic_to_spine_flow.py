import pandas as pd
import numpy as np
import pytest
from datetime import datetime, timezone

from strategy_validator.feature_factory.semantic.adapter import adapt_tribunal_to_feature_row
from strategy_validator.tribunal.constraints import FeatureFactoryArtifact
from strategy_validator.data_spine.joins.as_of import AsOfJoinEngine

def test_abstention_to_as_of_join_flow():
    """
    Integration test: Verifies that a Tribunal abstention propagates NaNs into the join engine.
    """
    # 1. Mock a Tribunal output with abstain_flag = True
    abstain_artifact = FeatureFactoryArtifact(
        event_id="evt-hallucinated-8k",
        forensic_status="adjudicated",
        novelty_score=0.9,
        polarity_score=0.1,
        belief_conflict=0.5,
        evidence_density=0.05, # Low evidence
        abstain_flag=True,     # PIPELINE OVERRIDE
        metadata={"reason": "forced_abstain_low_density"}
    )

    # 2. Extract metadata and adapt to row
    asset_id = "AAPL"
    published_at = pd.Timestamp("2024-01-01T10:00:00Z")
    available_at = pd.Timestamp("2024-01-01T10:05:00Z")
    
    feature_row = adapt_tribunal_to_feature_row(
        abstain_artifact,
        asset_id=asset_id,
        published_at=published_at,
        available_at=available_at
    )

    # 3. Create Feature DataFrame
    features_df = pd.DataFrame([feature_row])

    # 4. Create Decision/Target DataFrame (Backtest timestamps)
    # Target: 2024-01-01T10:10:00Z (Should pick up the semantic event)
    target_df = pd.DataFrame({
        "asset_id": ["AAPL"],
        "decision_at": [pd.Timestamp("2024-01-01T10:10:00Z")]
    })

    # 5. Execute As-Of Join
    engine = AsOfJoinEngine(
        decision_time_col="decision_at",
        available_at_col="available_at",
        group_keys=["asset_id"]
    )
    
    joined_df, provenance = engine.execute(target_df, features_df)

    # 6. Assertions: Prove contamination avoidance
    assert len(joined_df) == 1
    assert joined_df.loc[0, "asset_id"] == "AAPL"
    
    # RELENTLESS FACT: Hallucinated or weak evidence must be NaN
    assert np.isnan(joined_df.loc[0, "novelty_score"])
    assert np.isnan(joined_df.loc[0, "polarity_score"])
    assert np.isnan(joined_df.loc[0, "belief_conflict_score"])
    
    print("\n[SUCCESS] Abstention correctly yielded NaN in joined backtest state.")

if __name__ == "__main__":
    test_abstention_to_as_of_join_flow()
