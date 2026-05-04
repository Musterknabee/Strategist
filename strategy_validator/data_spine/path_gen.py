from __future__ import annotations

import hashlib
import json
from typing import List, Tuple, Any, Optional
import numpy as np
import pandas as pd

from strategy_validator.contracts.data_spine import (
    RobustnessPathProvenance,
    DataSpineAuditSeal,
    PITJoinProvenance,
    UniverseProvenance,
)
from strategy_validator.core.paths import generate_cpcv_paths

class LawfulPathGenerator:
    """
    Lawful orchestration of robustness paths from PIT-sanitized data.
    Ensures that every test fold combination is non-leaking and reproducible.
    """
    
    def __init__(
        self,
        n_folds: int = 5,
        test_folds_per_path: int = 2,
        purge_observations: int = 2,
        embargo_observations: int = 5
    ):
        self.n_folds = n_folds
        self.test_folds_per_path = test_folds_per_path
        self.purge_observations = purge_observations
        self.embargo_observations = embargo_observations

    def construct_cpcv_suite(
        self, 
        returns_df: pd.DataFrame,
        pit_provenance: List[PITJoinProvenance],
        universe_provenance: Optional[UniverseProvenance] = None
    ) -> Tuple[List[Tuple[List[int], List[int]]], DataSpineAuditSeal]:
        """
        Build a full suite of combinatorial paths with typed provenance.
        Now includes universe membership tracking.
        """
        n_obs = len(returns_df)
        
        # 1. Generate core combinatorial paths
        paths = generate_cpcv_paths(
            n_observations=n_obs,
            n_folds=self.n_folds,
            test_folds_per_path=self.test_folds_per_path,
            purge_observations=self.purge_observations,
            embargo_observations=self.embargo_observations
        )
        
        path_prov = RobustnessPathProvenance(
            path_generation_mode="combinatorial_cpcv",
            n_folds=self.n_folds,
            test_folds_per_path=self.test_folds_per_path,
            purge_units=self.purge_observations,
            embargo_units=self.embargo_observations,
            total_paths_generated=len(paths)
        )
        
        # 2. Compute Seal (Deterministic fingerprint)
        fingerprint_input = {
            "datasets": [p.dataset_id for p in pit_provenance],
            "cutoff": str(max(p.available_at_cutoff_utc for p in pit_provenance)) if pit_provenance else "none",
            "path_config": path_prov.model_dump(mode="json"),
            "obs_count": n_obs,
            "universe_hash": universe_provenance.universe_snapshot_hash if universe_provenance else "none",
            "universe_members": [m.asset_id for m in universe_provenance.memberships if m.is_member] if universe_provenance else []
        }
        # Sort members to ensure deterministic hash
        if "universe_members" in fingerprint_input:
            fingerprint_input["universe_members"].sort()

        fingerprint = hashlib.sha256(json.dumps(fingerprint_input, sort_keys=True).encode()).hexdigest()
        
        seal = DataSpineAuditSeal(
            spine_version="v1.1",
            as_of_provenance=pit_provenance,
            path_provenance=path_prov,
            universe_provenance=universe_provenance,
            fingerprint=fingerprint
        )
        
        return paths, seal
