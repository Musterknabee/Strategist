"""Governed multi-strategy batch research contracts (paper/research only; no live trading)."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, PrivateAttr, field_validator, model_validator

from strategy_validator.contracts.strategy_data_snapshot import LocalBarsDataSourceConfig
from strategy_validator.contracts.strategy_execution_realism import ExecutionRealismAssumptions
from strategy_validator.contracts.strategy_robustness import RobustnessAssumptions, _ROBUSTNESS_SPEC_KEYS

StrategyLabMode = Literal["research", "paper"]
WorkerModel = Literal["thread_pool", "process_pool"]
RobustnessMode = Literal["walk_forward", "cpcv", "both"]

_EXECUTION_REALISM_REQUIRED_KEYS = frozenset(
    {
        "starting_capital",
        "max_participation_rate",
        "fee_bps",
        "slippage_bps",
        "min_average_daily_volume",
    }
)
StrategyTypeId = Literal["momentum", "mean_reversion", "volatility_breakout"]


class StrategyRunStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    PAPER_ONLY = "PAPER_ONLY"


class PitPolicy(str, Enum):
    STRICT = "STRICT"
    DEGRADE_TO_PAPER_ONLY = "DEGRADE_TO_PAPER_ONLY"


class StrategyCandidateSpec(BaseModel):
    strategy_id: str = Field(min_length=1)
    strategy_type: StrategyTypeId
    universe: str = Field(min_length=1)
    timeframe: str = Field(min_length=1)
    as_of_utc: datetime
    lookback_days: int = Field(ge=1, le=10_000)
    params: dict[str, Any] = Field(default_factory=dict)
    data_requirements: list[str] = Field(default_factory=list)
    provider_preferences: list[str] = Field(default_factory=list)
    data_source: LocalBarsDataSourceConfig | None = None
    execution_assumptions: dict[str, Any] = Field(default_factory=dict)
    execution_realism_assumptions: ExecutionRealismAssumptions | None = None
    robustness_assumptions: dict[str, Any] = Field(default_factory=dict)
    robustness_mode: RobustnessMode = "both"
    tags: list[str] = Field(default_factory=list)

    _resolved_robustness: RobustnessAssumptions = PrivateAttr(default_factory=RobustnessAssumptions)

    model_config = {"extra": "forbid"}

    @property
    def robustness_config(self) -> RobustnessAssumptions:
        return self._resolved_robustness

    @field_validator("as_of_utc")
    @classmethod
    def _tz_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("as_of_utc must be timezone-aware")
        return v

    @model_validator(mode="after")
    def _parse_execution_realism_assumptions(self) -> StrategyCandidateSpec:
        keys = frozenset(ExecutionRealismAssumptions.model_fields)
        ea = self.execution_assumptions
        sub = {k: ea[k] for k in keys if k in ea}
        if not sub:
            object.__setattr__(self, "execution_realism_assumptions", None)
            return self
        missing = _EXECUTION_REALISM_REQUIRED_KEYS - sub.keys()
        if missing:
            raise ValueError(
                f"execution_assumptions: incomplete execution realism fields; missing {sorted(missing)}"
            )
        er = ExecutionRealismAssumptions.model_validate(sub)
        object.__setattr__(self, "execution_realism_assumptions", er)
        return self

    @model_validator(mode="after")
    def _parse_robustness_assumptions(self) -> StrategyCandidateSpec:
        ra = self.robustness_assumptions
        if not ra:
            object.__setattr__(self, "_resolved_robustness", RobustnessAssumptions())
            return self
        unknown = set(ra.keys()) - _ROBUSTNESS_SPEC_KEYS
        if unknown:
            raise ValueError(f"robustness_assumptions: unknown keys {sorted(unknown)}")
        missing = _ROBUSTNESS_SPEC_KEYS - set(ra.keys())
        if missing:
            raise ValueError(
                "robustness_assumptions: incomplete; provide all keys or omit the object; "
                f"missing {sorted(missing)}"
            )
        object.__setattr__(
            self, "_resolved_robustness", RobustnessAssumptions.model_validate(ra)
        )
        return self


class StrategyBatchSpec(BaseModel):
    batch_id: str = Field(min_length=1)
    created_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    as_of_utc: datetime
    mode: StrategyLabMode
    max_workers: int = Field(default=4, ge=1, le=64)
    worker_model: WorkerModel = "thread_pool"
    strategies: list[StrategyCandidateSpec]
    pit_policy: PitPolicy = PitPolicy.DEGRADE_TO_PAPER_ONLY
    output_root: str = Field(min_length=1, description="Absolute or repo-relative artifact root for this batch.")

    model_config = {"extra": "forbid"}

    @field_validator("as_of_utc", "created_at_utc")
    @classmethod
    def _tz_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("timestamps must be timezone-aware")
        return v

    @field_validator("mode")
    @classmethod
    def _no_live(cls, v: StrategyLabMode) -> StrategyLabMode:
        if v not in ("research", "paper"):
            raise ValueError("mode must be research or paper")
        return v

    @model_validator(mode="after")
    def _unique_ids(self) -> StrategyBatchSpec:
        ids = [s.strategy_id for s in self.strategies]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate strategy_id in batch")
        if not self.strategies:
            raise ValueError("strategies must be non-empty")
        return self


class StrategyGateSummary(BaseModel):
    pit_gate: str = Field(default="UNKNOWN")
    data_gate: str = Field(default="UNKNOWN")
    data_quality_gate: str = Field(default="NOT_RUN")
    robustness_gate: str = Field(default="NOT_RUN")
    cpcv_robustness_gate: str = Field(default="NOT_RUN")
    execution_realism_gate: str = Field(default="NOT_RUN")
    parameter_sensitivity_gate: str = Field(default="NOT_RUN")
    regime_analysis_gate: str = Field(default="NOT_RUN")
    adjudication_gate: str = Field(default="NOT_INVOKED")
    data_coverage_gate: str = Field(default="NOT_RUN")
    promotion_eligible: bool = False
    promotion_blocked_reasons: list[str] = Field(default_factory=list)
    sample_count: int | None = None
    data_coverage_ratio: float | None = None

    model_config = {"extra": "forbid"}


class StrategyEvidenceReference(BaseModel):
    evidence_manifest_path: str
    evidence_manifest_sha256: str
    input_manifest_sha256: str
    pit_context_sha256: str
    metrics_sha256: str
    gate_summary_sha256: str

    model_config = {"extra": "forbid"}


class StrategyRunResult(BaseModel):
    strategy_id: str
    status: StrategyRunStatus = StrategyRunStatus.PENDING
    started_at_utc: datetime | None = None
    completed_at_utc: datetime | None = None
    duration_ms: int | None = None
    pit_status: str = "UNKNOWN"
    pit_snapshot_status: str | None = None
    data_status: str = "UNKNOWN"
    data_plane: str = "UNKNOWN"
    robustness_status: str = "NOT_RUN"
    execution_realism_status: str = "NOT_RUN"
    adjudication_status: str = "NOT_INVOKED"
    decision: str | None = None
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    evidence_manifest_path: str | None = None
    evidence_manifest_sha256: str | None = None
    data_snapshot_manifest_path: str | None = None
    data_snapshot_manifest_sha256: str | None = None
    data_snapshot_digest: str | None = None
    bars_row_count: int | None = None
    execution_realism_digest: str | None = None
    execution_realism_gate: str | None = None
    execution_realism_model_label: str | None = None
    execution_realism_est_slippage_bps: float | None = None
    execution_realism_est_fee_bps: float | None = None
    execution_realism_capacity_notional: float | None = None
    execution_realism_est_participation: float | None = None
    robustness_gate_status: str | None = None
    robustness_model_label: str | None = None
    robustness_evidence_sha256: str | None = None
    robustness_artifact_path: str | None = None
    positive_fold_ratio: float | None = None
    worst_fold_return: float | None = None
    pbo_like_score: float | None = None
    dsr_like_score: float | None = None
    robustness_fold_count: int | None = None
    cpcv_robustness_gate_status: str | None = None
    cpcv_evidence_sha256: str | None = None
    cpcv_artifact_path: str | None = None
    data_quality_gate_status: str | None = None
    parameter_sensitivity_gate_status: str | None = None
    regime_analysis_gate_status: str | None = None
    data_quality_artifact_path: str | None = None
    parameter_sensitivity_artifact_path: str | None = None
    regime_analysis_artifact_path: str | None = None
    trade_markers_path: str | None = None
    total_return: float | None = None
    max_drawdown: float | None = None
    sharpe_like: float | None = None
    analytics_score: float | None = None
    analytics_rank: int | None = None
    strategy_scorecard_path: str | None = None
    equity_curve_path: str | None = None
    drawdown_curve_path: str | None = None
    rolling_metrics_path: str | None = None
    fold_performance_path: str | None = None
    charts_compact: dict[str, Any] | None = None
    analytics_rank_explanation: str | None = None
    metrics: dict[str, float] = Field(default_factory=dict)
    gate_summary: StrategyGateSummary = Field(default_factory=StrategyGateSummary)
    compute_backend: str = "cpu"
    compute_worker_model: str = "thread_pool"
    cuda_available: bool | None = False

    model_config = {"extra": "forbid"}


class StrategyBatchRunManifest(BaseModel):
    schema_version: Literal["strategy_batch_run_manifest/v1"] = "strategy_batch_run_manifest/v1"
    batch_id: str
    run_id: str
    spec_sha256: str
    mode: StrategyLabMode
    as_of_utc: datetime
    created_at_utc: datetime
    output_dir: str
    strategy_count: int
    max_workers: int
    fail_fast: bool = False
    allow_synthetic: bool = True
    adjudication_enabled: bool = False
    compute_backend: str = "cpu"
    compute_worker_model: str = "thread_pool"
    cuda_available: bool = False

    model_config = {"extra": "forbid"}


class StrategyBatchRunSummary(BaseModel):
    schema_version: Literal["strategy_batch_run_summary/v1"] = "strategy_batch_run_summary/v1"
    ok: bool
    batch_id: str
    run_id: str
    output_dir: str
    generated_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    strategy_count: int
    passed_count: int = 0
    blocked_count: int = 0
    paper_only_count: int = 0
    failed_count: int = 0
    pending_count: int = 0
    strategies: list[StrategyRunResult] = Field(default_factory=list)
    batch_ranking: list[dict[str, Any]] = Field(default_factory=list)
    portfolio_correlation_summary: dict[str, Any] | None = None
    top_candidate: dict[str, Any] | None = None
    promotion_blocked_counts: dict[str, int] = Field(default_factory=dict)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    manifest: StrategyBatchRunManifest | None = None

    model_config = {"extra": "forbid"}


class StrategyEvidenceManifest(BaseModel):
    schema_version: Literal["strategy_evidence_manifest/v1"] = "strategy_evidence_manifest/v1"
    strategy_id: str
    batch_id: str
    run_id: str
    as_of_utc: datetime
    input_spec_sha256: str
    pit_context_sha256: str
    metrics_sha256: str
    gate_summary_sha256: str
    data_source: str
    data_source_classification: str
    synthetic_demo: bool
    may_gate_live_promotion: bool
    promotion_eligible: bool = False
    data_snapshot_digest: str | None = None
    data_snapshot_manifest_sha256: str | None = None
    pit_snapshot_status: str | None = None
    bars_row_count: int | None = None
    execution_realism_evidence_sha256: str | None = None
    execution_realism_gate_status: str | None = None
    robustness_evidence_sha256: str | None = None
    robustness_gate_status: str | None = None
    robustness_model_label: str | None = None
    cpcv_evidence_sha256: str | None = None
    cpcv_gate_status: str | None = None
    data_quality_evidence_sha256: str | None = None
    data_quality_gate_status: str | None = None
    parameter_sensitivity_evidence_sha256: str | None = None
    parameter_sensitivity_gate_status: str | None = None
    regime_analysis_evidence_sha256: str | None = None
    regime_analysis_gate_status: str | None = None
    strategy_scorecard_sha256: str | None = None
    equity_curve_sha256: str | None = None
    drawdown_curve_sha256: str | None = None
    rolling_metrics_sha256: str | None = None
    fold_performance_sha256: str | None = None
    trade_markers_sha256: str | None = None
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


__all__ = [
    "PitPolicy",
    "StrategyBatchRunManifest",
    "StrategyBatchRunSummary",
    "StrategyBatchSpec",
    "StrategyCandidateSpec",
    "StrategyEvidenceManifest",
    "StrategyEvidenceReference",
    "StrategyGateSummary",
    "StrategyLabMode",
    "RobustnessMode",
    "StrategyRunResult",
    "StrategyRunStatus",
    "StrategyTypeId",
    "LocalBarsDataSourceConfig",
    "ExecutionRealismAssumptions",
    "RobustnessAssumptions",
]
