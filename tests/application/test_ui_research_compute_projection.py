from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.application.ui_research_compute import build_ui_research_compute_payload


def _write_result(root: Path, *, run_id: str, strategy_id: str, backend_used: str, fallback_reason: str, warnings: list[str] | None = None, blockers: list[str] | None = None) -> None:
    d = root / "research_compute"
    d.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "research_compute_result/v1",
        "run_id": run_id,
        "strategy_id": strategy_id,
        "research_task_id": f"task-{run_id}",
        "input_manifest_digest": "i" * 64,
        "provider_evidence_digest": "p" * 64,
        "pit_as_of_utc": "2026-05-06T00:00:00+00:00",
        "backend_requested": "auto",
        "backend_used": backend_used,
        "fallback_reason": fallback_reason,
        "device_info": {"backend": "cpu_numpy"},
        "deterministic_seed": 7,
        "started_at_utc": "2026-05-06T00:00:00+00:00",
        "completed_at_utc": "2026-05-06T00:00:01+00:00",
        "duration_ms": 1,
        "mean_return": 0.1,
        "std_return": 0.2,
        "cvar_95": -0.3,
        "max_drawdown_like": -0.4,
        "result_digest": "r" * 64,
        "artifact_paths": [],
        "warnings": warnings or [],
        "blockers": blockers or [],
    }
    (d / f"{run_id}.result.json").write_text(json.dumps(payload), encoding="utf-8")


def test_research_compute_payload_discovers_and_filters_results(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        "strategy_validator.application.ui_research_compute.probe_gpu_capability",
        lambda: {"gpu_available": False, "torch_available": False, "reason": "GPU_UNAVAILABLE_CPU_FALLBACK"},
    )
    _write_result(tmp_path, run_id="cpu-a", strategy_id="alpha", backend_used="cpu", fallback_reason="TORCH_NOT_INSTALLED")
    _write_result(tmp_path, run_id="cuda-b", strategy_id="beta", backend_used="cuda", fallback_reason="NONE", warnings=["cuda_warmup"])

    payload = build_ui_research_compute_payload(artifact_root=tmp_path, backend_used=("cuda",), warning_contains="warmup")

    assert payload["schema_version"] == "ui_research_compute/v1"
    assert payload["read_plane_only"] is True
    assert payload["advisory_only"] is True
    assert payload["summary"]["result_count_total"] == 2
    assert payload["summary"]["result_count_filtered"] == 1
    assert payload["summary"]["gpu_result_count"] == 1
    assert payload["results"][0]["run_id"] == "cuda-b"
    assert payload["guardrails"]


def test_research_compute_payload_reports_invalid_artifacts(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        "strategy_validator.application.ui_research_compute.probe_gpu_capability",
        lambda: {"gpu_available": True, "torch_available": True, "cuda_available": True},
    )
    d = tmp_path / "research_compute"
    d.mkdir()
    (d / "bad.result.json").write_text("{not-json", encoding="utf-8")

    payload = build_ui_research_compute_payload(artifact_root=tmp_path)

    assert payload["research_compute_readiness"] == "RESEARCH_COMPUTE_ARTIFACTS_DEGRADED"
    assert payload["summary"]["invalid_artifact_count"] == 1
    assert payload["invalid_artifacts"][0]["reason"] == "invalid_json_or_not_object"
