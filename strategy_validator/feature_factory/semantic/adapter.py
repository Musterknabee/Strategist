from __future__ import annotations

from typing import Any
import math
from strategy_validator.contracts.semantic import FeatureFactoryArtifact, SemanticFeatureRow


def adapt_tribunal_to_feature_row(
    artifact: FeatureFactoryArtifact,
    asset_id: str,
    published_at: str | Any,
    available_at: str | Any,
) -> SemanticFeatureRow:
    """
    Translate a tribunal artifact into a typed point-in-time feature row.

    If the tribunal abstained, score fields are explicit NaN values rather
    than silently neutral values. That preserves lineage while keeping
    downstream PIT joins from mistaking abstention for signal.
    """
    missingness_reason: str | None = None
    if artifact.abstain_flag:
        novelty = math.nan
        polarity = math.nan
        belief_conflict = math.nan
        missingness_reason = "TRIBUNAL_ABSTAINED"
    else:
        novelty = artifact.novelty_score
        polarity = artifact.polarity_score
        belief_conflict = artifact.belief_conflict

    return SemanticFeatureRow(
        event_id=artifact.event_id,
        asset_id=asset_id,
        published_at=published_at,
        available_at=available_at,
        novelty_score=float(novelty),
        polarity_score=float(polarity),
        belief_conflict_score=float(belief_conflict),
        abstain_flag=artifact.abstain_flag,
        missingness_reason=missingness_reason,
    )
