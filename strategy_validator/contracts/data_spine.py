from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional, List, Dict

from pydantic import BaseModel, Field

PathGenerationMode = Literal["combinatorial_cpcv", "sequential_purged_embargo", "walk_forward"]


class RevisionLineageProvenance(BaseModel):
    dataset_id: str
    selected_revision_id: str
    selected_available_at_utc: datetime
    discarded_revision_ids: List[str] = Field(default_factory=list)
    revision_policy: str
    selection_reason: str
    
    model_config = {"extra": "forbid"}


class PITJoinProvenance(BaseModel):
    dataset_id: str
    decision_time_utc: datetime
    available_at_cutoff_utc: datetime
    revision_policy: str
    latency_buffer_ms: int
    macro_embargo_ms: int
    row_count_before: int
    row_count_after: int
    lineage: Optional[RevisionLineageProvenance] = None
    
    model_config = {"extra": "forbid"}


class AssetMembership(BaseModel):
    asset_id: str
    is_member: bool
    valid_from_utc: Optional[datetime] = None
    valid_to_utc: Optional[datetime] = None
    inclusion_reason: Optional[str] = None
    
    model_config = {"extra": "forbid"}


class UniverseProvenance(BaseModel):
    universe_id: str
    universe_snapshot_hash: str
    decision_time_utc: datetime
    member_count: int
    memberships: List[AssetMembership] = Field(default_factory=list)
    
    model_config = {"extra": "forbid"}


class RobustnessPathProvenance(BaseModel):
    path_generation_mode: PathGenerationMode
    n_folds: int
    test_folds_per_path: int
    purge_units: int
    embargo_units: int
    total_paths_generated: int
    deterministic_seed: Optional[int] = None
    
    model_config = {"extra": "forbid"}


class DataSpineAuditSeal(BaseModel):
    spine_version: str = "v1.1" # Incremented for universe/lineage support
    as_of_provenance: List[PITJoinProvenance] = Field(default_factory=list)
    path_provenance: Optional[RobustnessPathProvenance] = None
    universe_provenance: Optional[UniverseProvenance] = None
    fingerprint: str # Deterministic hash of all provenance layers
    
    model_config = {"extra": "forbid"}
