import pytest
import pandas as pd
from datetime import datetime, timezone, timedelta
from strategy_validator.data_spine.joins.as_of import AsOfJoinEngine

def test_revision_lineage_captures_discarded_candidates():
    """
    LINEAGE LAW: Selected vs Discarded revisions must be explicitly recorded.
    """
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    target_df = pd.DataFrame({"asset_id": ["AAPL"], "dt": [now]})
    
    # Three revisions available at the same time
    feature_df = pd.DataFrame({
        "asset_id": ["AAPL"] * 3,
        "signal": [0.1, 0.5, 0.9],
        "avail": [now - timedelta(minutes=1)] * 3,
        "rev": ["v1", "v2", "v3"] # Sorted latest is v3
    })
    
    engine = AsOfJoinEngine(
        decision_time_col="dt", available_at_col="avail", group_keys=["asset_id"],
        revision_col="rev", revision_selection="latest_revision"
    )
    
    # EXECUTE
    result, prov = engine.execute(target_df, feature_df, dataset_id="alpha_signals")
    
    # VERIFY
    assert result.iloc[0]["signal"] == 0.9
    
    # Lineage Audit
    lineage = prov.lineage
    assert lineage is not None
    assert lineage.selected_revision_id == "v3"
    assert "v1" in lineage.discarded_revision_ids
    assert "v2" in lineage.discarded_revision_ids
    assert lineage.revision_policy == "latest_revision"
    assert "Tie-break" in lineage.selection_reason

if __name__ == "__main__":
    pytest.main([__file__])
