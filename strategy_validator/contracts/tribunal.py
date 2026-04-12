from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from pydantic import BaseModel, Field


class TribunalOpinion(BaseModel):
    opinion_id: str
    experiment_id: str
    reviewer_id: str
    approved: bool
    comments: str
    semantic_features_proposed: List[str]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"extra": "forbid"}


class TribunalRegistry(BaseModel):
    opinions: List[TribunalOpinion]

    model_config = {"extra": "forbid"}
