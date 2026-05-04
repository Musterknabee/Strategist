"""Benchmark-context gate evaluation for the adjudication orchestrator."""

from __future__ import annotations

from collections.abc import Iterable

from strategy_validator.contracts.benchmarks import BENCHMARK_RUNG_REGISTRY, validate_benchmark_observation
from strategy_validator.contracts.evidence import Evidence
from strategy_validator.contracts.experiments import ExperimentManifest, GateResult


def evaluate_benchmark_context_gate(manifest: ExperimentManifest, evidence: Iterable[Evidence]) -> GateResult:
    """Validate manifest/evidence benchmark identifiers before performance evaluation."""
    rung_id = manifest.evidence_bundle.benchmark_rung

    if rung_id not in BENCHMARK_RUNG_REGISTRY:
        return GateResult(
            gate_name="BenchmarkContext",
            passed=False,
            reason="UNKNOWN_BENCHMARK_RUNG",
            note=f"Rung '{rung_id}' not found in registry.",
        )

    if not validate_benchmark_observation(
        benchmark_rung=rung_id,
        benchmark_version=manifest.evidence_bundle.reproducibility.benchmark_version,
        observed_benchmark_id=None,
    ):
        return GateResult(
            gate_name="BenchmarkContext",
            passed=False,
            reason="MANIFEST_VERSION_MISMATCH",
            note="Manifest benchmark version does not match registry for this rung.",
        )

    for ev in evidence:
        payload = ev.payload
        if "benchmark_id" not in payload:
            continue
        if not validate_benchmark_observation(
            benchmark_rung=rung_id,
            benchmark_version=payload.get(
                "benchmark_version",
                manifest.evidence_bundle.reproducibility.benchmark_version,
            ),
            observed_benchmark_id=payload["benchmark_id"],
        ):
            return GateResult(
                gate_name="BenchmarkContext",
                passed=False,
                reason="BENCHMARK_ID_MISMATCH",
                note=(
                    f"Evidence benchmark {payload['benchmark_id']} "
                    f"(v{payload.get('benchmark_version')}) mismatches rung {rung_id}"
                ),
            )

    return GateResult(gate_name="BenchmarkContext", passed=True)


# Compatibility alias for callers that still use the private historical name.
_evaluate_benchmark_context = evaluate_benchmark_context_gate
