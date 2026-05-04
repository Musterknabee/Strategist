from __future__ import annotations

from pathlib import Path

from strategy_validator.contracts.research_compute import ComputeBackend, ComputeFallbackReason, ResearchComputeRequest
from strategy_validator.research_compute.monte_carlo import run_research_compute_demo


def _req(run_id: str, backend: ComputeBackend = ComputeBackend.AUTO) -> ResearchComputeRequest:
    return ResearchComputeRequest(
        run_id=run_id,
        strategy_id="s1",
        research_task_id="t1",
        input_manifest_digest="in-digest",
        provider_evidence_digest="provider-digest",
        pit_as_of_utc="2026-01-01T00:00:00+00:00",
        backend_requested=backend,
        deterministic_seed=123,
        paths=8000,
        steps=64,
    )


def test_cpu_deterministic_outputs(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(tmp_path))
    a = run_research_compute_demo(_req("run-a", ComputeBackend.CPU))
    b = run_research_compute_demo(_req("run-b", ComputeBackend.CPU))
    assert a.backend_used == ComputeBackend.CPU
    assert b.backend_used == ComputeBackend.CPU
    assert a.mean_return == b.mean_return
    assert a.cvar_95 == b.cvar_95
    assert len(a.artifact_paths) == 2
    assert (tmp_path / "research_compute" / "run-a.result.json").is_file()


def test_auto_falls_back_to_cpu_when_torch_missing(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(tmp_path))
    import importlib

    monkeypatch.setattr(importlib, "import_module", lambda _name: (_ for _ in ()).throw(ModuleNotFoundError("torch")))
    out = run_research_compute_demo(_req("run-fallback", ComputeBackend.AUTO))
    assert out.backend_used == ComputeBackend.CPU
    assert out.fallback_reason == ComputeFallbackReason.TORCH_NOT_INSTALLED


def test_research_compute_module_does_not_import_ledger_writer() -> None:
    import strategy_validator.research_compute.monte_carlo as mod

    src = Path(mod.__file__).read_text(encoding="utf-8")
    assert "ledger.writer" not in src
