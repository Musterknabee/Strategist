"""Fail if canonical contract modules cannot be imported (baseline wiring)."""


def test_contract_modules_importable() -> None:
    import strategy_validator.contracts.benchmarks as b  # noqa: F401
    import strategy_validator.contracts.evidence as e  # noqa: F401
    import strategy_validator.contracts.experiments as x  # noqa: F401
    import strategy_validator.contracts.tribunal as t  # noqa: F401

    assert hasattr(x, "ExperimentManifest")
    assert hasattr(e, "Evidence")
    assert hasattr(t, "TribunalOpinion")
    assert hasattr(b, "BenchmarkResult")
