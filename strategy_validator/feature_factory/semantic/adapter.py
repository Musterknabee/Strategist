from __future__ import annotations

from typing import Any
import numpy as np
from strategy_validator.contracts.semantic import FeatureFactoryArtifact

def adapt_tribunal_to_feature_row(
    artifact: FeatureFactoryArtifact, 
    asset_id: str, 
    published_at: str | Any, 
    available_at: str | Any
) -> dict[str, Any]:
    """
    Translates a Tribunal adjudicated artifact into a Point-In-Time numerical row.
    If the tribunal abstained, scores are explicitly set to NaN.
    """
    if artifact.abstain_flag:
        novelty = np.nan
        polarity = np.nan
        belief_conflict = np.nan
    else:
        novelty = artifact.novelty_score
        polarity = artifact.polarity_score
        belief_conflict = artifact.belief_conflict

    return {
        "event_id": artifact.event_id,
        "asset_id": asset_id,
        "published_at": published_at,
        "available_at": available_at,
        "novelty_score": novelty,
        "polarity_score": polarity,
        "belief_conflict_score": belief_conflict,
    }
