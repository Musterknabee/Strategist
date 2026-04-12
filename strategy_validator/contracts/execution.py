from __future__ import annotations

from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, Field

from strategy_validator.contracts.calibration import CalibrationMetadata
from strategy_validator.contracts.vendor_runtime import VendorFailureEvent

ImpactModelMode = Literal["FIXED_BPS", "NONLINEAR_HEURISTIC", "EMPIRICAL_CALIBRATED", "PROVISIONAL"]


class CapacityEvidence(BaseModel):
    """
    Typed capacity / liquidity evidence.
    Structural: participation_rate, trade_notional, nonlinear_impact_bps.
    Provisional: ADV is a proxy unless a live ADV feed is wired.
    """
    estimated_trade_notional: float = Field(default=0.0, ge=0.0)
    estimated_participation_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    adv_notional_proxy: float = Field(default=0.0, ge=0.0)
    """ADV proxy in notional units. Provisional unless live feed is integrated."""
    nonlinear_impact_bps: float = Field(default=0.0, ge=0.0)
    capacity_limit_passed: bool = True
    degradation_reason: Optional[str] = None

    model_config = {"extra": "forbid"}


class BorrowEvidence(BaseModel):
    """
    Typed borrow / shortability evidence.
    Structural: requires_shorting, borrow_available, borrow_cost_bps.
    Provisional: borrow_available is a flag unless a live borrow/locate feed is wired.
    """
    requires_shorting: bool = False
    borrow_available: bool = True
    borrow_cost_bps: float = Field(default=0.0, ge=0.0)
    locate_required: bool = False
    shortability_passed: bool = True
    degradation_reason: Optional[str] = None

    model_config = {"extra": "forbid"}


class ExecutionStressResult(BaseModel):
    """
    Forensic record of adverse execution scenarios.
    Ensures liquidity and inventory resilience.
    """
    baseline_impact_bps: float
    stressed_impact_bps: float
    baseline_borrow_cost_bps: float
    stressed_borrow_cost_bps: float
    borrow_recall_risk_flag: bool = False
    
    liquidity_stress_mode: str = "2X_IMPACT_HEURISTIC"
    borrow_stress_mode: str = "3X_COST_REGIME"
    
    passed: bool = True
    failure_reason: Optional[str] = None
    
    model_config = {"extra": "forbid"}


class MarketDataProvenance(BaseModel):
    """
    Point-in-time market-data provenance sealed to an adjudication decision.

    Records the exact lookup parameters and snapshot fingerprints used
    during execution realism evaluation.  Ensures no promotion-grade
    decision is time-ambiguous or identity-ambiguous at the market-data
    layer.
    """
    evaluation_time_utc: Optional[datetime] = None
    """The lawful PIT timestamp used for all snapshot lookups."""
    market_data_subject_id: Optional[str] = None
    """The typed subject identity (asset/instrument) used for lookups."""
    liquidity_snapshot_hash: Optional[str] = None
    """Fingerprint of the effective liquidity snapshot selected (if any)."""
    borrow_snapshot_hash: Optional[str] = None
    """Fingerprint of the effective borrow snapshot selected (if any)."""
    liquidity_source_mode: Optional[str] = None
    """Effective source mode of the liquidity snapshot: LIVE | SNAPSHOT | PROVISIONAL | NONE."""
    borrow_source_mode: Optional[str] = None
    """Effective source mode of the borrow snapshot: LIVE | SNAPSHOT | PROVISIONAL | NONE."""
    liquidity_source_id: Optional[str] = None
    """Effective source identifier for liquidity (provider or archive id)."""
    borrow_source_id: Optional[str] = None
    """Effective source identifier for borrow (provider or archive id)."""

    # Resilience and Freshness Provenance
    liquidity_freshness_status: Optional[str] = None
    """FRESH | STALE | MISSING | ERROR | UNKNOWN"""
    liquidity_market_hours_law: Optional[str] = None
    """When set, LIVE liquidity age law session label (e.g. US_RTH_CLOSED / US_RTH_OPEN / DISABLED)."""
    borrow_freshness_status: Optional[str] = None
    """FRESH | STALE | MISSING | ERROR | UNKNOWN"""
    borrow_market_hours_law: Optional[str] = None
    """When set, LIVE borrow age law session label."""
    liquidity_provider_status: Optional[str] = None
    """SUCCESS | ERROR | TIMEOUT | STALE | MISSING | NOT_CONFIGURED | CIRCUIT_OPEN for the liquidity primary lookup."""
    borrow_provider_status: Optional[str] = None
    """SUCCESS | ERROR | TIMEOUT | STALE | MISSING | NOT_CONFIGURED | CIRCUIT_OPEN for the borrow primary lookup."""
    liquidity_retry_count: int = 0
    borrow_retry_count: int = 0
    liquidity_circuit_state: Optional[str] = None
    borrow_circuit_state: Optional[str] = None
    fallback_applied: bool = False
    """True if the primary feed failed/deteriorated and a fallback source was used."""
    fallback_reason: Optional[str] = None
    provider_errors: list[str] = Field(default_factory=list)
    vendor_failure_events: list[VendorFailureEvent] = Field(default_factory=list)
    """Typed vendor/transport failures (parallel to provider_errors strings)."""

    model_config = {"extra": "forbid"}


class ExecutionRealismResult(BaseModel):
    """
    Forensic record of the strategy's viability in live market conditions.
    Protects against alpha theater, midpoint optimism, capacity theater, and borrow fiction.
    """
    # Microstructure Friction
    spread_bps: float = Field(default=0.0)
    slippage_bps: float = Field(default=0.0)
    fees_bps: float = Field(default=0.0)
    latency_minutes: float = Field(default=0.0)
    half_life_minutes: Optional[float] = None

    # Capacity Modeling (typed sub-object)
    capacity: CapacityEvidence = Field(default_factory=CapacityEvidence)
    """Primary typed capacity evidence. Legacy flat fields preserved for backward compatibility."""
    estimated_trade_notional: float = Field(default=0.0)
    estimated_participation_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    nonlinear_impact_bps: float = Field(default=0.0)
    total_post_cost_bps: float = Field(default=0.0)
    impact_model_mode: ImpactModelMode = "PROVISIONAL"
    impact_calibration_metadata: Optional[CalibrationMetadata] = None
    """Sealed only when impact_model_mode == EMPIRICAL_CALIBRATED and artifact validated."""

    # Borrow / Shortability (typed sub-object)
    borrow: BorrowEvidence = Field(default_factory=BorrowEvidence)
    """Primary typed borrow evidence. Legacy flat fields preserved for backward compatibility."""
    requires_shorting: bool = False
    borrow_available: bool = True
    borrow_cost_bps: float = Field(default=0.0)
    locate_required: bool = False
    shortability_passed: bool = True

    # Stress Scenarios
    stress_report: Optional[ExecutionStressResult] = None

    midpoint_only_flag: bool = False
    passed: bool = False
    failure_reason: Optional[str] = None
    capacity_note: Optional[str] = None
    borrow_constraint_note: Optional[str] = None

    # Market-Data Provenance Seal
    market_data_provenance: MarketDataProvenance = Field(default_factory=MarketDataProvenance)
    """Point-in-time market-data provenance: lookup timestamp, subject, snapshot hashes."""

    model_config = {"extra": "forbid"}
