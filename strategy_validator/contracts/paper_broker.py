"""Paper-only broker integration contracts (evidence only; no live trading)."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class PaperBrokerPolicyStatus(str, Enum):
    DISABLED = "DISABLED"
    PENDING_KEY = "PENDING_KEY"
    PAPER_READY = "PAPER_READY"
    BLOCKED_BY_POLICY = "BLOCKED_BY_POLICY"
    DEGRADED = "DEGRADED"


class PaperBrokerAccountStatus(BaseModel):
    schema_version: Literal["paper_broker_account_status/v1"] = "paper_broker_account_status/v1"
    broker_id: str = "alpaca_paper"
    policy_status: PaperBrokerPolicyStatus
    trading_blocked_reason: str | None = None
    account_id: str | None = None
    equity: float | None = None
    buying_power: float | None = None
    currency: str | None = None
    paper_endpoint_verified: bool = False
    warnings: list[str] = Field(default_factory=list)
    retrieved_at_utc: datetime | None = None

    model_config = {"extra": "forbid"}


class PaperBrokerOrderIntent(BaseModel):
    schema_version: Literal["paper_broker_order_intent/v1"] = "paper_broker_order_intent/v1"
    tracking_id: str
    symbol: str = Field(min_length=1)
    side: Literal["buy", "sell"]
    qty: float = Field(gt=0)
    order_type: Literal["market", "limit"] = "market"
    time_in_force: str = "day"
    limit_price: float | None = None
    note: str = ""

    model_config = {"extra": "forbid"}


class PaperBrokerOrderResult(BaseModel):
    schema_version: Literal["paper_broker_order_result/v1"] = "paper_broker_order_result/v1"
    ok: bool
    policy_status: PaperBrokerPolicyStatus
    dry_run: bool = False
    client_order_id: str | None = None
    broker_order_id: str | None = None
    status: str | None = None
    filled_qty: float | None = None
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    evidence_redacted: dict[str, Any] = Field(default_factory=dict)
    retrieved_at_utc: datetime | None = None

    model_config = {"extra": "forbid"}

    @field_validator("retrieved_at_utc")
    @classmethod
    def _tz(cls, v: datetime | None) -> datetime | None:
        if v is not None and v.tzinfo is None:
            raise ValueError("retrieved_at_utc must be timezone-aware when set")
        return v


class PaperBrokerStatusArtifact(BaseModel):
    """Durable paper broker policy / account hints (no secrets; digest-linked)."""

    schema_version: Literal["paper_broker_status_manifest/v1"] = "paper_broker_status_manifest/v1"
    generated_at_utc: datetime
    broker_id: str = "alpaca_paper"
    mode: str | None = None
    endpoint_classification: Literal["PAPER_HOST", "LIVE_HOST_BLOCKED", "UNKNOWN", "UNSET"] = "UNKNOWN"
    key_configured: bool = False
    policy_status: str
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    account_summary: dict[str, Any] | None = None
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    manifest_sha256: str = ""

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperBrokerPositionSnapshot(BaseModel):
    schema_version: Literal["paper_broker_position_snapshot/v1"] = "paper_broker_position_snapshot/v1"
    symbol: str
    qty: float
    market_value: float | None = None
    avg_entry_price: float | None = None

    model_config = {"extra": "forbid"}


__all__ = [
    "PaperBrokerStatusArtifact",
    "PaperBrokerAccountStatus",
    "PaperBrokerOrderIntent",
    "PaperBrokerOrderResult",
    "PaperBrokerPolicyStatus",
    "PaperBrokerPositionSnapshot",
]
