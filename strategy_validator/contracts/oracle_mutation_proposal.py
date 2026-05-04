"""Read-only Oracle mutation proposals (research / paper; no ledger authority)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


class OracleMutationProposalItem(BaseModel):
    proposal_id: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    suggested_param_delta: dict[str, Any] = Field(default_factory=dict)
    rationale: str = Field(default="", description="Evidence-only rationale; not an execution instruction.")

    model_config = {"extra": "forbid"}


class OracleMutationProposalArtifact(BaseModel):
    schema_version: Literal["oracle_mutation_proposal/v1"] = "oracle_mutation_proposal/v1"
    batch_run_id: str = Field(min_length=1)
    thesis_id: str = Field(min_length=1)
    generated_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    proposals: list[OracleMutationProposalItem] = Field(default_factory=list)
    digest_sha256: str = Field(default="", min_length=0)

    model_config = {"extra": "forbid"}
