from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class TribunalOpinion(BaseModel):
    """Compatibility-preserving tribunal opinion contract used by experiment manifests."""

    tribunal_id: str = Field(min_length=1)
    stance: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    rationale: str | None = None
    recorded_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, object] = Field(default_factory=dict)

    model_config = {'extra': 'forbid'}


class TribunalChallengePacket(BaseModel):
    proposal_id: str = Field(min_length=1)
    challenge_type: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    supporting_evidence_refs: tuple[str, ...] = ()

    model_config = {'extra': 'forbid'}
