from __future__ import annotations

import math


def estimate_dsr(
    *,
    observed_sharpe: float,
    num_trials: int,
    sample_size: int,
    skewness: float = 0.0,
    kurtosis: float = 3.0,
) -> float:
    """
    Deflated Sharpe Ratio approximation (Bailey/Prado-style approximation).
    """
    trials = max(1, num_trials)
    n = max(2, sample_size)
    
    sigma_sr = math.sqrt((1.0 - skewness * observed_sharpe + ((kurtosis - 1.0) / 4.0) * observed_sharpe**2) / (n - 1))
    sigma_sr = max(1e-12, sigma_sr)
    
    if trials <= 1:
        sr_star = 0.0
    else:
        gamma = 0.5772156649
        z_max = ((1.0 - gamma) * _norm_ppf(1.0 - (1.0 / trials))) + (gamma * _norm_ppf(1.0 - (1.0 / (trials * math.e))))
        sr_star = sigma_sr * z_max
    
    return (observed_sharpe - sr_star) / sigma_sr


def estimate_pbo(*, train_sharpes: list[float], test_sharpes: list[float]) -> float:
    """
    Probability of Backtest Overfitting approximation from train/test ranking mismatch.
    Returns 1.0 if best IS strategy performs poorly in OOS ranking (Overfit), 0.0 otherwise.
    """
    if not train_sharpes or not test_sharpes or len(train_sharpes) != len(test_sharpes):
        raise ValueError("train_sharpes and test_sharpes must be non-empty and equal length")
    n = len(train_sharpes)
    best_train_idx = max(range(n), key=lambda i: train_sharpes[i])
    sorted_test = sorted(test_sharpes, reverse=True)
    rank = sorted_test.index(test_sharpes[best_train_idx]) + 1
    w = rank / (n + 1.0)
    
    if w <= 0.0 or w >= 1.0:
        return 1.0
        
    logit_w = math.log(w / (1.0 - w))
    
    # Standard logic: if logit(rank_ratio) is positive (rank > 0.5), PBO is high.
    return 1.0 if logit_w > 0 else 0.0


def _norm_ppf(p: float) -> float:
    # Acklam rational approximation
    if p <= 0.0 or p >= 1.0:
        raise ValueError("p must be in (0,1)")
    a = [-3.969683028665376e01, 2.209460984245205e02, -2.759285104469687e02, 1.383577518672690e02, -3.066479806614716e01, 2.506628277459239e00]
    b = [-5.447609879822406e01, 1.615858368580409e02, -1.556989798598866e02, 6.680131188771972e01, -1.328068155288572e01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e00, -2.549732539343734e00, 4.374664141464968e00, 2.938163982698783e00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e00, 3.754408661907416e00]
    plow = 0.02425
    phigh = 1 - plow
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    if phigh < p:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    q = p - 0.5
    r = q * q
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)
