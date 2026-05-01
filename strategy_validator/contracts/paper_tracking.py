"""Paper tracking contracts (research / evidence only; no live trading)."""
from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from strategy_validator.contracts.candidate_lifecycle import (
    CandidateLifecycleAssessment,
    CandidateLifecycleEvidenceRef,
    CandidateLifecycleState,
    CandidateLifecycleTransitionReason,
)

class PaperPosture(str, Enum):
    RESEARCH_PAPER_TRACKING = "RESEARCH_PAPER_TRACKING"
    DEMO_PAPER_ONLY = "DEMO_PAPER_ONLY"


class KillRulePosture(str, Enum):
    """How falsification rules posture the candidate in lifecycle (orthogonal to scorecard kill_state)."""

    NONE = "NONE"
    SOFT_TRIGGERED = "SOFT_TRIGGERED"
    HARD_TRIGGERED = "HARD_TRIGGERED"


class KillState(str, Enum):
    ACTIVE = "ACTIVE"
    WARNED = "WARNED"
    KILLED = "KILLED"


class ExecutionRealismDecayLevel(str, Enum):
    NONE = "NONE"
    WARN = "WARN"
    SEVERE = "SEVERE"


class FalsificationRuleKind(str, Enum):
    MAX_CUMULATIVE_LOSS = "MAX_CUMULATIVE_LOSS"
    MAX_DRAWDOWN = "MAX_DRAWDOWN"
    SIGNAL_DRIFT = "SIGNAL_DRIFT"
    EXECUTION_ASSUMPTION_STALE = "EXECUTION_ASSUMPTION_STALE"
    MANUAL_OPERATOR_HALT = "MANUAL_OPERATOR_HALT"


class FalsificationRule(BaseModel):
    """Deterministic kill / falsification rule definition (frozen at enroll)."""

    rule_id: str = Field(min_length=1)
    kind: FalsificationRuleKind
    threshold: float | None = None
    window_days: int = Field(default=5, ge=1, le=3650)
    description: str = ""

    model_config = {"extra": "forbid"}


# Alias for docs / CLI wording
KillRule = FalsificationRule


