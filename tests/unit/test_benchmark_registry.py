from strategy_validator.contracts.benchmarks import validate_benchmark_observation


def test_validate_benchmark_observation_accepts_matching_context() -> None:
    assert (
        validate_benchmark_observation(
            benchmark_rung="L1",
            benchmark_version="bench-v1",
            observed_benchmark_id="SPY",
        )
        is True
    )


def test_validate_benchmark_observation_rejects_mismatched_benchmark_id() -> None:
    assert (
        validate_benchmark_observation(
            benchmark_rung="L1",
            benchmark_version="bench-v1",
            observed_benchmark_id="QQQ",
        )
        is False
    )
