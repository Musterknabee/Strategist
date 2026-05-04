"""Paper execution cockpit contracts (read-plane only; no browser orders)."""
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


class PaperExecutionEvidenceBundleSource(BaseModel):
    """Source artifact reference sealed into a paper execution evidence bundle."""

    schema_version: Literal["paper_execution_evidence_bundle_source/v1"] = "paper_execution_evidence_bundle_source/v1"
    stage: str
    tracking_id: str | None = None
    generated_at_utc: str | None = None
    artifact_path: str | None = None
    artifact_sha256: str | None = None
    status: str = "UNKNOWN"
    trusted: bool = False
    blocker_count: int = 0
    warning_count: int = 0

    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleArtifact(BaseModel):
    """Durable bundle sealing the current paper execution timeline.

    The bundle is an attestable review package only. It does not authorize a
    trade, submit an order, promote a strategy, or mutate the decision ledger.
    """

    schema_version: Literal["paper_execution_evidence_bundle/v1"] = "paper_execution_evidence_bundle/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    bundle_authority: Literal["CLI_EVIDENCE_ONLY"] = "CLI_EVIDENCE_ONLY"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    bundle_status: Literal["SEALED", "SEALED_RESTRICTED", "SEALED_BLOCKED"] = "SEALED_RESTRICTED"
    timeline_sequence_status: Literal["EMPTY", "PARTIAL", "BLOCKED", "COMPLETE"] = "EMPTY"
    timeline_event_count: int = 0
    timeline_trusted_event_count: int = 0
    timeline_blocker_count: int = 0
    timeline_warning_count: int = 0
    source_artifact_count: int = 0
    missing_stages: list[str] = Field(default_factory=list)
    source_artifacts: list[PaperExecutionEvidenceBundleSource] = Field(default_factory=list)
    timeline_summary: PaperExecutionTimelineSummary = Field(default_factory=PaperExecutionTimelineSummary)
    timeline: list[PaperExecutionTimelineEntry] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    bundle_sha256: str = ""

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _bundle_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleView(BaseModel):
    """Read-plane summary of a sealed paper execution evidence bundle."""

    schema_version: Literal["paper_execution_evidence_bundle_view/v1"] = "paper_execution_evidence_bundle_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    bundle_sha256: str | None = None
    generated_at_utc: str | None = None
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    bundle_status: Literal["SEALED", "SEALED_RESTRICTED", "SEALED_BLOCKED", "UNKNOWN"] = "UNKNOWN"
    timeline_sequence_status: str = "EMPTY"
    timeline_event_count: int = 0
    timeline_trusted_event_count: int = 0
    timeline_blocker_count: int = 0
    source_artifact_count: int = 0
    missing_stages: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleVerificationSource(BaseModel):
    """Per-source digest verification row for a sealed evidence bundle."""

    schema_version: Literal["paper_execution_evidence_bundle_verification_source/v1"] = "paper_execution_evidence_bundle_verification_source/v1"
    stage: str
    tracking_id: str | None = None
    artifact_path: str | None = None
    declared_sha256: str | None = None
    computed_sha256: str | None = None
    verified: bool = False
    issue: str | None = None

    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleVerificationArtifact(BaseModel):
    """Durable verification result for a paper execution evidence bundle.

    Verification is read-only: it recomputes bundle/source digests and records
    whether the sealed bundle still matches the artifacts it claims to seal.
    """

    schema_version: Literal["paper_execution_evidence_bundle_verification/v1"] = "paper_execution_evidence_bundle_verification/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    verification_authority: Literal["CLI_EVIDENCE_ONLY"] = "CLI_EVIDENCE_ONLY"
    verification_status: Literal["PASS", "FAIL"] = "FAIL"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "UNTRUSTED"
    source_bundle_artifact_path: str
    source_bundle_declared_sha256: str | None = None
    source_bundle_computed_sha256: str | None = None
    bundle_hash_valid: bool = False
    timeline_source_link_valid: bool = False
    source_artifact_count: int = 0
    verified_source_artifact_count: int = 0
    missing_source_artifact_count: int = 0
    mismatched_source_artifact_count: int = 0
    source_verifications: list[PaperExecutionEvidenceBundleVerificationSource] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleVerificationView(BaseModel):
    """Read-plane summary of a paper evidence bundle verification artifact."""

    schema_version: Literal["paper_execution_evidence_bundle_verification_view/v1"] = "paper_execution_evidence_bundle_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "UNTRUSTED"
    source_bundle_artifact_path: str | None = None
    source_bundle_declared_sha256: str | None = None
    source_bundle_computed_sha256: str | None = None
    bundle_hash_valid: bool = False
    timeline_source_link_valid: bool = False
    source_artifact_count: int = 0
    verified_source_artifact_count: int = 0
    missing_source_artifact_count: int = 0
    mismatched_source_artifact_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleDriftArtifact(BaseModel):
    """Durable drift check for a sealed paper execution evidence bundle.

    A bundle can verify cryptographically while still being stale relative to
    newer paper execution timeline artifacts. This artifact records whether the
    current timeline source set still matches the latest sealed bundle.
    """

    schema_version: Literal["paper_execution_evidence_bundle_drift/v1"] = "paper_execution_evidence_bundle_drift/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    drift_check_authority: Literal["CLI_EVIDENCE_ONLY"] = "CLI_EVIDENCE_ONLY"
    drift_status: Literal["IN_SYNC", "DRIFTED", "NO_BUNDLE", "NO_TIMELINE", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_bundle_artifact_path: str | None = None
    source_bundle_sha256: str | None = None
    source_bundle_generated_at_utc: str | None = None
    current_timeline_sequence_status: str | None = None
    current_timeline_event_count: int = 0
    bundled_timeline_event_count: int = 0
    current_source_artifact_count: int = 0
    bundled_source_artifact_count: int = 0
    current_timeline_fingerprint: str | None = None
    bundled_timeline_fingerprint: str | None = None
    new_source_artifacts: list[str] = Field(default_factory=list)
    removed_source_artifacts: list[str] = Field(default_factory=list)
    changed_stage_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _drift_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleDriftView(BaseModel):
    """Read-plane summary of a paper evidence bundle drift artifact."""

    schema_version: Literal["paper_execution_evidence_bundle_drift_view/v1"] = "paper_execution_evidence_bundle_drift_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    drift_status: Literal["IN_SYNC", "DRIFTED", "NO_BUNDLE", "NO_TIMELINE", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_bundle_artifact_path: str | None = None
    source_bundle_sha256: str | None = None
    source_bundle_generated_at_utc: str | None = None
    current_timeline_sequence_status: str | None = None
    current_timeline_event_count: int = 0
    bundled_timeline_event_count: int = 0
    current_source_artifact_count: int = 0
    bundled_source_artifact_count: int = 0
    current_timeline_fingerprint: str | None = None
    bundled_timeline_fingerprint: str | None = None
    new_source_artifact_count: int = 0
    removed_source_artifact_count: int = 0
    changed_stage_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}

