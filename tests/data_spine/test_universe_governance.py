import pytest
import pandas as pd
from datetime import datetime, timezone, timedelta
from strategy_validator.data_spine.universe.governance import PITUniverseGovernor
from strategy_validator.contracts.data_spine import UniverseProvenance

def test_universe_governance_excludes_invalid_assets():
    """
    UNIVERSE LAW: Assets not in universe at decision time must be excluded.
    """
    now = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)
    
    # Membership registry
    membership_df = pd.DataFrame([
        {"asset_id": "AAPL", "valid_from": now - timedelta(days=1), "valid_to": now + timedelta(days=1)},
        {"asset_id": "TSLA", "valid_from": now - timedelta(days=1), "valid_to": now - timedelta(hours=1)},
        {"asset_id": "MSFT", "valid_from": now + timedelta(hours=1), "valid_to": now + timedelta(days=1)},
    ])
    
    # Input Observations
    obs_df = pd.DataFrame({"asset_id": ["AAPL", "TSLA", "MSFT"], "ret": [0.01, 0.02, 0.03]})
    
    governor = PITUniverseGovernor(universe_id="tech-250", snapshot_hash="snap-123")
    
    # EXECUTE
    filtered, prov = governor.filter_df_to_universe(obs_df, membership_df, now)
    
    # VERIFY
    assert len(filtered) == 1
    assert filtered.iloc[0]["asset_id"] == "AAPL"
    
    # Provenance Audit
    assert prov.member_count == 1
    membership_map = {m.asset_id: m.is_member for m in prov.memberships}
    assert membership_map["AAPL"] is True
    assert membership_map["TSLA"] is False
    assert membership_map["MSFT"] is False

def test_universe_change_flips_audit_fingerprint():
    """
    Ensures that different universe memberships yield different forensic seals.
    """
    from strategy_validator.data_spine.path_gen import LawfulPathGenerator
    from strategy_validator.contracts.data_spine import PITJoinProvenance
    
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    governor = PITUniverseGovernor(universe_id="u1", snapshot_hash="h1")
    gen = LawfulPathGenerator(n_folds=2, test_folds_per_path=1) # Minimal folds
    
    membership_a = pd.DataFrame([{"asset_id": "AAPL", "valid_from": now - timedelta(days=1), "valid_to": now + timedelta(days=1)}])
    membership_b = pd.DataFrame(columns=["asset_id", "valid_from", "valid_to"])
    
    # Use 2 observations so folds can be formed
    obs_a = pd.DataFrame({"asset_id": ["AAPL", "AAPL"], "ret": [0.01, 0.02]})
    obs_b = pd.DataFrame({"asset_id": ["AAPL", "AAPL"], "ret": [0.01, 0.02]})
    
    # Under membership_a, AAPL is kept. Under membership_b, AAPL is dropped.
    filtered_a, prov_a = governor.filter_df_to_universe(obs_a, membership_a, now)
    filtered_b, prov_b = governor.filter_df_to_universe(obs_b, membership_b, now)
    
    # Seal A has 2 obs. Seal B will have 0 obs if filtered, 
    # but generator requires positive n_observations.
    # So we'll keep obs_b but use different universe provenance.
    _, seal_a = gen.construct_cpcv_suite(filtered_a, [], universe_provenance=prov_a)
    _, seal_b = gen.construct_cpcv_suite(filtered_a, [], universe_provenance=prov_b)
    
    assert seal_a.fingerprint != seal_b.fingerprint

if __name__ == "__main__":
    pytest.main([__file__])
