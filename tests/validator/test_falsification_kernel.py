import numpy as np
import pandas as pd
import pytest
from strategy_validator.validator.robustness.incrementality import calculate_orthogonal_incrementality

def test_orthogonal_incrementality_rejects_correlated_mirage():
    """
    Adversarial test: 
    1. Feature is highly correlated with Target via a shared Nuisance (Market Beta).
    2. Feature has ZERO independent edge.
    3. Naive correlation should fail (look good), Orthogonal test should reject (p > 0.05).
    """
    np.random.seed(42)
    n = 1000
    
    # 1. Generate Nuisance (Market Beta)
    market_beta = np.random.normal(0, 1, n)
    
    # 2. Target: 90% Beta, 10% Noise
    target = 0.9 * market_beta + 0.1 * np.random.normal(0, 1, n)
    
    # 3. Proposed Feature: Correlated with Beta, but NO independent edge on Target
    proposed_feature = 0.8 * market_beta + 0.2 * np.random.normal(0, 1, n)
    
    # Put into pandas with nuisance metadata
    index = pd.date_range("2020-01-01", periods=n, freq="D")
    y = pd.Series(target, index=index)
    f = pd.Series(proposed_feature, index=index)
    nuisances = pd.DataFrame({"market_beta": market_beta}, index=index)
    
    # VALIDATION: Check naive correlation
    naive_corr = y.corr(f)
    print(f"\nNaive Correlation: {naive_corr:.4f}")
    assert naive_corr > 0.5  # It looks highly predictive!
    
    # EXECUTION: Apply Orthogonal Incrementality Filter
    result = calculate_orthogonal_incrementality(y, f, nuisances)
    
    print(f"p-value: {result.p_value:.4f}")
    print(f"Coefficient: {result.coefficient:.4f}")
    
    # ASSERTION: DML should see through the mirage
    assert result.p_value > 0.05
    assert result.is_significant is False

def test_incrementality_handles_nans_gracefully():
    """
    Check that NaNs in the proposed feature (from Tribunal abstentions) 
    do not crash the engine.
    """
    np.random.seed(42)
    n = 100
    market_beta = np.random.normal(0, 1, n)
    target = 0.5 * market_beta + np.random.normal(0, 1, n)
    proposed = 0.1 * market_beta + np.random.normal(0, 1, n)
    
    # Introduce NaNs (50% abstention rate)
    indices_to_nan = np.random.choice(n, size=n//2, replace=False)
    proposed[indices_to_nan] = np.nan
    
    index = pd.date_range("2020-01-01", periods=n, freq="D")
    y = pd.Series(target, index=index)
    f = pd.Series(proposed, index=index)
    nuisances = pd.DataFrame({"market_beta": market_beta}, index=index)
    
    result = calculate_orthogonal_incrementality(y, f, nuisances)
    assert isinstance(result.p_value, float)

if __name__ == "__main__":
    test_orthogonal_incrementality_rejects_correlated_mirage()
    test_incrementality_handles_nans_gracefully()
    print("\n[SUCCESS] Falsification Kernel validated against correlated mirages.")
