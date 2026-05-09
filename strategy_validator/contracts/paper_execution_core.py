"""Core paper execution contracts (read-plane only; no browser orders)."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class PaperExecutionIntentPreview(BaseModel):
    schema_version: Literal["paper_execution_intent_preview/v1"] = "paper_execution_intent_preview/v1"
    tracking_id: str | None = None
    strategy_id: str | None = None
    symbol: str
    side: Literal["buy", "sell"]
    qty: float = Field(gt=0)
    order_type: Literal["market", "limit"] = "market"
    time_in_force: str = "day"
    source: str
    rationale: str
    confidence: Literal["LOW", "MEDIUM", "HIGH"] = "LOW"
    warnings: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class PaperExecutionIntentSelectionArtifact(BaseModel):
    """Durable operator-selected paper execution intent.

    The artifact selects a target for paper-only dry-run preparation. It is not
    an order, not an approval, and not a browser/API submission control.
    """

    schema_version: Literal["paper_execution_intent_selection/v1"] = "paper_execution_intent_selection/v1"
    generated_at_utc: datetime
    tracking_id: str
    strategy_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    no_network_calls: bool = True
    no_order_submitted: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    submission_authority: Literal["NONE"] = "NONE"
    selection_authority: Literal["CLI_ARTIFACT_ONLY"] = "CLI_ARTIFACT_ONLY"
    selected_by: str = "operator"
    selection_reason: str = "manual paper dry-run preparation"
    source_artifact_path: str | None = None
    selected_intent: PaperExecutionIntentPreview
    broker_intent: dict[str, Any]
    dry_run_command_hint: str
    artifact_sha256: str = ""

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionJournalEntry(BaseModel):
    schema_version: Literal["paper_execution_journal_entry/v1"] = "paper_execution_journal_entry/v1"
    tracking_id: str
    artifact_kind: Literal["DRY_RUN", "SUBMISSION"] = "SUBMISSION"
    artifact_path: str
    broker_order_id: str | None = None
    status: str | None = None
    ok: bool | None = None
    dry_run: bool | None = None
    retrieved_at_utc: str | None = None
    digest_prefix: str | None = None
    source_selection_artifact_path: str | None = None
    source_selection_artifact_sha256: str | None = None
    linked_dry_run_artifact_sha256: str | None = None
    submission_guard_status: str | None = None
    evidence_freshness_status: str | None = None
    selected_intent_match: bool | None = None
    linked_dry_run_match: bool | None = None
    linked_dry_run_ok: bool | None = None
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class PaperExecutionDryRunArtifact(BaseModel):
    """Durable dry-run evidence for paper-only order validation.

    This artifact is deliberately separate from broker submission evidence. It can
    be materialized on an operator host without placing an order or calling the
    broker network, then consumed by the UI evidence journal.
    """

    schema_version: Literal["paper_execution_dry_run_artifact/v1"] = "paper_execution_dry_run_artifact/v1"
    generated_at_utc: datetime
    tracking_id: str
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    no_network_calls: bool = True
    no_order_submitted: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    submission_authority: Literal["NONE"] = "NONE"
    intent: dict[str, Any]
    result: dict[str, Any]
    source_selection_artifact_path: str | None = None
    source_selection_artifact_sha256: str | None = None
    replayed_from_selected_intent: bool = False
    artifact_sha256: str = ""

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionFreshnessGate(BaseModel):
    schema_version: Literal["paper_execution_freshness_gate/v1"] = "paper_execution_freshness_gate/v1"
    status: Literal["FRESH", "STALE", "REPLAY_REQUIRED", "MISSING_EVIDENCE", "UNKNOWN"] = "UNKNOWN"
    max_selected_intent_age_hours: int = 24
    max_linked_dry_run_age_hours: int = 12
    max_tracking_signal_age_hours: int = 48
    max_broker_policy_age_hours: int = 24
    selected_intent_age_hours: float | None = None
    latest_linked_dry_run_age_hours: float | None = None
    latest_tracking_signal_age_hours: float | None = None
    broker_policy_age_hours: float | None = None
    selected_intent_generated_at_utc: str | None = None
    latest_linked_dry_run_at_utc: str | None = None
    latest_tracking_signal_at_utc: str | None = None
    broker_policy_generated_at_utc: str | None = None
    stale_reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class PaperExecutionSubmissionGuardSnapshot(BaseModel):
    """Fail-closed preflight snapshot for CLI-only paper submission.

    The guard proves that a paper submission attempt is based on the current
    selected intent and a fresh, linked dry-run artifact. It is deliberately a
    paper-only CLI guard, not a browser/API order control.
    """

    schema_version: Literal["paper_execution_submission_guard/v1"] = "paper_execution_submission_guard/v1"
    evaluated_at_utc: datetime
    tracking_id: str
    status: Literal["PASS", "BLOCKED"] = "BLOCKED"
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_submission_blocked: bool = True
    submission_authority: Literal["CLI_ONLY"] = "CLI_ONLY"
    policy_status: str = "UNKNOWN"
    selected_intent_artifact_path: str | None = None
    selected_intent_artifact_sha256: str | None = None
    linked_dry_run_artifact_path: str | None = None
    linked_dry_run_artifact_sha256: str | None = None
    linked_dry_run_source_selection_sha256: str | None = None
    selected_intent_age_hours: float | None = None
    linked_dry_run_age_hours: float | None = None
    evidence_freshness_status: Literal["FRESH", "STALE", "REPLAY_REQUIRED", "MISSING_EVIDENCE", "UNKNOWN"] = "UNKNOWN"
    submission_intent_matches_selection: bool = False
    linked_dry_run_matches_selection: bool = False
    linked_dry_run_ok: bool = False
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}

    @field_validator("evaluated_at_utc")
    @classmethod
    def _evaluated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("evaluated_at_utc must be timezone-aware")
        return v


class PaperExecutionSubmissionArtifact(BaseModel):
    """Durable paper submission evidence with the guard snapshot attached."""

    schema_version: Literal["paper_execution_submission_artifact/v1"] = "paper_execution_submission_artifact/v1"
    generated_at_utc: datetime
    tracking_id: str
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_submission_blocked: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    submission_authority: Literal["CLI_ONLY"] = "CLI_ONLY"
    intent: dict[str, Any]
    result: dict[str, Any]
    submission_guard: PaperExecutionSubmissionGuardSnapshot
    artifact_sha256: str = ""

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _submission_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v




class PaperExecutionSubmissionReceiptView(BaseModel):
    """Normalized operator receipt for guarded paper submissions.

    This is a read-plane view of durable submission artifacts. It surfaces the
    broker result and guard posture without giving the browser an order-control
    path.
    """

    schema_version: Literal["paper_execution_submission_receipt_view/v1"] = "paper_execution_submission_receipt_view/v1"
    tracking_id: str
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    broker_order_id: str | None = None
    broker_status: str | None = None
    result_ok: bool | None = None
    symbol: str | None = None
    side: str | None = None
    qty: float | None = None
    filled_qty: float | None = None
    policy_status: str | None = None
    guard_status: Literal["PASS", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    evidence_freshness_status: Literal["FRESH", "STALE", "REPLAY_REQUIRED", "MISSING_EVIDENCE", "UNKNOWN"] = "UNKNOWN"
    selected_intent_artifact_sha256: str | None = None
    linked_dry_run_artifact_sha256: str | None = None
    linked_dry_run_source_selection_sha256: str | None = None
    submission_intent_matches_selection: bool | None = None
    linked_dry_run_matches_selection: bool | None = None
    linked_dry_run_ok: bool | None = None
    guard_blocker_count: int = 0
    guard_warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class PaperExecutionOrderStatusArtifact(BaseModel):
    """Durable paper broker order-status refresh evidence.

    This artifact is captured by the CLI after a guarded paper submission. It
    refreshes broker fill/status state without submitting a new order and without
    exposing secrets to the UI read plane.
    """

    schema_version: Literal["paper_execution_order_status_artifact/v1"] = "paper_execution_order_status_artifact/v1"
    generated_at_utc: datetime
    tracking_id: str
    broker_order_id: str
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    status_refresh_authority: Literal["CLI_EVIDENCE_ONLY"] = "CLI_EVIDENCE_ONLY"
    source_submission_artifact_path: str | None = None
    source_submission_artifact_sha256: str | None = None
    result: dict[str, Any]
    artifact_sha256: str = ""

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _order_status_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionOrderStatusView(BaseModel):
    """Read-plane view of refreshed paper broker order status."""

    schema_version: Literal["paper_execution_order_status_view/v1"] = "paper_execution_order_status_view/v1"
    tracking_id: str | None = None
    artifact_path: str | None = None
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    broker_order_id: str | None = None
    status: str | None = None
    ok: bool | None = None
    filled_qty: float | None = None
    symbol: str | None = None
    side: str | None = None
    policy_status: str | None = None
    source_submission_artifact_sha256: str | None = None
    source_submission_artifact_path: str | None = None
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class PaperExecutionAccountPositionSnapshotArtifact(BaseModel):
    """Durable paper broker account/position snapshot.

    This artifact is captured by the CLI on a trusted host. It contains no API
    secrets and gives the read-plane cockpit broker-state evidence to compare
    against guarded paper submission receipts.
    """

    schema_version: Literal["paper_execution_account_position_snapshot/v1"] = "paper_execution_account_position_snapshot/v1"
    generated_at_utc: datetime
    broker_id: str = "alpaca_paper"
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_order_submitted: bool = True
    snapshot_authority: Literal["CLI_EVIDENCE_ONLY"] = "CLI_EVIDENCE_ONLY"
    policy_status: str = "UNKNOWN"
    account_status: dict[str, Any] = Field(default_factory=dict)
    positions: list[dict[str, Any]] = Field(default_factory=list)
    position_count: int = 0
    notes: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _snapshot_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionPositionReconciliationView(BaseModel):
    """Read-plane reconciliation between latest guarded submission and positions."""

    schema_version: Literal["paper_execution_position_reconciliation/v1"] = "paper_execution_position_reconciliation/v1"
    status: Literal["RECONCILED", "PENDING_FILL", "MISMATCHED", "NO_SUBMISSION", "NO_POSITION_SNAPSHOT", "UNKNOWN"] = "UNKNOWN"
    tracking_id: str | None = None
    symbol: str | None = None
    side: str | None = None
    submitted_qty: float | None = None
    filled_qty: float | None = None
    expected_position_delta_qty: float | None = None
    observed_position_qty: float | None = None
    broker_status: str | None = None
    latest_submission_receipt_at_utc: str | None = None
    latest_submission_receipt_artifact_sha256: str | None = None
    account_position_snapshot_path: str | None = None
    account_position_snapshot_sha256: str | None = None
    account_position_snapshot_at_utc: str | None = None
    account_position_snapshot_age_hours: float | None = None
    reconciliation_blocker_count: int = 0
    reconciliation_warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class PaperExecutionTimelineEntry(BaseModel):
    """Chronological read-plane event in the paper execution evidence chain.

    The timeline stitches together selected intent, linked dry-run, guarded
    submission, order-status refresh, and position reconciliation evidence. It is
    not an order-control surface.
    """

    schema_version: Literal["paper_execution_timeline_entry/v1"] = "paper_execution_timeline_entry/v1"
    stage: Literal[
        "SELECTED_INTENT",
        "DRY_RUN",
        "SUBMISSION",
        "ORDER_STATUS",
        "POSITION_SNAPSHOT",
        "POSITION_RECONCILIATION",
    ]
    stage_order: int = 0
    tracking_id: str | None = None
    generated_at_utc: str | None = None
    artifact_path: str | None = None
    artifact_sha256: str | None = None
    status: str = "UNKNOWN"
    ok: bool | None = None
    trusted: bool = False
    summary_line: str
    broker_order_id: str | None = None
    symbol: str | None = None
    side: str | None = None
    qty: float | None = None
    source_selection_artifact_sha256: str | None = None
    linked_dry_run_artifact_sha256: str | None = None
    source_submission_artifact_sha256: str | None = None
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class PaperExecutionTimelineSummary(BaseModel):
    schema_version: Literal["paper_execution_timeline_summary/v1"] = "paper_execution_timeline_summary/v1"
    event_count: int = 0
    stage_count: int = 0
    trusted_event_count: int = 0
    blocker_count: int = 0
    warning_count: int = 0
    latest_event_at_utc: str | None = None
    sequence_status: Literal["EMPTY", "PARTIAL", "BLOCKED", "COMPLETE"] = "EMPTY"
    completed_stages: list[str] = Field(default_factory=list)
    missing_stages: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


__all__ = (
    "PaperExecutionIntentPreview",
    "PaperExecutionIntentSelectionArtifact",
    "PaperExecutionJournalEntry",
    "PaperExecutionDryRunArtifact",
    "PaperExecutionFreshnessGate",
    "PaperExecutionSubmissionGuardSnapshot",
    "PaperExecutionSubmissionArtifact",
    "PaperExecutionSubmissionReceiptView",
    "PaperExecutionOrderStatusArtifact",
    "PaperExecutionOrderStatusView",
    "PaperExecutionAccountPositionSnapshotArtifact",
    "PaperExecutionPositionReconciliationView",
    "PaperExecutionTimelineEntry",
    "PaperExecutionTimelineSummary",
)
