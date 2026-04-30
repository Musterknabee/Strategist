from __future__ import annotations

from typing import Dict, Optional

from pydantic import BaseModel


class BenchmarkTarget(BaseModel):
    benchmark_id: str
    name: str
    target_metric: str
    minimum_threshold: float
    is_absolute: bool

    model_config = {"extra": "forbid"}


class BenchmarkResult(BaseModel):
    benchmark_id: str
    experiment_id: str
    rung_id: str
    raw_strategy_metric: float
    benchmark_metric: float
    excess_metric: float  # Pre-cost
    post_cost_excess_metric: Optional[float] = None
    evaluation_horizon: str  # e.g., "3y", "full-sample"
    passed: bool
    failure_reason: Optional[str] = None
    confidence_note: Optional[str] = None

    model_config = {"extra": "forbid"}


class BenchmarkRung(BaseModel):
    rung_id: str
    benchmark_id: str
    description: str
    minimum_delta: float
    benchmark_version: str

    model_config = {"extra": "forbid"}


BENCHMARK_RUNG_REGISTRY: Dict[str, BenchmarkRung] = {
    "L1": BenchmarkRung(
        rung_id="L1",
        benchmark_id="SPY",
        description="US large-cap equity baseline",
        minimum_delta=0.01,
        benchmark_version="bench-v1",
    ),
    "core-equity": BenchmarkRung(
        rung_id="core-equity",
        benchmark_id="SPY",
        description="Core equity benchmark rung",
        minimum_delta=0.0,
        benchmark_version="v1",
    ),
}


def validate_benchmark_observation(
    *,
    benchmark_rung: str,
    benchmark_version: str,
    observed_benchmark_id: str | None,
) -> bool:
    rung = BENCHMARK_RUNG_REGISTRY.get(benchmark_rung)
    if rung is None:
        return False
    if benchmark_version != rung.benchmark_version:
        return False
    if observed_benchmark_id is None:
        return True
    return observed_benchmark_id == rung.benchmark_id
