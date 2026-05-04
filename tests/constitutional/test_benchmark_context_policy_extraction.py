from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ORCHESTRATOR_DIR = ROOT / "strategy_validator" / "validator" / "orchestrator"


def test_benchmark_context_policy_owns_benchmark_registry_validation() -> None:
    policy_source = (ORCHESTRATOR_DIR / "benchmark_context_policy.py").read_text(encoding="utf-8")
    evidence_gates_source = (ORCHESTRATOR_DIR / "evidence_gates.py").read_text(encoding="utf-8")
    orchestrator_source = (ORCHESTRATOR_DIR / "__init__.py").read_text(encoding="utf-8")

    assert "BENCHMARK_RUNG_REGISTRY" in policy_source
    assert "validate_benchmark_observation" in policy_source
    assert "evaluate_benchmark_context_gate" in orchestrator_source
    assert "BENCHMARK_RUNG_REGISTRY" not in evidence_gates_source
    assert "validate_benchmark_observation" not in evidence_gates_source


def test_evidence_gates_stays_bounded_after_policy_extractions() -> None:
    source = (ORCHESTRATOR_DIR / "evidence_gates.py").read_text(encoding="utf-8")

    assert len(source.splitlines()) <= 130
    assert "def _evaluate_benchmark_context" not in source