class PaperTrackingCandidate(BaseModel):
    """One strategy selected for paper evidence tracking."""

    strategy_id: str
    strategy_type: str = "unknown"
    batch_id: str
    run_id: str
    enrolled_at_utc: datetime
    promotion_eligible_at_enrollment: bool = False
    synthetic_demo: bool = False
    paper_posture: PaperPosture = PaperPosture.RESEARCH_PAPER_TRACKING
    data_plane_at_enrollment: str = "UNKNOWN"
    gauntlet_gate_snapshot: dict[str, Any] = Field(default_factory=dict)
    source_evidence_manifest_sha256: str | None = None
    source_strategy_scorecard_sha256: str | None = None
    source_equity_curve_sha256: str | None = None

    model_config = {"extra": "forbid"}

    @field_validator("enrolled_at_utc")
    @classmethod
    def _tz_enrolled(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("enrolled_at_utc must be timezone-aware")
        return v


class PortfolioCarryForward(BaseModel):
    """DUPLICATIVE / correlation posture copied from batch gauntlet (not production proof)."""

    portfolio_gate_status: str = "NOT_APPLICABLE"
    duplicate_alpha_warnings: list[str] = Field(default_factory=list)
    average_correlation: float | None = None
    disclaimer: str = "Carried from batch summary; not production diversification proof."

    model_config = {"extra": "forbid"}


class PaperTrackingGovernance(BaseModel):
    """Explicit governance knobs (artifact edits or `paper-track assess` flags)."""

    allow_promotion_despite_duplicative: bool = False
    duplicative_promotion_rationale: str = ""
    lifecycle_rejected: bool = False

    model_config = {"extra": "forbid"}


class PaperTrackingManifest(BaseModel):
    schema_version: Literal["paper_tracking_manifest/v1"] = "paper_tracking_manifest/v1"
    tracking_id: str = Field(min_length=8)
    batch_run_dir: str = Field(min_length=1)
    candidate: PaperTrackingCandidate
    portfolio_carry_forward: PortfolioCarryForward = Field(default_factory=PortfolioCarryForward)
    governance: PaperTrackingGovernance = Field(default_factory=PaperTrackingGovernance)
    kill_rules: list[FalsificationRule] = Field(default_factory=list)
    manifest_sha256: str = ""
    created_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    enrollment_notes: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}

    @field_validator("created_at_utc")
    @classmethod
    def _tz_created(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("created_at_utc must be timezone-aware")
        return v


class DailySignalSnapshot(BaseModel):
    schema_version: Literal["paper_daily_signal/v1"] = "paper_daily_signal/v1"
    tracking_id: str
    strategy_id: str
    observation_date_utc: date
    model_label: str = "DETERMINISTIC_PAPER_SIGNAL_V1"
    signal_exposure: float = 0.0
    signal_metadata: dict[str, Any] = Field(default_factory=dict)
    evidence_sha256: str = ""
    disclaimer: str = "Synthetic paper signal for evidence; not a live order."

    model_config = {"extra": "forbid"}


class RealizedOutcomeSnapshot(BaseModel):
    schema_version: Literal["paper_realized_outcome/v1"] = "paper_realized_outcome/v1"
    tracking_id: str
    strategy_id: str
    observation_date_utc: date
    model_label: str = "DETERMINISTIC_PAPER_OUTCOME_V1"
    paper_return_1d: float = 0.0
    cumulative_paper_equity_factor: float = 1.0
    benchmark_return_1d: float | None = None
    evidence_sha256: str = ""
    disclaimer: str = "Mark-to-model paper return; not broker realized PnL."

    model_config = {"extra": "forbid"}


class TriggeredRule(BaseModel):
    rule_id: str
    kind: str
    detail: str

    model_config = {"extra": "forbid"}


class PaperTrackingScorecard(BaseModel):
    schema_version: Literal["paper_tracking_scorecard/v1"] = "paper_tracking_scorecard/v1"
    tracking_id: str
    strategy_id: str
    evaluated_at_utc: datetime
    days_of_signals: int = 0
    cumulative_paper_return: float = 0.0
    drift_score: float = 0.0
    execution_realism_decay_level: ExecutionRealismDecayLevel = ExecutionRealismDecayLevel.NONE
    kill_state: KillState = KillState.ACTIVE
    triggered_rules: list[TriggeredRule] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    portfolio_carry_forward_warnings: list[str] = Field(default_factory=list)
    scorecard_sha256: str = ""
    disclaimer: str = "Paper tracking scorecard; no live readiness or profitability claim."

    model_config = {"extra": "forbid"}

    @field_validator("evaluated_at_utc")
    @classmethod
    def _tz_eval(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("evaluated_at_utc must be timezone-aware")
        return v


def default_kill_rules() -> list[FalsificationRule]:
    return [
        FalsificationRule(
            rule_id="paper-max-cum-loss",
            kind=FalsificationRuleKind.MAX_CUMULATIVE_LOSS,
            threshold=-0.15,
            window_days=252,
            description="Cumulative paper return below -15% triggers kill.",
        ),
        FalsificationRule(
            rule_id="paper-max-dd",
            kind=FalsificationRuleKind.MAX_DRAWDOWN,
            threshold=0.20,
            window_days=252,
            description="Peak-to-trough paper equity drawdown above 20%.",
        ),
        FalsificationRule(
            rule_id="paper-signal-drift",
            kind=FalsificationRuleKind.SIGNAL_DRIFT,
            threshold=0.75,
            window_days=10,
            description="Signal drift score above threshold (heuristic).",
        ),
        FalsificationRule(
            rule_id="paper-exec-stale",
            kind=FalsificationRuleKind.EXECUTION_ASSUMPTION_STALE,
            threshold=500.0,
            window_days=365,
            description="Days since enrollment without execution realism revalidation (tighten in production policy).",
        ),
    ]


__all__ = [
    "CandidateLifecycleAssessment",
    "CandidateLifecycleEvidenceRef",
    "CandidateLifecycleState",
    "CandidateLifecycleTransitionReason",
    "DailySignalSnapshot",
    "ExecutionRealismDecayLevel",
    "FalsificationRule",
    "FalsificationRuleKind",
    "KillRule",
    "KillRulePosture",
    "KillState",
    "PaperPosture",
    "PaperTrackingCandidate",
    "PaperTrackingGovernance",
    "PaperTrackingManifest",
    "PaperTrackingScorecard",
    "PortfolioCarryForward",
    "RealizedOutcomeSnapshot",
    "TriggeredRule",
    "default_kill_rules",
]
