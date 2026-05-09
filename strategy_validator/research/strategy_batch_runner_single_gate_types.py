"""Typed outputs for single-strategy gate evaluation."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from strategy_validator.contracts.strategy_batch import StrategyRunStatus


@dataclass(frozen=True)
class StrategySingleGateEvaluation:
    """Gate and diagnostic artifacts produced before chart/evidence emission."""

    warnings: list[str]
    blockers: list[str]
    status: StrategyRunStatus
    metrics_payload: dict[str, Any]
    metrics_sha: str
    ds_digest: str | None
    pit_snap_s: str | None
    data_status: str
    data_plane: str
    pit_status: str
    rob_status: str
    ds_class: str
    ds_label: str
    dq: Any
    dq_path: Path
    mdi: Any
    mdi_path: Path
    er: Any
    er_sha: str
    er_digest: str | None
    exec_realism_status: str
    rob: Any
    rob_charts: Any
    rob_path: Path
    cpcv: Any | None
    cpcv_path: Path
    ps: Any
    ps_path: Path
    reg: Any
    reg_path: Path
    promo_ok: bool
    promo_reasons: list[str]


__all__ = ["StrategySingleGateEvaluation"]
