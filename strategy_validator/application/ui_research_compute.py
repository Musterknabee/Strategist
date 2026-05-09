"""Read-plane summary payload for optional research compute acceleration."""
from __future__ import annotations

import hashlib
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.research_compute.gpu_probe import probe_gpu_capability


def _artifact_root(root: str | Path | None = None) -> Path:
    if root is not None and str(root).strip():
        return Path(root)
    raw = os.environ.get("STRATEGY_VALIDATOR_ARTIFACT_ROOT", "").strip()
    if raw:
        return Path(raw)
    return Path.cwd() / "artifacts"


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _file_sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _read_last_benchmark(root: Path) -> dict[str, Any] | None:
    p = root / "research_compute" / "benchmark.json"
    data = _read_json(p)
    if data is None:
        return None
    data["_artifact_path"] = str(p.as_posix())
    data["_artifact_sha256"] = _file_sha256(p)
    return data


def _as_text(value: object) -> str:
    return str(value or "").strip()


def _as_list(value: object) -> list[str]:
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if str(item).strip()]
    return []


def _norm_set(values: tuple[str, ...] | list[str] | None) -> set[str]:
    return {str(v).strip().lower() for v in (values or ()) if str(v).strip()}


def _contains(haystack: object, needle: str | None) -> bool:
    if not needle:
        return True
    return needle.strip().lower() in str(haystack or "").lower()


def _entry_from_result(path: Path, raw: dict[str, Any]) -> dict[str, Any]:
    warnings = _as_list(raw.get("warnings"))
    blockers = _as_list(raw.get("blockers"))
    return {
        "run_id": _as_text(raw.get("run_id")) or path.stem.replace(".result", ""),
        "strategy_id": _as_text(raw.get("strategy_id")) or None,
        "research_task_id": _as_text(raw.get("research_task_id")) or None,
        "pit_as_of_utc": _as_text(raw.get("pit_as_of_utc")) or None,
        "backend_requested": _as_text(raw.get("backend_requested")) or "UNKNOWN",
        "backend_used": _as_text(raw.get("backend_used")) or "UNKNOWN",
        "fallback_reason": _as_text(raw.get("fallback_reason")) or "UNKNOWN",
        "deterministic_seed": raw.get("deterministic_seed"),
        "started_at_utc": _as_text(raw.get("started_at_utc")) or None,
        "completed_at_utc": _as_text(raw.get("completed_at_utc")) or None,
        "duration_ms": raw.get("duration_ms"),
        "mean_return": raw.get("mean_return"),
        "std_return": raw.get("std_return"),
        "cvar_95": raw.get("cvar_95"),
        "max_drawdown_like": raw.get("max_drawdown_like"),
        "result_digest": _as_text(raw.get("result_digest")) or None,
        "artifact_path": str(path.as_posix()),
        "artifact_sha256": _file_sha256(path),
        "artifact_paths": _as_list(raw.get("artifact_paths")),
        "warning_count": len(warnings),
        "blocker_count": len(blockers),
        "warnings": warnings,
        "blockers": blockers,
    }


def _discover_results(root: Path) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    compute_root = root / "research_compute"
    if not compute_root.is_dir():
        return [], []
    entries: list[dict[str, Any]] = []
    invalid: list[dict[str, str]] = []
    for path in sorted(compute_root.glob("*.result.json")):
        raw = _read_json(path)
        if raw is None:
            invalid.append({"path": str(path.as_posix()), "reason": "invalid_json_or_not_object"})
            continue
        if raw.get("schema_version") != "research_compute_result/v1":
            invalid.append({"path": str(path.as_posix()), "reason": "unexpected_schema_version"})
            continue
        entries.append(_entry_from_result(path, raw))
    entries.sort(key=lambda e: str(e.get("completed_at_utc") or e.get("started_at_utc") or e.get("artifact_path") or ""), reverse=True)
    return entries, invalid


def _matches_entry(
    entry: dict[str, Any],
    *,
    backend_used: set[str],
    fallback_reason: set[str],
    strategy_id_contains: str | None,
    task_contains: str | None,
    warning_contains: str | None,
    blocker_contains: str | None,
) -> bool:
    if backend_used and str(entry.get("backend_used") or "").lower() not in backend_used:
        return False
    if fallback_reason and str(entry.get("fallback_reason") or "").lower() not in fallback_reason:
        return False
    if not _contains(entry.get("strategy_id"), strategy_id_contains):
        return False
    task_haystack = " ".join([str(entry.get("research_task_id") or ""), str(entry.get("run_id") or "")])
    if not _contains(task_haystack, task_contains):
        return False
    if warning_contains and not any(_contains(w, warning_contains) for w in _as_list(entry.get("warnings"))):
        return False
    if blocker_contains and not any(_contains(b, blocker_contains) for b in _as_list(entry.get("blockers"))):
        return False
    return True


