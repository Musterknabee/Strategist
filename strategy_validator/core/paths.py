from __future__ import annotations

import itertools
from typing import List, Tuple


def _fold_bounds(n_observations: int, n_folds: int) -> list[tuple[int, int]]:
    fold_size = max(1, n_observations // n_folds)
    out: list[tuple[int, int]] = []
    for i in range(n_folds):
        start = i * fold_size
        end = n_observations if i == n_folds - 1 else min(n_observations, (i + 1) * fold_size)
        if start < end:
            out.append((start, end))
    return out


def generate_cpcv_paths(
    *,
    n_observations: int,
    n_folds: int,
    test_folds_per_path: int,
    purge_observations: int,
    embargo_observations: int,
) -> list[tuple[list[int], list[int]]]:
    """
    True Combinatorial Purged Cross-Validation path generation logic.
    Centralized in core to satisfy boundary law while remaining executable.
    """
    if n_observations <= 0:
        raise ValueError("n_observations must be positive")
    if n_folds < 2:
        raise ValueError("n_folds must be at least 2")
    if test_folds_per_path < 1 or test_folds_per_path >= n_folds:
        raise ValueError("test_folds_per_path must be in [1, n_folds-1]")

    bounds = _fold_bounds(n_observations, n_folds)
    paths: list[tuple[list[int], list[int]]] = []
    for fold_combo in itertools.combinations(range(len(bounds)), test_folds_per_path):
        test_ranges = [bounds[i] for i in fold_combo]
        test_idx = sorted({j for a, b in test_ranges for j in range(a, b)})
        blocked = [False] * n_observations
        for a, b in test_ranges:
            left = max(0, a - purge_observations)
            right = min(n_observations, b + embargo_observations)
            for j in range(left, right):
                blocked[j] = True
        train_idx = [j for j in range(n_observations) if not blocked[j]]
        if train_idx and test_idx:
            paths.append((train_idx, test_idx))
    return paths
