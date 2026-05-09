"""Common path, JSON, and promotion helpers for strategy batch runs."""
from __future__ import annotations

import csv
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from strategy_validator.contracts.strategy_batch import (
    StrategyBatchSpec,
    StrategyCandidateSpec,
    StrategyGateSummary,
)
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256

def _resolve_output_base(spec: StrategyBatchSpec) -> Path:
    raw = Path(spec.output_root)
    if raw.is_absolute():
        return raw
    return (Path.cwd() / raw).resolve()


def _run_id_for_batch(spec: StrategyBatchSpec) -> str:
    override = os.environ.get("STRATEGY_VALIDATOR_TEST_STRATEGY_RUN_ID", "").strip()
    if override:
        return override
    basis = "|".join(sorted(s.strategy_id for s in spec.strategies))
    return canonical_json_sha256({"batch_id": spec.batch_id, "as_of": spec.as_of_utc.isoformat(), "ids": basis})[:24]


def _resolve_batch_run_directory(output_base: Path, batch_id: str, run_id: str) -> Path:
    bid = batch_id.strip()
    rid = run_id.strip()
    if not bid or bid != batch_id or ".." in bid or bid.startswith(("/", "\\")):
        raise ValueError("INVALID_BATCH_ID")
    if not rid or Path(rid).name != rid or ".." in rid or rid.startswith(("/", "\\")):
        raise ValueError("INVALID_RUN_ID")
    return (output_base / bid / rid).resolve()


def _assert_path_under(parent: Path, child: Path) -> None:
    try:
        child.resolve().relative_to(parent.resolve())
    except ValueError as exc:
        raise ValueError(f"RUN_DIRECTORY_TRAVERSAL:{child}") from exc


def _prepare_run_directory(*, output_base: Path, batch_id: str, run_id: str, overwrite: bool) -> Path:
    base_r = output_base.resolve()
    run_dir = _resolve_batch_run_directory(base_r, batch_id, run_id)
    _assert_path_under(base_r, run_dir)
    if run_dir.exists():
        if not overwrite:
            raise FileExistsError(f"RUN_DIRECTORY_EXISTS:{run_dir}")
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def _write_json(path: Path, obj: Any) -> None:
    import json

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, default=_json_dt) + "\n", encoding="utf-8")


def _json_dt(o: Any) -> str:
    if isinstance(o, datetime):
        return o.isoformat()
    raise TypeError(type(o))


def _write_filtered_bars_csv(path: Path, bars: list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        w = csv.writer(handle)
        w.writerow(["symbol", "timestamp_utc", "open", "high", "low", "close", "volume"])
        for b in bars:
            w.writerow(
                [
                    b.symbol,
                    b.timestamp_utc.isoformat(),
                    b.open,
                    b.high,
                    b.low,
                    b.close,
                    b.volume,
                ]
            )


def _enrich_metrics(
    metrics: dict[str, float],
    prices: np.ndarray,
    candidate: StrategyCandidateSpec,
    *,
    synthetic: bool,
) -> dict[str, float]:
    out = {k: float(v) for k, v in metrics.items()}
    n = int(prices.shape[0])
    out["sample_count"] = float(n)
    out["data_coverage_ratio"] = float(n) / float(max(candidate.lookback_days, 1))
    out["synthetic_demo_flag"] = 1.0 if synthetic else 0.0
    return out


def _promotion_state(
    gate: StrategyGateSummary, *, synthetic: bool, sample_count: int | None
) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if synthetic:
        reasons.append("SYNTHETIC_DEMO")
    if not synthetic and gate.pit_gate != "PIT_VERIFIED":
        reasons.append(f"PIT:{gate.pit_gate}")
    if gate.data_coverage_gate.startswith("BLOCKED"):
        reasons.append(f"DATA_COVERAGE:{gate.data_coverage_gate}")
    if not synthetic and gate.data_quality_gate == "BLOCKED":
        reasons.append(f"DATA_QUALITY:{gate.data_quality_gate}")
    if not synthetic and gate.market_data_integrity_gate == "BLOCKED":
        reasons.append("MARKET_DATA_INTEGRITY:BLOCKED")
    if not synthetic and sample_count is not None and sample_count < 30:
        reasons.append("STRATEGY_METRICS_LOW_SAMPLE")
    if not synthetic and gate.robustness_gate != "PROVEN":
        reasons.append(f"ROBUSTNESS:{gate.robustness_gate}")
    if not synthetic and gate.cpcv_robustness_gate not in ("NOT_RUN", "NOT_APPLICABLE", "PROVEN"):
        reasons.append(f"CPCV:{gate.cpcv_robustness_gate}")
    if not synthetic and gate.execution_realism_gate != "PROVEN":
        reasons.append("EXECUTION_REALISM_NOT_PROVEN")
    if not synthetic and gate.parameter_sensitivity_gate == "FRAGILE":
        reasons.append("PARAMETER_SENSITIVITY:FRAGILE")
    if not synthetic and gate.regime_analysis_gate == "BLOCKED":
        reasons.append("REGIME_ANALYSIS:BLOCKED")
    if not synthetic and gate.oos_holdout_gate == "BLOCKED":
        reasons.append("OOS_HOLDOUT:BLOCKED")
    eligible = len(reasons) == 0
    return eligible, reasons



__all__ = [
    "_resolve_output_base",
    "_run_id_for_batch",
    "_resolve_batch_run_directory",
    "_assert_path_under",
    "_prepare_run_directory",
    "_write_json",
    "_write_filtered_bars_csv",
    "_enrich_metrics",
    "_promotion_state",
]