def _counts(entries: list[dict[str, Any]], field: str) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for entry in entries:
        counter[str(entry.get(field) or "UNKNOWN")] += 1
    return dict(sorted(counter.items()))


def build_ui_research_compute_payload(
    *,
    artifact_root: str | Path | None = None,
    backend_used: tuple[str, ...] = (),
    fallback_reason: tuple[str, ...] = (),
    strategy_id_contains: str | None = None,
    task_contains: str | None = None,
    warning_contains: str | None = None,
    blocker_contains: str | None = None,
    limit: int = 200,
    include_raw: bool = False,
) -> dict[str, Any]:
    root = _artifact_root(artifact_root)
    probe = probe_gpu_capability()
    benchmark = _read_last_benchmark(root)
    results, invalid_artifacts = _discover_results(root)
    backend_filter = _norm_set(backend_used)
    fallback_filter = _norm_set(fallback_reason)
    filtered = [
        entry
        for entry in results
        if _matches_entry(
            entry,
            backend_used=backend_filter,
            fallback_reason=fallback_filter,
            strategy_id_contains=strategy_id_contains,
            task_contains=task_contains,
            warning_contains=warning_contains,
            blocker_contains=blocker_contains,
        )
    ]
    safe_limit = max(1, min(int(limit or 200), 1000))
    returned = filtered[:safe_limit]
    gpu_available = bool(probe.get("gpu_available"))
    readiness = "GPU_ACCELERATION_READY" if gpu_available else "CPU_FALLBACK_READY"
    fallback = probe.get("reason")
    if not gpu_available and fallback is None:
        fallback = "CUDA_UNAVAILABLE"
    if invalid_artifacts:
        readiness = "RESEARCH_COMPUTE_ARTIFACTS_DEGRADED"
    worker_model = benchmark.get("process_pool_workers") if isinstance(benchmark, dict) else None
    summary = {
        "artifact_root": str(root.as_posix()),
        "research_compute_root": str((root / "research_compute").as_posix()),
        "result_count_total": len(results),
        "result_count_filtered": len(filtered),
        "result_count_returned": len(returned),
        "invalid_artifact_count": len(invalid_artifacts),
        "backend_used_counts": _counts(filtered, "backend_used"),
        "fallback_reason_counts": _counts(filtered, "fallback_reason"),
        "warning_count": sum(int(e.get("warning_count") or 0) for e in filtered),
        "blocker_count": sum(int(e.get("blocker_count") or 0) for e in filtered),
        "gpu_result_count": sum(1 for e in filtered if str(e.get("backend_used") or "").lower() == "cuda"),
        "cpu_result_count": sum(1 for e in filtered if str(e.get("backend_used") or "").lower() == "cpu"),
        "latest_completed_at_utc": next((e.get("completed_at_utc") for e in filtered if e.get("completed_at_utc")), None),
    }
    return {
        "schema_version": "ui_research_compute/v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "read_plane_only": True,
        "advisory_only": True,
        "gpu_probe": probe,
        "last_benchmark": benchmark,
        "gpu_available": gpu_available,
        "cpu_fallback_status": "READY" if not gpu_available else "NOT_APPLICABLE",
        "fallback_reason": fallback,
        "research_compute_readiness": readiness,
        "last_worker_pool_workers": worker_model,
        "filters": {
            "backend_used": list(backend_used),
            "fallback_reason": list(fallback_reason),
            "strategy_id_contains": strategy_id_contains,
            "task_contains": task_contains,
            "warning_contains": warning_contains,
            "blocker_contains": blocker_contains,
            "limit": safe_limit,
            "include_raw": include_raw,
        },
        "summary": summary,
        "results": returned,
        "invalid_artifacts": invalid_artifacts[:50],
        "guardrails": [
            "read_plane_only_no_compute_execution",
            "advisory_only_no_promotion_authority",
            "gpu_probe_is_optional_and_non_blocking",
            "missing_cuda_degrades_to_cpu_fallback_not_startup_failure",
            "result_artifacts_are_operator_evidence_not_live_trading_claims",
        ],
    }


__all__ = ["build_ui_research_compute_payload"]
