from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
from dataclasses import dataclass

@dataclass(frozen=True)
class IncrementalityResult:
    """
    Result of orthogonalized incrementality testing. 
    NOTE: This measures statistical edge relative to nuisance variables; 
    it does not constitute a proof of causal effect.
    """
    p_value: float
    coefficient: float
    is_significant: bool

def calculate_orthogonal_incrementality(
    target: pd.Series,
    proposed_feature: pd.Series,
    nuisance_variables: pd.DataFrame,
    significance_level: float = 0.05
) -> IncrementalityResult:
    """
    Calculates the statistical edge of a proposed feature after orthogonalizing 
    it against known nuisance (risk/control) variables.
    
    This uses a residual-on-residual approach to isolate the feature's 
    independent contribution.
    """
    # 1. Coordinate indices
    valid_nuisance = nuisance_variables.dropna()
    common_indices = valid_nuisance.index.intersection(target.dropna().index)
    
    if len(common_indices) < 2:
        return IncrementalityResult(p_value=1.0, coefficient=0.0, is_significant=False)
        
    y = target.loc[common_indices]
    X_nuisance = sm.add_constant(valid_nuisance.loc[common_indices])
    
    # Step 1: Residualize Target against Nuisance
    model_y = sm.OLS(y, X_nuisance).fit()
    target_residuals = model_y.resid

    # Step 2: Residualize Feature against Nuisance
    feature_indices = common_indices.intersection(proposed_feature.dropna().index)
    if len(feature_indices) < 2:
        return IncrementalityResult(p_value=1.0, coefficient=0.0, is_significant=False)
    
    f = proposed_feature.loc[feature_indices]
    X_nuisance_f = sm.add_constant(valid_nuisance.loc[feature_indices])
    
    model_f = sm.OLS(f, X_nuisance_f).fit()
    feature_residuals = model_f.resid

    # Step 3: Orthogonal Regression (Residual-on-Residual)
    y_res = target_residuals.loc[feature_indices]
    model_res = sm.OLS(y_res, feature_residuals).fit()
    
    try:
        # P-value for the orthogonalized feature
        p_val = float(model_res.pvalues.iloc[0])
        coef = float(model_res.params.iloc[0])
    except (IndexError, AttributeError):
        p_val = 1.0
        coef = 0.0

    return IncrementalityResult(
        p_value=p_val,
        coefficient=coef,
        is_significant=bool(p_val < significance_level)
    )
