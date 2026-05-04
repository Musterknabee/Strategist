from __future__ import annotations

import pytest
from pydantic import ValidationError

from strategy_validator.contracts.strategy_robustness import (
    DSR_LIKE_MODEL_LABEL,
    PBO_LIKE_MODEL_LABEL,
    ROBUSTNESS_MODEL_LABEL,
    RobustnessAssumptions,
    RobustnessGateStatus,
    RobustnessResult,
    WalkForwardFoldResult,
)


def test_enum_values_stable() -> None:
    assert RobustnessGateStatus.PROVEN.value == "PROVEN"
    assert RobustnessGateStatus.WARNING.value == "WARNING"
    assert RobustnessGateStatus.BLOCKED.value == "BLOCKED"
    assert RobustnessGateStatus.NOT_APPLICABLE.value == "NOT_APPLICABLE"


def test_model_labels() -> None:
    assert ROBUSTNESS_MODEL_LABEL == "WALK_FORWARD_LOCAL_BAR_MODEL"
    assert DSR_LIKE_MODEL_LABEL == "DSR_LIKE_HEURISTIC"
    assert PBO_LIKE_MODEL_LABEL == "PBO_LIKE_HEURISTIC"


def test_assumptions_defaults_and_validation() -> None:
    a = RobustnessAssumptions()
    assert a.fold_count == 4
    assert a.min_train_bars == 20
    with pytest.raises(ValidationError):
        RobustnessAssumptions(fold_count=1)
    with pytest.raises(ValidationError):
        RobustnessAssumptions(min_positive_fold_ratio=1.1)
    with pytest.raises(ValidationError):
        RobustnessAssumptions(max_worst_fold_return=0.01)
    RobustnessAssumptions(min_dsr_like_score=-1.0)
    RobustnessAssumptions(min_dsr_like_score=1.0)


def test_robustness_result_serialization_roundtrip() -> None:
    r = RobustnessResult(
        strategy_id="s",
        batch_id="b",
        run_id="r",
        sample_count=10,
        fold_count=2,
        robustness_evidence_sha256="abc",
    )
    d = r.model_dump(mode="json")
    r2 = RobustnessResult.model_validate(d)
    assert r2.strategy_id == "s"
    assert r2.robustness_evidence_sha256 == "abc"
    assert r2.model_label == ROBUSTNESS_MODEL_LABEL


def test_walk_forward_fold_requires_fields() -> None:
    with pytest.raises(ValidationError):
        WalkForwardFoldResult.model_validate({"fold_index": 0})


def test_robustness_result_rejects_extra_keys() -> None:
    with pytest.raises(ValidationError):
        RobustnessResult.model_validate(
            {
                "strategy_id": "s",
                "batch_id": "b",
                "run_id": "r",
                "extra_field": 1,
            }
        )
