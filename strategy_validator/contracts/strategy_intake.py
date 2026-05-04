from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from strategy_validator.contracts.proposal_manifest import ProposalManifest

STRATEGY_INTAKE_ARTIFACT_SCHEMA_VERSION = "strategy_intake_artifact/v1"
STRATEGY_INTAKE_RECEIPT_SCHEMA_VERSION = "strategy_intake_receipt/v1"
STRATEGY_INTAKE_INDEX_SCHEMA_VERSION = "strategy_intake_index/v1"


class StrategyIntakeRequest(BaseModel):
    """Operator-entered strategy idea before validator authority is involved."""

    strategy_name: str = Field(min_length=1, max_length=160)
    thesis: str = Field(min_length=1, max_length=6000)
    target_universe: str = Field(min_length=1, max_length=240)
    intended_horizon: str = Field(min_length=1, max_length=120)
    expected_edge: str = Field(min_length=1, max_length=2000)
    required_evidence_class: str = Field(default="institutional", min_length=1, max_length=120)
    data_dependencies: tuple[str, ...] = ()
    feature_dependencies: tuple[str, ...] = ()
    source_registry_references: tuple[str, ...] = ()
    falsification_rules: tuple[str, ...] = ()
    risk_assumptions: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    evaluation_plan: dict[str, Any] = Field(default_factory=dict)
    operator_id: str = Field(default="operator", min_length=1, max_length=128)
    idempotency_key: str | None = Field(default=None, max_length=240)

    model_config = {"extra": "forbid"}


class StrategyIntakeArtifact(BaseModel):
    schema_version: Literal["strategy_intake_artifact/v1"] = STRATEGY_INTAKE_ARTIFACT_SCHEMA_VERSION
    intake_id: str = Field(min_length=1)
    proposal_id: str = Field(min_length=1)
    strategy_name: str = Field(min_length=1)
    created_at_utc: datetime
    operator_id: str = Field(min_length=1)
    proposal_manifest: ProposalManifest
    expected_edge: str = Field(min_length=1)
    data_dependencies: tuple[str, ...] = ()
    falsification_rules: tuple[str, ...] = ()
    risk_assumptions: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    authority_boundary: str = "ADVISORY_ARTIFACT_ONLY"
    readiness_state: str = "RESEARCH_INTAKE_RECORDED"
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    intake_sha256: str = ""

    model_config = {"extra": "forbid"}


class StrategyIntakeIndexEntry(BaseModel):
    intake_id: str
    proposal_id: str
    strategy_name: str
    created_at_utc: datetime
    operator_id: str
    target_universe: str
    intended_horizon: str
    readiness_state: str
    artifact_path: str
    artifact_sha256: str
    tags: tuple[str, ...] = ()

    model_config = {"extra": "forbid"}


class StrategyIntakeIndex(BaseModel):
    schema_version: Literal["strategy_intake_index/v1"] = STRATEGY_INTAKE_INDEX_SCHEMA_VERSION
    generated_at_utc: datetime
    read_plane_only: bool = True
    no_live_trading: bool = True
    authority_boundary: str = "ADVISORY_ARTIFACT_ONLY"
    intake_count: int
    entries: tuple[StrategyIntakeIndexEntry, ...] = ()

    model_config = {"extra": "forbid"}


class StrategyIntakeReceipt(BaseModel):
    schema_version: Literal["strategy_intake_receipt/v1"] = STRATEGY_INTAKE_RECEIPT_SCHEMA_VERSION
    generated_at_utc: datetime
    accepted: bool
    intake_id: str
    proposal_id: str
    artifact_path: str
    artifact_sha256: str
    index_path: str
    read_plane_route: str = "/ui/strategy-intake/latest"
    authority_boundary: str = "ADVISORY_ARTIFACT_ONLY"
    promotion_authority: str = "NONE"
    execution_authority: str = "NONE"
    requires_projection_refresh: bool = True
    idempotency_status: str = "RECORDED"
    duplicate_of_intake_id: str | None = None
    summary_line: str
    authorization: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}


__all__ = [
    "StrategyIntakeArtifact",
    "StrategyIntakeIndex",
    "StrategyIntakeIndexEntry",
    "StrategyIntakeReceipt",
    "StrategyIntakeRequest",
]
