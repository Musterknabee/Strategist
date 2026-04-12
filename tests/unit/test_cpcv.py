import pytest

from strategy_validator.contracts.evidence import Evidence
from strategy_validator.core.enums import EvidenceType
from strategy_validator.validator.robustness.cpcv import evaluate_cpcv_hook, generate_cpcv_paths


def _ev(**payload) -> Evidence:
    return Evidence(
        evidence_id="c1",
        experiment_id="EXP-C",
        evidence_type=EvidenceType.COST_SUMMARY,
        payload=payload,
        source_module="tests",
        checksum="c" * 64,
    )


def test_generate_cpcv_paths_produces_multiple_non_overlapping_paths() -> None:
    splits = generate_cpcv_paths(
        n_observations=100,
        n_folds=5,
        test_folds_per_path=2,
        purge_observations=2,
        embargo_observations=3,
    )
    assert len(splits) >= 2
    for train_idx, test_idx in splits:
        assert train_idx
        assert test_idx
        assert set(train_idx).isdisjoint(set(test_idx))


def test_generate_cpcv_paths_applies_purge_and_embargo_windows() -> None:
    paths = generate_cpcv_paths(
        n_observations=30,
        n_folds=5,
        test_folds_per_path=1,
        purge_observations=2,
        embargo_observations=2,
    )
    for train_idx, test_idx in paths:
        lo = min(test_idx)
        hi = max(test_idx)
        forbidden = set(range(max(0, lo - 2), min(30, hi + 3)))
        assert forbidden.isdisjoint(set(train_idx))


def test_evaluate_cpcv_hook_from_returns_path() -> None:
    returns = [0.001] * 60 + [0.002] * 60
    result = evaluate_cpcv_hook(
        [_ev(returns=returns, cpcv_folds=4, cpcv_test_folds_per_path=2, cpcv_purge_observations=1, cpcv_embargo_observations=1)]
    )
    assert result.folds is not None and result.folds >= 2
    assert result.path_coverage is not None
    assert result.passed is True


def test_cpcv_invalid_fold_count_fails() -> None:
    with pytest.raises(ValueError, match="at least 2"):
        generate_cpcv_paths(
            n_observations=20,
            n_folds=1,
            test_folds_per_path=1,
            purge_observations=0,
            embargo_observations=0,
        )


def test_cpcv_invalid_test_folds_per_path_fails() -> None:
    with pytest.raises(ValueError, match="test_folds_per_path"):
        generate_cpcv_paths(
            n_observations=20,
            n_folds=4,
            test_folds_per_path=4,
            purge_observations=0,
            embargo_observations=0,
        )


def test_cpcv_explicit_payload_is_reflected() -> None:
    result = evaluate_cpcv_hook(
        [_ev(cpcv_passed=True, cpcv_folds=5, cpcv_path_coverage=0.9, cpcv_path_stability=0.2)]
    )
    assert result.passed is True
    assert result.folds == 5
    assert result.path_coverage == 0.9
    assert result.path_stability == 0.2


def test_cpcv_returns_path_with_invalid_config_fails() -> None:
    result = evaluate_cpcv_hook(
        [_ev(returns=[0.01] * 10, cpcv_folds=1, cpcv_test_folds_per_path=1)]
    )
    assert result.passed is False
    assert result.path_coverage == 0.0


def test_cpcv_fold_sharpes_with_single_fold_fails() -> None:
    result = evaluate_cpcv_hook([_ev(cpcv_fold_sharpes=[0.2])])
    assert result.passed is False
    assert result.folds == 1


def test_cpcv_explicit_payload_invalid_coverage_fails() -> None:
    result = evaluate_cpcv_hook(
        [_ev(cpcv_passed=True, cpcv_folds=4, cpcv_path_coverage=1.2, cpcv_path_stability=0.1)]
    )
    assert result.passed is False


def test_cpcv_explicit_payload_invalid_stability_fails() -> None:
    result = evaluate_cpcv_hook(
        [_ev(cpcv_passed=True, cpcv_folds=4, cpcv_path_coverage=0.9, cpcv_path_stability=-0.1)]
    )
    assert result.passed is False


def test_cpcv_explicit_payload_preserves_fold_count_for_structural_checks() -> None:
    result = evaluate_cpcv_hook(
        [_ev(cpcv_passed=True, cpcv_folds=1, cpcv_path_coverage=0.9, cpcv_path_stability=0.1)]
    )
    assert result.passed is True
    assert result.folds == 1
