from __future__ import annotations

from pydantic import BaseModel, Field


class ProposalManifest(BaseModel):
    proposal_id: str = Field(min_length=1)
    thesis: str = Field(min_length=1)
    target_universe: str = Field(min_length=1)
    intended_horizon: str = Field(min_length=1)
    required_evidence_class: str = Field(min_length=1)
    feature_dependencies: tuple[str, ...] = ()
    source_registry_references: tuple[str, ...] = ()
    evaluation_plan: dict[str, object] = Field(default_factory=dict)

    model_config = {'extra': 'forbid'}
