from __future__ import annotations

import itertools
import math
import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Iterable, Iterator

from strategy_validator.contracts.evidence import Evidence
from strategy_validator.core.paths import generate_cpcv_paths


@dataclass(frozen=True)
class CPCVEvaluation:
    passed: bool | None
    folds: int | None
    path_coverage: float | None
    path_stability: float | None


class PurgedEmbargoTimeSeriesSplitter:
    def __init__(
        self, 
        n_splits: int = 5, 
        purge_days: int = 2, 
        embargo_days: int = 5
    ):
        self.n_splits = n_splits
        self.purge_days = purge_days
        self.embargo_days = embargo_days

    def split(self, X: pd.DataFrame) -> Iterator[tuple[np.ndarray, np.ndarray]]:
        if not isinstance(X.index, pd.DatetimeIndex):
            raise ValueError("X must have a pandas DatetimeIndex.")
        if not X.index.is_monotonic_increasing:
            X = X.sort_index()
        indices = np.arange(len(X))
        test_size = len(X) // self.n_splits
        for i in range(self.n_splits):
            test_start = i * test_size
            test_end = (i + 1) * test_size if i < self.n_splits - 1 else len(X)
            test_indices = indices[test_start:test_end]
            if len(test_indices) == 0:
                continue
            test_times = X.index[test_indices]
            t0, t1 = test_times[0], test_times[-1]
            purge_cutoff = t0 - pd.Timedelta(days=self.purge_days)
            embargo_cutoff = t1 + pd.Timedelta(days=self.embargo_days)
            train_indices = []
            for idx in indices:
                if idx in test_indices:
                    continue
                t = X.index[idx]
                if t < t0 and t > purge_cutoff:
                    continue
                if t > t1 and t < embargo_cutoff:
                    continue
                train_indices.append(idx)
            yield np.array(train_indices), test_indices


def _annualized_sharpe(returns: list[float]) -> float:
    if len(returns) < 2:
        return 0.0
    mean = sum(returns) / len(returns)
    var = sum((x - mean) ** 2 for x in returns) / (len(returns) - 1)
    std = math.sqrt(var)
    if std == 0.0:
        return 0.0
    return (mean / std) * math.sqrt(252.0)


def evaluate_cpcv_hook(evidence: Iterable[Evidence]) -> CPCVEvaluation:
    """Orchestrates CPCV evaluation from evidence payloads with strict boundary validation."""
    for ev in evidence:
        # Task 6: Direct metadata support (without returns)
        if "cpcv_passed" in ev.payload:
            passed = bool(ev.payload["cpcv_passed"])
            folds = int(ev.payload.get("cpcv_folds", 0) or 0) or None
            coverage = float(ev.payload.get("cpcv_path_coverage", 0.0))
            stability = float(ev.payload.get("cpcv_path_stability", 0.0))
            
            # Basic range validation
            if coverage < 0.0 or coverage > 1.0 or (stability is not None and stability < 0.0):
                passed = False
            
            return CPCVEvaluation(
                passed=passed,
                folds=folds,
                path_coverage=coverage,
                path_stability=stability
            )

        # Support for pre-computed fold sharpes (Task 6)
        if "cpcv_fold_sharpes" in ev.payload:
            fold_sharpes = [float(s) for s in ev.payload["cpcv_fold_sharpes"]]
            folds = len(fold_sharpes)
            positives = [s for s in fold_sharpes if s >= 0]
            coverage = len(positives) / folds if folds > 0 else 0.0
            
            # Task 6: Single fold cannot pass CPCV
            return CPCVEvaluation(
                passed=(coverage >= 1.0 and folds >= 2),
                folds=folds,
                path_coverage=coverage,
                path_stability=None
            )

        if "returns" in ev.payload and "cpcv_folds" in ev.payload:
            returns = [float(v) for v in ev.payload["returns"]]
            folds = int(ev.payload["cpcv_folds"])
            test_folds = int(ev.payload.get("cpcv_test_folds_per_path", 1))
            purge = int(ev.payload.get("cpcv_purge_observations", 0))
            embargo = int(ev.payload.get("cpcv_embargo_observations", 0))
            min_sharpe = float(ev.payload.get("cpcv_min_path_sharpe", 0.0))
            
            try:
                paths = generate_cpcv_paths(
                    n_observations=len(returns),
                    n_folds=folds,
                    test_folds_per_path=test_folds,
                    purge_observations=purge,
                    embargo_observations=embargo,
                )
            except ValueError:
                return CPCVEvaluation(False, folds, 0.0, None)
                
            path_sharpes = [_annualized_sharpe([returns[i] for i in test_idx]) for _, test_idx in paths]
            positives = [s for s in path_sharpes if s >= min_sharpe]
            
            coverage = len(positives) / len(path_sharpes) if paths else 0.0
            mean = sum(path_sharpes) / len(path_sharpes) if paths else 0.0
            variance = sum((s - mean) ** 2 for s in path_sharpes) / max(1, len(path_sharpes) - 1) if len(paths) > 1 else 0.0
            
            return CPCVEvaluation(
                passed=(coverage >= 1.0), # Strict pass only if all paths pass
                folds=folds,
                path_coverage=coverage,
                path_stability=math.sqrt(variance),
            )
    return CPCVEvaluation(None, None, None, None)
