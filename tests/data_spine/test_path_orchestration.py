import pytest
import pandas as pd
from datetime import datetime, timezone
from strategy_validator.data_spine.path_gen import LawfulPathGenerator
from strategy_validator.contracts.data_spine import PITJoinProvenance

def test_combinatorial_path_determinism_with_seal():
    """
    PATH REPRODUCIBILITY: identical returns and PIT history must yield identical audit seals.
    """
    generator = LawfulPathGenerator(
        n_folds=3, 
        test_folds_per_path=1, 
        purge_observations=0, 
        embargo_observations=0
    )
    
    returns_df = pd.DataFrame({"r": [0.01, -0.01, 0.02, 0.005]})
    prov = [
        PITJoinProvenance(
            dataset_id="p1", 
            decision_time_utc=datetime(2026, 1, 1, tzinfo=timezone.utc),
            available_at_cutoff_utc=datetime(2026, 1, 1, tzinfo=timezone.utc),
            revision_policy="none:latest",
            latency_buffer_ms=0,
            macro_embargo_ms=0,
            row_count_before=10,
            row_count_after=5
        )
    ]
    
    paths1, seal1 = generator.construct_cpcv_suite(returns_df, prov)
    paths2, seal2 = generator.construct_cpcv_suite(returns_df, prov)
    
    # 1. Determinism
    assert seal1.fingerprint == seal2.fingerprint
    assert len(paths1) == 3 # Combinations(3, 1) = 3
    
    print(f"Audit Fingerprint: {seal1.fingerprint[:12]}")
    
    # 2. Tamper evidence (Changing folds changes fingerprint)
    gen_strict = LawfulPathGenerator(n_folds=4)
    _, seal_strict = gen_strict.construct_cpcv_suite(returns_df, prov)
    assert seal_strict.fingerprint != seal1.fingerprint

if __name__ == "__main__":
    pytest.main([__file__])
