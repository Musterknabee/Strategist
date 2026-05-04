"""Parameter sensitivity / fragility contracts (toy strategies; research)."""
from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class ParameterSensitivityGateStatus(str, Enum):
    STABLE = "STABLE"
    WARNING = "WARNING"
    FRAGILE = "FRAGILE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ParameterPerturbationResult(BaseModel):
    param_key: str
    base_value: Any
    perturbed_value: Any
    total_return: float
    sharpe_like: float

    model_config = {"extra": "forbid"}


class ParameterSensitivityResult(BaseModel):
    schema_version: Literal["strategy_parameter_sensitivity_result/v1"] = (
        "strategy_parameter_sensitivity_result/v1"
    )
    strategy_id: str
    batch_id: str
    run_id: str
    model_label: str = "TOY_PARAMETER_SENSITIVITY_MODEL"
    base_total_return: float = 0.0
    base_sharpe_like: float = 0.0
    perturbations: list[ParameterPerturbationResult] = Field(default_factory=list)
    median_perturbed_return: float = 0.0
    worst_perturbed_return: float = 0.0
    pct_positive_perturbations: float = 0.0
    gate_status: ParameterSensitivityGateStatus = ParameterSensitivityGateStatus.NOT_APPLICABLE
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    parameter_sensitivity_evidence_sha256: str = ""

    model_config = {"extra": "forbid"}


__all__ = [
    "ParameterPerturbationResult",
    "ParameterSensitivityGateStatus",
    "ParameterSensitivityResult",
]
