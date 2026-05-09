from __future__ import annotations

import ast
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RESEARCH = REPO / "strategy_validator" / "research"


def _module(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


def _function_names(path: Path) -> set[str]:
    return {node.name for node in _module(path).body if isinstance(node, ast.FunctionDef)}


def test_strategy_batch_runner_is_public_facade() -> None:
    path = RESEARCH / "strategy_batch_runner.py"
    text = path.read_text(encoding="utf-8")

    assert len(text.splitlines()) <= 90
    assert _function_names(path) == {"run_single_strategy", "run_strategy_batch"}
    assert "ThreadPoolExecutor" not in text
    assert "ProcessPoolExecutor" not in text
    assert "evaluate_strategy_robustness" not in text
    assert "load_local_bars_snapshot" not in text


def test_strategy_batch_runner_phase_modules_own_expected_responsibilities() -> None:
    expected = {
        "strategy_batch_runner_common.py": {
            "_resolve_output_base",
            "_run_id_for_batch",
            "_resolve_batch_run_directory",
            "_assert_path_under",
            "_prepare_run_directory",
            "_write_json",
            "_write_filtered_bars_csv",
            "_enrich_metrics",
            "_promotion_state",
        },
        "strategy_batch_runner_single.py": {"run_single_strategy_impl"},
        "strategy_batch_runner_single_data.py": {
            "_bar_arrays",
            "_blocked_result",
            "_write_data_snapshot_manifest",
            "resolve_single_strategy_data",
        },
        "strategy_batch_runner_single_gates.py": {
            "evaluate_single_strategy_gates",
        },
        "strategy_batch_runner_single_artifacts.py": {
            "emit_single_strategy_artifacts",
        },
        "strategy_batch_runner_batch.py": {"_process_pool_run_single", "run_strategy_batch_impl"},
    }

    for filename, required_functions in expected.items():
        assert required_functions <= _function_names(RESEARCH / filename)


def test_legacy_strategy_batch_runner_exports_remain_stable() -> None:
    import strategy_validator.research.strategy_batch_runner as runner

    assert hasattr(runner, "run_single_strategy")
    assert hasattr(runner, "run_strategy_batch")
    assert hasattr(runner, "deterministic_prices")


def test_strategy_batch_runner_single_data_plane_is_extracted() -> None:
    single = (RESEARCH / "strategy_batch_runner_single.py").read_text(encoding="utf-8")
    data = (RESEARCH / "strategy_batch_runner_single_data.py").read_text(encoding="utf-8")

    assert len(single.splitlines()) <= 700
    assert "load_local_bars_snapshot" not in single
    assert "load_provider_snapshot_bars" not in single
    assert "StrategyDataSnapshotManifest" not in single
    assert "deterministic_prices(" not in single

    assert "load_local_bars_snapshot" in data
    assert "load_provider_snapshot_bars" in data
    assert "StrategyDataSnapshotManifest" in data
    assert "StrategySingleDataContext" in data


def test_strategy_batch_runner_single_gate_plane_is_extracted() -> None:
    single = (RESEARCH / "strategy_batch_runner_single.py").read_text(encoding="utf-8")
    gates = (RESEARCH / "strategy_batch_runner_single_gates.py").read_text(encoding="utf-8")
    data_metrics = (RESEARCH / "strategy_batch_runner_single_data_metrics.py").read_text(encoding="utf-8")
    robustness = (RESEARCH / "strategy_batch_runner_single_robustness.py").read_text(encoding="utf-8")
    diagnostics = (RESEARCH / "strategy_batch_runner_single_diagnostics.py").read_text(encoding="utf-8")
    gate_types = (RESEARCH / "strategy_batch_runner_single_gate_types.py").read_text(encoding="utf-8")

    assert len(single.splitlines()) <= 260
    assert len(gates.splitlines()) <= 120
    assert "evaluate_local_bars_data_quality" not in single
    assert "evaluate_market_data_integrity" not in single
    assert "evaluate_strategy_robustness" not in single
    assert "evaluate_parameter_sensitivity" not in single
    assert "evaluate_regime_analysis" not in single

    assert "StrategySingleGateEvaluation" in gate_types
    assert "evaluate_single_strategy_data_metrics" in gates
    assert "evaluate_single_strategy_robustness" in gates
    assert "evaluate_single_strategy_diagnostics" in gates
    assert "evaluate_local_bars_data_quality" in data_metrics
    assert "evaluate_market_data_integrity" in data_metrics
    assert "evaluate_strategy_robustness" in robustness
    assert "evaluate_parameter_sensitivity" in diagnostics
    assert "evaluate_regime_analysis" in diagnostics


def test_strategy_batch_runner_single_gate_phase_modules_own_expected_responsibilities() -> None:
    expected = {
        "strategy_batch_runner_single_gate_types.py": {"StrategySingleGateEvaluation"},
        "strategy_batch_runner_single_data_metrics.py": {
            "StrategySingleDataMetricEvaluation",
            "evaluate_single_strategy_data_metrics",
        },
        "strategy_batch_runner_single_robustness.py": {
            "StrategySingleRobustnessEvaluation",
            "evaluate_single_strategy_robustness",
        },
        "strategy_batch_runner_single_diagnostics.py": {
            "StrategySingleDiagnosticEvaluation",
            "evaluate_single_strategy_diagnostics",
        },
    }

    for filename, required in expected.items():
        module = _module(RESEARCH / filename)
        names = {
            node.name
            for node in module.body
            if isinstance(node, (ast.FunctionDef, ast.ClassDef))
        }
        assert required <= names


def test_strategy_batch_runner_single_artifact_plane_is_extracted() -> None:
    single = (RESEARCH / "strategy_batch_runner_single.py").read_text(encoding="utf-8")
    artifacts = (RESEARCH / "strategy_batch_runner_single_artifacts.py").read_text(encoding="utf-8")

    assert len(single.splitlines()) <= 260
    assert "build_chart_artifacts" not in single
    assert "StrategyEvidenceManifest" not in single
    assert "strategy_scorecard_sha256" not in single

    assert "StrategySingleArtifacts" in artifacts
    assert "build_chart_artifacts" in artifacts
    assert "StrategyEvidenceManifest" in artifacts
    assert "emit_single_strategy_artifacts" in artifacts