class PaperExecutionEvidenceBundleRotationArtifact(BaseModel):
    """Durable operator recommendation for evidence-bundle rotation.

    Rotation is a recovery workflow recommendation only. It never submits orders
    and never mutates the adjudication ledger. It records whether the current
    paper execution evidence should be re-sealed, re-verified, and rechecked for
    drift after timeline/source changes.
    """

    schema_version: Literal["paper_execution_evidence_bundle_rotation/v1"] = "paper_execution_evidence_bundle_rotation/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    rotation_authority: Literal["CLI_RECOMMENDATION_ONLY"] = "CLI_RECOMMENDATION_ONLY"
    rotation_status: Literal["NOT_NEEDED", "RECOMMENDED", "REQUIRED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_bundle_sha256: str | None = None
    source_bundle_status: str | None = None
    source_bundle_trust_banner: str | None = None
    source_verification_status: str | None = None
    source_verification_trust_banner: str | None = None
    source_drift_status: str | None = None
    source_drift_trust_banner: str | None = None
    timeline_sequence_status: str | None = None
    timeline_event_count: int = 0
    rotation_reason_codes: list[str] = Field(default_factory=list)
    recommended_operator_sequence: list[str] = Field(default_factory=list)
    one_command_sequence_hint: str | None = None
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _rotation_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRotationView(BaseModel):
    """Read-plane summary of a paper evidence-bundle rotation recommendation."""

    schema_version: Literal["paper_execution_evidence_bundle_rotation_view/v1"] = "paper_execution_evidence_bundle_rotation_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    rotation_status: Literal["NOT_NEEDED", "RECOMMENDED", "REQUIRED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_bundle_sha256: str | None = None
    source_bundle_status: str | None = None
    source_verification_status: str | None = None
    source_drift_status: str | None = None
    timeline_sequence_status: str | None = None
    timeline_event_count: int = 0
    rotation_reason_codes: list[str] = Field(default_factory=list)
    recommended_operator_sequence: list[str] = Field(default_factory=list)
    one_command_sequence_hint: str | None = None
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRotationExecutionStep(BaseModel):
    """Single audited step in the bundle-rotation recovery workflow."""

    schema_version: Literal["paper_execution_evidence_bundle_rotation_execution_step/v1"] = "paper_execution_evidence_bundle_rotation_execution_step/v1"
    step_name: Literal["SEAL", "VERIFY", "DRIFT_CHECK", "SKIP", "BLOCK"]
    status: Literal["PASS", "FAIL", "SKIPPED", "BLOCKED"]
    artifact_path: str | None = None
    history_artifact_path: str | None = None
    artifact_sha256: str | None = None
    output_status: str | None = None
    trust_banner: str | None = None
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRotationExecutionArtifact(BaseModel):
    """Durable manifest for executing the bundle-rotation recovery sequence.

    This is a CLI-only local evidence workflow. It may seal/verify/drift-check
    paper execution evidence artifacts, but it never submits orders, calls broker
    mutation endpoints, promotes strategies, or mutates the adjudication ledger.
    """

    schema_version: Literal["paper_execution_evidence_bundle_rotation_execution/v1"] = "paper_execution_evidence_bundle_rotation_execution/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    rotation_execution_authority: Literal["CLI_WORKFLOW_ONLY"] = "CLI_WORKFLOW_ONLY"
    rotation_execution_status: Literal["PASS", "FAILED", "BLOCKED", "SKIPPED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_recommendation_artifact_path: str | None = None
    source_recommendation_artifact_sha256: str | None = None
    source_recommendation_status: str | None = None
    source_recommendation_trust_banner: str | None = None
    force: bool = False
    timeline_sequence_status: str | None = None
    timeline_event_count: int = 0
    sealed_bundle_artifact_path: str | None = None
    sealed_bundle_sha256: str | None = None
    verification_artifact_path: str | None = None
    verification_status: str | None = None
    drift_artifact_path: str | None = None
    drift_status: str | None = None
    step_count: int = 0
    passed_step_count: int = 0
    failed_step_count: int = 0
    skipped_step_count: int = 0
    steps: list[PaperExecutionEvidenceBundleRotationExecutionStep] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _rotation_execution_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRotationExecutionView(BaseModel):
    """Read-plane summary of a bundle-rotation execution manifest."""

    schema_version: Literal["paper_execution_evidence_bundle_rotation_execution_view/v1"] = "paper_execution_evidence_bundle_rotation_execution_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    rotation_execution_status: Literal["PASS", "FAILED", "BLOCKED", "SKIPPED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_recommendation_status: str | None = None
    timeline_sequence_status: str | None = None
    sealed_bundle_sha256: str | None = None
    verification_status: str | None = None
    drift_status: str | None = None
    step_count: int = 0
    passed_step_count: int = 0
    failed_step_count: int = 0
    skipped_step_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleAttestationArtifact(BaseModel):
    """Keyless local DSSE-style attestation envelope for paper execution bundles.

    This deliberately does not use private keys. It binds a sealed, verified,
    in-sync paper execution evidence bundle to a structured in-toto-like
    statement so the operator can inspect attestability before introducing real
    signing infrastructure.
    """

    schema_version: Literal["paper_execution_evidence_bundle_attestation/v1"] = "paper_execution_evidence_bundle_attestation/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    attestation_authority: Literal["KEYLESS_LOCAL_STUB"] = "KEYLESS_LOCAL_STUB"
    attestation_mode: Literal["KEYLESS_LOCAL_STUB"] = "KEYLESS_LOCAL_STUB"
    signature_status: Literal["UNSIGNED_KEYLESS_STUB"] = "UNSIGNED_KEYLESS_STUB"
    attestation_status: Literal["ATTESTED", "ATTESTED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    signer_identity: str = "local-operator-keyless-stub"
    source_bundle_artifact_path: str | None = None
    source_bundle_sha256: str | None = None
    source_bundle_status: str | None = None
    source_verification_artifact_path: str | None = None
    source_verification_artifact_sha256: str | None = None
    source_verification_status: str | None = None
    source_drift_artifact_path: str | None = None
    source_drift_artifact_sha256: str | None = None
    source_drift_status: str | None = None
    statement_payload_sha256: str | None = None
    envelope: dict[str, Any] = Field(default_factory=dict)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _attestation_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleAttestationView(BaseModel):
    """Read-plane summary of a keyless local attestation envelope."""

    schema_version: Literal["paper_execution_evidence_bundle_attestation_view/v1"] = "paper_execution_evidence_bundle_attestation_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    attestation_status: Literal["ATTESTED", "ATTESTED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    attestation_mode: str = "KEYLESS_LOCAL_STUB"
    signature_status: str = "UNSIGNED_KEYLESS_STUB"
    signer_identity: str | None = None
    source_bundle_sha256: str | None = None
    source_bundle_status: str | None = None
    source_verification_status: str | None = None
    source_drift_status: str | None = None
    statement_payload_sha256: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleAttestationVerificationArtifact(BaseModel):
    """Read-only verification result for a keyless local attestation envelope.

    The verifier recomputes the attestation artifact digest, validates the
    embedded statement payload hash, checks the keyless-stub signature marker,
    and re-hashes the attestation's referenced bundle / verification / drift
    artifacts when their paths are available. It is read-only and paper-only.
    """

    schema_version: Literal["paper_execution_evidence_bundle_attestation_verification/v1"] = "paper_execution_evidence_bundle_attestation_verification/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    verification_authority: Literal["READ_ONLY"] = "READ_ONLY"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_attestation_artifact_path: str | None = None
    source_attestation_declared_sha256: str | None = None
    source_attestation_computed_sha256: str | None = None
    source_attestation_status: str | None = None
    source_attestation_trust_banner: str | None = None
    artifact_hash_valid: bool = False
    statement_payload_hash_valid: bool = False
    envelope_payload_hash_valid: bool = False
    keyless_stub_signature_valid: bool = False
    source_bundle_sha256: str | None = None
    source_bundle_hash_valid: bool = False
    source_verification_artifact_sha256: str | None = None
    source_verification_hash_valid: bool = False
    source_drift_artifact_sha256: str | None = None
    source_drift_hash_valid: bool = False
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _attestation_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleAttestationVerificationView(BaseModel):
    """Read-plane summary for attestation verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_attestation_verification_view/v1"] = "paper_execution_evidence_bundle_attestation_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_attestation_artifact_path: str | None = None
    source_attestation_declared_sha256: str | None = None
    source_attestation_computed_sha256: str | None = None
    source_attestation_status: str | None = None
    source_attestation_trust_banner: str | None = None
    artifact_hash_valid: bool = False
    statement_payload_hash_valid: bool = False
    envelope_payload_hash_valid: bool = False
    keyless_stub_signature_valid: bool = False
    source_bundle_hash_valid: bool = False
    source_verification_hash_valid: bool = False
    source_drift_hash_valid: bool = False
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleClosureArtifact(BaseModel):
    """Durable final review packet for a paper execution evidence bundle chain.

    Closure is a read-only operator review artifact. It aggregates the latest
    sealed bundle, bundle verification, drift check, keyless attestation, and
    attestation verification into one final decision posture. It never submits
    orders, grants live authority, promotes strategies, or mutates the ledger.
    """

    schema_version: Literal["paper_execution_evidence_bundle_closure/v1"] = "paper_execution_evidence_bundle_closure/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    closure_authority: Literal["CLI_REVIEW_PACKET_ONLY"] = "CLI_REVIEW_PACKET_ONLY"
    closure_status: Literal["READY_FOR_OPERATOR_REVIEW", "READY_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_bundle_artifact_path: str | None = None
    source_bundle_sha256: str | None = None
    source_bundle_status: str | None = None
    source_bundle_trust_banner: str | None = None
    source_verification_artifact_path: str | None = None
    source_verification_artifact_sha256: str | None = None
    source_verification_status: str | None = None
    source_verification_trust_banner: str | None = None
    source_drift_artifact_path: str | None = None
    source_drift_artifact_sha256: str | None = None
    source_drift_status: str | None = None
    source_drift_trust_banner: str | None = None
    source_attestation_artifact_path: str | None = None
    source_attestation_artifact_sha256: str | None = None
    source_attestation_status: str | None = None
    source_attestation_trust_banner: str | None = None
    source_attestation_verification_artifact_path: str | None = None
    source_attestation_verification_artifact_sha256: str | None = None
    source_attestation_verification_status: str | None = None
    source_attestation_verification_trust_banner: str | None = None
    source_attestation_artifact_hash_valid: bool = False
    source_attestation_statement_hash_valid: bool = False
    source_attestation_envelope_hash_valid: bool = False
    source_attestation_keyless_stub_valid: bool = False
    source_attestation_bundle_hash_valid: bool = False
    source_attestation_bundle_verification_hash_valid: bool = False
    source_attestation_drift_hash_valid: bool = False
    closure_reason_codes: list[str] = Field(default_factory=list)
    recommended_operator_sequence: list[str] = Field(default_factory=list)
    one_command_sequence_hint: str | None = None
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _closure_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleClosureView(BaseModel):
    """Read-plane summary of a paper execution evidence-bundle closure packet."""

    schema_version: Literal["paper_execution_evidence_bundle_closure_view/v1"] = "paper_execution_evidence_bundle_closure_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    closure_status: Literal["READY_FOR_OPERATOR_REVIEW", "READY_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_bundle_sha256: str | None = None
    source_bundle_status: str | None = None
    source_verification_status: str | None = None
    source_drift_status: str | None = None
    source_attestation_status: str | None = None
    source_attestation_verification_status: str | None = None
    source_attestation_artifact_hash_valid: bool = False
    source_attestation_statement_hash_valid: bool = False
    source_attestation_envelope_hash_valid: bool = False
    source_attestation_keyless_stub_valid: bool = False
    source_attestation_bundle_hash_valid: bool = False
    source_attestation_bundle_verification_hash_valid: bool = False
    source_attestation_drift_hash_valid: bool = False
    closure_reason_codes: list[str] = Field(default_factory=list)
    recommended_operator_sequence: list[str] = Field(default_factory=list)
    one_command_sequence_hint: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleClosureVerificationArtifact(BaseModel):
    """Read-only verification result for a paper evidence-bundle closure packet.

    The verifier recomputes the closure packet digest and re-hashes every
    source artifact referenced by the closure packet. It is deliberately
    read-only: no broker orders, no live authority, no promotion authority,
    and no decision-ledger mutation.
    """

    schema_version: Literal["paper_execution_evidence_bundle_closure_verification/v1"] = "paper_execution_evidence_bundle_closure_verification/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    verification_authority: Literal["READ_ONLY"] = "READ_ONLY"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_closure_artifact_path: str | None = None
    source_closure_declared_sha256: str | None = None
    source_closure_computed_sha256: str | None = None
    source_closure_status: str | None = None
    source_closure_trust_banner: str | None = None
    closure_artifact_hash_valid: bool = False
    source_bundle_sha256: str | None = None
    source_bundle_hash_valid: bool = False
    source_verification_artifact_sha256: str | None = None
    source_verification_hash_valid: bool = False
    source_drift_artifact_sha256: str | None = None
    source_drift_hash_valid: bool = False
    source_attestation_artifact_sha256: str | None = None
    source_attestation_hash_valid: bool = False
    source_attestation_verification_artifact_sha256: str | None = None
    source_attestation_verification_hash_valid: bool = False
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _closure_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleClosureVerificationView(BaseModel):
    """Read-plane summary for closure packet verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_closure_verification_view/v1"] = "paper_execution_evidence_bundle_closure_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_closure_artifact_path: str | None = None
    source_closure_declared_sha256: str | None = None
    source_closure_computed_sha256: str | None = None
    source_closure_status: str | None = None
    source_closure_trust_banner: str | None = None
    closure_artifact_hash_valid: bool = False
    source_bundle_hash_valid: bool = False
    source_verification_hash_valid: bool = False
    source_drift_hash_valid: bool = False
    source_attestation_hash_valid: bool = False
    source_attestation_verification_hash_valid: bool = False
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleExportEntry(BaseModel):
    """Single artifact row in a paper evidence-chain export handoff manifest."""

    schema_version: Literal["paper_execution_evidence_bundle_export_entry/v1"] = "paper_execution_evidence_bundle_export_entry/v1"
    kind: str
    artifact_path: str | None = None
    handoff_name: str
    declared_sha256: str | None = None
    computed_sha256: str | None = None
    file_sha256: str | None = None
    size_bytes: int | None = None
    present: bool = False
    digest_valid: bool = False

    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleExportManifestArtifact(BaseModel):
    """Read-only export handoff manifest for a verified paper evidence chain.

    The manifest inventories the closure-verification artifact, closure packet,
    sealed bundle, bundle verification, drift check, attestation, and
    attestation verification. It does not copy files or grant execution,
    promotion, broker, or ledger mutation authority.
    """

    schema_version: Literal["paper_execution_evidence_bundle_export_manifest/v1"] = "paper_execution_evidence_bundle_export_manifest/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    export_authority: Literal["READ_ONLY_HANDOFF_MANIFEST"] = "READ_ONLY_HANDOFF_MANIFEST"
    export_status: Literal["READY_FOR_EXPORT", "READY_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_closure_verification_artifact_path: str | None = None
    source_closure_verification_artifact_sha256: str | None = None
    source_closure_verification_status: str | None = None
    source_closure_verification_trust_banner: str | None = None
    closure_verification_artifact_hash_valid: bool = False
    source_closure_status: str | None = None
    export_entry_count: int = 0
    export_digest_valid_entry_count: int = 0
    total_size_bytes: int = 0
    export_index_sha256: str | None = None
    entries: list[PaperExecutionEvidenceBundleExportEntry] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _export_manifest_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleExportManifestView(BaseModel):
    """Read-plane summary of a paper evidence-chain export handoff manifest."""

    schema_version: Literal["paper_execution_evidence_bundle_export_manifest_view/v1"] = "paper_execution_evidence_bundle_export_manifest_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    export_status: Literal["READY_FOR_EXPORT", "READY_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_closure_verification_artifact_path: str | None = None
    source_closure_verification_artifact_sha256: str | None = None
    source_closure_verification_status: str | None = None
    source_closure_status: str | None = None
    closure_verification_artifact_hash_valid: bool = False
    export_entry_count: int = 0
    export_digest_valid_entry_count: int = 0
    total_size_bytes: int = 0
    export_index_sha256: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleExportVerificationEntry(BaseModel):
    """Verification row for one retained export handoff artifact entry."""

    schema_version: Literal["paper_execution_evidence_bundle_export_verification_entry/v1"] = "paper_execution_evidence_bundle_export_verification_entry/v1"
    kind: str
    artifact_path: str | None = None
    handoff_name: str | None = None
    declared_sha256: str | None = None
    manifest_computed_sha256: str | None = None
    recomputed_sha256: str | None = None
    manifest_file_sha256: str | None = None
    recomputed_file_sha256: str | None = None
    manifest_size_bytes: int | None = None
    recomputed_size_bytes: int | None = None
    present: bool = False
    manifest_entry_digest_valid: bool = False
    declared_digest_valid: bool = False
    manifest_computed_digest_valid: bool = False
    file_digest_valid: bool = False
    size_valid: bool = False
    verification_digest_valid: bool = False

    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleExportVerificationArtifact(BaseModel):
    """Read-only verification result for a paper evidence-chain export manifest.

    The verifier recomputes the export manifest digest, the export index digest,
    and every retained artifact digest/size declared by the manifest. It never
    copies files and has no trading, promotion, or ledger authority.
    """

    schema_version: Literal["paper_execution_evidence_bundle_export_verification/v1"] = "paper_execution_evidence_bundle_export_verification/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    verification_authority: Literal["READ_ONLY"] = "READ_ONLY"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_export_manifest_artifact_path: str | None = None
    source_export_manifest_declared_sha256: str | None = None
    source_export_manifest_computed_sha256: str | None = None
    source_export_manifest_status: str | None = None
    source_export_manifest_trust_banner: str | None = None
    export_manifest_hash_valid: bool = False
    source_export_index_declared_sha256: str | None = None
    source_export_index_computed_sha256: str | None = None
    export_index_hash_valid: bool = False
    source_export_entry_count: int = 0
    source_export_digest_valid_entry_count: int = 0
    recomputed_export_entry_count: int = 0
    recomputed_export_digest_valid_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    entries: list[PaperExecutionEvidenceBundleExportVerificationEntry] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _export_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleExportVerificationView(BaseModel):
    """Read-plane summary of export handoff verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_export_verification_view/v1"] = "paper_execution_evidence_bundle_export_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_export_manifest_artifact_path: str | None = None
    source_export_manifest_declared_sha256: str | None = None
    source_export_manifest_computed_sha256: str | None = None
    source_export_manifest_status: str | None = None
    source_export_manifest_trust_banner: str | None = None
    export_manifest_hash_valid: bool = False
    source_export_index_declared_sha256: str | None = None
    source_export_index_computed_sha256: str | None = None
    export_index_hash_valid: bool = False
    source_export_entry_count: int = 0
    source_export_digest_valid_entry_count: int = 0
    recomputed_export_entry_count: int = 0
    recomputed_export_digest_valid_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}




class PaperExecutionEvidenceBundleRetentionReceiptEntry(BaseModel):
    """Single verified artifact row in a paper evidence-chain retention receipt."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_receipt_entry/v1"] = "paper_execution_evidence_bundle_retention_receipt_entry/v1"
    kind: str
    artifact_path: str | None = None
    handoff_name: str | None = None
    retention_name: str
    declared_sha256: str | None = None
    verified_sha256: str | None = None
    file_sha256: str | None = None
    expected_file_sha256: str | None = None
    size_bytes: int | None = None
    expected_size_bytes: int | None = None
    present: bool = False
    source_verification_digest_valid: bool = False
    file_digest_valid: bool = False
    size_valid: bool = False
    ready_for_retention: bool = False

    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionReceiptArtifact(BaseModel):
    """Read-only receipt describing the verified export artifacts to retain."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_receipt/v1"] = "paper_execution_evidence_bundle_retention_receipt/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    retention_authority: Literal["READ_ONLY_RETENTION_RECEIPT"] = "READ_ONLY_RETENTION_RECEIPT"
    retention_status: Literal["READY_FOR_RETENTION", "READY_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_export_verification_artifact_path: str | None = None
    source_export_verification_artifact_sha256: str | None = None
    source_export_verification_computed_sha256: str | None = None
    source_export_verification_status: str | None = None
    source_export_verification_trust_banner: str | None = None
    export_verification_artifact_hash_valid: bool = False
    source_export_manifest_artifact_path: str | None = None
    source_export_manifest_sha256: str | None = None
    source_export_manifest_status: str | None = None
    source_export_index_sha256: str | None = None
    retained_entry_count: int = 0
    retained_ready_entry_count: int = 0
    total_size_bytes: int = 0
    retention_index_sha256: str | None = None
    entries: list[PaperExecutionEvidenceBundleRetentionReceiptEntry] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_receipt_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionReceiptView(BaseModel):
    """Read-plane summary of a paper evidence-chain retention receipt."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_receipt_view/v1"] = "paper_execution_evidence_bundle_retention_receipt_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    retention_status: Literal["READY_FOR_RETENTION", "READY_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_export_verification_artifact_path: str | None = None
    source_export_verification_artifact_sha256: str | None = None
    source_export_verification_status: str | None = None
    source_export_manifest_artifact_path: str | None = None
    source_export_manifest_status: str | None = None
    export_verification_artifact_hash_valid: bool = False
    retained_entry_count: int = 0
    retained_ready_entry_count: int = 0
    total_size_bytes: int = 0
    retention_index_sha256: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionVerificationEntry(BaseModel):
    """Single retained artifact row rechecked from a retention receipt."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_verification_entry/v1"] = "paper_execution_evidence_bundle_retention_verification_entry/v1"
    kind: str
    artifact_path: str | None = None
    retention_name: str | None = None
    receipt_declared_sha256: str | None = None
    receipt_verified_sha256: str | None = None
    receipt_file_sha256: str | None = None
    receipt_expected_file_sha256: str | None = None
    recomputed_file_sha256: str | None = None
    receipt_size_bytes: int | None = None
    receipt_expected_size_bytes: int | None = None
    recomputed_size_bytes: int | None = None
    present: bool = False
    retention_entry_ready: bool = False
    source_verification_digest_valid: bool = False
    file_digest_valid: bool = False
    size_valid: bool = False
    verification_digest_valid: bool = False

    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionVerificationArtifact(BaseModel):
    """Read-only verifier for a paper evidence-chain retention receipt."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_verification/v1"] = "paper_execution_evidence_bundle_retention_verification/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    retention_authority: Literal["READ_ONLY_RETENTION_VERIFICATION"] = "READ_ONLY_RETENTION_VERIFICATION"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_receipt_artifact_path: str | None = None
    source_retention_receipt_declared_sha256: str | None = None
    source_retention_receipt_computed_sha256: str | None = None
    source_retention_receipt_status: str | None = None
    source_retention_receipt_trust_banner: str | None = None
    retention_receipt_hash_valid: bool = False
    source_retention_index_declared_sha256: str | None = None
    source_retention_index_computed_sha256: str | None = None
    retention_index_hash_valid: bool = False
    source_retention_entry_count: int = 0
    source_retention_ready_entry_count: int = 0
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    entries: list[PaperExecutionEvidenceBundleRetentionVerificationEntry] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionVerificationView(BaseModel):
    """Read-plane summary of retention receipt verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_verification_view/v1"] = "paper_execution_evidence_bundle_retention_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_receipt_artifact_path: str | None = None
    source_retention_receipt_declared_sha256: str | None = None
    source_retention_receipt_computed_sha256: str | None = None
    source_retention_receipt_status: str | None = None
    source_retention_receipt_trust_banner: str | None = None
    retention_receipt_hash_valid: bool = False
    source_retention_index_declared_sha256: str | None = None
    source_retention_index_computed_sha256: str | None = None
    retention_index_hash_valid: bool = False
    source_retention_entry_count: int = 0
    source_retention_ready_entry_count: int = 0
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionSignoffArtifact(BaseModel):
    """Read-only operator signoff certificate for a verified retention receipt."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_signoff/v1"] = "paper_execution_evidence_bundle_retention_signoff/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    signoff_authority: Literal["READ_ONLY_OPERATOR_SIGNOFF"] = "READ_ONLY_OPERATOR_SIGNOFF"
    signoff_status: Literal["SIGNED_OFF", "SIGNED_OFF_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    operator_id: str = "operator"
    decision_note: str | None = None
    source_retention_verification_artifact_path: str | None = None
    source_retention_verification_declared_sha256: str | None = None
    source_retention_verification_computed_sha256: str | None = None
    source_retention_verification_status: str | None = None
    source_retention_verification_trust_banner: str | None = None
    retention_verification_artifact_hash_valid: bool = False
    source_retention_receipt_artifact_path: str | None = None
    source_retention_receipt_status: str | None = None
    source_retention_index_sha256: str | None = None
    source_retention_entry_count: int = 0
    source_retention_ready_entry_count: int = 0
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    checklist: list[str] = Field(default_factory=list)
    signoff_statement_sha256: str | None = None
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_signoff_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionSignoffView(BaseModel):
    """Read-plane summary of paper retention signoff certificates."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_signoff_view/v1"] = "paper_execution_evidence_bundle_retention_signoff_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    signoff_status: Literal["SIGNED_OFF", "SIGNED_OFF_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    operator_id: str | None = None
    decision_note: str | None = None
    source_retention_verification_artifact_path: str | None = None
    source_retention_verification_declared_sha256: str | None = None
    source_retention_verification_status: str | None = None
    source_retention_verification_trust_banner: str | None = None
    retention_verification_artifact_hash_valid: bool = False
    source_retention_receipt_artifact_path: str | None = None
    source_retention_receipt_status: str | None = None
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    signoff_statement_sha256: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionSignoffVerificationArtifact(BaseModel):
    """Read-only verifier for a paper retention signoff certificate."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_signoff_verification/v1"] = "paper_execution_evidence_bundle_retention_signoff_verification/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    signoff_verification_authority: Literal["READ_ONLY_SIGNOFF_VERIFICATION"] = "READ_ONLY_SIGNOFF_VERIFICATION"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_signoff_artifact_path: str | None = None
    source_retention_signoff_declared_sha256: str | None = None
    source_retention_signoff_computed_sha256: str | None = None
    source_retention_signoff_status: str | None = None
    source_retention_signoff_trust_banner: str | None = None
    retention_signoff_artifact_hash_valid: bool = False
    operator_id: str | None = None
    decision_note: str | None = None
    signoff_statement_declared_sha256: str | None = None
    signoff_statement_computed_sha256: str | None = None
    signoff_statement_hash_valid: bool = False
    source_retention_verification_artifact_path: str | None = None
    source_retention_verification_declared_sha256: str | None = None
    source_retention_verification_computed_sha256: str | None = None
    source_retention_verification_recomputed_sha256: str | None = None
    source_retention_verification_status: str | None = None
    source_retention_verification_trust_banner: str | None = None
    retention_verification_artifact_hash_valid: bool = False
    source_retention_receipt_artifact_path: str | None = None
    source_retention_receipt_status: str | None = None
    source_retention_index_sha256: str | None = None
    source_retention_entry_count: int = 0
    source_retention_ready_entry_count: int = 0
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_signoff_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionSignoffVerificationView(BaseModel):
    """Read-plane summary of retention signoff verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_signoff_verification_view/v1"] = "paper_execution_evidence_bundle_retention_signoff_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_signoff_artifact_path: str | None = None
    source_retention_signoff_declared_sha256: str | None = None
    source_retention_signoff_computed_sha256: str | None = None
    source_retention_signoff_status: str | None = None
    source_retention_signoff_trust_banner: str | None = None
    retention_signoff_artifact_hash_valid: bool = False
    operator_id: str | None = None
    decision_note: str | None = None
    signoff_statement_declared_sha256: str | None = None
    signoff_statement_computed_sha256: str | None = None
    signoff_statement_hash_valid: bool = False
    source_retention_verification_artifact_path: str | None = None
    source_retention_verification_declared_sha256: str | None = None
    source_retention_verification_status: str | None = None
    source_retention_verification_trust_banner: str | None = None
    retention_verification_artifact_hash_valid: bool = False
    source_retention_receipt_artifact_path: str | None = None
    source_retention_receipt_status: str | None = None
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionHandoffArtifact(BaseModel):
    """Read-only custody handoff capsule for verified paper evidence retention."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_handoff/v1"] = "paper_execution_evidence_bundle_retention_handoff/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    handoff_authority: Literal["READ_ONLY_RETENTION_HANDOFF"] = "READ_ONLY_RETENTION_HANDOFF"
    handoff_status: Literal["READY_FOR_HANDOFF", "READY_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custodian_id: str | None = None
    handoff_note: str | None = None
    source_retention_signoff_verification_artifact_path: str | None = None
    source_retention_signoff_verification_declared_sha256: str | None = None
    source_retention_signoff_verification_computed_sha256: str | None = None
    source_retention_signoff_verification_status: str | None = None
    source_retention_signoff_verification_trust_banner: str | None = None
    retention_signoff_verification_artifact_hash_valid: bool = False
    source_retention_signoff_artifact_path: str | None = None
    source_retention_signoff_status: str | None = None
    source_retention_signoff_trust_banner: str | None = None
    retention_signoff_artifact_hash_valid: bool = False
    signoff_statement_hash_valid: bool = False
    source_retention_verification_artifact_path: str | None = None
    source_retention_verification_status: str | None = None
    retention_verification_artifact_hash_valid: bool = False
    source_retention_receipt_artifact_path: str | None = None
    source_retention_receipt_status: str | None = None
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    handoff_statement_sha256: str | None = None
    checklist: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_handoff_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionHandoffView(BaseModel):
    """Read-plane summary of paper evidence retention handoff capsules."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_handoff_view/v1"] = "paper_execution_evidence_bundle_retention_handoff_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    handoff_status: Literal["READY_FOR_HANDOFF", "READY_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custodian_id: str | None = None
    handoff_note: str | None = None
    source_retention_signoff_verification_artifact_path: str | None = None
    source_retention_signoff_verification_declared_sha256: str | None = None
    source_retention_signoff_verification_status: str | None = None
    source_retention_signoff_verification_trust_banner: str | None = None
    retention_signoff_verification_artifact_hash_valid: bool = False
    source_retention_signoff_artifact_path: str | None = None
    source_retention_signoff_status: str | None = None
    source_retention_signoff_trust_banner: str | None = None
    retention_signoff_artifact_hash_valid: bool = False
    signoff_statement_hash_valid: bool = False
    source_retention_verification_artifact_path: str | None = None
    source_retention_verification_status: str | None = None
    retention_verification_artifact_hash_valid: bool = False
    source_retention_receipt_artifact_path: str | None = None
    source_retention_receipt_status: str | None = None
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    handoff_statement_sha256: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionHandoffVerificationArtifact(BaseModel):
    """Read-only verifier for paper evidence retention handoff capsules."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_handoff_verification/v1"] = "paper_execution_evidence_bundle_retention_handoff_verification/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    handoff_verification_authority: Literal["READ_ONLY_RETENTION_HANDOFF_VERIFICATION"] = "READ_ONLY_RETENTION_HANDOFF_VERIFICATION"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_handoff_artifact_path: str | None = None
    source_retention_handoff_declared_sha256: str | None = None
    source_retention_handoff_computed_sha256: str | None = None
    source_retention_handoff_status: str | None = None
    source_retention_handoff_trust_banner: str | None = None
    retention_handoff_artifact_hash_valid: bool = False
    custodian_id: str | None = None
    handoff_note: str | None = None
    handoff_statement_declared_sha256: str | None = None
    handoff_statement_computed_sha256: str | None = None
    handoff_statement_hash_valid: bool = False
    source_retention_signoff_verification_artifact_path: str | None = None
    source_retention_signoff_verification_declared_sha256: str | None = None
    source_retention_signoff_verification_computed_sha256: str | None = None
    source_retention_signoff_verification_recomputed_sha256: str | None = None
    source_retention_signoff_verification_status: str | None = None
    source_retention_signoff_verification_trust_banner: str | None = None
    retention_signoff_verification_artifact_hash_valid: bool = False
    retention_signoff_artifact_hash_valid: bool = False
    signoff_statement_hash_valid: bool = False
    retention_verification_artifact_hash_valid: bool = False
    source_retention_receipt_artifact_path: str | None = None
    source_retention_receipt_status: str | None = None
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_handoff_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionHandoffVerificationView(BaseModel):
    """Read-plane summary of paper evidence retention handoff verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_handoff_verification_view/v1"] = "paper_execution_evidence_bundle_retention_handoff_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_handoff_artifact_path: str | None = None
    source_retention_handoff_declared_sha256: str | None = None
    source_retention_handoff_computed_sha256: str | None = None
    source_retention_handoff_status: str | None = None
    source_retention_handoff_trust_banner: str | None = None
    retention_handoff_artifact_hash_valid: bool = False
    custodian_id: str | None = None
    handoff_note: str | None = None
    handoff_statement_declared_sha256: str | None = None
    handoff_statement_computed_sha256: str | None = None
    handoff_statement_hash_valid: bool = False
    source_retention_signoff_verification_artifact_path: str | None = None
    source_retention_signoff_verification_declared_sha256: str | None = None
    source_retention_signoff_verification_status: str | None = None
    source_retention_signoff_verification_trust_banner: str | None = None
    retention_signoff_verification_artifact_hash_valid: bool = False
    retention_signoff_artifact_hash_valid: bool = False
    signoff_statement_hash_valid: bool = False
    retention_verification_artifact_hash_valid: bool = False
    source_retention_receipt_artifact_path: str | None = None
    source_retention_receipt_status: str | None = None
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionHandoffAcceptanceArtifact(BaseModel):
    """Read-only custodian acceptance certificate for paper evidence retention handoff."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_handoff_acceptance/v1"] = "paper_execution_evidence_bundle_retention_handoff_acceptance/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    acceptance_authority: Literal["READ_ONLY_RETENTION_HANDOFF_ACCEPTANCE"] = "READ_ONLY_RETENTION_HANDOFF_ACCEPTANCE"
    acceptance_status: Literal["ACCEPTED_FOR_CUSTODY", "ACCEPTED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    accepting_custodian_id: str | None = None
    custody_location: str | None = None
    acceptance_note: str | None = None
    source_retention_handoff_verification_artifact_path: str | None = None
    source_retention_handoff_verification_declared_sha256: str | None = None
    source_retention_handoff_verification_computed_sha256: str | None = None
    source_retention_handoff_verification_status: str | None = None
    source_retention_handoff_verification_trust_banner: str | None = None
    retention_handoff_verification_artifact_hash_valid: bool = False
    source_retention_handoff_artifact_path: str | None = None
    source_retention_handoff_status: str | None = None
    source_retention_handoff_trust_banner: str | None = None
    retention_handoff_artifact_hash_valid: bool = False
    handoff_statement_hash_valid: bool = False
    retention_signoff_verification_artifact_hash_valid: bool = False
    source_retention_receipt_artifact_path: str | None = None
    source_retention_receipt_status: str | None = None
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    acceptance_statement_sha256: str | None = None
    checklist: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_handoff_acceptance_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionHandoffAcceptanceView(BaseModel):
    """Read-plane summary of paper evidence retention handoff acceptance certificates."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_handoff_acceptance_view/v1"] = "paper_execution_evidence_bundle_retention_handoff_acceptance_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    acceptance_status: Literal["ACCEPTED_FOR_CUSTODY", "ACCEPTED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    accepting_custodian_id: str | None = None
    custody_location: str | None = None
    acceptance_note: str | None = None
    source_retention_handoff_verification_artifact_path: str | None = None
    source_retention_handoff_verification_declared_sha256: str | None = None
    source_retention_handoff_verification_status: str | None = None
    source_retention_handoff_verification_trust_banner: str | None = None
    retention_handoff_verification_artifact_hash_valid: bool = False
    source_retention_handoff_artifact_path: str | None = None
    source_retention_handoff_status: str | None = None
    source_retention_handoff_trust_banner: str | None = None
    retention_handoff_artifact_hash_valid: bool = False
    handoff_statement_hash_valid: bool = False
    retention_signoff_verification_artifact_hash_valid: bool = False
    source_retention_receipt_artifact_path: str | None = None
    source_retention_receipt_status: str | None = None
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    acceptance_statement_sha256: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionHandoffAcceptanceVerificationArtifact(BaseModel):
    """Read-only verifier for paper evidence retention handoff acceptance certificates."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_handoff_acceptance_verification/v1"] = "paper_execution_evidence_bundle_retention_handoff_acceptance_verification/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    acceptance_verification_authority: Literal["READ_ONLY_RETENTION_HANDOFF_ACCEPTANCE_VERIFICATION"] = "READ_ONLY_RETENTION_HANDOFF_ACCEPTANCE_VERIFICATION"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_handoff_acceptance_artifact_path: str | None = None
    source_retention_handoff_acceptance_declared_sha256: str | None = None
    source_retention_handoff_acceptance_computed_sha256: str | None = None
    source_retention_handoff_acceptance_status: str | None = None
    source_retention_handoff_acceptance_trust_banner: str | None = None
    retention_handoff_acceptance_artifact_hash_valid: bool = False
    accepting_custodian_id: str | None = None
    custody_location: str | None = None
    acceptance_note: str | None = None
    acceptance_statement_declared_sha256: str | None = None
    acceptance_statement_computed_sha256: str | None = None
    acceptance_statement_hash_valid: bool = False
    source_retention_handoff_verification_artifact_path: str | None = None
    source_retention_handoff_verification_declared_sha256: str | None = None
    source_retention_handoff_verification_computed_sha256: str | None = None
    source_retention_handoff_verification_recomputed_sha256: str | None = None
    source_retention_handoff_verification_status: str | None = None
    source_retention_handoff_verification_trust_banner: str | None = None
    retention_handoff_verification_artifact_hash_valid: bool = False
    retention_handoff_artifact_hash_valid: bool = False
    handoff_statement_hash_valid: bool = False
    retention_signoff_verification_artifact_hash_valid: bool = False
    source_retention_receipt_artifact_path: str | None = None
    source_retention_receipt_status: str | None = None
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_handoff_acceptance_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionHandoffAcceptanceVerificationView(BaseModel):
    """Read-plane summary of paper evidence retention handoff acceptance verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_handoff_acceptance_verification_view/v1"] = "paper_execution_evidence_bundle_retention_handoff_acceptance_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_handoff_acceptance_artifact_path: str | None = None
    source_retention_handoff_acceptance_declared_sha256: str | None = None
    source_retention_handoff_acceptance_computed_sha256: str | None = None
    source_retention_handoff_acceptance_status: str | None = None
    source_retention_handoff_acceptance_trust_banner: str | None = None
    retention_handoff_acceptance_artifact_hash_valid: bool = False
    accepting_custodian_id: str | None = None
    custody_location: str | None = None
    acceptance_note: str | None = None
    acceptance_statement_declared_sha256: str | None = None
    acceptance_statement_computed_sha256: str | None = None
    acceptance_statement_hash_valid: bool = False
    source_retention_handoff_verification_artifact_path: str | None = None
    source_retention_handoff_verification_declared_sha256: str | None = None
    source_retention_handoff_verification_status: str | None = None
    source_retention_handoff_verification_trust_banner: str | None = None
    retention_handoff_verification_artifact_hash_valid: bool = False
    retention_handoff_artifact_hash_valid: bool = False
    handoff_statement_hash_valid: bool = False
    retention_signoff_verification_artifact_hash_valid: bool = False
    source_retention_receipt_artifact_path: str | None = None
    source_retention_receipt_status: str | None = None
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyRegisterArtifact(BaseModel):
    """Read-only custody register entry for accepted paper evidence retention."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_register/v1"] = "paper_execution_evidence_bundle_retention_custody_register/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    register_authority: Literal["READ_ONLY_RETENTION_CUSTODY_REGISTER"] = "READ_ONLY_RETENTION_CUSTODY_REGISTER"
    register_status: Literal["REGISTERED", "REGISTERED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_register_id: str | None = None
    registered_by: str | None = None
    custody_location: str | None = None
    register_note: str | None = None
    source_retention_handoff_acceptance_verification_artifact_path: str | None = None
    source_retention_handoff_acceptance_verification_declared_sha256: str | None = None
    source_retention_handoff_acceptance_verification_computed_sha256: str | None = None
    source_retention_handoff_acceptance_verification_status: str | None = None
    source_retention_handoff_acceptance_verification_trust_banner: str | None = None
    retention_handoff_acceptance_verification_artifact_hash_valid: bool = False
    source_retention_handoff_acceptance_artifact_path: str | None = None
    source_retention_handoff_acceptance_status: str | None = None
    source_retention_handoff_acceptance_trust_banner: str | None = None
    retention_handoff_acceptance_artifact_hash_valid: bool = False
    acceptance_statement_hash_valid: bool = False
    retention_handoff_verification_artifact_hash_valid: bool = False
    retention_handoff_artifact_hash_valid: bool = False
    handoff_statement_hash_valid: bool = False
    retention_signoff_verification_artifact_hash_valid: bool = False
    source_retention_receipt_artifact_path: str | None = None
    source_retention_receipt_status: str | None = None
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_register_statement_sha256: str | None = None
    checklist: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_register_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyRegisterView(BaseModel):
    """Read-plane summary of paper evidence retention custody register entries."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_register_view/v1"] = "paper_execution_evidence_bundle_retention_custody_register_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    register_status: Literal["REGISTERED", "REGISTERED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_register_id: str | None = None
    registered_by: str | None = None
    custody_location: str | None = None
    register_note: str | None = None
    source_retention_handoff_acceptance_verification_artifact_path: str | None = None
    source_retention_handoff_acceptance_verification_declared_sha256: str | None = None
    source_retention_handoff_acceptance_verification_status: str | None = None
    retention_handoff_acceptance_verification_artifact_hash_valid: bool = False
    source_retention_handoff_acceptance_status: str | None = None
    retention_handoff_acceptance_artifact_hash_valid: bool = False
    acceptance_statement_hash_valid: bool = False
    retention_handoff_verification_artifact_hash_valid: bool = False
    retention_handoff_artifact_hash_valid: bool = False
    handoff_statement_hash_valid: bool = False
    retention_signoff_verification_artifact_hash_valid: bool = False
    source_retention_receipt_artifact_path: str | None = None
    source_retention_receipt_status: str | None = None
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_register_statement_sha256: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyRegisterVerificationArtifact(BaseModel):
    """Read-only verifier for paper evidence retention custody register entries."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_register_verification/v1"] = "paper_execution_evidence_bundle_retention_custody_register_verification/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    register_verification_authority: Literal["READ_ONLY_RETENTION_CUSTODY_REGISTER_VERIFICATION"] = "READ_ONLY_RETENTION_CUSTODY_REGISTER_VERIFICATION"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_register_artifact_path: str | None = None
    source_retention_custody_register_declared_sha256: str | None = None
    source_retention_custody_register_computed_sha256: str | None = None
    source_retention_custody_register_status: str | None = None
    source_retention_custody_register_trust_banner: str | None = None
    retention_custody_register_artifact_hash_valid: bool = False
    custody_register_id: str | None = None
    registered_by: str | None = None
    custody_location: str | None = None
    register_note: str | None = None
    custody_register_statement_declared_sha256: str | None = None
    custody_register_statement_computed_sha256: str | None = None
    custody_register_statement_hash_valid: bool = False
    source_retention_handoff_acceptance_verification_artifact_path: str | None = None
    source_retention_handoff_acceptance_verification_declared_sha256: str | None = None
    source_retention_handoff_acceptance_verification_status: str | None = None
    retention_handoff_acceptance_verification_artifact_hash_valid: bool = False
    retention_handoff_acceptance_artifact_hash_valid: bool = False
    acceptance_statement_hash_valid: bool = False
    retention_handoff_verification_artifact_hash_valid: bool = False
    retention_handoff_artifact_hash_valid: bool = False
    handoff_statement_hash_valid: bool = False
    retention_signoff_verification_artifact_hash_valid: bool = False
    source_retention_receipt_artifact_path: str | None = None
    source_retention_receipt_status: str | None = None
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_register_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyRegisterVerificationView(BaseModel):
    """Read-plane summary of paper evidence retention custody register verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_register_verification_view/v1"] = "paper_execution_evidence_bundle_retention_custody_register_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_register_artifact_path: str | None = None
    source_retention_custody_register_declared_sha256: str | None = None
    source_retention_custody_register_computed_sha256: str | None = None
    source_retention_custody_register_status: str | None = None
    retention_custody_register_artifact_hash_valid: bool = False
    custody_register_id: str | None = None
    registered_by: str | None = None
    custody_location: str | None = None
    register_note: str | None = None
    custody_register_statement_declared_sha256: str | None = None
    custody_register_statement_computed_sha256: str | None = None
    custody_register_statement_hash_valid: bool = False
    source_retention_handoff_acceptance_verification_artifact_path: str | None = None
    source_retention_handoff_acceptance_verification_declared_sha256: str | None = None
    source_retention_handoff_acceptance_verification_status: str | None = None
    retention_handoff_acceptance_verification_artifact_hash_valid: bool = False
    retention_handoff_acceptance_artifact_hash_valid: bool = False
    acceptance_statement_hash_valid: bool = False
    retention_handoff_verification_artifact_hash_valid: bool = False
    retention_handoff_artifact_hash_valid: bool = False
    handoff_statement_hash_valid: bool = False
    retention_signoff_verification_artifact_hash_valid: bool = False
    source_retention_receipt_artifact_path: str | None = None
    source_retention_receipt_status: str | None = None
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}




class PaperExecutionEvidenceBundleRetentionCustodySealArtifact(BaseModel):
    """Read-only final seal for verified paper evidence retention custody."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_seal/v1"] = "paper_execution_evidence_bundle_retention_custody_seal/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    seal_authority: Literal["READ_ONLY_RETENTION_CUSTODY_SEAL"] = "READ_ONLY_RETENTION_CUSTODY_SEAL"
    seal_status: Literal["SEALED", "SEALED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_seal_id: str | None = None
    sealed_by: str | None = None
    custody_location: str | None = None
    seal_note: str | None = None
    source_retention_custody_register_verification_artifact_path: str | None = None
    source_retention_custody_register_verification_declared_sha256: str | None = None
    source_retention_custody_register_verification_computed_sha256: str | None = None
    source_retention_custody_register_verification_status: str | None = None
    source_retention_custody_register_verification_trust_banner: str | None = None
    retention_custody_register_verification_artifact_hash_valid: bool = False
    source_retention_custody_register_artifact_path: str | None = None
    source_retention_custody_register_status: str | None = None
    source_retention_custody_register_trust_banner: str | None = None
    retention_custody_register_artifact_hash_valid: bool = False
    custody_register_id: str | None = None
    custody_register_statement_hash_valid: bool = False
    source_retention_handoff_acceptance_verification_artifact_path: str | None = None
    source_retention_handoff_acceptance_verification_status: str | None = None
    retention_handoff_acceptance_verification_artifact_hash_valid: bool = False
    retention_handoff_acceptance_artifact_hash_valid: bool = False
    acceptance_statement_hash_valid: bool = False
    retention_handoff_verification_artifact_hash_valid: bool = False
    retention_handoff_artifact_hash_valid: bool = False
    handoff_statement_hash_valid: bool = False
    retention_signoff_verification_artifact_hash_valid: bool = False
    source_retention_receipt_artifact_path: str | None = None
    source_retention_receipt_status: str | None = None
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_seal_statement_sha256: str | None = None
    checklist: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_seal_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodySealView(BaseModel):
    """Read-plane summary of paper evidence retention custody seals."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_seal_view/v1"] = "paper_execution_evidence_bundle_retention_custody_seal_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    seal_status: Literal["SEALED", "SEALED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_seal_id: str | None = None
    sealed_by: str | None = None
    custody_location: str | None = None
    seal_note: str | None = None
    source_retention_custody_register_verification_artifact_path: str | None = None
    source_retention_custody_register_verification_declared_sha256: str | None = None
    source_retention_custody_register_verification_status: str | None = None
    retention_custody_register_verification_artifact_hash_valid: bool = False
    source_retention_custody_register_status: str | None = None
    retention_custody_register_artifact_hash_valid: bool = False
    custody_register_id: str | None = None
    custody_register_statement_hash_valid: bool = False
    retention_handoff_acceptance_verification_artifact_hash_valid: bool = False
    retention_handoff_acceptance_artifact_hash_valid: bool = False
    acceptance_statement_hash_valid: bool = False
    retention_handoff_verification_artifact_hash_valid: bool = False
    retention_handoff_artifact_hash_valid: bool = False
    handoff_statement_hash_valid: bool = False
    retention_signoff_verification_artifact_hash_valid: bool = False
    source_retention_receipt_artifact_path: str | None = None
    source_retention_receipt_status: str | None = None
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_seal_statement_sha256: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodySealVerificationArtifact(BaseModel):
    """Read-only verifier for paper evidence retention custody seals."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_seal_verification/v1"] = "paper_execution_evidence_bundle_retention_custody_seal_verification/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    seal_verification_authority: Literal["READ_ONLY_RETENTION_CUSTODY_SEAL_VERIFICATION"] = "READ_ONLY_RETENTION_CUSTODY_SEAL_VERIFICATION"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_seal_artifact_path: str | None = None
    source_retention_custody_seal_declared_sha256: str | None = None
    source_retention_custody_seal_computed_sha256: str | None = None
    source_retention_custody_seal_status: str | None = None
    source_retention_custody_seal_trust_banner: str | None = None
    retention_custody_seal_artifact_hash_valid: bool = False
    custody_seal_id: str | None = None
    sealed_by: str | None = None
    custody_location: str | None = None
    seal_note: str | None = None
    custody_seal_statement_declared_sha256: str | None = None
    custody_seal_statement_computed_sha256: str | None = None
    custody_seal_statement_hash_valid: bool = False
    source_retention_custody_register_verification_artifact_path: str | None = None
    source_retention_custody_register_verification_declared_sha256: str | None = None
    source_retention_custody_register_verification_status: str | None = None
    retention_custody_register_verification_artifact_hash_valid: bool = False
    source_retention_custody_register_status: str | None = None
    retention_custody_register_artifact_hash_valid: bool = False
    custody_register_id: str | None = None
    custody_register_statement_hash_valid: bool = False
    retention_handoff_acceptance_verification_artifact_hash_valid: bool = False
    retention_handoff_acceptance_artifact_hash_valid: bool = False
    acceptance_statement_hash_valid: bool = False
    retention_handoff_verification_artifact_hash_valid: bool = False
    retention_handoff_artifact_hash_valid: bool = False
    handoff_statement_hash_valid: bool = False
    retention_signoff_verification_artifact_hash_valid: bool = False
    source_retention_receipt_artifact_path: str | None = None
    source_retention_receipt_status: str | None = None
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_seal_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodySealVerificationView(BaseModel):
    """Read-plane summary of paper evidence retention custody seal verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_seal_verification_view/v1"] = "paper_execution_evidence_bundle_retention_custody_seal_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_seal_artifact_path: str | None = None
    source_retention_custody_seal_declared_sha256: str | None = None
    source_retention_custody_seal_computed_sha256: str | None = None
    source_retention_custody_seal_status: str | None = None
    retention_custody_seal_artifact_hash_valid: bool = False
    custody_seal_id: str | None = None
    sealed_by: str | None = None
    custody_location: str | None = None
    seal_note: str | None = None
    custody_seal_statement_declared_sha256: str | None = None
    custody_seal_statement_computed_sha256: str | None = None
    custody_seal_statement_hash_valid: bool = False
    source_retention_custody_register_verification_artifact_path: str | None = None
    source_retention_custody_register_verification_declared_sha256: str | None = None
    source_retention_custody_register_verification_status: str | None = None
    retention_custody_register_verification_artifact_hash_valid: bool = False
    source_retention_custody_register_status: str | None = None
    retention_custody_register_artifact_hash_valid: bool = False
    custody_register_id: str | None = None
    custody_register_statement_hash_valid: bool = False
    retention_handoff_acceptance_verification_artifact_hash_valid: bool = False
    retention_handoff_acceptance_artifact_hash_valid: bool = False
    acceptance_statement_hash_valid: bool = False
    retention_handoff_verification_artifact_hash_valid: bool = False
    retention_handoff_artifact_hash_valid: bool = False
    handoff_statement_hash_valid: bool = False
    retention_signoff_verification_artifact_hash_valid: bool = False
    source_retention_receipt_artifact_path: str | None = None
    source_retention_receipt_status: str | None = None
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyAuditArtifact(BaseModel):
    """Read-only custody audit certificate for verified paper evidence retention custody."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_audit/v1"] = "paper_execution_evidence_bundle_retention_custody_audit/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    audit_authority: Literal["READ_ONLY_RETENTION_CUSTODY_AUDIT"] = "READ_ONLY_RETENTION_CUSTODY_AUDIT"
    audit_status: Literal["AUDITED", "AUDITED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_audit_id: str | None = None
    audited_by: str | None = None
    custody_location: str | None = None
    audit_note: str | None = None
    source_retention_custody_seal_verification_artifact_path: str | None = None
    source_retention_custody_seal_verification_declared_sha256: str | None = None
    source_retention_custody_seal_verification_computed_sha256: str | None = None
    source_retention_custody_seal_verification_status: str | None = None
    source_retention_custody_seal_verification_trust_banner: str | None = None
    retention_custody_seal_verification_artifact_hash_valid: bool = False
    source_retention_custody_seal_artifact_path: str | None = None
    source_retention_custody_seal_status: str | None = None
    source_retention_custody_seal_trust_banner: str | None = None
    retention_custody_seal_artifact_hash_valid: bool = False
    custody_seal_id: str | None = None
    custody_seal_statement_hash_valid: bool = False
    source_retention_custody_register_verification_artifact_path: str | None = None
    source_retention_custody_register_verification_status: str | None = None
    retention_custody_register_verification_artifact_hash_valid: bool = False
    source_retention_custody_register_status: str | None = None
    retention_custody_register_artifact_hash_valid: bool = False
    custody_register_id: str | None = None
    custody_register_statement_hash_valid: bool = False
    retention_handoff_acceptance_verification_artifact_hash_valid: bool = False
    retention_handoff_acceptance_artifact_hash_valid: bool = False
    acceptance_statement_hash_valid: bool = False
    retention_handoff_verification_artifact_hash_valid: bool = False
    retention_handoff_artifact_hash_valid: bool = False
    handoff_statement_hash_valid: bool = False
    retention_signoff_verification_artifact_hash_valid: bool = False
    source_retention_receipt_artifact_path: str | None = None
    source_retention_receipt_status: str | None = None
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_audit_statement_sha256: str | None = None
    checklist: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_audit_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyAuditView(BaseModel):
    """Read-plane summary of paper evidence retention custody audits."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_audit_view/v1"] = "paper_execution_evidence_bundle_retention_custody_audit_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    audit_status: Literal["AUDITED", "AUDITED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_audit_id: str | None = None
    audited_by: str | None = None
    custody_location: str | None = None
    audit_note: str | None = None
    source_retention_custody_seal_verification_artifact_path: str | None = None
    source_retention_custody_seal_verification_declared_sha256: str | None = None
    source_retention_custody_seal_verification_status: str | None = None
    retention_custody_seal_verification_artifact_hash_valid: bool = False
    source_retention_custody_seal_status: str | None = None
    retention_custody_seal_artifact_hash_valid: bool = False
    custody_seal_id: str | None = None
    custody_seal_statement_hash_valid: bool = False
    retention_custody_register_verification_artifact_hash_valid: bool = False
    retention_custody_register_artifact_hash_valid: bool = False
    custody_register_id: str | None = None
    custody_register_statement_hash_valid: bool = False
    retention_handoff_acceptance_verification_artifact_hash_valid: bool = False
    retention_handoff_acceptance_artifact_hash_valid: bool = False
    acceptance_statement_hash_valid: bool = False
    retention_handoff_verification_artifact_hash_valid: bool = False
    retention_handoff_artifact_hash_valid: bool = False
    handoff_statement_hash_valid: bool = False
    retention_signoff_verification_artifact_hash_valid: bool = False
    source_retention_receipt_artifact_path: str | None = None
    source_retention_receipt_status: str | None = None
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_audit_statement_sha256: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyAuditVerificationArtifact(BaseModel):
    """Read-only verifier for paper evidence retention custody audits."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_audit_verification/v1"] = "paper_execution_evidence_bundle_retention_custody_audit_verification/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    audit_verification_authority: Literal["READ_ONLY_RETENTION_CUSTODY_AUDIT_VERIFICATION"] = "READ_ONLY_RETENTION_CUSTODY_AUDIT_VERIFICATION"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_audit_artifact_path: str | None = None
    source_retention_custody_audit_declared_sha256: str | None = None
    source_retention_custody_audit_computed_sha256: str | None = None
    source_retention_custody_audit_status: str | None = None
    source_retention_custody_audit_trust_banner: str | None = None
    retention_custody_audit_artifact_hash_valid: bool = False
    custody_audit_id: str | None = None
    audited_by: str | None = None
    custody_location: str | None = None
    audit_note: str | None = None
    custody_audit_statement_declared_sha256: str | None = None
    custody_audit_statement_computed_sha256: str | None = None
    custody_audit_statement_hash_valid: bool = False
    source_retention_custody_seal_verification_artifact_path: str | None = None
    source_retention_custody_seal_verification_declared_sha256: str | None = None
    source_retention_custody_seal_verification_status: str | None = None
    retention_custody_seal_verification_artifact_hash_valid: bool = False
    source_retention_custody_seal_status: str | None = None
    retention_custody_seal_artifact_hash_valid: bool = False
    custody_seal_id: str | None = None
    custody_seal_statement_hash_valid: bool = False
    retention_custody_register_verification_artifact_hash_valid: bool = False
    retention_custody_register_artifact_hash_valid: bool = False
    custody_register_id: str | None = None
    custody_register_statement_hash_valid: bool = False
    retention_handoff_acceptance_verification_artifact_hash_valid: bool = False
    retention_handoff_acceptance_artifact_hash_valid: bool = False
    acceptance_statement_hash_valid: bool = False
    retention_handoff_verification_artifact_hash_valid: bool = False
    retention_handoff_artifact_hash_valid: bool = False
    handoff_statement_hash_valid: bool = False
    retention_signoff_verification_artifact_hash_valid: bool = False
    source_retention_receipt_artifact_path: str | None = None
    source_retention_receipt_status: str | None = None
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_audit_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyAuditVerificationView(BaseModel):
    """Read-plane summary of paper evidence retention custody audit verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_audit_verification_view/v1"] = "paper_execution_evidence_bundle_retention_custody_audit_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_audit_artifact_path: str | None = None
    source_retention_custody_audit_declared_sha256: str | None = None
    source_retention_custody_audit_status: str | None = None
    retention_custody_audit_artifact_hash_valid: bool = False
    custody_audit_id: str | None = None
    audited_by: str | None = None
    custody_location: str | None = None
    audit_note: str | None = None
    custody_audit_statement_declared_sha256: str | None = None
    custody_audit_statement_computed_sha256: str | None = None
    custody_audit_statement_hash_valid: bool = False
    source_retention_custody_seal_verification_artifact_path: str | None = None
    source_retention_custody_seal_verification_declared_sha256: str | None = None
    source_retention_custody_seal_verification_status: str | None = None
    retention_custody_seal_verification_artifact_hash_valid: bool = False
    source_retention_custody_seal_status: str | None = None
    retention_custody_seal_artifact_hash_valid: bool = False
    custody_seal_id: str | None = None
    custody_seal_statement_hash_valid: bool = False
    retention_custody_register_verification_artifact_hash_valid: bool = False
    retention_custody_register_artifact_hash_valid: bool = False
    custody_register_id: str | None = None
    custody_register_statement_hash_valid: bool = False
    retention_handoff_acceptance_verification_artifact_hash_valid: bool = False
    retention_handoff_acceptance_artifact_hash_valid: bool = False
    acceptance_statement_hash_valid: bool = False
    retention_handoff_verification_artifact_hash_valid: bool = False
    retention_handoff_artifact_hash_valid: bool = False
    handoff_statement_hash_valid: bool = False
    retention_signoff_verification_artifact_hash_valid: bool = False
    source_retention_receipt_artifact_path: str | None = None
    source_retention_receipt_status: str | None = None
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyContinuityArtifact(BaseModel):
    """Read-only continuity attestation for verified paper evidence retention custody."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_continuity/v1"] = "paper_execution_evidence_bundle_retention_custody_continuity/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    continuity_authority: Literal["READ_ONLY_RETENTION_CUSTODY_CONTINUITY"] = "READ_ONLY_RETENTION_CUSTODY_CONTINUITY"
    continuity_status: Literal["CONTINUITY_ATTESTED", "CONTINUITY_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_continuity_id: str | None = None
    attested_by: str | None = None
    custody_location: str | None = None
    continuity_note: str | None = None
    source_retention_custody_audit_verification_artifact_path: str | None = None
    source_retention_custody_audit_verification_declared_sha256: str | None = None
    source_retention_custody_audit_verification_computed_sha256: str | None = None
    source_retention_custody_audit_verification_status: str | None = None
    source_retention_custody_audit_verification_trust_banner: str | None = None
    retention_custody_audit_verification_artifact_hash_valid: bool = False
    source_retention_custody_audit_artifact_path: str | None = None
    source_retention_custody_audit_status: str | None = None
    retention_custody_audit_artifact_hash_valid: bool = False
    custody_audit_id: str | None = None
    custody_audit_statement_hash_valid: bool = False
    source_retention_custody_seal_verification_status: str | None = None
    retention_custody_seal_verification_artifact_hash_valid: bool = False
    source_retention_custody_seal_status: str | None = None
    retention_custody_seal_artifact_hash_valid: bool = False
    custody_seal_id: str | None = None
    custody_seal_statement_hash_valid: bool = False
    retention_custody_register_verification_artifact_hash_valid: bool = False
    retention_custody_register_artifact_hash_valid: bool = False
    custody_register_id: str | None = None
    custody_register_statement_hash_valid: bool = False
    retention_handoff_acceptance_verification_artifact_hash_valid: bool = False
    retention_handoff_acceptance_artifact_hash_valid: bool = False
    acceptance_statement_hash_valid: bool = False
    retention_handoff_verification_artifact_hash_valid: bool = False
    retention_handoff_artifact_hash_valid: bool = False
    handoff_statement_hash_valid: bool = False
    retention_signoff_verification_artifact_hash_valid: bool = False
    source_retention_receipt_artifact_path: str | None = None
    source_retention_receipt_status: str | None = None
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_continuity_statement_sha256: str | None = None
    checklist: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_continuity_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyContinuityView(BaseModel):
    """Read-plane summary of paper evidence retention custody continuity attestations."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_continuity_view/v1"] = "paper_execution_evidence_bundle_retention_custody_continuity_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    continuity_status: Literal["CONTINUITY_ATTESTED", "CONTINUITY_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_continuity_id: str | None = None
    attested_by: str | None = None
    custody_location: str | None = None
    continuity_note: str | None = None
    source_retention_custody_audit_verification_artifact_path: str | None = None
    source_retention_custody_audit_verification_declared_sha256: str | None = None
    source_retention_custody_audit_verification_status: str | None = None
    retention_custody_audit_verification_artifact_hash_valid: bool = False
    source_retention_custody_audit_status: str | None = None
    retention_custody_audit_artifact_hash_valid: bool = False
    custody_audit_id: str | None = None
    custody_audit_statement_hash_valid: bool = False
    source_retention_custody_seal_verification_status: str | None = None
    retention_custody_seal_verification_artifact_hash_valid: bool = False
    source_retention_custody_seal_status: str | None = None
    retention_custody_seal_artifact_hash_valid: bool = False
    custody_seal_id: str | None = None
    custody_seal_statement_hash_valid: bool = False
    retention_custody_register_verification_artifact_hash_valid: bool = False
    retention_custody_register_artifact_hash_valid: bool = False
    custody_register_id: str | None = None
    custody_register_statement_hash_valid: bool = False
    retention_handoff_acceptance_verification_artifact_hash_valid: bool = False
    retention_handoff_acceptance_artifact_hash_valid: bool = False
    acceptance_statement_hash_valid: bool = False
    retention_handoff_verification_artifact_hash_valid: bool = False
    retention_handoff_artifact_hash_valid: bool = False
    handoff_statement_hash_valid: bool = False
    retention_signoff_verification_artifact_hash_valid: bool = False
    source_retention_receipt_artifact_path: str | None = None
    source_retention_receipt_status: str | None = None
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_continuity_statement_sha256: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyContinuityVerificationArtifact(BaseModel):
    """Read-only verifier for paper evidence retention custody continuity attestations."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_continuity_verification/v1"] = "paper_execution_evidence_bundle_retention_custody_continuity_verification/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    continuity_verification_authority: Literal["READ_ONLY_RETENTION_CUSTODY_CONTINUITY_VERIFICATION"] = "READ_ONLY_RETENTION_CUSTODY_CONTINUITY_VERIFICATION"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_continuity_artifact_path: str | None = None
    source_retention_custody_continuity_declared_sha256: str | None = None
    source_retention_custody_continuity_computed_sha256: str | None = None
    source_retention_custody_continuity_status: str | None = None
    source_retention_custody_continuity_trust_banner: str | None = None
    retention_custody_continuity_artifact_hash_valid: bool = False
    custody_continuity_id: str | None = None
    attested_by: str | None = None
    custody_location: str | None = None
    continuity_note: str | None = None
    custody_continuity_statement_declared_sha256: str | None = None
    custody_continuity_statement_computed_sha256: str | None = None
    custody_continuity_statement_hash_valid: bool = False
    source_retention_custody_audit_verification_artifact_path: str | None = None
    source_retention_custody_audit_verification_declared_sha256: str | None = None
    source_retention_custody_audit_verification_status: str | None = None
    retention_custody_audit_verification_artifact_hash_valid: bool = False
    source_retention_custody_audit_status: str | None = None
    retention_custody_audit_artifact_hash_valid: bool = False
    custody_audit_id: str | None = None
    custody_audit_statement_hash_valid: bool = False
    source_retention_custody_seal_verification_status: str | None = None
    retention_custody_seal_verification_artifact_hash_valid: bool = False
    source_retention_custody_seal_status: str | None = None
    retention_custody_seal_artifact_hash_valid: bool = False
    custody_seal_id: str | None = None
    custody_seal_statement_hash_valid: bool = False
    retention_custody_register_verification_artifact_hash_valid: bool = False
    retention_custody_register_artifact_hash_valid: bool = False
    custody_register_id: str | None = None
    custody_register_statement_hash_valid: bool = False
    retention_handoff_acceptance_verification_artifact_hash_valid: bool = False
    retention_handoff_acceptance_artifact_hash_valid: bool = False
    acceptance_statement_hash_valid: bool = False
    retention_handoff_verification_artifact_hash_valid: bool = False
    retention_handoff_artifact_hash_valid: bool = False
    handoff_statement_hash_valid: bool = False
    retention_signoff_verification_artifact_hash_valid: bool = False
    source_retention_receipt_artifact_path: str | None = None
    source_retention_receipt_status: str | None = None
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_continuity_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyContinuityVerificationView(BaseModel):
    """Read-plane summary of paper evidence retention custody continuity verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_continuity_verification_view/v1"] = "paper_execution_evidence_bundle_retention_custody_continuity_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_continuity_artifact_path: str | None = None
    source_retention_custody_continuity_declared_sha256: str | None = None
    source_retention_custody_continuity_status: str | None = None
    retention_custody_continuity_artifact_hash_valid: bool = False
    custody_continuity_id: str | None = None
    attested_by: str | None = None
    custody_location: str | None = None
    continuity_note: str | None = None
    custody_continuity_statement_declared_sha256: str | None = None
    custody_continuity_statement_computed_sha256: str | None = None
    custody_continuity_statement_hash_valid: bool = False
    source_retention_custody_audit_verification_artifact_path: str | None = None
    source_retention_custody_audit_verification_declared_sha256: str | None = None
    source_retention_custody_audit_verification_status: str | None = None
    retention_custody_audit_verification_artifact_hash_valid: bool = False
    source_retention_custody_audit_status: str | None = None
    retention_custody_audit_artifact_hash_valid: bool = False
    custody_audit_id: str | None = None
    custody_audit_statement_hash_valid: bool = False
    source_retention_custody_seal_verification_status: str | None = None
    retention_custody_seal_verification_artifact_hash_valid: bool = False
    source_retention_custody_seal_status: str | None = None
    retention_custody_seal_artifact_hash_valid: bool = False
    custody_seal_id: str | None = None
    custody_seal_statement_hash_valid: bool = False
    retention_custody_register_verification_artifact_hash_valid: bool = False
    retention_custody_register_artifact_hash_valid: bool = False
    custody_register_id: str | None = None
    custody_register_statement_hash_valid: bool = False
    retention_handoff_acceptance_verification_artifact_hash_valid: bool = False
    retention_handoff_acceptance_artifact_hash_valid: bool = False
    acceptance_statement_hash_valid: bool = False
    retention_handoff_verification_artifact_hash_valid: bool = False
    retention_handoff_artifact_hash_valid: bool = False
    handoff_statement_hash_valid: bool = False
    retention_signoff_verification_artifact_hash_valid: bool = False
    source_retention_receipt_artifact_path: str | None = None
    source_retention_receipt_status: str | None = None
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}

class PaperExecutionEvidenceBundleRetentionCustodyReviewArtifact(BaseModel):
    """Read-only review review for verified paper evidence retention custody."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_review/v1"] = "paper_execution_evidence_bundle_retention_custody_review/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    review_authority: Literal["READ_ONLY_RETENTION_CUSTODY_REVIEW"] = "READ_ONLY_RETENTION_CUSTODY_REVIEW"
    review_status: Literal["REVIEWED", "REVIEW_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_review_id: str | None = None
    reviewed_by: str | None = None
    custody_location: str | None = None
    review_note: str | None = None
    source_retention_custody_continuity_verification_artifact_path: str | None = None
    source_retention_custody_continuity_verification_declared_sha256: str | None = None
    source_retention_custody_continuity_verification_computed_sha256: str | None = None
    source_retention_custody_continuity_verification_status: str | None = None
    source_retention_custody_continuity_verification_trust_banner: str | None = None
    retention_custody_continuity_verification_artifact_hash_valid: bool = False
    source_retention_custody_audit_artifact_path: str | None = None
    source_retention_custody_audit_status: str | None = None
    retention_custody_audit_artifact_hash_valid: bool = False
    custody_audit_id: str | None = None
    custody_audit_statement_hash_valid: bool = False
    source_retention_custody_seal_verification_status: str | None = None
    retention_custody_seal_verification_artifact_hash_valid: bool = False
    source_retention_custody_seal_status: str | None = None
    retention_custody_seal_artifact_hash_valid: bool = False
    custody_seal_id: str | None = None
    custody_seal_statement_hash_valid: bool = False
    retention_custody_register_verification_artifact_hash_valid: bool = False
    retention_custody_register_artifact_hash_valid: bool = False
    custody_register_id: str | None = None
    custody_register_statement_hash_valid: bool = False
    retention_handoff_acceptance_verification_artifact_hash_valid: bool = False
    retention_handoff_acceptance_artifact_hash_valid: bool = False
    acceptance_statement_hash_valid: bool = False
    retention_handoff_verification_artifact_hash_valid: bool = False
    retention_handoff_artifact_hash_valid: bool = False
    handoff_statement_hash_valid: bool = False
    retention_signoff_verification_artifact_hash_valid: bool = False
    source_retention_receipt_artifact_path: str | None = None
    source_retention_receipt_status: str | None = None
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_review_statement_sha256: str | None = None
    checklist: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_review_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyReviewView(BaseModel):
    """Read-plane summary of paper evidence retention custody review reviews."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_review_view/v1"] = "paper_execution_evidence_bundle_retention_custody_review_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    review_status: Literal["REVIEWED", "REVIEW_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_review_id: str | None = None
    reviewed_by: str | None = None
    custody_location: str | None = None
    review_note: str | None = None
    source_retention_custody_continuity_verification_artifact_path: str | None = None
    source_retention_custody_continuity_verification_declared_sha256: str | None = None
    source_retention_custody_continuity_verification_status: str | None = None
    retention_custody_continuity_verification_artifact_hash_valid: bool = False
    source_retention_custody_audit_status: str | None = None
    retention_custody_audit_artifact_hash_valid: bool = False
    custody_audit_id: str | None = None
    custody_audit_statement_hash_valid: bool = False
    source_retention_custody_seal_verification_status: str | None = None
    retention_custody_seal_verification_artifact_hash_valid: bool = False
    source_retention_custody_seal_status: str | None = None
    retention_custody_seal_artifact_hash_valid: bool = False
    custody_seal_id: str | None = None
    custody_seal_statement_hash_valid: bool = False
    retention_custody_register_verification_artifact_hash_valid: bool = False
    retention_custody_register_artifact_hash_valid: bool = False
    custody_register_id: str | None = None
    custody_register_statement_hash_valid: bool = False
    retention_handoff_acceptance_verification_artifact_hash_valid: bool = False
    retention_handoff_acceptance_artifact_hash_valid: bool = False
    acceptance_statement_hash_valid: bool = False
    retention_handoff_verification_artifact_hash_valid: bool = False
    retention_handoff_artifact_hash_valid: bool = False
    handoff_statement_hash_valid: bool = False
    retention_signoff_verification_artifact_hash_valid: bool = False
    source_retention_receipt_artifact_path: str | None = None
    source_retention_receipt_status: str | None = None
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_review_statement_sha256: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyReviewVerificationArtifact(BaseModel):
    """Read-only verifier for paper evidence retention custody review reviews."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_review_verification/v1"] = "paper_execution_evidence_bundle_retention_custody_review_verification/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    review_verification_authority: Literal["READ_ONLY_RETENTION_CUSTODY_REVIEW_VERIFICATION"] = "READ_ONLY_RETENTION_CUSTODY_REVIEW_VERIFICATION"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_review_artifact_path: str | None = None
    source_retention_custody_review_declared_sha256: str | None = None
    source_retention_custody_review_computed_sha256: str | None = None
    source_retention_custody_review_status: str | None = None
    source_retention_custody_review_trust_banner: str | None = None
    retention_custody_review_artifact_hash_valid: bool = False
    custody_review_id: str | None = None
    reviewed_by: str | None = None
    custody_location: str | None = None
    review_note: str | None = None
    custody_review_statement_declared_sha256: str | None = None
    custody_review_statement_computed_sha256: str | None = None
    custody_review_statement_hash_valid: bool = False
    source_retention_custody_continuity_verification_artifact_path: str | None = None
    source_retention_custody_continuity_verification_declared_sha256: str | None = None
    source_retention_custody_continuity_verification_status: str | None = None
    retention_custody_continuity_verification_artifact_hash_valid: bool = False
    source_retention_custody_audit_status: str | None = None
    retention_custody_audit_artifact_hash_valid: bool = False
    custody_audit_id: str | None = None
    custody_audit_statement_hash_valid: bool = False
    source_retention_custody_seal_verification_status: str | None = None
    retention_custody_seal_verification_artifact_hash_valid: bool = False
    source_retention_custody_seal_status: str | None = None
    retention_custody_seal_artifact_hash_valid: bool = False
    custody_seal_id: str | None = None
    custody_seal_statement_hash_valid: bool = False
    retention_custody_register_verification_artifact_hash_valid: bool = False
    retention_custody_register_artifact_hash_valid: bool = False
    custody_register_id: str | None = None
    custody_register_statement_hash_valid: bool = False
    retention_handoff_acceptance_verification_artifact_hash_valid: bool = False
    retention_handoff_acceptance_artifact_hash_valid: bool = False
    acceptance_statement_hash_valid: bool = False
    retention_handoff_verification_artifact_hash_valid: bool = False
    retention_handoff_artifact_hash_valid: bool = False
    handoff_statement_hash_valid: bool = False
    retention_signoff_verification_artifact_hash_valid: bool = False
    source_retention_receipt_artifact_path: str | None = None
    source_retention_receipt_status: str | None = None
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_review_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyReviewVerificationView(BaseModel):
    """Read-plane summary of paper evidence retention custody continuity verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_review_verification_view/v1"] = "paper_execution_evidence_bundle_retention_custody_review_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_review_artifact_path: str | None = None
    source_retention_custody_review_declared_sha256: str | None = None
    source_retention_custody_review_status: str | None = None
    retention_custody_review_artifact_hash_valid: bool = False
    custody_review_id: str | None = None
    reviewed_by: str | None = None
    custody_location: str | None = None
    review_note: str | None = None
    custody_review_statement_declared_sha256: str | None = None
    custody_review_statement_computed_sha256: str | None = None
    custody_review_statement_hash_valid: bool = False
    source_retention_custody_continuity_verification_artifact_path: str | None = None
    source_retention_custody_continuity_verification_declared_sha256: str | None = None
    source_retention_custody_continuity_verification_status: str | None = None
    retention_custody_continuity_verification_artifact_hash_valid: bool = False
    source_retention_custody_audit_status: str | None = None
    retention_custody_audit_artifact_hash_valid: bool = False
    custody_audit_id: str | None = None
    custody_audit_statement_hash_valid: bool = False
    source_retention_custody_seal_verification_status: str | None = None
    retention_custody_seal_verification_artifact_hash_valid: bool = False
    source_retention_custody_seal_status: str | None = None
    retention_custody_seal_artifact_hash_valid: bool = False
    custody_seal_id: str | None = None
    custody_seal_statement_hash_valid: bool = False
    retention_custody_register_verification_artifact_hash_valid: bool = False
    retention_custody_register_artifact_hash_valid: bool = False
    custody_register_id: str | None = None
    custody_register_statement_hash_valid: bool = False
    retention_handoff_acceptance_verification_artifact_hash_valid: bool = False
    retention_handoff_acceptance_artifact_hash_valid: bool = False
    acceptance_statement_hash_valid: bool = False
    retention_handoff_verification_artifact_hash_valid: bool = False
    retention_handoff_artifact_hash_valid: bool = False
    handoff_statement_hash_valid: bool = False
    retention_signoff_verification_artifact_hash_valid: bool = False
    source_retention_receipt_artifact_path: str | None = None
    source_retention_receipt_status: str | None = None
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyRenewalArtifact(BaseModel):
    """Read-only renewal certificate for verified paper evidence retention custody reviews."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_renewal/v1"] = "paper_execution_evidence_bundle_retention_custody_renewal/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    renewal_authority: Literal["READ_ONLY_RETENTION_CUSTODY_RENEWAL"] = "READ_ONLY_RETENTION_CUSTODY_RENEWAL"
    renewal_status: Literal["RENEWED", "RENEWAL_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_renewal_id: str | None = None
    renewed_by: str | None = None
    custody_location: str | None = None
    renewal_interval_days: int = 30
    renewal_note: str | None = None
    source_retention_custody_review_verification_artifact_path: str | None = None
    source_retention_custody_review_verification_declared_sha256: str | None = None
    source_retention_custody_review_verification_computed_sha256: str | None = None
    source_retention_custody_review_verification_status: str | None = None
    source_retention_custody_review_verification_trust_banner: str | None = None
    retention_custody_review_verification_artifact_hash_valid: bool = False
    source_retention_custody_review_status: str | None = None
    retention_custody_review_artifact_hash_valid: bool = False
    custody_review_id: str | None = None
    custody_review_statement_hash_valid: bool = False
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_renewal_statement_sha256: str | None = None
    checklist: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_renewal_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyRenewalView(BaseModel):
    """Read-plane summary of paper evidence retention custody renewal certificates."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_renewal_view/v1"] = "paper_execution_evidence_bundle_retention_custody_renewal_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    renewal_status: Literal["RENEWED", "RENEWAL_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_renewal_id: str | None = None
    renewed_by: str | None = None
    custody_location: str | None = None
    renewal_interval_days: int = 30
    renewal_note: str | None = None
    source_retention_custody_review_verification_artifact_path: str | None = None
    source_retention_custody_review_verification_status: str | None = None
    retention_custody_review_verification_artifact_hash_valid: bool = False
    source_retention_custody_review_status: str | None = None
    retention_custody_review_artifact_hash_valid: bool = False
    custody_review_id: str | None = None
    custody_review_statement_hash_valid: bool = False
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_renewal_statement_sha256: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyRenewalVerificationArtifact(BaseModel):
    """Read-only verifier for paper evidence retention custody renewal certificates."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_renewal_verification/v1"] = "paper_execution_evidence_bundle_retention_custody_renewal_verification/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    renewal_verification_authority: Literal["READ_ONLY_RETENTION_CUSTODY_RENEWAL_VERIFICATION"] = "READ_ONLY_RETENTION_CUSTODY_RENEWAL_VERIFICATION"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_renewal_artifact_path: str | None = None
    source_retention_custody_renewal_declared_sha256: str | None = None
    source_retention_custody_renewal_computed_sha256: str | None = None
    source_retention_custody_renewal_status: str | None = None
    source_retention_custody_renewal_trust_banner: str | None = None
    retention_custody_renewal_artifact_hash_valid: bool = False
    custody_renewal_id: str | None = None
    renewed_by: str | None = None
    custody_location: str | None = None
    renewal_interval_days: int = 30
    renewal_note: str | None = None
    custody_renewal_statement_declared_sha256: str | None = None
    custody_renewal_statement_computed_sha256: str | None = None
    custody_renewal_statement_hash_valid: bool = False
    source_retention_custody_review_verification_artifact_path: str | None = None
    source_retention_custody_review_verification_status: str | None = None
    retention_custody_review_verification_artifact_hash_valid: bool = False
    source_retention_custody_review_status: str | None = None
    retention_custody_review_artifact_hash_valid: bool = False
    custody_review_id: str | None = None
    custody_review_statement_hash_valid: bool = False
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_renewal_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyRenewalVerificationView(BaseModel):
    """Read-plane summary of paper evidence retention custody renewal verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_renewal_verification_view/v1"] = "paper_execution_evidence_bundle_retention_custody_renewal_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_renewal_artifact_path: str | None = None
    source_retention_custody_renewal_status: str | None = None
    retention_custody_renewal_artifact_hash_valid: bool = False
    custody_renewal_id: str | None = None
    renewed_by: str | None = None
    custody_location: str | None = None
    renewal_interval_days: int = 30
    renewal_note: str | None = None
    custody_renewal_statement_hash_valid: bool = False
    source_retention_custody_review_verification_artifact_path: str | None = None
    source_retention_custody_review_verification_status: str | None = None
    retention_custody_review_verification_artifact_hash_valid: bool = False
    source_retention_custody_review_status: str | None = None
    retention_custody_review_artifact_hash_valid: bool = False
    custody_review_id: str | None = None
    custody_review_statement_hash_valid: bool = False
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyScheduleArtifact(BaseModel):
    """Read-only schedule for the next verified paper evidence retention custody renewal."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_schedule/v1"] = "paper_execution_evidence_bundle_retention_custody_schedule/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    schedule_authority: Literal["READ_ONLY_RETENTION_CUSTODY_SCHEDULE"] = "READ_ONLY_RETENTION_CUSTODY_SCHEDULE"
    schedule_status: Literal["SCHEDULED", "SCHEDULE_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_schedule_id: str | None = None
    scheduled_by: str | None = None
    custody_location: str | None = None
    schedule_start_at_utc: str | None = None
    next_renewal_due_at_utc: str | None = None
    renewal_interval_days: int = 30
    reminder_days_before_due: int = 7
    schedule_note: str | None = None
    source_retention_custody_renewal_verification_artifact_path: str | None = None
    source_retention_custody_renewal_verification_declared_sha256: str | None = None
    source_retention_custody_renewal_verification_computed_sha256: str | None = None
    source_retention_custody_renewal_verification_status: str | None = None
    source_retention_custody_renewal_verification_trust_banner: str | None = None
    retention_custody_renewal_verification_artifact_hash_valid: bool = False
    source_retention_custody_renewal_status: str | None = None
    retention_custody_renewal_artifact_hash_valid: bool = False
    custody_renewal_id: str | None = None
    custody_renewal_statement_hash_valid: bool = False
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_schedule_statement_sha256: str | None = None
    checklist: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_schedule_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyScheduleView(BaseModel):
    """Read-plane summary of paper evidence retention custody renewal schedules."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_schedule_view/v1"] = "paper_execution_evidence_bundle_retention_custody_schedule_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    schedule_status: Literal["SCHEDULED", "SCHEDULE_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_schedule_id: str | None = None
    scheduled_by: str | None = None
    custody_location: str | None = None
    schedule_start_at_utc: str | None = None
    next_renewal_due_at_utc: str | None = None
    renewal_interval_days: int = 30
    reminder_days_before_due: int = 7
    schedule_note: str | None = None
    source_retention_custody_renewal_verification_artifact_path: str | None = None
    source_retention_custody_renewal_verification_status: str | None = None
    retention_custody_renewal_verification_artifact_hash_valid: bool = False
    source_retention_custody_renewal_status: str | None = None
    retention_custody_renewal_artifact_hash_valid: bool = False
    custody_renewal_id: str | None = None
    custody_renewal_statement_hash_valid: bool = False
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_schedule_statement_sha256: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyScheduleVerificationArtifact(BaseModel):
    """Read-only verifier for paper evidence retention custody renewal schedules."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_schedule_verification/v1"] = "paper_execution_evidence_bundle_retention_custody_schedule_verification/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    schedule_verification_authority: Literal["READ_ONLY_RETENTION_CUSTODY_SCHEDULE_VERIFICATION"] = "READ_ONLY_RETENTION_CUSTODY_SCHEDULE_VERIFICATION"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_schedule_artifact_path: str | None = None
    source_retention_custody_schedule_declared_sha256: str | None = None
    source_retention_custody_schedule_computed_sha256: str | None = None
    source_retention_custody_schedule_status: str | None = None
    source_retention_custody_schedule_trust_banner: str | None = None
    retention_custody_schedule_artifact_hash_valid: bool = False
    custody_schedule_id: str | None = None
    scheduled_by: str | None = None
    custody_location: str | None = None
    schedule_start_at_utc: str | None = None
    next_renewal_due_at_utc: str | None = None
    renewal_interval_days: int = 30
    reminder_days_before_due: int = 7
    schedule_note: str | None = None
    custody_schedule_statement_declared_sha256: str | None = None
    custody_schedule_statement_computed_sha256: str | None = None
    custody_schedule_statement_hash_valid: bool = False
    source_retention_custody_renewal_verification_artifact_path: str | None = None
    source_retention_custody_renewal_verification_status: str | None = None
    retention_custody_renewal_verification_artifact_hash_valid: bool = False
    source_retention_custody_renewal_status: str | None = None
    retention_custody_renewal_artifact_hash_valid: bool = False
    custody_renewal_id: str | None = None
    custody_renewal_statement_hash_valid: bool = False
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_schedule_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyScheduleVerificationView(BaseModel):
    """Read-plane summary of paper evidence retention custody renewal schedule verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_schedule_verification_view/v1"] = "paper_execution_evidence_bundle_retention_custody_schedule_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_schedule_artifact_path: str | None = None
    source_retention_custody_schedule_status: str | None = None
    retention_custody_schedule_artifact_hash_valid: bool = False
    custody_schedule_id: str | None = None
    scheduled_by: str | None = None
    custody_location: str | None = None
    schedule_start_at_utc: str | None = None
    next_renewal_due_at_utc: str | None = None
    renewal_interval_days: int = 30
    reminder_days_before_due: int = 7
    custody_schedule_statement_hash_valid: bool = False
    source_retention_custody_renewal_verification_artifact_path: str | None = None
    source_retention_custody_renewal_verification_status: str | None = None
    retention_custody_renewal_verification_artifact_hash_valid: bool = False
    source_retention_custody_renewal_status: str | None = None
    retention_custody_renewal_artifact_hash_valid: bool = False
    custody_renewal_id: str | None = None
    custody_renewal_statement_hash_valid: bool = False
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyNoticeArtifact(BaseModel):
    """Read-only operator notice for scheduled paper evidence retention custody renewal."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_notice/v1"] = "paper_execution_evidence_bundle_retention_custody_notice/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    notice_authority: Literal["READ_ONLY_RETENTION_CUSTODY_NOTICE"] = "READ_ONLY_RETENTION_CUSTODY_NOTICE"
    notice_status: Literal["NOTICE_DUE", "NOTICE_PENDING", "NOTICE_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_notice_id: str | None = None
    notified_by: str | None = None
    custody_location: str | None = None
    notice_generated_for_utc: str | None = None
    next_renewal_due_at_utc: str | None = None
    reminder_window_starts_at_utc: str | None = None
    days_until_due: int = 0
    renewal_interval_days: int = 30
    reminder_days_before_due: int = 7
    notice_message: str | None = None
    notice_note: str | None = None
    source_retention_custody_schedule_verification_artifact_path: str | None = None
    source_retention_custody_schedule_verification_declared_sha256: str | None = None
    source_retention_custody_schedule_verification_computed_sha256: str | None = None
    source_retention_custody_schedule_verification_status: str | None = None
    source_retention_custody_schedule_verification_trust_banner: str | None = None
    retention_custody_schedule_verification_artifact_hash_valid: bool = False
    source_retention_custody_schedule_status: str | None = None
    retention_custody_schedule_artifact_hash_valid: bool = False
    custody_schedule_id: str | None = None
    custody_schedule_statement_hash_valid: bool = False
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_notice_statement_sha256: str | None = None
    checklist: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_notice_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyNoticeView(BaseModel):
    """Read-plane summary of paper evidence retention custody renewal notices."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_notice_view/v1"] = "paper_execution_evidence_bundle_retention_custody_notice_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    notice_status: Literal["NOTICE_DUE", "NOTICE_PENDING", "NOTICE_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_notice_id: str | None = None
    notified_by: str | None = None
    custody_location: str | None = None
    notice_generated_for_utc: str | None = None
    next_renewal_due_at_utc: str | None = None
    reminder_window_starts_at_utc: str | None = None
    days_until_due: int = 0
    renewal_interval_days: int = 30
    reminder_days_before_due: int = 7
    notice_message: str | None = None
    notice_note: str | None = None
    source_retention_custody_schedule_verification_artifact_path: str | None = None
    source_retention_custody_schedule_verification_status: str | None = None
    retention_custody_schedule_verification_artifact_hash_valid: bool = False
    source_retention_custody_schedule_status: str | None = None
    retention_custody_schedule_artifact_hash_valid: bool = False
    custody_schedule_id: str | None = None
    custody_schedule_statement_hash_valid: bool = False
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_notice_statement_sha256: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyNoticeVerificationArtifact(BaseModel):
    """Read-only verifier for paper evidence retention custody renewal notices."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_notice_verification/v1"] = "paper_execution_evidence_bundle_retention_custody_notice_verification/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    notice_verification_authority: Literal["READ_ONLY_RETENTION_CUSTODY_NOTICE_VERIFICATION"] = "READ_ONLY_RETENTION_CUSTODY_NOTICE_VERIFICATION"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_notice_artifact_path: str | None = None
    source_retention_custody_notice_declared_sha256: str | None = None
    source_retention_custody_notice_computed_sha256: str | None = None
    source_retention_custody_notice_status: str | None = None
    source_retention_custody_notice_trust_banner: str | None = None
    retention_custody_notice_artifact_hash_valid: bool = False
    custody_notice_id: str | None = None
    notified_by: str | None = None
    custody_location: str | None = None
    notice_generated_for_utc: str | None = None
    next_renewal_due_at_utc: str | None = None
    reminder_window_starts_at_utc: str | None = None
    days_until_due: int = 0
    renewal_interval_days: int = 30
    reminder_days_before_due: int = 7
    notice_message: str | None = None
    notice_note: str | None = None
    custody_notice_statement_declared_sha256: str | None = None
    custody_notice_statement_computed_sha256: str | None = None
    custody_notice_statement_hash_valid: bool = False
    source_retention_custody_schedule_verification_artifact_path: str | None = None
    source_retention_custody_schedule_verification_status: str | None = None
    retention_custody_schedule_verification_artifact_hash_valid: bool = False
    source_retention_custody_schedule_status: str | None = None
    retention_custody_schedule_artifact_hash_valid: bool = False
    custody_schedule_id: str | None = None
    custody_schedule_statement_hash_valid: bool = False
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_notice_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyNoticeVerificationView(BaseModel):
    """Read-plane summary of paper evidence retention custody renewal notice verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_notice_verification_view/v1"] = "paper_execution_evidence_bundle_retention_custody_notice_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_notice_artifact_path: str | None = None
    source_retention_custody_notice_status: str | None = None
    retention_custody_notice_artifact_hash_valid: bool = False
    custody_notice_id: str | None = None
    notified_by: str | None = None
    custody_location: str | None = None
    notice_generated_for_utc: str | None = None
    next_renewal_due_at_utc: str | None = None
    reminder_window_starts_at_utc: str | None = None
    days_until_due: int = 0
    renewal_interval_days: int = 30
    reminder_days_before_due: int = 7
    notice_message: str | None = None
    custody_notice_statement_hash_valid: bool = False
    source_retention_custody_schedule_verification_artifact_path: str | None = None
    source_retention_custody_schedule_verification_status: str | None = None
    retention_custody_schedule_verification_artifact_hash_valid: bool = False
    source_retention_custody_schedule_status: str | None = None
    retention_custody_schedule_artifact_hash_valid: bool = False
    custody_schedule_id: str | None = None
    custody_schedule_statement_hash_valid: bool = False
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyAcknowledgmentArtifact(BaseModel):
    """Read-only operator acknowledgment of a verified paper evidence retention custody renewal notice."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_acknowledgment/v1"] = "paper_execution_evidence_bundle_retention_custody_acknowledgment/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    acknowledgment_authority: Literal["READ_ONLY_RETENTION_CUSTODY_ACKNOWLEDGMENT"] = "READ_ONLY_RETENTION_CUSTODY_ACKNOWLEDGMENT"
    acknowledgment_status: Literal["ACKNOWLEDGED", "ACKNOWLEDGED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_acknowledgment_id: str | None = None
    acknowledged_by: str | None = None
    custody_location: str | None = None
    acknowledged_at_utc: str | None = None
    acknowledgment_note: str | None = None
    source_retention_custody_notice_verification_artifact_path: str | None = None
    source_retention_custody_notice_verification_declared_sha256: str | None = None
    source_retention_custody_notice_verification_computed_sha256: str | None = None
    source_retention_custody_notice_verification_status: str | None = None
    source_retention_custody_notice_verification_trust_banner: str | None = None
    retention_custody_notice_verification_artifact_hash_valid: bool = False
    source_retention_custody_notice_status: str | None = None
    retention_custody_notice_artifact_hash_valid: bool = False
    custody_notice_id: str | None = None
    custody_notice_statement_hash_valid: bool = False
    notice_generated_for_utc: str | None = None
    next_renewal_due_at_utc: str | None = None
    reminder_window_starts_at_utc: str | None = None
    days_until_due: int = 0
    renewal_interval_days: int = 30
    reminder_days_before_due: int = 7
    notice_message: str | None = None
    custody_schedule_id: str | None = None
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_acknowledgment_statement_sha256: str | None = None
    checklist: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_acknowledgment_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyAcknowledgmentView(BaseModel):
    """Read-plane summary of paper evidence retention custody renewal notice acknowledgments."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_acknowledgment_view/v1"] = "paper_execution_evidence_bundle_retention_custody_acknowledgment_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    acknowledgment_status: Literal["ACKNOWLEDGED", "ACKNOWLEDGED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_acknowledgment_id: str | None = None
    acknowledged_by: str | None = None
    custody_location: str | None = None
    acknowledged_at_utc: str | None = None
    acknowledgment_note: str | None = None
    source_retention_custody_notice_verification_artifact_path: str | None = None
    source_retention_custody_notice_verification_status: str | None = None
    retention_custody_notice_verification_artifact_hash_valid: bool = False
    source_retention_custody_notice_status: str | None = None
    retention_custody_notice_artifact_hash_valid: bool = False
    custody_notice_id: str | None = None
    custody_notice_statement_hash_valid: bool = False
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_acknowledgment_statement_sha256: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyAcknowledgmentVerificationArtifact(BaseModel):
    """Read-only verifier for paper evidence retention custody renewal notice acknowledgments."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_acknowledgment_verification/v1"] = "paper_execution_evidence_bundle_retention_custody_acknowledgment_verification/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    acknowledgment_verification_authority: Literal["READ_ONLY_RETENTION_CUSTODY_ACKNOWLEDGMENT_VERIFICATION"] = "READ_ONLY_RETENTION_CUSTODY_ACKNOWLEDGMENT_VERIFICATION"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_acknowledgment_artifact_path: str | None = None
    source_retention_custody_acknowledgment_declared_sha256: str | None = None
    source_retention_custody_acknowledgment_computed_sha256: str | None = None
    source_retention_custody_acknowledgment_status: str | None = None
    source_retention_custody_acknowledgment_trust_banner: str | None = None
    retention_custody_acknowledgment_artifact_hash_valid: bool = False
    custody_acknowledgment_id: str | None = None
    acknowledged_by: str | None = None
    custody_location: str | None = None
    acknowledged_at_utc: str | None = None
    acknowledgment_note: str | None = None
    custody_acknowledgment_statement_declared_sha256: str | None = None
    custody_acknowledgment_statement_computed_sha256: str | None = None
    custody_acknowledgment_statement_hash_valid: bool = False
    source_retention_custody_notice_verification_artifact_path: str | None = None
    source_retention_custody_notice_verification_status: str | None = None
    retention_custody_notice_verification_artifact_hash_valid: bool = False
    source_retention_custody_notice_status: str | None = None
    retention_custody_notice_artifact_hash_valid: bool = False
    custody_notice_id: str | None = None
    custody_notice_statement_hash_valid: bool = False
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_acknowledgment_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyAcknowledgmentVerificationView(BaseModel):
    """Read-plane summary of paper evidence retention custody renewal acknowledgment verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_acknowledgment_verification_view/v1"] = "paper_execution_evidence_bundle_retention_custody_acknowledgment_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_acknowledgment_artifact_path: str | None = None
    source_retention_custody_acknowledgment_status: str | None = None
    retention_custody_acknowledgment_artifact_hash_valid: bool = False
    custody_acknowledgment_id: str | None = None
    acknowledged_by: str | None = None
    custody_location: str | None = None
    acknowledged_at_utc: str | None = None
    custody_acknowledgment_statement_hash_valid: bool = False
    source_retention_custody_notice_verification_artifact_path: str | None = None
    source_retention_custody_notice_verification_status: str | None = None
    retention_custody_notice_verification_artifact_hash_valid: bool = False
    source_retention_custody_notice_status: str | None = None
    retention_custody_notice_artifact_hash_valid: bool = False
    custody_notice_id: str | None = None
    custody_notice_statement_hash_valid: bool = False
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyCompletionArtifact(BaseModel):
    """Read-only completion record for an acknowledged paper evidence retention custody renewal."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_completion/v1"] = "paper_execution_evidence_bundle_retention_custody_completion/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    completion_authority: Literal["READ_ONLY_RETENTION_CUSTODY_COMPLETION"] = "READ_ONLY_RETENTION_CUSTODY_COMPLETION"
    completion_status: Literal["COMPLETED", "COMPLETED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_completion_id: str | None = None
    completed_by: str | None = None
    custody_location: str | None = None
    completed_at_utc: str | None = None
    completion_note: str | None = None
    source_retention_custody_acknowledgment_verification_artifact_path: str | None = None
    source_retention_custody_acknowledgment_verification_declared_sha256: str | None = None
    source_retention_custody_acknowledgment_verification_computed_sha256: str | None = None
    source_retention_custody_acknowledgment_verification_status: str | None = None
    source_retention_custody_acknowledgment_verification_trust_banner: str | None = None
    retention_custody_acknowledgment_verification_artifact_hash_valid: bool = False
    source_retention_custody_acknowledgment_status: str | None = None
    retention_custody_acknowledgment_artifact_hash_valid: bool = False
    custody_acknowledgment_id: str | None = None
    custody_acknowledgment_statement_hash_valid: bool = False
    acknowledged_by: str | None = None
    acknowledged_at_utc: str | None = None
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_completion_statement_sha256: str | None = None
    checklist: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_completion_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyCompletionView(BaseModel):
    """Read-plane summary of paper evidence retention custody completion records."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_completion_view/v1"] = "paper_execution_evidence_bundle_retention_custody_completion_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    completion_status: Literal["COMPLETED", "COMPLETED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_completion_id: str | None = None
    completed_by: str | None = None
    custody_location: str | None = None
    completed_at_utc: str | None = None
    completion_note: str | None = None
    source_retention_custody_acknowledgment_verification_artifact_path: str | None = None
    source_retention_custody_acknowledgment_verification_status: str | None = None
    retention_custody_acknowledgment_verification_artifact_hash_valid: bool = False
    source_retention_custody_acknowledgment_status: str | None = None
    retention_custody_acknowledgment_artifact_hash_valid: bool = False
    custody_acknowledgment_id: str | None = None
    custody_acknowledgment_statement_hash_valid: bool = False
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_completion_statement_sha256: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyCompletionVerificationArtifact(BaseModel):
    """Read-only verifier for paper evidence retention custody completion records."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_completion_verification/v1"] = "paper_execution_evidence_bundle_retention_custody_completion_verification/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    completion_verification_authority: Literal["READ_ONLY_RETENTION_CUSTODY_COMPLETION_VERIFICATION"] = "READ_ONLY_RETENTION_CUSTODY_COMPLETION_VERIFICATION"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_completion_artifact_path: str | None = None
    source_retention_custody_completion_declared_sha256: str | None = None
    source_retention_custody_completion_computed_sha256: str | None = None
    source_retention_custody_completion_status: str | None = None
    source_retention_custody_completion_trust_banner: str | None = None
    retention_custody_completion_artifact_hash_valid: bool = False
    custody_completion_id: str | None = None
    completed_by: str | None = None
    custody_location: str | None = None
    completed_at_utc: str | None = None
    completion_note: str | None = None
    custody_completion_statement_declared_sha256: str | None = None
    custody_completion_statement_computed_sha256: str | None = None
    custody_completion_statement_hash_valid: bool = False
    source_retention_custody_acknowledgment_verification_artifact_path: str | None = None
    source_retention_custody_acknowledgment_verification_status: str | None = None
    retention_custody_acknowledgment_verification_artifact_hash_valid: bool = False
    source_retention_custody_acknowledgment_status: str | None = None
    retention_custody_acknowledgment_artifact_hash_valid: bool = False
    custody_acknowledgment_id: str | None = None
    custody_acknowledgment_statement_hash_valid: bool = False
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_completion_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyCompletionVerificationView(BaseModel):
    """Read-plane summary of paper evidence retention custody completion verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_completion_verification_view/v1"] = "paper_execution_evidence_bundle_retention_custody_completion_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_completion_artifact_path: str | None = None
    source_retention_custody_completion_status: str | None = None
    retention_custody_completion_artifact_hash_valid: bool = False
    custody_completion_id: str | None = None
    completed_by: str | None = None
    custody_location: str | None = None
    completed_at_utc: str | None = None
    custody_completion_statement_hash_valid: bool = False
    source_retention_custody_acknowledgment_verification_artifact_path: str | None = None
    source_retention_custody_acknowledgment_verification_status: str | None = None
    retention_custody_acknowledgment_verification_artifact_hash_valid: bool = False
    source_retention_custody_acknowledgment_status: str | None = None
    retention_custody_acknowledgment_artifact_hash_valid: bool = False
    custody_acknowledgment_id: str | None = None
    custody_acknowledgment_statement_hash_valid: bool = False
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}



class PaperExecutionEvidenceBundleRetentionCustodyCloseoutArtifact(BaseModel):
    """Read-only closeout record for a verified paper evidence retention custody renewal completion."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_closeout/v1"] = "paper_execution_evidence_bundle_retention_custody_closeout/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    closeout_authority: Literal["READ_ONLY_RETENTION_CUSTODY_CLOSEOUT"] = "READ_ONLY_RETENTION_CUSTODY_CLOSEOUT"
    closeout_status: Literal["CLOSED", "CLOSED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_closeout_id: str | None = None
    closed_out_by: str | None = None
    custody_location: str | None = None
    closed_out_at_utc: str | None = None
    closeout_note: str | None = None
    source_retention_custody_completion_verification_artifact_path: str | None = None
    source_retention_custody_completion_verification_declared_sha256: str | None = None
    source_retention_custody_completion_verification_computed_sha256: str | None = None
    source_retention_custody_completion_verification_status: str | None = None
    source_retention_custody_completion_verification_trust_banner: str | None = None
    retention_custody_completion_verification_artifact_hash_valid: bool = False
    source_retention_custody_completion_status: str | None = None
    retention_custody_completion_artifact_hash_valid: bool = False
    custody_completion_id: str | None = None
    custody_completion_statement_hash_valid: bool = False
    completed_by: str | None = None
    completed_at_utc: str | None = None
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_closeout_statement_sha256: str | None = None
    checklist: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_closeout_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyCloseoutView(BaseModel):
    """Read-plane summary of paper evidence retention custody closeout records."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_closeout_view/v1"] = "paper_execution_evidence_bundle_retention_custody_closeout_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    closeout_status: Literal["CLOSED", "CLOSED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_closeout_id: str | None = None
    closed_out_by: str | None = None
    custody_location: str | None = None
    closed_out_at_utc: str | None = None
    closeout_note: str | None = None
    source_retention_custody_completion_verification_artifact_path: str | None = None
    source_retention_custody_completion_verification_status: str | None = None
    retention_custody_completion_verification_artifact_hash_valid: bool = False
    source_retention_custody_completion_status: str | None = None
    retention_custody_completion_artifact_hash_valid: bool = False
    custody_completion_id: str | None = None
    custody_completion_statement_hash_valid: bool = False
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_closeout_statement_sha256: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyCloseoutVerificationArtifact(BaseModel):
    """Read-only verifier for paper evidence retention custody closeout records."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_closeout_verification/v1"] = "paper_execution_evidence_bundle_retention_custody_closeout_verification/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    closeout_verification_authority: Literal["READ_ONLY_RETENTION_CUSTODY_CLOSEOUT_VERIFICATION"] = "READ_ONLY_RETENTION_CUSTODY_CLOSEOUT_VERIFICATION"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_closeout_artifact_path: str | None = None
    source_retention_custody_closeout_declared_sha256: str | None = None
    source_retention_custody_closeout_computed_sha256: str | None = None
    source_retention_custody_closeout_status: str | None = None
    source_retention_custody_closeout_trust_banner: str | None = None
    retention_custody_closeout_artifact_hash_valid: bool = False
    custody_closeout_id: str | None = None
    closed_out_by: str | None = None
    custody_location: str | None = None
    closed_out_at_utc: str | None = None
    closeout_note: str | None = None
    custody_closeout_statement_declared_sha256: str | None = None
    custody_closeout_statement_computed_sha256: str | None = None
    custody_closeout_statement_hash_valid: bool = False
    source_retention_custody_completion_verification_artifact_path: str | None = None
    source_retention_custody_completion_verification_status: str | None = None
    retention_custody_completion_verification_artifact_hash_valid: bool = False
    source_retention_custody_completion_status: str | None = None
    retention_custody_completion_artifact_hash_valid: bool = False
    custody_completion_id: str | None = None
    custody_completion_statement_hash_valid: bool = False
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_closeout_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyCloseoutVerificationView(BaseModel):
    """Read-plane summary of paper evidence retention custody closeout verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_closeout_verification_view/v1"] = "paper_execution_evidence_bundle_retention_custody_closeout_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_closeout_artifact_path: str | None = None
    source_retention_custody_closeout_status: str | None = None
    retention_custody_closeout_artifact_hash_valid: bool = False
    custody_closeout_id: str | None = None
    closed_out_by: str | None = None
    custody_location: str | None = None
    closed_out_at_utc: str | None = None
    custody_closeout_statement_hash_valid: bool = False
    source_retention_custody_completion_verification_artifact_path: str | None = None
    source_retention_custody_completion_verification_status: str | None = None
    retention_custody_completion_verification_artifact_hash_valid: bool = False
    source_retention_custody_completion_status: str | None = None
    retention_custody_completion_artifact_hash_valid: bool = False
    custody_completion_id: str | None = None
    custody_completion_statement_hash_valid: bool = False
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyArchiveArtifact(BaseModel):
    """Read-only archive record for a verified paper evidence retention custody closeout."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_archive/v1"] = "paper_execution_evidence_bundle_retention_custody_archive/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    archive_authority: Literal["READ_ONLY_RETENTION_CUSTODY_ARCHIVE"] = "READ_ONLY_RETENTION_CUSTODY_ARCHIVE"
    archive_status: Literal["ARCHIVED", "ARCHIVED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_archive_id: str | None = None
    archived_by: str | None = None
    custody_location: str | None = None
    archived_at_utc: str | None = None
    archive_note: str | None = None
    source_retention_custody_closeout_verification_artifact_path: str | None = None
    source_retention_custody_closeout_verification_declared_sha256: str | None = None
    source_retention_custody_closeout_verification_computed_sha256: str | None = None
    source_retention_custody_closeout_verification_status: str | None = None
    source_retention_custody_closeout_verification_trust_banner: str | None = None
    retention_custody_closeout_verification_artifact_hash_valid: bool = False
    source_retention_custody_closeout_status: str | None = None
    retention_custody_closeout_artifact_hash_valid: bool = False
    custody_closeout_id: str | None = None
    custody_closeout_statement_hash_valid: bool = False
    custody_completion_id: str | None = None
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_archive_statement_sha256: str | None = None
    checklist: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_archive_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyArchiveView(BaseModel):
    """Read-plane summary of paper evidence retention custody archive records."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_archive_view/v1"] = "paper_execution_evidence_bundle_retention_custody_archive_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    archive_status: Literal["ARCHIVED", "ARCHIVED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_archive_id: str | None = None
    archived_by: str | None = None
    custody_location: str | None = None
    archived_at_utc: str | None = None
    archive_note: str | None = None
    source_retention_custody_closeout_verification_artifact_path: str | None = None
    source_retention_custody_closeout_verification_status: str | None = None
    retention_custody_closeout_verification_artifact_hash_valid: bool = False
    source_retention_custody_closeout_status: str | None = None
    retention_custody_closeout_artifact_hash_valid: bool = False
    custody_closeout_id: str | None = None
    custody_closeout_statement_hash_valid: bool = False
    custody_completion_id: str | None = None
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_archive_statement_sha256: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyArchiveVerificationArtifact(BaseModel):
    """Read-only verifier for paper evidence retention custody archive records."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_archive_verification/v1"] = "paper_execution_evidence_bundle_retention_custody_archive_verification/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    archive_verification_authority: Literal["READ_ONLY_RETENTION_CUSTODY_ARCHIVE_VERIFICATION"] = "READ_ONLY_RETENTION_CUSTODY_ARCHIVE_VERIFICATION"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_archive_artifact_path: str | None = None
    source_retention_custody_archive_declared_sha256: str | None = None
    source_retention_custody_archive_computed_sha256: str | None = None
    source_retention_custody_archive_status: str | None = None
    source_retention_custody_archive_trust_banner: str | None = None
    retention_custody_archive_artifact_hash_valid: bool = False
    custody_archive_id: str | None = None
    archived_by: str | None = None
    custody_location: str | None = None
    archived_at_utc: str | None = None
    archive_note: str | None = None
    custody_archive_statement_declared_sha256: str | None = None
    custody_archive_statement_computed_sha256: str | None = None
    custody_archive_statement_hash_valid: bool = False
    source_retention_custody_closeout_verification_artifact_path: str | None = None
    source_retention_custody_closeout_verification_status: str | None = None
    retention_custody_closeout_verification_artifact_hash_valid: bool = False
    source_retention_custody_closeout_status: str | None = None
    retention_custody_closeout_artifact_hash_valid: bool = False
    custody_closeout_id: str | None = None
    custody_closeout_statement_hash_valid: bool = False
    custody_completion_id: str | None = None
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_archive_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyArchiveVerificationView(BaseModel):
    """Read-plane summary of paper evidence retention custody archive verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_archive_verification_view/v1"] = "paper_execution_evidence_bundle_retention_custody_archive_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_archive_artifact_path: str | None = None
    source_retention_custody_archive_status: str | None = None
    retention_custody_archive_artifact_hash_valid: bool = False
    custody_archive_id: str | None = None
    archived_by: str | None = None
    custody_location: str | None = None
    archived_at_utc: str | None = None
    custody_archive_statement_hash_valid: bool = False
    source_retention_custody_closeout_verification_artifact_path: str | None = None
    source_retention_custody_closeout_verification_status: str | None = None
    retention_custody_closeout_verification_artifact_hash_valid: bool = False
    source_retention_custody_closeout_status: str | None = None
    retention_custody_closeout_artifact_hash_valid: bool = False
    custody_closeout_id: str | None = None
    custody_closeout_statement_hash_valid: bool = False
    custody_completion_id: str | None = None
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyRetrievalArtifact(BaseModel):
    """Read-only retrieval record for verified archived paper evidence retention custody."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_retrieval/v1"] = "paper_execution_evidence_bundle_retention_custody_retrieval/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    retrieval_authority: Literal["READ_ONLY_RETENTION_CUSTODY_RETRIEVAL"] = "READ_ONLY_RETENTION_CUSTODY_RETRIEVAL"
    retrieval_status: Literal["RETRIEVED", "RETRIEVED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_retrieval_id: str | None = None
    retrieved_by: str | None = None
    retrieval_purpose: str | None = None
    custody_location: str | None = None
    retrieved_at_utc: str | None = None
    retrieval_note: str | None = None
    source_retention_custody_archive_verification_artifact_path: str | None = None
    source_retention_custody_archive_verification_declared_sha256: str | None = None
    source_retention_custody_archive_verification_computed_sha256: str | None = None
    source_retention_custody_archive_verification_status: str | None = None
    source_retention_custody_archive_verification_trust_banner: str | None = None
    retention_custody_archive_verification_artifact_hash_valid: bool = False
    source_retention_custody_archive_status: str | None = None
    retention_custody_archive_artifact_hash_valid: bool = False
    custody_archive_id: str | None = None
    custody_archive_statement_hash_valid: bool = False
    custody_closeout_id: str | None = None
    custody_completion_id: str | None = None
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_retrieval_statement_sha256: str | None = None
    checklist: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_retrieval_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyRetrievalView(BaseModel):
    """Read-plane summary of paper evidence retention custody retrieval records."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_retrieval_view/v1"] = "paper_execution_evidence_bundle_retention_custody_retrieval_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    retrieval_status: Literal["RETRIEVED", "RETRIEVED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_retrieval_id: str | None = None
    retrieved_by: str | None = None
    retrieval_purpose: str | None = None
    custody_location: str | None = None
    retrieved_at_utc: str | None = None
    retrieval_note: str | None = None
    source_retention_custody_archive_verification_artifact_path: str | None = None
    source_retention_custody_archive_verification_status: str | None = None
    retention_custody_archive_verification_artifact_hash_valid: bool = False
    source_retention_custody_archive_status: str | None = None
    retention_custody_archive_artifact_hash_valid: bool = False
    custody_archive_id: str | None = None
    custody_archive_statement_hash_valid: bool = False
    custody_closeout_id: str | None = None
    custody_completion_id: str | None = None
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_retrieval_statement_sha256: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyRetrievalVerificationArtifact(BaseModel):
    """Read-only verifier for paper evidence retention custody retrieval records."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_retrieval_verification/v1"] = "paper_execution_evidence_bundle_retention_custody_retrieval_verification/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    retrieval_verification_authority: Literal["READ_ONLY_RETENTION_CUSTODY_RETRIEVAL_VERIFICATION"] = "READ_ONLY_RETENTION_CUSTODY_RETRIEVAL_VERIFICATION"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_retrieval_artifact_path: str | None = None
    source_retention_custody_retrieval_declared_sha256: str | None = None
    source_retention_custody_retrieval_computed_sha256: str | None = None
    source_retention_custody_retrieval_status: str | None = None
    source_retention_custody_retrieval_trust_banner: str | None = None
    retention_custody_retrieval_artifact_hash_valid: bool = False
    custody_retrieval_id: str | None = None
    retrieved_by: str | None = None
    retrieval_purpose: str | None = None
    custody_location: str | None = None
    retrieved_at_utc: str | None = None
    retrieval_note: str | None = None
    custody_retrieval_statement_declared_sha256: str | None = None
    custody_retrieval_statement_computed_sha256: str | None = None
    custody_retrieval_statement_hash_valid: bool = False
    source_retention_custody_archive_verification_artifact_path: str | None = None
    source_retention_custody_archive_verification_status: str | None = None
    retention_custody_archive_verification_artifact_hash_valid: bool = False
    source_retention_custody_archive_status: str | None = None
    retention_custody_archive_artifact_hash_valid: bool = False
    custody_archive_id: str | None = None
    custody_archive_statement_hash_valid: bool = False
    custody_closeout_id: str | None = None
    custody_completion_id: str | None = None
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_retrieval_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyRetrievalVerificationView(BaseModel):
    """Read-plane summary of paper evidence retention custody retrieval verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_retrieval_verification_view/v1"] = "paper_execution_evidence_bundle_retention_custody_retrieval_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_retrieval_artifact_path: str | None = None
    source_retention_custody_retrieval_status: str | None = None
    retention_custody_retrieval_artifact_hash_valid: bool = False
    custody_retrieval_id: str | None = None
    retrieved_by: str | None = None
    retrieval_purpose: str | None = None
    custody_location: str | None = None
    retrieved_at_utc: str | None = None
    custody_retrieval_statement_hash_valid: bool = False
    source_retention_custody_archive_verification_artifact_path: str | None = None
    source_retention_custody_archive_verification_status: str | None = None
    retention_custody_archive_verification_artifact_hash_valid: bool = False
    source_retention_custody_archive_status: str | None = None
    retention_custody_archive_artifact_hash_valid: bool = False
    custody_archive_id: str | None = None
    custody_archive_statement_hash_valid: bool = False
    custody_closeout_id: str | None = None
    custody_completion_id: str | None = None
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyReturnArtifact(BaseModel):
    """Read-only return record for verified retrieved paper evidence retention custody."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_return/v1"] = "paper_execution_evidence_bundle_retention_custody_return/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    return_authority: Literal["READ_ONLY_RETENTION_CUSTODY_RETURN"] = "READ_ONLY_RETENTION_CUSTODY_RETURN"
    return_status: Literal["RETURNED", "RETURNED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_return_id: str | None = None
    returned_by: str | None = None
    return_reason: str | None = None
    custody_location: str | None = None
    returned_at_utc: str | None = None
    return_note: str | None = None
    source_retention_custody_retrieval_verification_artifact_path: str | None = None
    source_retention_custody_retrieval_verification_declared_sha256: str | None = None
    source_retention_custody_retrieval_verification_computed_sha256: str | None = None
    source_retention_custody_retrieval_verification_status: str | None = None
    source_retention_custody_retrieval_verification_trust_banner: str | None = None
    retention_custody_retrieval_verification_artifact_hash_valid: bool = False
    source_retention_custody_retrieval_status: str | None = None
    retention_custody_retrieval_artifact_hash_valid: bool = False
    custody_retrieval_id: str | None = None
    custody_retrieval_statement_hash_valid: bool = False
    custody_archive_id: str | None = None
    custody_closeout_id: str | None = None
    custody_completion_id: str | None = None
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_return_statement_sha256: str | None = None
    checklist: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_return_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyReturnView(BaseModel):
    """Read-plane summary of paper evidence retention custody return records."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_return_view/v1"] = "paper_execution_evidence_bundle_retention_custody_return_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    return_status: Literal["RETURNED", "RETURNED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_return_id: str | None = None
    returned_by: str | None = None
    return_reason: str | None = None
    custody_location: str | None = None
    returned_at_utc: str | None = None
    return_note: str | None = None
    source_retention_custody_retrieval_verification_artifact_path: str | None = None
    source_retention_custody_retrieval_verification_status: str | None = None
    retention_custody_retrieval_verification_artifact_hash_valid: bool = False
    source_retention_custody_retrieval_status: str | None = None
    retention_custody_retrieval_artifact_hash_valid: bool = False
    custody_retrieval_id: str | None = None
    custody_retrieval_statement_hash_valid: bool = False
    custody_archive_id: str | None = None
    custody_closeout_id: str | None = None
    custody_completion_id: str | None = None
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_return_statement_sha256: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyReturnVerificationArtifact(BaseModel):
    """Read-only verifier for paper evidence retention custody return records."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_return_verification/v1"] = "paper_execution_evidence_bundle_retention_custody_return_verification/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    return_verification_authority: Literal["READ_ONLY_RETENTION_CUSTODY_RETURN_VERIFICATION"] = "READ_ONLY_RETENTION_CUSTODY_RETURN_VERIFICATION"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_return_artifact_path: str | None = None
    source_retention_custody_return_declared_sha256: str | None = None
    source_retention_custody_return_computed_sha256: str | None = None
    source_retention_custody_return_status: str | None = None
    source_retention_custody_return_trust_banner: str | None = None
    retention_custody_return_artifact_hash_valid: bool = False
    custody_return_id: str | None = None
    returned_by: str | None = None
    return_reason: str | None = None
    custody_location: str | None = None
    returned_at_utc: str | None = None
    return_note: str | None = None
    custody_return_statement_declared_sha256: str | None = None
    custody_return_statement_computed_sha256: str | None = None
    custody_return_statement_hash_valid: bool = False
    source_retention_custody_retrieval_verification_artifact_path: str | None = None
    source_retention_custody_retrieval_verification_status: str | None = None
    retention_custody_retrieval_verification_artifact_hash_valid: bool = False
    source_retention_custody_retrieval_status: str | None = None
    retention_custody_retrieval_artifact_hash_valid: bool = False
    custody_retrieval_id: str | None = None
    custody_retrieval_statement_hash_valid: bool = False
    custody_archive_id: str | None = None
    custody_closeout_id: str | None = None
    custody_completion_id: str | None = None
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_return_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyReturnVerificationView(BaseModel):
    """Read-plane summary of paper evidence retention custody return verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_return_verification_view/v1"] = "paper_execution_evidence_bundle_retention_custody_return_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_return_artifact_path: str | None = None
    source_retention_custody_return_status: str | None = None
    retention_custody_return_artifact_hash_valid: bool = False
    custody_return_id: str | None = None
    returned_by: str | None = None
    return_reason: str | None = None
    custody_location: str | None = None
    returned_at_utc: str | None = None
    custody_return_statement_hash_valid: bool = False
    source_retention_custody_retrieval_verification_artifact_path: str | None = None
    source_retention_custody_retrieval_verification_status: str | None = None
    retention_custody_retrieval_verification_artifact_hash_valid: bool = False
    source_retention_custody_retrieval_status: str | None = None
    retention_custody_retrieval_artifact_hash_valid: bool = False
    custody_retrieval_id: str | None = None
    custody_retrieval_statement_hash_valid: bool = False
    custody_archive_id: str | None = None
    custody_closeout_id: str | None = None
    custody_completion_id: str | None = None
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyRedepositArtifact(BaseModel):
    """Read-only redeposit record for verified retrieved paper evidence retention custody."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_redeposit/v1"] = "paper_execution_evidence_bundle_retention_custody_redeposit/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    redeposit_authority: Literal["READ_ONLY_RETENTION_CUSTODY_REDEPOSIT"] = "READ_ONLY_RETENTION_CUSTODY_REDEPOSIT"
    redeposit_status: Literal["REDEPOSITED", "REDEPOSITED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_redeposit_id: str | None = None
    redeposited_by: str | None = None
    redeposit_reason: str | None = None
    custody_location: str | None = None
    redeposited_at_utc: str | None = None
    redeposit_note: str | None = None
    source_retention_custody_return_verification_artifact_path: str | None = None
    source_retention_custody_return_verification_declared_sha256: str | None = None
    source_retention_custody_return_verification_computed_sha256: str | None = None
    source_retention_custody_return_verification_status: str | None = None
    source_retention_custody_return_verification_trust_banner: str | None = None
    retention_custody_return_verification_artifact_hash_valid: bool = False
    source_retention_custody_return_status: str | None = None
    retention_custody_return_artifact_hash_valid: bool = False
    custody_return_id: str | None = None
    custody_return_statement_hash_valid: bool = False
    custody_archive_id: str | None = None
    custody_closeout_id: str | None = None
    custody_completion_id: str | None = None
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_redeposit_statement_sha256: str | None = None
    checklist: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_redeposit_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyRedepositView(BaseModel):
    """Read-plane summary of paper evidence retention custody redeposit records."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_redeposit_view/v1"] = "paper_execution_evidence_bundle_retention_custody_redeposit_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    redeposit_status: Literal["REDEPOSITED", "REDEPOSITED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_redeposit_id: str | None = None
    redeposited_by: str | None = None
    redeposit_reason: str | None = None
    custody_location: str | None = None
    redeposited_at_utc: str | None = None
    redeposit_note: str | None = None
    source_retention_custody_return_verification_artifact_path: str | None = None
    source_retention_custody_return_verification_status: str | None = None
    retention_custody_return_verification_artifact_hash_valid: bool = False
    source_retention_custody_return_status: str | None = None
    retention_custody_return_artifact_hash_valid: bool = False
    custody_return_id: str | None = None
    custody_return_statement_hash_valid: bool = False
    custody_archive_id: str | None = None
    custody_closeout_id: str | None = None
    custody_completion_id: str | None = None
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_redeposit_statement_sha256: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyRedepositVerificationArtifact(BaseModel):
    """Read-only verifier for paper evidence retention custody redeposit records."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_redeposit_verification/v1"] = "paper_execution_evidence_bundle_retention_custody_redeposit_verification/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    redeposit_verification_authority: Literal["READ_ONLY_RETENTION_CUSTODY_REDEPOSIT_VERIFICATION"] = "READ_ONLY_RETENTION_CUSTODY_REDEPOSIT_VERIFICATION"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_redeposit_artifact_path: str | None = None
    source_retention_custody_redeposit_declared_sha256: str | None = None
    source_retention_custody_redeposit_computed_sha256: str | None = None
    source_retention_custody_redeposit_status: str | None = None
    source_retention_custody_redeposit_trust_banner: str | None = None
    retention_custody_redeposit_artifact_hash_valid: bool = False
    custody_redeposit_id: str | None = None
    redeposited_by: str | None = None
    redeposit_reason: str | None = None
    custody_location: str | None = None
    redeposited_at_utc: str | None = None
    redeposit_note: str | None = None
    custody_redeposit_statement_declared_sha256: str | None = None
    custody_redeposit_statement_computed_sha256: str | None = None
    custody_redeposit_statement_hash_valid: bool = False
    source_retention_custody_return_verification_artifact_path: str | None = None
    source_retention_custody_return_verification_status: str | None = None
    retention_custody_return_verification_artifact_hash_valid: bool = False
    source_retention_custody_return_status: str | None = None
    retention_custody_return_artifact_hash_valid: bool = False
    custody_return_id: str | None = None
    custody_return_statement_hash_valid: bool = False
    custody_archive_id: str | None = None
    custody_closeout_id: str | None = None
    custody_completion_id: str | None = None
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_redeposit_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyRedepositVerificationView(BaseModel):
    """Read-plane summary of paper evidence retention custody return verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_redeposit_verification_view/v1"] = "paper_execution_evidence_bundle_retention_custody_redeposit_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_redeposit_artifact_path: str | None = None
    source_retention_custody_redeposit_status: str | None = None
    retention_custody_redeposit_artifact_hash_valid: bool = False
    custody_redeposit_id: str | None = None
    redeposited_by: str | None = None
    redeposit_reason: str | None = None
    custody_location: str | None = None
    redeposited_at_utc: str | None = None
    custody_redeposit_statement_hash_valid: bool = False
    source_retention_custody_return_verification_artifact_path: str | None = None
    source_retention_custody_return_verification_status: str | None = None
    retention_custody_return_verification_artifact_hash_valid: bool = False
    source_retention_custody_return_status: str | None = None
    retention_custody_return_artifact_hash_valid: bool = False
    custody_return_id: str | None = None
    custody_return_statement_hash_valid: bool = False
    custody_archive_id: str | None = None
    custody_closeout_id: str | None = None
    custody_completion_id: str | None = None
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}




class PaperExecutionEvidenceBundleRetentionCustodyInventoryArtifact(BaseModel):
    """Read-only inventory record for verified redeposited paper evidence retention custody."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_inventory/v1"] = "paper_execution_evidence_bundle_retention_custody_inventory/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    inventory_authority: Literal["READ_ONLY_RETENTION_CUSTODY_INVENTORY"] = "READ_ONLY_RETENTION_CUSTODY_INVENTORY"
    inventory_status: Literal["INVENTORIED", "INVENTORIED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_inventory_id: str | None = None
    inventoried_by: str | None = None
    inventory_reason: str | None = None
    custody_location: str | None = None
    inventoried_at_utc: str | None = None
    inventory_note: str | None = None
    source_retention_custody_redeposit_verification_artifact_path: str | None = None
    source_retention_custody_redeposit_verification_declared_sha256: str | None = None
    source_retention_custody_redeposit_verification_computed_sha256: str | None = None
    source_retention_custody_redeposit_verification_status: str | None = None
    source_retention_custody_redeposit_verification_trust_banner: str | None = None
    retention_custody_redeposit_verification_artifact_hash_valid: bool = False
    source_retention_custody_redeposit_status: str | None = None
    retention_custody_redeposit_artifact_hash_valid: bool = False
    custody_redeposit_id: str | None = None
    custody_redeposit_statement_hash_valid: bool = False
    custody_return_id: str | None = None
    custody_archive_id: str | None = None
    custody_closeout_id: str | None = None
    custody_completion_id: str | None = None
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_inventory_statement_sha256: str | None = None
    checklist: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_inventory_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyInventoryView(BaseModel):
    """Read-plane summary of paper evidence retention custody inventory records."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_inventory_view/v1"] = "paper_execution_evidence_bundle_retention_custody_inventory_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    inventory_status: Literal["INVENTORIED", "INVENTORIED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_inventory_id: str | None = None
    inventoried_by: str | None = None
    inventory_reason: str | None = None
    custody_location: str | None = None
    inventoried_at_utc: str | None = None
    inventory_note: str | None = None
    source_retention_custody_redeposit_verification_artifact_path: str | None = None
    source_retention_custody_redeposit_verification_status: str | None = None
    retention_custody_redeposit_verification_artifact_hash_valid: bool = False
    source_retention_custody_redeposit_status: str | None = None
    retention_custody_redeposit_artifact_hash_valid: bool = False
    custody_redeposit_id: str | None = None
    custody_redeposit_statement_hash_valid: bool = False
    custody_return_id: str | None = None
    custody_archive_id: str | None = None
    custody_closeout_id: str | None = None
    custody_completion_id: str | None = None
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_inventory_statement_sha256: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyInventoryVerificationArtifact(BaseModel):
    """Read-only verifier for paper evidence retention custody inventory records."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_inventory_verification/v1"] = "paper_execution_evidence_bundle_retention_custody_inventory_verification/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    inventory_verification_authority: Literal["READ_ONLY_RETENTION_CUSTODY_INVENTORY_VERIFICATION"] = "READ_ONLY_RETENTION_CUSTODY_INVENTORY_VERIFICATION"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_inventory_artifact_path: str | None = None
    source_retention_custody_inventory_declared_sha256: str | None = None
    source_retention_custody_inventory_computed_sha256: str | None = None
    source_retention_custody_inventory_status: str | None = None
    source_retention_custody_inventory_trust_banner: str | None = None
    retention_custody_inventory_artifact_hash_valid: bool = False
    custody_inventory_id: str | None = None
    inventoried_by: str | None = None
    inventory_reason: str | None = None
    custody_location: str | None = None
    inventoried_at_utc: str | None = None
    inventory_note: str | None = None
    custody_inventory_statement_declared_sha256: str | None = None
    custody_inventory_statement_computed_sha256: str | None = None
    custody_inventory_statement_hash_valid: bool = False
    source_retention_custody_redeposit_verification_artifact_path: str | None = None
    source_retention_custody_redeposit_verification_status: str | None = None
    retention_custody_redeposit_verification_artifact_hash_valid: bool = False
    source_retention_custody_redeposit_status: str | None = None
    retention_custody_redeposit_artifact_hash_valid: bool = False
    custody_redeposit_id: str | None = None
    custody_redeposit_statement_hash_valid: bool = False
    custody_return_id: str | None = None
    custody_archive_id: str | None = None
    custody_closeout_id: str | None = None
    custody_completion_id: str | None = None
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_inventory_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyInventoryVerificationView(BaseModel):
    """Read-plane summary of paper evidence retention custody inventory verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_inventory_verification_view/v1"] = "paper_execution_evidence_bundle_retention_custody_inventory_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_inventory_artifact_path: str | None = None
    source_retention_custody_inventory_status: str | None = None
    retention_custody_inventory_artifact_hash_valid: bool = False
    custody_inventory_id: str | None = None
    inventoried_by: str | None = None
    inventory_reason: str | None = None
    custody_location: str | None = None
    inventoried_at_utc: str | None = None
    custody_inventory_statement_hash_valid: bool = False
    source_retention_custody_redeposit_verification_artifact_path: str | None = None
    source_retention_custody_redeposit_verification_status: str | None = None
    retention_custody_redeposit_verification_artifact_hash_valid: bool = False
    source_retention_custody_redeposit_status: str | None = None
    retention_custody_redeposit_artifact_hash_valid: bool = False
    custody_redeposit_id: str | None = None
    custody_redeposit_statement_hash_valid: bool = False
    custody_return_id: str | None = None
    custody_archive_id: str | None = None
    custody_closeout_id: str | None = None
    custody_completion_id: str | None = None
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyReconciliationArtifact(BaseModel):
    """Read-only reconciliation record for verified paper evidence retention custody inventory."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_reconciliation/v1"] = "paper_execution_evidence_bundle_retention_custody_reconciliation/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    reconciliation_authority: Literal["READ_ONLY_RETENTION_CUSTODY_RECONCILIATION"] = "READ_ONLY_RETENTION_CUSTODY_RECONCILIATION"
    reconciliation_status: Literal["RECONCILED", "RECONCILED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_reconciliation_id: str | None = None
    reconciled_by: str | None = None
    reconciliation_reason: str | None = None
    custody_location: str | None = None
    reconciled_at_utc: str | None = None
    reconciliation_note: str | None = None
    source_retention_custody_inventory_verification_artifact_path: str | None = None
    source_retention_custody_inventory_verification_declared_sha256: str | None = None
    source_retention_custody_inventory_verification_computed_sha256: str | None = None
    source_retention_custody_inventory_verification_status: str | None = None
    source_retention_custody_inventory_verification_trust_banner: str | None = None
    retention_custody_inventory_verification_artifact_hash_valid: bool = False
    source_retention_custody_inventory_status: str | None = None
    retention_custody_inventory_artifact_hash_valid: bool = False
    custody_inventory_id: str | None = None
    custody_inventory_statement_hash_valid: bool = False
    custody_redeposit_id: str | None = None
    custody_redeposit_statement_hash_valid: bool = False
    source_retention_custody_redeposit_verification_status: str | None = None
    retention_custody_redeposit_verification_artifact_hash_valid: bool = False
    source_retention_custody_redeposit_status: str | None = None
    retention_custody_redeposit_artifact_hash_valid: bool = False
    custody_return_id: str | None = None
    custody_archive_id: str | None = None
    custody_closeout_id: str | None = None
    custody_completion_id: str | None = None
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_reconciliation_statement_sha256: str | None = None
    checklist: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_reconciliation_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyReconciliationView(BaseModel):
    """Read-plane summary of paper evidence retention custody reconciliation records."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_reconciliation_view/v1"] = "paper_execution_evidence_bundle_retention_custody_reconciliation_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    reconciliation_status: Literal["RECONCILED", "RECONCILED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_reconciliation_id: str | None = None
    reconciled_by: str | None = None
    reconciliation_reason: str | None = None
    custody_location: str | None = None
    reconciled_at_utc: str | None = None
    reconciliation_note: str | None = None
    source_retention_custody_inventory_verification_artifact_path: str | None = None
    source_retention_custody_inventory_verification_status: str | None = None
    retention_custody_inventory_verification_artifact_hash_valid: bool = False
    source_retention_custody_inventory_status: str | None = None
    retention_custody_inventory_artifact_hash_valid: bool = False
    custody_inventory_id: str | None = None
    custody_inventory_statement_hash_valid: bool = False
    custody_redeposit_id: str | None = None
    custody_redeposit_statement_hash_valid: bool = False
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_reconciliation_statement_sha256: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyReconciliationVerificationArtifact(BaseModel):
    """Read-only verifier for paper evidence retention custody reconciliation records."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_reconciliation_verification/v1"] = "paper_execution_evidence_bundle_retention_custody_reconciliation_verification/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    reconciliation_verification_authority: Literal["READ_ONLY_RETENTION_CUSTODY_RECONCILIATION_VERIFICATION"] = "READ_ONLY_RETENTION_CUSTODY_RECONCILIATION_VERIFICATION"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_reconciliation_artifact_path: str | None = None
    source_retention_custody_reconciliation_declared_sha256: str | None = None
    source_retention_custody_reconciliation_computed_sha256: str | None = None
    source_retention_custody_reconciliation_status: str | None = None
    source_retention_custody_reconciliation_trust_banner: str | None = None
    retention_custody_reconciliation_artifact_hash_valid: bool = False
    custody_reconciliation_id: str | None = None
    reconciled_by: str | None = None
    reconciliation_reason: str | None = None
    custody_location: str | None = None
    reconciled_at_utc: str | None = None
    reconciliation_note: str | None = None
    custody_reconciliation_statement_declared_sha256: str | None = None
    custody_reconciliation_statement_computed_sha256: str | None = None
    custody_reconciliation_statement_hash_valid: bool = False
    source_retention_custody_inventory_verification_artifact_path: str | None = None
    source_retention_custody_inventory_verification_status: str | None = None
    retention_custody_inventory_verification_artifact_hash_valid: bool = False
    source_retention_custody_inventory_status: str | None = None
    retention_custody_inventory_artifact_hash_valid: bool = False
    custody_inventory_id: str | None = None
    custody_inventory_statement_hash_valid: bool = False
    custody_redeposit_id: str | None = None
    custody_redeposit_statement_hash_valid: bool = False
    source_retention_custody_redeposit_verification_status: str | None = None
    retention_custody_redeposit_verification_artifact_hash_valid: bool = False
    source_retention_custody_redeposit_status: str | None = None
    retention_custody_redeposit_artifact_hash_valid: bool = False
    custody_return_id: str | None = None
    custody_archive_id: str | None = None
    custody_closeout_id: str | None = None
    custody_completion_id: str | None = None
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_reconciliation_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyReconciliationVerificationView(BaseModel):
    """Read-plane summary of paper evidence retention custody reconciliation verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_reconciliation_verification_view/v1"] = "paper_execution_evidence_bundle_retention_custody_reconciliation_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_reconciliation_artifact_path: str | None = None
    source_retention_custody_reconciliation_status: str | None = None
    retention_custody_reconciliation_artifact_hash_valid: bool = False
    custody_reconciliation_id: str | None = None
    reconciled_by: str | None = None
    reconciliation_reason: str | None = None
    custody_location: str | None = None
    reconciled_at_utc: str | None = None
    custody_reconciliation_statement_hash_valid: bool = False
    source_retention_custody_inventory_verification_artifact_path: str | None = None
    source_retention_custody_inventory_verification_status: str | None = None
    retention_custody_inventory_verification_artifact_hash_valid: bool = False
    source_retention_custody_inventory_status: str | None = None
    retention_custody_inventory_artifact_hash_valid: bool = False
    custody_inventory_id: str | None = None
    custody_inventory_statement_hash_valid: bool = False
    custody_redeposit_id: str | None = None
    custody_redeposit_statement_hash_valid: bool = False
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyCertificationArtifact(BaseModel):
    """Read-only certification record for verified paper evidence retention custody reconciliation."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_certification/v1"] = "paper_execution_evidence_bundle_retention_custody_certification/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    certification_authority: Literal["READ_ONLY_RETENTION_CUSTODY_CERTIFICATION"] = "READ_ONLY_RETENTION_CUSTODY_CERTIFICATION"
    certification_status: Literal["CERTIFIED", "CERTIFIED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_certification_id: str | None = None
    certified_by: str | None = None
    certification_reason: str | None = None
    custody_location: str | None = None
    certified_at_utc: str | None = None
    certification_note: str | None = None
    source_retention_custody_reconciliation_verification_artifact_path: str | None = None
    source_retention_custody_reconciliation_verification_declared_sha256: str | None = None
    source_retention_custody_reconciliation_verification_computed_sha256: str | None = None
    source_retention_custody_reconciliation_verification_status: str | None = None
    source_retention_custody_reconciliation_verification_trust_banner: str | None = None
    retention_custody_reconciliation_verification_artifact_hash_valid: bool = False
    source_retention_custody_reconciliation_status: str | None = None
    retention_custody_reconciliation_artifact_hash_valid: bool = False
    custody_reconciliation_id: str | None = None
    custody_reconciliation_statement_hash_valid: bool = False
    source_retention_custody_inventory_verification_status: str | None = None
    retention_custody_inventory_verification_artifact_hash_valid: bool = False
    source_retention_custody_inventory_status: str | None = None
    retention_custody_inventory_artifact_hash_valid: bool = False
    custody_inventory_id: str | None = None
    custody_inventory_statement_hash_valid: bool = False
    custody_redeposit_id: str | None = None
    custody_redeposit_statement_hash_valid: bool = False
    source_retention_custody_redeposit_verification_status: str | None = None
    retention_custody_redeposit_verification_artifact_hash_valid: bool = False
    source_retention_custody_redeposit_status: str | None = None
    retention_custody_redeposit_artifact_hash_valid: bool = False
    custody_return_id: str | None = None
    custody_archive_id: str | None = None
    custody_closeout_id: str | None = None
    custody_completion_id: str | None = None
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_certification_statement_sha256: str | None = None
    checklist: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_certification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyCertificationView(BaseModel):
    """Read-plane summary of paper evidence retention custody certification records."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_certification_view/v1"] = "paper_execution_evidence_bundle_retention_custody_certification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    certification_status: Literal["CERTIFIED", "CERTIFIED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_certification_id: str | None = None
    certified_by: str | None = None
    certification_reason: str | None = None
    custody_location: str | None = None
    certified_at_utc: str | None = None
    certification_note: str | None = None
    source_retention_custody_reconciliation_verification_artifact_path: str | None = None
    source_retention_custody_reconciliation_verification_status: str | None = None
    retention_custody_reconciliation_verification_artifact_hash_valid: bool = False
    source_retention_custody_reconciliation_status: str | None = None
    retention_custody_reconciliation_artifact_hash_valid: bool = False
    custody_reconciliation_id: str | None = None
    custody_reconciliation_statement_hash_valid: bool = False
    custody_inventory_id: str | None = None
    custody_redeposit_id: str | None = None
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_certification_statement_sha256: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyCertificationVerificationArtifact(BaseModel):
    """Read-only verifier for paper evidence retention custody certification records."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_certification_verification/v1"] = "paper_execution_evidence_bundle_retention_custody_certification_verification/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    certification_verification_authority: Literal["READ_ONLY_RETENTION_CUSTODY_CERTIFICATION_VERIFICATION"] = "READ_ONLY_RETENTION_CUSTODY_CERTIFICATION_VERIFICATION"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_certification_artifact_path: str | None = None
    source_retention_custody_certification_declared_sha256: str | None = None
    source_retention_custody_certification_computed_sha256: str | None = None
    source_retention_custody_certification_status: str | None = None
    source_retention_custody_certification_trust_banner: str | None = None
    retention_custody_certification_artifact_hash_valid: bool = False
    custody_certification_id: str | None = None
    certified_by: str | None = None
    certification_reason: str | None = None
    custody_location: str | None = None
    certified_at_utc: str | None = None
    certification_note: str | None = None
    custody_certification_statement_declared_sha256: str | None = None
    custody_certification_statement_computed_sha256: str | None = None
    custody_certification_statement_hash_valid: bool = False
    source_retention_custody_reconciliation_verification_artifact_path: str | None = None
    source_retention_custody_reconciliation_verification_status: str | None = None
    retention_custody_reconciliation_verification_artifact_hash_valid: bool = False
    source_retention_custody_reconciliation_status: str | None = None
    retention_custody_reconciliation_artifact_hash_valid: bool = False
    custody_reconciliation_id: str | None = None
    custody_reconciliation_statement_hash_valid: bool = False
    source_retention_custody_inventory_verification_status: str | None = None
    retention_custody_inventory_verification_artifact_hash_valid: bool = False
    source_retention_custody_inventory_status: str | None = None
    retention_custody_inventory_artifact_hash_valid: bool = False
    custody_inventory_id: str | None = None
    custody_inventory_statement_hash_valid: bool = False
    custody_redeposit_id: str | None = None
    custody_redeposit_statement_hash_valid: bool = False
    source_retention_custody_redeposit_verification_status: str | None = None
    retention_custody_redeposit_verification_artifact_hash_valid: bool = False
    source_retention_custody_redeposit_status: str | None = None
    retention_custody_redeposit_artifact_hash_valid: bool = False
    custody_return_id: str | None = None
    custody_archive_id: str | None = None
    custody_closeout_id: str | None = None
    custody_completion_id: str | None = None
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_certification_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyCertificationVerificationView(BaseModel):
    """Read-plane summary of paper evidence retention custody certification verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_certification_verification_view/v1"] = "paper_execution_evidence_bundle_retention_custody_certification_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_certification_artifact_path: str | None = None
    source_retention_custody_certification_status: str | None = None
    retention_custody_certification_artifact_hash_valid: bool = False
    custody_certification_id: str | None = None
    certified_by: str | None = None
    certification_reason: str | None = None
    custody_location: str | None = None
    certified_at_utc: str | None = None
    custody_certification_statement_hash_valid: bool = False
    source_retention_custody_reconciliation_verification_artifact_path: str | None = None
    source_retention_custody_reconciliation_verification_status: str | None = None
    retention_custody_reconciliation_verification_artifact_hash_valid: bool = False
    source_retention_custody_reconciliation_status: str | None = None
    retention_custody_reconciliation_artifact_hash_valid: bool = False
    custody_reconciliation_id: str | None = None
    custody_reconciliation_statement_hash_valid: bool = False
    custody_inventory_id: str | None = None
    custody_redeposit_id: str | None = None
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyAttestationArtifact(BaseModel):
    """Read-only attestation record for verified certified paper evidence retention custody."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_attestation/v1"] = "paper_execution_evidence_bundle_retention_custody_attestation/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    attestation_authority: Literal["READ_ONLY_RETENTION_CUSTODY_ATTESTATION"] = "READ_ONLY_RETENTION_CUSTODY_ATTESTATION"
    attestation_status: Literal["ATTESTED", "ATTESTED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_attestation_id: str | None = None
    attested_by: str | None = None
    attestation_reason: str | None = None
    attestation_scope: str | None = None
    attested_at_utc: str | None = None
    attestation_note: str | None = None
    source_retention_custody_certification_verification_artifact_path: str | None = None
    source_retention_custody_certification_verification_declared_sha256: str | None = None
    source_retention_custody_certification_verification_computed_sha256: str | None = None
    source_retention_custody_certification_verification_status: str | None = None
    source_retention_custody_certification_verification_trust_banner: str | None = None
    retention_custody_certification_verification_artifact_hash_valid: bool = False
    source_retention_custody_certification_status: str | None = None
    retention_custody_certification_artifact_hash_valid: bool = False
    custody_certification_id: str | None = None
    custody_certification_statement_hash_valid: bool = False
    source_retention_custody_reconciliation_verification_status: str | None = None
    retention_custody_reconciliation_verification_artifact_hash_valid: bool = False
    source_retention_custody_reconciliation_status: str | None = None
    retention_custody_reconciliation_artifact_hash_valid: bool = False
    custody_reconciliation_id: str | None = None
    custody_reconciliation_statement_hash_valid: bool = False
    custody_inventory_id: str | None = None
    custody_redeposit_id: str | None = None
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_attestation_statement_sha256: str | None = None
    checklist: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_attestation_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyAttestationView(BaseModel):
    """Read-plane summary of paper evidence retention custody attestation records."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_attestation_view/v1"] = "paper_execution_evidence_bundle_retention_custody_attestation_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    attestation_status: Literal["ATTESTED", "ATTESTED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_attestation_id: str | None = None
    attested_by: str | None = None
    attestation_reason: str | None = None
    attestation_scope: str | None = None
    attested_at_utc: str | None = None
    attestation_note: str | None = None
    source_retention_custody_certification_verification_artifact_path: str | None = None
    source_retention_custody_certification_verification_status: str | None = None
    retention_custody_certification_verification_artifact_hash_valid: bool = False
    source_retention_custody_certification_status: str | None = None
    retention_custody_certification_artifact_hash_valid: bool = False
    custody_certification_id: str | None = None
    custody_certification_statement_hash_valid: bool = False
    custody_reconciliation_id: str | None = None
    custody_reconciliation_statement_hash_valid: bool = False
    custody_inventory_id: str | None = None
    custody_redeposit_id: str | None = None
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_attestation_statement_sha256: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyAttestationVerificationArtifact(BaseModel):
    """Read-only verifier for paper evidence retention custody attestation records."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_attestation_verification/v1"] = "paper_execution_evidence_bundle_retention_custody_attestation_verification/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    attestation_verification_authority: Literal["READ_ONLY_RETENTION_CUSTODY_ATTESTATION_VERIFICATION"] = "READ_ONLY_RETENTION_CUSTODY_ATTESTATION_VERIFICATION"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_attestation_artifact_path: str | None = None
    source_retention_custody_attestation_declared_sha256: str | None = None
    source_retention_custody_attestation_computed_sha256: str | None = None
    source_retention_custody_attestation_status: str | None = None
    source_retention_custody_attestation_trust_banner: str | None = None
    retention_custody_attestation_artifact_hash_valid: bool = False
    custody_attestation_id: str | None = None
    attested_by: str | None = None
    attestation_reason: str | None = None
    attestation_scope: str | None = None
    attested_at_utc: str | None = None
    attestation_note: str | None = None
    custody_attestation_statement_declared_sha256: str | None = None
    custody_attestation_statement_computed_sha256: str | None = None
    custody_attestation_statement_hash_valid: bool = False
    source_retention_custody_certification_verification_artifact_path: str | None = None
    source_retention_custody_certification_verification_status: str | None = None
    retention_custody_certification_verification_artifact_hash_valid: bool = False
    source_retention_custody_certification_status: str | None = None
    retention_custody_certification_artifact_hash_valid: bool = False
    custody_certification_id: str | None = None
    custody_certification_statement_hash_valid: bool = False
    custody_reconciliation_id: str | None = None
    custody_reconciliation_statement_hash_valid: bool = False
    custody_inventory_id: str | None = None
    custody_redeposit_id: str | None = None
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_attestation_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyAttestationVerificationView(BaseModel):
    """Read-plane summary of paper evidence retention custody attestation verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_attestation_verification_view/v1"] = "paper_execution_evidence_bundle_retention_custody_attestation_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_attestation_artifact_path: str | None = None
    source_retention_custody_attestation_status: str | None = None
    retention_custody_attestation_artifact_hash_valid: bool = False
    custody_attestation_id: str | None = None
    attested_by: str | None = None
    attestation_reason: str | None = None
    attestation_scope: str | None = None
    attested_at_utc: str | None = None
    custody_attestation_statement_hash_valid: bool = False
    source_retention_custody_certification_verification_artifact_path: str | None = None
    source_retention_custody_certification_verification_status: str | None = None
    retention_custody_certification_verification_artifact_hash_valid: bool = False
    source_retention_custody_certification_status: str | None = None
    retention_custody_certification_artifact_hash_valid: bool = False
    custody_certification_id: str | None = None
    custody_certification_statement_hash_valid: bool = False
    custody_reconciliation_id: str | None = None
    custody_reconciliation_statement_hash_valid: bool = False
    custody_inventory_id: str | None = None
    custody_redeposit_id: str | None = None
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionSummary(BaseModel):
    schema_version: Literal["paper_execution_summary/v1"] = "paper_execution_summary/v1"
    broker_policy_status: str
    latest_tracking_id: str | None = None
    latest_strategy_id: str | None = None
    candidate_intent_count: int = 0
    dry_run_ok_count: int = 0
    dry_run_blocked_count: int = 0
    journal_entry_count: int = 0
    dry_run_artifact_count: int = 0
    submission_artifact_count: int = 0
    submission_receipt_count: int = 0
    latest_submission_receipt_at_utc: str | None = None
    latest_submission_guard_status: str | None = None
    latest_submission_evidence_freshness_status: str | None = None
    latest_submission_broker_order_id: str | None = None
    submission_guard_blocker_count: int = 0
    position_snapshot_count: int = 0
    latest_position_snapshot_at_utc: str | None = None
    order_status_artifact_count: int = 0
    latest_order_status_at_utc: str | None = None
    latest_order_status: str | None = None
    latest_order_status_broker_order_id: str | None = None
    latest_order_status_filled_qty: float | None = None
    order_status_blocker_count: int = 0
    position_reconciliation_status: str | None = None
    position_reconciliation_blocker_count: int = 0
    position_reconciliation_warning_count: int = 0
    latest_reconciled_symbol: str | None = None
    latest_reconciled_position_qty: float | None = None
    timeline_event_count: int = 0
    timeline_stage_count: int = 0
    timeline_blocker_count: int = 0
    timeline_warning_count: int = 0
    timeline_trusted_event_count: int = 0
    latest_timeline_event_at_utc: str | None = None
    timeline_sequence_status: str | None = None
    evidence_bundle_count: int = 0
    latest_evidence_bundle_at_utc: str | None = None
    latest_evidence_bundle_trust_banner: str | None = None
    latest_evidence_bundle_status: str | None = None
    latest_evidence_bundle_sha256: str | None = None
    evidence_bundle_blocker_count: int = 0
    evidence_bundle_verification_count: int = 0
    latest_evidence_bundle_verification_at_utc: str | None = None
    latest_evidence_bundle_verification_status: str | None = None
    latest_evidence_bundle_verification_trust_banner: str | None = None
    latest_evidence_bundle_verification_sha256: str | None = None
    evidence_bundle_verification_blocker_count: int = 0
    evidence_bundle_drift_count: int = 0
    latest_evidence_bundle_drift_at_utc: str | None = None
    latest_evidence_bundle_drift_status: str | None = None
    latest_evidence_bundle_drift_trust_banner: str | None = None
    latest_evidence_bundle_drift_sha256: str | None = None
    evidence_bundle_drift_blocker_count: int = 0
    evidence_bundle_drift_new_source_count: int = 0
    evidence_bundle_drift_removed_source_count: int = 0
    evidence_bundle_rotation_count: int = 0
    latest_evidence_bundle_rotation_at_utc: str | None = None
    latest_evidence_bundle_rotation_status: str | None = None
    latest_evidence_bundle_rotation_trust_banner: str | None = None
    latest_evidence_bundle_rotation_sha256: str | None = None
    evidence_bundle_rotation_blocker_count: int = 0
    evidence_bundle_rotation_execution_count: int = 0
    latest_evidence_bundle_rotation_execution_at_utc: str | None = None
    latest_evidence_bundle_rotation_execution_status: str | None = None
    latest_evidence_bundle_rotation_execution_trust_banner: str | None = None
    latest_evidence_bundle_rotation_execution_sha256: str | None = None
    evidence_bundle_rotation_execution_blocker_count: int = 0
    evidence_bundle_attestation_count: int = 0
    latest_evidence_bundle_attestation_at_utc: str | None = None
    latest_evidence_bundle_attestation_status: str | None = None
    latest_evidence_bundle_attestation_trust_banner: str | None = None
    latest_evidence_bundle_attestation_sha256: str | None = None
    evidence_bundle_attestation_blocker_count: int = 0
    evidence_bundle_attestation_verification_count: int = 0
    latest_evidence_bundle_attestation_verification_at_utc: str | None = None
    latest_evidence_bundle_attestation_verification_status: str | None = None
    latest_evidence_bundle_attestation_verification_trust_banner: str | None = None
    latest_evidence_bundle_attestation_verification_sha256: str | None = None
    evidence_bundle_attestation_verification_blocker_count: int = 0
    evidence_bundle_closure_count: int = 0
    latest_evidence_bundle_closure_at_utc: str | None = None
    latest_evidence_bundle_closure_status: str | None = None
    latest_evidence_bundle_closure_trust_banner: str | None = None
    latest_evidence_bundle_closure_sha256: str | None = None
    evidence_bundle_closure_blocker_count: int = 0
    evidence_bundle_closure_verification_count: int = 0
    latest_evidence_bundle_closure_verification_at_utc: str | None = None
    latest_evidence_bundle_closure_verification_status: str | None = None
    latest_evidence_bundle_closure_verification_trust_banner: str | None = None
    latest_evidence_bundle_closure_verification_sha256: str | None = None
    evidence_bundle_closure_verification_blocker_count: int = 0
    evidence_bundle_export_manifest_count: int = 0
    latest_evidence_bundle_export_manifest_at_utc: str | None = None
    latest_evidence_bundle_export_manifest_status: str | None = None
    latest_evidence_bundle_export_manifest_trust_banner: str | None = None
    latest_evidence_bundle_export_manifest_sha256: str | None = None
    evidence_bundle_export_manifest_blocker_count: int = 0
    evidence_bundle_export_verification_count: int = 0
    latest_evidence_bundle_export_verification_at_utc: str | None = None
    latest_evidence_bundle_export_verification_status: str | None = None
    latest_evidence_bundle_export_verification_trust_banner: str | None = None
    latest_evidence_bundle_export_verification_sha256: str | None = None
    evidence_bundle_export_verification_blocker_count: int = 0
    evidence_bundle_retention_receipt_count: int = 0
    latest_evidence_bundle_retention_receipt_at_utc: str | None = None
    latest_evidence_bundle_retention_receipt_status: str | None = None
    latest_evidence_bundle_retention_receipt_trust_banner: str | None = None
    latest_evidence_bundle_retention_receipt_sha256: str | None = None
    evidence_bundle_retention_receipt_blocker_count: int = 0
    evidence_bundle_retention_verification_count: int = 0
    latest_evidence_bundle_retention_verification_at_utc: str | None = None
    latest_evidence_bundle_retention_verification_status: str | None = None
    latest_evidence_bundle_retention_verification_trust_banner: str | None = None
    latest_evidence_bundle_retention_verification_sha256: str | None = None
    evidence_bundle_retention_verification_blocker_count: int = 0
    evidence_bundle_retention_signoff_count: int = 0
    latest_evidence_bundle_retention_signoff_at_utc: str | None = None
    latest_evidence_bundle_retention_signoff_status: str | None = None
    latest_evidence_bundle_retention_signoff_trust_banner: str | None = None
    latest_evidence_bundle_retention_signoff_sha256: str | None = None
    evidence_bundle_retention_signoff_blocker_count: int = 0
    evidence_bundle_retention_signoff_verification_count: int = 0
    latest_evidence_bundle_retention_signoff_verification_at_utc: str | None = None
    latest_evidence_bundle_retention_signoff_verification_status: str | None = None
    latest_evidence_bundle_retention_signoff_verification_trust_banner: str | None = None
    latest_evidence_bundle_retention_signoff_verification_sha256: str | None = None
    evidence_bundle_retention_signoff_verification_blocker_count: int = 0
    evidence_bundle_retention_handoff_count: int = 0
    latest_evidence_bundle_retention_handoff_at_utc: str | None = None
    latest_evidence_bundle_retention_handoff_status: str | None = None
    latest_evidence_bundle_retention_handoff_trust_banner: str | None = None
    latest_evidence_bundle_retention_handoff_sha256: str | None = None
    evidence_bundle_retention_handoff_blocker_count: int = 0
    evidence_bundle_retention_handoff_verification_count: int = 0
    latest_evidence_bundle_retention_handoff_verification_at_utc: str | None = None
    latest_evidence_bundle_retention_handoff_verification_status: str | None = None
    latest_evidence_bundle_retention_handoff_verification_trust_banner: str | None = None
    latest_evidence_bundle_retention_handoff_verification_sha256: str | None = None
    evidence_bundle_retention_handoff_verification_blocker_count: int = 0
    evidence_bundle_retention_handoff_acceptance_count: int = 0
    latest_evidence_bundle_retention_handoff_acceptance_at_utc: str | None = None
    latest_evidence_bundle_retention_handoff_acceptance_status: str | None = None
    latest_evidence_bundle_retention_handoff_acceptance_trust_banner: str | None = None
    latest_evidence_bundle_retention_handoff_acceptance_sha256: str | None = None
    evidence_bundle_retention_handoff_acceptance_blocker_count: int = 0
    evidence_bundle_retention_handoff_acceptance_verification_count: int = 0
    latest_evidence_bundle_retention_handoff_acceptance_verification_at_utc: str | None = None
    latest_evidence_bundle_retention_handoff_acceptance_verification_status: str | None = None
    latest_evidence_bundle_retention_handoff_acceptance_verification_trust_banner: str | None = None
    latest_evidence_bundle_retention_handoff_acceptance_verification_sha256: str | None = None
    evidence_bundle_retention_handoff_acceptance_verification_blocker_count: int = 0
    evidence_bundle_retention_custody_register_count: int = 0
    latest_evidence_bundle_retention_custody_register_at_utc: str | None = None
    latest_evidence_bundle_retention_custody_register_status: str | None = None
    latest_evidence_bundle_retention_custody_register_trust_banner: str | None = None
    latest_evidence_bundle_retention_custody_register_sha256: str | None = None
    evidence_bundle_retention_custody_register_blocker_count: int = 0
    evidence_bundle_retention_custody_register_verification_count: int = 0
    latest_evidence_bundle_retention_custody_register_verification_at_utc: str | None = None
    latest_evidence_bundle_retention_custody_register_verification_status: str | None = None
    latest_evidence_bundle_retention_custody_register_verification_trust_banner: str | None = None
    latest_evidence_bundle_retention_custody_register_verification_sha256: str | None = None
    evidence_bundle_retention_custody_register_verification_blocker_count: int = 0
    evidence_bundle_retention_custody_seal_count: int = 0
    latest_evidence_bundle_retention_custody_seal_at_utc: str | None = None
    latest_evidence_bundle_retention_custody_seal_status: str | None = None
    latest_evidence_bundle_retention_custody_seal_trust_banner: str | None = None
    latest_evidence_bundle_retention_custody_seal_sha256: str | None = None
    evidence_bundle_retention_custody_seal_blocker_count: int = 0
    evidence_bundle_retention_custody_seal_verification_count: int = 0
    latest_evidence_bundle_retention_custody_seal_verification_at_utc: str | None = None
    latest_evidence_bundle_retention_custody_seal_verification_status: str | None = None
    latest_evidence_bundle_retention_custody_seal_verification_trust_banner: str | None = None
    latest_evidence_bundle_retention_custody_seal_verification_sha256: str | None = None
    evidence_bundle_retention_custody_seal_verification_blocker_count: int = 0
    evidence_bundle_retention_custody_audit_count: int = 0
    latest_evidence_bundle_retention_custody_audit_at_utc: str | None = None
    latest_evidence_bundle_retention_custody_audit_status: str | None = None
    latest_evidence_bundle_retention_custody_audit_trust_banner: str | None = None
    latest_evidence_bundle_retention_custody_audit_sha256: str | None = None
    evidence_bundle_retention_custody_audit_blocker_count: int = 0
    evidence_bundle_retention_custody_audit_verification_count: int = 0
    latest_evidence_bundle_retention_custody_audit_verification_at_utc: str | None = None
    latest_evidence_bundle_retention_custody_audit_verification_status: str | None = None
    latest_evidence_bundle_retention_custody_audit_verification_trust_banner: str | None = None
    latest_evidence_bundle_retention_custody_audit_verification_sha256: str | None = None
    evidence_bundle_retention_custody_audit_verification_blocker_count: int = 0
    evidence_bundle_retention_custody_continuity_count: int = 0
    latest_evidence_bundle_retention_custody_continuity_at_utc: str | None = None
    latest_evidence_bundle_retention_custody_continuity_status: str | None = None
    latest_evidence_bundle_retention_custody_continuity_trust_banner: str | None = None
    latest_evidence_bundle_retention_custody_continuity_sha256: str | None = None
    evidence_bundle_retention_custody_continuity_blocker_count: int = 0
    evidence_bundle_retention_custody_continuity_verification_count: int = 0
    latest_evidence_bundle_retention_custody_continuity_verification_at_utc: str | None = None
    latest_evidence_bundle_retention_custody_continuity_verification_status: str | None = None
    latest_evidence_bundle_retention_custody_continuity_verification_trust_banner: str | None = None
    latest_evidence_bundle_retention_custody_continuity_verification_sha256: str | None = None
    evidence_bundle_retention_custody_continuity_verification_blocker_count: int = 0
    evidence_bundle_retention_custody_review_count: int = 0
    latest_evidence_bundle_retention_custody_review_at_utc: str | None = None
    latest_evidence_bundle_retention_custody_review_status: str | None = None
    latest_evidence_bundle_retention_custody_review_trust_banner: str | None = None
    latest_evidence_bundle_retention_custody_review_sha256: str | None = None
    evidence_bundle_retention_custody_review_blocker_count: int = 0
    evidence_bundle_retention_custody_review_verification_count: int = 0
    latest_evidence_bundle_retention_custody_review_verification_at_utc: str | None = None
    latest_evidence_bundle_retention_custody_review_verification_status: str | None = None
    latest_evidence_bundle_retention_custody_review_verification_trust_banner: str | None = None
    latest_evidence_bundle_retention_custody_review_verification_sha256: str | None = None
    evidence_bundle_retention_custody_review_verification_blocker_count: int = 0
    evidence_bundle_retention_custody_renewal_count: int = 0
    latest_evidence_bundle_retention_custody_renewal_at_utc: str | None = None
    latest_evidence_bundle_retention_custody_renewal_status: str | None = None
    latest_evidence_bundle_retention_custody_renewal_trust_banner: str | None = None
    latest_evidence_bundle_retention_custody_renewal_sha256: str | None = None
    evidence_bundle_retention_custody_renewal_blocker_count: int = 0
    evidence_bundle_retention_custody_renewal_verification_count: int = 0
    latest_evidence_bundle_retention_custody_renewal_verification_at_utc: str | None = None
    latest_evidence_bundle_retention_custody_renewal_verification_status: str | None = None
    latest_evidence_bundle_retention_custody_renewal_verification_trust_banner: str | None = None
    latest_evidence_bundle_retention_custody_renewal_verification_sha256: str | None = None
    evidence_bundle_retention_custody_renewal_verification_blocker_count: int = 0
    evidence_bundle_retention_custody_schedule_count: int = 0
    latest_evidence_bundle_retention_custody_schedule_at_utc: str | None = None
    latest_evidence_bundle_retention_custody_schedule_status: str | None = None
    latest_evidence_bundle_retention_custody_schedule_trust_banner: str | None = None
    latest_evidence_bundle_retention_custody_schedule_sha256: str | None = None
    latest_evidence_bundle_retention_custody_schedule_due_at_utc: str | None = None
    evidence_bundle_retention_custody_schedule_blocker_count: int = 0
    evidence_bundle_retention_custody_schedule_verification_count: int = 0
    latest_evidence_bundle_retention_custody_schedule_verification_at_utc: str | None = None
    latest_evidence_bundle_retention_custody_schedule_verification_status: str | None = None
    latest_evidence_bundle_retention_custody_schedule_verification_trust_banner: str | None = None
    latest_evidence_bundle_retention_custody_schedule_verification_sha256: str | None = None
    latest_evidence_bundle_retention_custody_schedule_verification_due_at_utc: str | None = None
    evidence_bundle_retention_custody_schedule_verification_blocker_count: int = 0
    evidence_bundle_retention_custody_notice_count: int = 0
    latest_evidence_bundle_retention_custody_notice_at_utc: str | None = None
    latest_evidence_bundle_retention_custody_notice_status: str | None = None
    latest_evidence_bundle_retention_custody_notice_trust_banner: str | None = None
    latest_evidence_bundle_retention_custody_notice_sha256: str | None = None
    latest_evidence_bundle_retention_custody_notice_due_at_utc: str | None = None
    evidence_bundle_retention_custody_notice_blocker_count: int = 0
    evidence_bundle_retention_custody_notice_verification_count: int = 0
    latest_evidence_bundle_retention_custody_notice_verification_at_utc: str | None = None
    latest_evidence_bundle_retention_custody_notice_verification_status: str | None = None
    latest_evidence_bundle_retention_custody_notice_verification_trust_banner: str | None = None
    latest_evidence_bundle_retention_custody_notice_verification_sha256: str | None = None
    latest_evidence_bundle_retention_custody_notice_verification_due_at_utc: str | None = None
    evidence_bundle_retention_custody_notice_verification_blocker_count: int = 0
    evidence_bundle_retention_custody_acknowledgment_count: int = 0
    latest_evidence_bundle_retention_custody_acknowledgment_at_utc: str | None = None
    latest_evidence_bundle_retention_custody_acknowledgment_status: str | None = None
    latest_evidence_bundle_retention_custody_acknowledgment_trust_banner: str | None = None
    latest_evidence_bundle_retention_custody_acknowledgment_sha256: str | None = None
    latest_evidence_bundle_retention_custody_acknowledgment_due_at_utc: str | None = None
    evidence_bundle_retention_custody_acknowledgment_blocker_count: int = 0
    evidence_bundle_retention_custody_acknowledgment_verification_count: int = 0
    latest_evidence_bundle_retention_custody_acknowledgment_verification_at_utc: str | None = None
    latest_evidence_bundle_retention_custody_acknowledgment_verification_status: str | None = None
    latest_evidence_bundle_retention_custody_acknowledgment_verification_trust_banner: str | None = None
    latest_evidence_bundle_retention_custody_acknowledgment_verification_sha256: str | None = None
    latest_evidence_bundle_retention_custody_acknowledgment_verification_due_at_utc: str | None = None
    evidence_bundle_retention_custody_acknowledgment_verification_blocker_count: int = 0
    evidence_bundle_retention_custody_completion_count: int = 0
    latest_evidence_bundle_retention_custody_completion_at_utc: str | None = None
    latest_evidence_bundle_retention_custody_completion_status: str | None = None
    latest_evidence_bundle_retention_custody_completion_trust_banner: str | None = None
    latest_evidence_bundle_retention_custody_completion_sha256: str | None = None
    latest_evidence_bundle_retention_custody_completion_due_at_utc: str | None = None
    evidence_bundle_retention_custody_completion_blocker_count: int = 0
    evidence_bundle_retention_custody_completion_verification_count: int = 0
    latest_evidence_bundle_retention_custody_completion_verification_at_utc: str | None = None
    latest_evidence_bundle_retention_custody_completion_verification_status: str | None = None
    latest_evidence_bundle_retention_custody_completion_verification_trust_banner: str | None = None
    latest_evidence_bundle_retention_custody_completion_verification_sha256: str | None = None
    latest_evidence_bundle_retention_custody_completion_verification_due_at_utc: str | None = None
    evidence_bundle_retention_custody_completion_verification_blocker_count: int = 0
    evidence_bundle_retention_custody_closeout_count: int = 0
    latest_evidence_bundle_retention_custody_closeout_at_utc: str | None = None
    latest_evidence_bundle_retention_custody_closeout_status: str | None = None
    latest_evidence_bundle_retention_custody_closeout_trust_banner: str | None = None
    latest_evidence_bundle_retention_custody_closeout_sha256: str | None = None
    latest_evidence_bundle_retention_custody_closeout_due_at_utc: str | None = None
    evidence_bundle_retention_custody_closeout_blocker_count: int = 0
    evidence_bundle_retention_custody_closeout_verification_count: int = 0
    latest_evidence_bundle_retention_custody_closeout_verification_at_utc: str | None = None
    latest_evidence_bundle_retention_custody_closeout_verification_status: str | None = None
    latest_evidence_bundle_retention_custody_closeout_verification_trust_banner: str | None = None
    latest_evidence_bundle_retention_custody_closeout_verification_sha256: str | None = None
    latest_evidence_bundle_retention_custody_closeout_verification_due_at_utc: str | None = None
    evidence_bundle_retention_custody_closeout_verification_blocker_count: int = 0
    evidence_bundle_retention_custody_archive_count: int = 0
    latest_evidence_bundle_retention_custody_archive_at_utc: str | None = None
    latest_evidence_bundle_retention_custody_archive_status: str | None = None
    latest_evidence_bundle_retention_custody_archive_trust_banner: str | None = None
    latest_evidence_bundle_retention_custody_archive_sha256: str | None = None
    latest_evidence_bundle_retention_custody_archive_due_at_utc: str | None = None
    evidence_bundle_retention_custody_archive_blocker_count: int = 0
    evidence_bundle_retention_custody_archive_verification_count: int = 0
    latest_evidence_bundle_retention_custody_archive_verification_at_utc: str | None = None
    latest_evidence_bundle_retention_custody_archive_verification_status: str | None = None
    latest_evidence_bundle_retention_custody_archive_verification_trust_banner: str | None = None
    latest_evidence_bundle_retention_custody_archive_verification_sha256: str | None = None
    latest_evidence_bundle_retention_custody_archive_verification_due_at_utc: str | None = None
    evidence_bundle_retention_custody_archive_verification_blocker_count: int = 0
    evidence_bundle_retention_custody_retrieval_count: int = 0
    latest_evidence_bundle_retention_custody_retrieval_at_utc: str | None = None
    latest_evidence_bundle_retention_custody_retrieval_status: str | None = None
    latest_evidence_bundle_retention_custody_retrieval_trust_banner: str | None = None
    latest_evidence_bundle_retention_custody_retrieval_sha256: str | None = None
    latest_evidence_bundle_retention_custody_retrieval_due_at_utc: str | None = None
    evidence_bundle_retention_custody_retrieval_blocker_count: int = 0
    evidence_bundle_retention_custody_retrieval_verification_count: int = 0
    latest_evidence_bundle_retention_custody_retrieval_verification_at_utc: str | None = None
    latest_evidence_bundle_retention_custody_retrieval_verification_status: str | None = None
    latest_evidence_bundle_retention_custody_retrieval_verification_trust_banner: str | None = None
    latest_evidence_bundle_retention_custody_retrieval_verification_sha256: str | None = None
    latest_evidence_bundle_retention_custody_retrieval_verification_due_at_utc: str | None = None
    evidence_bundle_retention_custody_retrieval_verification_blocker_count: int = 0
    evidence_bundle_retention_custody_return_count: int = 0
    latest_evidence_bundle_retention_custody_return_at_utc: str | None = None
    latest_evidence_bundle_retention_custody_return_status: str | None = None
    latest_evidence_bundle_retention_custody_return_trust_banner: str | None = None
    latest_evidence_bundle_retention_custody_return_sha256: str | None = None
    latest_evidence_bundle_retention_custody_return_due_at_utc: str | None = None
    evidence_bundle_retention_custody_return_blocker_count: int = 0
    evidence_bundle_retention_custody_return_verification_count: int = 0
    latest_evidence_bundle_retention_custody_return_verification_at_utc: str | None = None
    latest_evidence_bundle_retention_custody_return_verification_status: str | None = None
    latest_evidence_bundle_retention_custody_return_verification_trust_banner: str | None = None
    latest_evidence_bundle_retention_custody_return_verification_sha256: str | None = None
    latest_evidence_bundle_retention_custody_return_verification_due_at_utc: str | None = None
    evidence_bundle_retention_custody_return_verification_blocker_count: int = 0
    evidence_bundle_retention_custody_redeposit_count: int = 0
    latest_evidence_bundle_retention_custody_redeposit_at_utc: str | None = None
    latest_evidence_bundle_retention_custody_redeposit_status: str | None = None
    latest_evidence_bundle_retention_custody_redeposit_trust_banner: str | None = None
    latest_evidence_bundle_retention_custody_redeposit_sha256: str | None = None
    latest_evidence_bundle_retention_custody_redeposit_due_at_utc: str | None = None
    evidence_bundle_retention_custody_redeposit_blocker_count: int = 0
    evidence_bundle_retention_custody_redeposit_verification_count: int = 0
    latest_evidence_bundle_retention_custody_redeposit_verification_at_utc: str | None = None
    latest_evidence_bundle_retention_custody_redeposit_verification_status: str | None = None
    latest_evidence_bundle_retention_custody_redeposit_verification_trust_banner: str | None = None
    latest_evidence_bundle_retention_custody_redeposit_verification_sha256: str | None = None
    latest_evidence_bundle_retention_custody_redeposit_verification_due_at_utc: str | None = None
    evidence_bundle_retention_custody_redeposit_verification_blocker_count: int = 0
    evidence_bundle_retention_custody_inventory_count: int = 0
    latest_evidence_bundle_retention_custody_inventory_at_utc: str | None = None
    latest_evidence_bundle_retention_custody_inventory_status: str | None = None
    latest_evidence_bundle_retention_custody_inventory_trust_banner: str | None = None
    latest_evidence_bundle_retention_custody_inventory_sha256: str | None = None
    latest_evidence_bundle_retention_custody_inventory_due_at_utc: str | None = None
    evidence_bundle_retention_custody_inventory_blocker_count: int = 0
    evidence_bundle_retention_custody_inventory_verification_count: int = 0
    latest_evidence_bundle_retention_custody_inventory_verification_at_utc: str | None = None
    latest_evidence_bundle_retention_custody_inventory_verification_status: str | None = None
    latest_evidence_bundle_retention_custody_inventory_verification_trust_banner: str | None = None
    latest_evidence_bundle_retention_custody_inventory_verification_sha256: str | None = None
    latest_evidence_bundle_retention_custody_inventory_verification_due_at_utc: str | None = None
    evidence_bundle_retention_custody_inventory_verification_blocker_count: int = 0
    evidence_bundle_retention_custody_reconciliation_count: int = 0
    latest_evidence_bundle_retention_custody_reconciliation_at_utc: str | None = None
    latest_evidence_bundle_retention_custody_reconciliation_status: str | None = None
    latest_evidence_bundle_retention_custody_reconciliation_trust_banner: str | None = None
    latest_evidence_bundle_retention_custody_reconciliation_sha256: str | None = None
    latest_evidence_bundle_retention_custody_reconciliation_due_at_utc: str | None = None
    evidence_bundle_retention_custody_reconciliation_blocker_count: int = 0
    evidence_bundle_retention_custody_reconciliation_verification_count: int = 0
    latest_evidence_bundle_retention_custody_reconciliation_verification_at_utc: str | None = None
    latest_evidence_bundle_retention_custody_reconciliation_verification_status: str | None = None
    latest_evidence_bundle_retention_custody_reconciliation_verification_trust_banner: str | None = None
    latest_evidence_bundle_retention_custody_reconciliation_verification_sha256: str | None = None
    latest_evidence_bundle_retention_custody_reconciliation_verification_due_at_utc: str | None = None
    evidence_bundle_retention_custody_reconciliation_verification_blocker_count: int = 0
    evidence_bundle_retention_custody_certification_count: int = 0
    latest_evidence_bundle_retention_custody_certification_at_utc: str | None = None
    latest_evidence_bundle_retention_custody_certification_status: str | None = None
    latest_evidence_bundle_retention_custody_certification_trust_banner: str | None = None
    latest_evidence_bundle_retention_custody_certification_sha256: str | None = None
    latest_evidence_bundle_retention_custody_certification_due_at_utc: str | None = None
    evidence_bundle_retention_custody_certification_blocker_count: int = 0
    evidence_bundle_retention_custody_certification_verification_count: int = 0
    latest_evidence_bundle_retention_custody_certification_verification_at_utc: str | None = None
    latest_evidence_bundle_retention_custody_certification_verification_status: str | None = None
    latest_evidence_bundle_retention_custody_certification_verification_trust_banner: str | None = None
    latest_evidence_bundle_retention_custody_certification_verification_sha256: str | None = None
    latest_evidence_bundle_retention_custody_certification_verification_due_at_utc: str | None = None
    evidence_bundle_retention_custody_certification_verification_blocker_count: int = 0
    evidence_bundle_retention_custody_attestation_count: int = 0
    latest_evidence_bundle_retention_custody_attestation_at_utc: str | None = None
    latest_evidence_bundle_retention_custody_attestation_status: str | None = None
    latest_evidence_bundle_retention_custody_attestation_trust_banner: str | None = None
    latest_evidence_bundle_retention_custody_attestation_sha256: str | None = None
    latest_evidence_bundle_retention_custody_attestation_due_at_utc: str | None = None
    evidence_bundle_retention_custody_attestation_blocker_count: int = 0
    evidence_bundle_retention_custody_attestation_verification_count: int = 0
    latest_evidence_bundle_retention_custody_attestation_verification_at_utc: str | None = None
    latest_evidence_bundle_retention_custody_attestation_verification_status: str | None = None
    latest_evidence_bundle_retention_custody_attestation_verification_trust_banner: str | None = None
    latest_evidence_bundle_retention_custody_attestation_verification_sha256: str | None = None
    latest_evidence_bundle_retention_custody_attestation_verification_due_at_utc: str | None = None
    evidence_bundle_retention_custody_attestation_verification_blocker_count: int = 0
    latest_dry_run_artifact_at_utc: str | None = None
    latest_dry_run_source_selection_sha256: str | None = None
    selected_intent_dry_run_match: bool | None = None
    selected_intent_dry_run_status: Literal["NO_SELECTED_INTENT", "NO_DRY_RUN", "MATCHED", "MISMATCHED"] = "NO_SELECTED_INTENT"
    selected_intent_count: int = 0
    latest_selected_tracking_id: str | None = None
    latest_selected_intent_at_utc: str | None = None
    selected_intent_artifact_path: str | None = None
    broker_ready: bool = False
    tracking_present: bool = False
    paper_submission_capability: str = "CLI_ONLY"
    evidence_freshness_status: Literal["FRESH", "STALE", "REPLAY_REQUIRED", "MISSING_EVIDENCE", "UNKNOWN"] = "UNKNOWN"
    evidence_freshness_blocker_count: int = 0
    selected_intent_age_hours: float | None = None
    latest_linked_dry_run_age_hours: float | None = None
    latest_tracking_signal_age_hours: float | None = None

    model_config = {"extra": "forbid"}


class PaperExecutionCockpitPayload(BaseModel):
    schema_version: Literal["ui_paper_execution_cockpit/v1"] = "ui_paper_execution_cockpit/v1"
    generated_at_utc: datetime
    read_plane_only: bool = True
    no_live_trading: bool = True
    no_browser_orders: bool = True
    no_network_calls: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    paper_submission_authority: Literal["CLI_ONLY"] = "CLI_ONLY"
    scan_root: str
    broker_artifact_path: str | None = None
    degraded: list[str] = Field(default_factory=list)
    summary: PaperExecutionSummary
    broker_status: dict[str, Any] = Field(default_factory=dict)
    latest_tracking: dict[str, Any] | None = None
    candidate_intents: list[PaperExecutionIntentPreview] = Field(default_factory=list)
    selected_intent: PaperExecutionIntentSelectionArtifact | None = None
    dry_run_command_hint: str | None = None
    dry_run_results: list[dict[str, Any]] = Field(default_factory=list)
    freshness_gate: PaperExecutionFreshnessGate = Field(default_factory=PaperExecutionFreshnessGate)
    journal_entries: list[PaperExecutionJournalEntry] = Field(default_factory=list)
    submission_receipts: list[PaperExecutionSubmissionReceiptView] = Field(default_factory=list)
    order_statuses: list[PaperExecutionOrderStatusView] = Field(default_factory=list)
    account_position_snapshot: PaperExecutionAccountPositionSnapshotArtifact | None = None
    position_reconciliation: PaperExecutionPositionReconciliationView = Field(default_factory=PaperExecutionPositionReconciliationView)
    execution_timeline: list[PaperExecutionTimelineEntry] = Field(default_factory=list)
    execution_timeline_summary: PaperExecutionTimelineSummary = Field(default_factory=PaperExecutionTimelineSummary)
    evidence_bundles: list[PaperExecutionEvidenceBundleView] = Field(default_factory=list)
    latest_evidence_bundle: PaperExecutionEvidenceBundleView | None = None
    evidence_bundle_verifications: list[PaperExecutionEvidenceBundleVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_verification: PaperExecutionEvidenceBundleVerificationView | None = None
    evidence_bundle_drifts: list[PaperExecutionEvidenceBundleDriftView] = Field(default_factory=list)
    latest_evidence_bundle_drift: PaperExecutionEvidenceBundleDriftView | None = None
    evidence_bundle_rotations: list[PaperExecutionEvidenceBundleRotationView] = Field(default_factory=list)
    latest_evidence_bundle_rotation: PaperExecutionEvidenceBundleRotationView | None = None
    evidence_bundle_rotation_executions: list[PaperExecutionEvidenceBundleRotationExecutionView] = Field(default_factory=list)
    latest_evidence_bundle_rotation_execution: PaperExecutionEvidenceBundleRotationExecutionView | None = None
    evidence_bundle_attestations: list[PaperExecutionEvidenceBundleAttestationView] = Field(default_factory=list)
    latest_evidence_bundle_attestation: PaperExecutionEvidenceBundleAttestationView | None = None
    evidence_bundle_attestation_verifications: list[PaperExecutionEvidenceBundleAttestationVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_attestation_verification: PaperExecutionEvidenceBundleAttestationVerificationView | None = None
    evidence_bundle_closures: list[PaperExecutionEvidenceBundleClosureView] = Field(default_factory=list)
    latest_evidence_bundle_closure: PaperExecutionEvidenceBundleClosureView | None = None
    evidence_bundle_closure_verifications: list[PaperExecutionEvidenceBundleClosureVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_closure_verification: PaperExecutionEvidenceBundleClosureVerificationView | None = None
    evidence_bundle_export_manifests: list[PaperExecutionEvidenceBundleExportManifestView] = Field(default_factory=list)
    latest_evidence_bundle_export_manifest: PaperExecutionEvidenceBundleExportManifestView | None = None
    evidence_bundle_export_verifications: list[PaperExecutionEvidenceBundleExportVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_export_verification: PaperExecutionEvidenceBundleExportVerificationView | None = None
    evidence_bundle_retention_receipts: list[PaperExecutionEvidenceBundleRetentionReceiptView] = Field(default_factory=list)
    latest_evidence_bundle_retention_receipt: PaperExecutionEvidenceBundleRetentionReceiptView | None = None
    evidence_bundle_retention_verifications: list[PaperExecutionEvidenceBundleRetentionVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_verification: PaperExecutionEvidenceBundleRetentionVerificationView | None = None
    evidence_bundle_retention_signoffs: list[PaperExecutionEvidenceBundleRetentionSignoffView] = Field(default_factory=list)
    latest_evidence_bundle_retention_signoff: PaperExecutionEvidenceBundleRetentionSignoffView | None = None
    evidence_bundle_retention_signoff_verifications: list[PaperExecutionEvidenceBundleRetentionSignoffVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_signoff_verification: PaperExecutionEvidenceBundleRetentionSignoffVerificationView | None = None
    evidence_bundle_retention_handoffs: list[PaperExecutionEvidenceBundleRetentionHandoffView] = Field(default_factory=list)
    latest_evidence_bundle_retention_handoff: PaperExecutionEvidenceBundleRetentionHandoffView | None = None
    evidence_bundle_retention_handoff_verifications: list[PaperExecutionEvidenceBundleRetentionHandoffVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_handoff_verification: PaperExecutionEvidenceBundleRetentionHandoffVerificationView | None = None
    evidence_bundle_retention_handoff_acceptances: list[PaperExecutionEvidenceBundleRetentionHandoffAcceptanceView] = Field(default_factory=list)
    latest_evidence_bundle_retention_handoff_acceptance: PaperExecutionEvidenceBundleRetentionHandoffAcceptanceView | None = None
    evidence_bundle_retention_handoff_acceptance_verifications: list[PaperExecutionEvidenceBundleRetentionHandoffAcceptanceVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_handoff_acceptance_verification: PaperExecutionEvidenceBundleRetentionHandoffAcceptanceVerificationView | None = None
    evidence_bundle_retention_custody_registers: list[PaperExecutionEvidenceBundleRetentionCustodyRegisterView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_register: PaperExecutionEvidenceBundleRetentionCustodyRegisterView | None = None
    evidence_bundle_retention_custody_register_verifications: list[PaperExecutionEvidenceBundleRetentionCustodyRegisterVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_register_verification: PaperExecutionEvidenceBundleRetentionCustodyRegisterVerificationView | None = None
    evidence_bundle_retention_custody_seals: list[PaperExecutionEvidenceBundleRetentionCustodySealView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_seal: PaperExecutionEvidenceBundleRetentionCustodySealView | None = None
    evidence_bundle_retention_custody_seal_verifications: list[PaperExecutionEvidenceBundleRetentionCustodySealVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_seal_verification: PaperExecutionEvidenceBundleRetentionCustodySealVerificationView | None = None
    evidence_bundle_retention_custody_audits: list[PaperExecutionEvidenceBundleRetentionCustodyAuditView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_audit: PaperExecutionEvidenceBundleRetentionCustodyAuditView | None = None
    evidence_bundle_retention_custody_audit_verifications: list[PaperExecutionEvidenceBundleRetentionCustodyAuditVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_audit_verification: PaperExecutionEvidenceBundleRetentionCustodyAuditVerificationView | None = None
    evidence_bundle_retention_custody_continuities: list[PaperExecutionEvidenceBundleRetentionCustodyContinuityView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_continuity: PaperExecutionEvidenceBundleRetentionCustodyContinuityView | None = None
    evidence_bundle_retention_custody_continuity_verifications: list[PaperExecutionEvidenceBundleRetentionCustodyContinuityVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_continuity_verification: PaperExecutionEvidenceBundleRetentionCustodyContinuityVerificationView | None = None
    evidence_bundle_retention_custody_reviews: list[PaperExecutionEvidenceBundleRetentionCustodyReviewView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_review: PaperExecutionEvidenceBundleRetentionCustodyReviewView | None = None
    evidence_bundle_retention_custody_review_verifications: list[PaperExecutionEvidenceBundleRetentionCustodyReviewVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_review_verification: PaperExecutionEvidenceBundleRetentionCustodyReviewVerificationView | None = None
    evidence_bundle_retention_custody_renewals: list[PaperExecutionEvidenceBundleRetentionCustodyRenewalView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_renewal: PaperExecutionEvidenceBundleRetentionCustodyRenewalView | None = None
    evidence_bundle_retention_custody_renewal_verifications: list[PaperExecutionEvidenceBundleRetentionCustodyRenewalVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_renewal_verification: PaperExecutionEvidenceBundleRetentionCustodyRenewalVerificationView | None = None
    evidence_bundle_retention_custody_schedules: list[PaperExecutionEvidenceBundleRetentionCustodyScheduleView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_schedule: PaperExecutionEvidenceBundleRetentionCustodyScheduleView | None = None
    evidence_bundle_retention_custody_schedule_verifications: list[PaperExecutionEvidenceBundleRetentionCustodyScheduleVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_schedule_verification: PaperExecutionEvidenceBundleRetentionCustodyScheduleVerificationView | None = None
    evidence_bundle_retention_custody_notices: list[PaperExecutionEvidenceBundleRetentionCustodyNoticeView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_notice: PaperExecutionEvidenceBundleRetentionCustodyNoticeView | None = None
    evidence_bundle_retention_custody_notice_verifications: list[PaperExecutionEvidenceBundleRetentionCustodyNoticeVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_notice_verification: PaperExecutionEvidenceBundleRetentionCustodyNoticeVerificationView | None = None
    evidence_bundle_retention_custody_acknowledgments: list[PaperExecutionEvidenceBundleRetentionCustodyAcknowledgmentView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_acknowledgment: PaperExecutionEvidenceBundleRetentionCustodyAcknowledgmentView | None = None
    evidence_bundle_retention_custody_acknowledgment_verifications: list[PaperExecutionEvidenceBundleRetentionCustodyAcknowledgmentVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_acknowledgment_verification: PaperExecutionEvidenceBundleRetentionCustodyAcknowledgmentVerificationView | None = None
    evidence_bundle_retention_custody_completions: list[PaperExecutionEvidenceBundleRetentionCustodyCompletionView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_completion: PaperExecutionEvidenceBundleRetentionCustodyCompletionView | None = None
    evidence_bundle_retention_custody_completion_verifications: list[PaperExecutionEvidenceBundleRetentionCustodyCompletionVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_completion_verification: PaperExecutionEvidenceBundleRetentionCustodyCompletionVerificationView | None = None
    evidence_bundle_retention_custody_closeouts: list[PaperExecutionEvidenceBundleRetentionCustodyCloseoutView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_closeout: PaperExecutionEvidenceBundleRetentionCustodyCloseoutView | None = None
    evidence_bundle_retention_custody_closeout_verifications: list[PaperExecutionEvidenceBundleRetentionCustodyCloseoutVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_closeout_verification: PaperExecutionEvidenceBundleRetentionCustodyCloseoutVerificationView | None = None
    evidence_bundle_retention_custody_archives: list[PaperExecutionEvidenceBundleRetentionCustodyArchiveView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_archive: PaperExecutionEvidenceBundleRetentionCustodyArchiveView | None = None
    evidence_bundle_retention_custody_archive_verifications: list[PaperExecutionEvidenceBundleRetentionCustodyArchiveVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_archive_verification: PaperExecutionEvidenceBundleRetentionCustodyArchiveVerificationView | None = None
    evidence_bundle_retention_custody_retrievals: list[PaperExecutionEvidenceBundleRetentionCustodyRetrievalView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_retrieval: PaperExecutionEvidenceBundleRetentionCustodyRetrievalView | None = None
    evidence_bundle_retention_custody_retrieval_verifications: list[PaperExecutionEvidenceBundleRetentionCustodyRetrievalVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_retrieval_verification: PaperExecutionEvidenceBundleRetentionCustodyRetrievalVerificationView | None = None
    evidence_bundle_retention_custody_returns: list[PaperExecutionEvidenceBundleRetentionCustodyReturnView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_return: PaperExecutionEvidenceBundleRetentionCustodyReturnView | None = None
    evidence_bundle_retention_custody_return_verifications: list[PaperExecutionEvidenceBundleRetentionCustodyReturnVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_return_verification: PaperExecutionEvidenceBundleRetentionCustodyReturnVerificationView | None = None
    evidence_bundle_retention_custody_redeposits: list[PaperExecutionEvidenceBundleRetentionCustodyRedepositView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_redeposit: PaperExecutionEvidenceBundleRetentionCustodyRedepositView | None = None
    evidence_bundle_retention_custody_redeposit_verifications: list[PaperExecutionEvidenceBundleRetentionCustodyRedepositVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_redeposit_verification: PaperExecutionEvidenceBundleRetentionCustodyRedepositVerificationView | None = None
    evidence_bundle_retention_custody_inventories: list[PaperExecutionEvidenceBundleRetentionCustodyInventoryView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_inventory: PaperExecutionEvidenceBundleRetentionCustodyInventoryView | None = None
    evidence_bundle_retention_custody_inventory_verifications: list[PaperExecutionEvidenceBundleRetentionCustodyInventoryVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_inventory_verification: PaperExecutionEvidenceBundleRetentionCustodyInventoryVerificationView | None = None
    evidence_bundle_retention_custody_reconciliations: list[PaperExecutionEvidenceBundleRetentionCustodyReconciliationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_reconciliation: PaperExecutionEvidenceBundleRetentionCustodyReconciliationView | None = None
    evidence_bundle_retention_custody_reconciliation_verifications: list[PaperExecutionEvidenceBundleRetentionCustodyReconciliationVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_reconciliation_verification: PaperExecutionEvidenceBundleRetentionCustodyReconciliationVerificationView | None = None
    evidence_bundle_retention_custody_certifications: list[PaperExecutionEvidenceBundleRetentionCustodyCertificationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_certification: PaperExecutionEvidenceBundleRetentionCustodyCertificationView | None = None
    evidence_bundle_retention_custody_certification_verifications: list[PaperExecutionEvidenceBundleRetentionCustodyCertificationVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_certification_verification: PaperExecutionEvidenceBundleRetentionCustodyCertificationVerificationView | None = None
    evidence_bundle_retention_custody_attestations: list[PaperExecutionEvidenceBundleRetentionCustodyAttestationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_attestation: PaperExecutionEvidenceBundleRetentionCustodyAttestationView | None = None
    evidence_bundle_retention_custody_attestation_verifications: list[PaperExecutionEvidenceBundleRetentionCustodyAttestationVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_attestation_verification: PaperExecutionEvidenceBundleRetentionCustodyAttestationVerificationView | None = None
    recommended_actions: list[str] = Field(default_factory=list)
    disclaimer: str = "Paper execution cockpit is a read-plane preview. Browser/API routes do not submit orders. Use the paper-broker CLI on a trusted host for authenticated paper-only submissions."

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


__all__ = [
    "PaperExecutionAccountPositionSnapshotArtifact",
    "PaperExecutionCockpitPayload",
    "PaperExecutionDryRunArtifact",
    "PaperExecutionEvidenceBundleArtifact",
    "PaperExecutionEvidenceBundleAttestationArtifact",
    "PaperExecutionEvidenceBundleAttestationView",
    "PaperExecutionEvidenceBundleAttestationVerificationArtifact",
    "PaperExecutionEvidenceBundleAttestationVerificationView",
    "PaperExecutionEvidenceBundleClosureArtifact",
    "PaperExecutionEvidenceBundleClosureView",
    "PaperExecutionEvidenceBundleClosureVerificationArtifact",
    "PaperExecutionEvidenceBundleClosureVerificationView",
    "PaperExecutionEvidenceBundleExportEntry",
    "PaperExecutionEvidenceBundleExportManifestArtifact",
    "PaperExecutionEvidenceBundleExportManifestView",
    "PaperExecutionEvidenceBundleExportVerificationArtifact",
    "PaperExecutionEvidenceBundleExportVerificationEntry",
    "PaperExecutionEvidenceBundleExportVerificationView",
    "PaperExecutionEvidenceBundleRetentionReceiptArtifact",
    "PaperExecutionEvidenceBundleRetentionReceiptEntry",
    "PaperExecutionEvidenceBundleRetentionReceiptView",
    "PaperExecutionEvidenceBundleRetentionVerificationArtifact",
    "PaperExecutionEvidenceBundleRetentionVerificationEntry",
    "PaperExecutionEvidenceBundleRetentionVerificationView",
    "PaperExecutionEvidenceBundleRetentionSignoffArtifact",
    "PaperExecutionEvidenceBundleRetentionSignoffView",
    "PaperExecutionEvidenceBundleRetentionSignoffVerificationArtifact",
    "PaperExecutionEvidenceBundleRetentionSignoffVerificationView",
    "PaperExecutionEvidenceBundleRetentionHandoffVerificationView",
    "PaperExecutionEvidenceBundleRetentionHandoffVerificationArtifact",
    "PaperExecutionEvidenceBundleRetentionHandoffView",
    "PaperExecutionEvidenceBundleRetentionHandoffArtifact",
    "PaperExecutionEvidenceBundleRetentionHandoffAcceptanceArtifact",
    "PaperExecutionEvidenceBundleRetentionHandoffAcceptanceView",
    "PaperExecutionEvidenceBundleRetentionHandoffAcceptanceVerificationArtifact",
    "PaperExecutionEvidenceBundleRetentionHandoffAcceptanceVerificationView",
    "PaperExecutionEvidenceBundleRetentionCustodyRegisterArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyRegisterView",
    "PaperExecutionEvidenceBundleRetentionCustodyRegisterVerificationArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyRegisterVerificationView",
    "PaperExecutionEvidenceBundleRetentionCustodySealArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodySealView",
    "PaperExecutionEvidenceBundleRetentionCustodySealVerificationArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodySealVerificationView",
    "PaperExecutionEvidenceBundleRetentionCustodyContinuityVerificationView",
    "PaperExecutionEvidenceBundleRetentionCustodyContinuityVerificationArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyContinuityView",
    "PaperExecutionEvidenceBundleRetentionCustodyContinuityArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyReviewVerificationView",
    "PaperExecutionEvidenceBundleRetentionCustodyReviewVerificationArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyReviewView",
    "PaperExecutionEvidenceBundleRetentionCustodyReviewArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyAuditVerificationView",
    "PaperExecutionEvidenceBundleRetentionCustodyAuditVerificationArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyAuditView",
    "PaperExecutionEvidenceBundleRetentionCustodyAuditArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyAcknowledgmentArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyAcknowledgmentView",
    "PaperExecutionEvidenceBundleRetentionCustodyAcknowledgmentVerificationArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyAcknowledgmentVerificationView",
    "PaperExecutionEvidenceBundleRetentionCustodyCompletionVerificationView",
    "PaperExecutionEvidenceBundleRetentionCustodyCompletionVerificationArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyCompletionView",
    "PaperExecutionEvidenceBundleRetentionCustodyCompletionArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyCloseoutVerificationView",
    "PaperExecutionEvidenceBundleRetentionCustodyCloseoutVerificationArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyCloseoutView",
    "PaperExecutionEvidenceBundleRetentionCustodyCloseoutArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyArchiveArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyArchiveView",
    "PaperExecutionEvidenceBundleRetentionCustodyArchiveVerificationArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyArchiveVerificationView",
    "PaperExecutionEvidenceBundleRetentionCustodyRetrievalArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyRetrievalView",
    "PaperExecutionEvidenceBundleRetentionCustodyRetrievalVerificationArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyRetrievalVerificationView",
    "PaperExecutionEvidenceBundleRetentionCustodyReturnArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyReturnView",
    "PaperExecutionEvidenceBundleRetentionCustodyReturnVerificationArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyReturnVerificationView",
    "PaperExecutionEvidenceBundleRetentionCustodyRedepositArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyRedepositView",
    "PaperExecutionEvidenceBundleRetentionCustodyRedepositVerificationArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyRedepositVerificationView",
    "PaperExecutionEvidenceBundleRetentionCustodyInventoryVerificationView",
    "PaperExecutionEvidenceBundleRetentionCustodyInventoryVerificationArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyInventoryView",
    "PaperExecutionEvidenceBundleRetentionCustodyInventoryArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyReconciliationArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyReconciliationView",
    "PaperExecutionEvidenceBundleRetentionCustodyReconciliationVerificationArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyReconciliationVerificationView",
    "PaperExecutionEvidenceBundleRetentionCustodyCertificationArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyCertificationView",
    "PaperExecutionEvidenceBundleRetentionCustodyCertificationVerificationArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyCertificationVerificationView",
    "PaperExecutionEvidenceBundleSource",
    "PaperExecutionEvidenceBundleView",
    "PaperExecutionEvidenceBundleDriftArtifact",
    "PaperExecutionEvidenceBundleDriftView",
    "PaperExecutionEvidenceBundleRotationView",
    "PaperExecutionEvidenceBundleRotationArtifact",
    "PaperExecutionEvidenceBundleRotationExecutionArtifact",
    "PaperExecutionEvidenceBundleRotationExecutionStep",
    "PaperExecutionEvidenceBundleRotationExecutionView",
    "PaperExecutionEvidenceBundleVerificationArtifact",
    "PaperExecutionEvidenceBundleVerificationSource",
    "PaperExecutionEvidenceBundleVerificationView",
    "PaperExecutionFreshnessGate",
    "PaperExecutionIntentPreview",
    "PaperExecutionIntentSelectionArtifact",
    "PaperExecutionJournalEntry",
    "PaperExecutionOrderStatusArtifact",
    "PaperExecutionOrderStatusView",
    "PaperExecutionSubmissionArtifact",
    "PaperExecutionSubmissionGuardSnapshot",
    "PaperExecutionSubmissionReceiptView",
    "PaperExecutionPositionReconciliationView",
    "PaperExecutionSummary",
    "PaperExecutionTimelineEntry",
    "PaperExecutionTimelineSummary",
]
