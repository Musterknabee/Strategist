from __future__ import annotations

from datetime import datetime

import pandas as pd

from strategy_validator.contracts.experiments import ExperimentManifest
from strategy_validator.contracts.semantic import (
    FeatureFactoryArtifact,
    SemanticResearchFeatureMaterialization,
)
from strategy_validator.data_spine.joins.as_of import AsOfJoinEngine
from strategy_validator.feature_factory.semantic.adapter import adapt_tribunal_to_feature_row


def materialize_semantic_feature_for_proposal(
    proposal: ExperimentManifest,
    artifact: FeatureFactoryArtifact,
    *,
    asset_id: str | None = None,
    published_at: str | datetime,
    available_at: str | datetime,
    dataset_id: str = "semantic_tribunal_features/v1",
) -> SemanticResearchFeatureMaterialization:
    """Materialize a tribunal artifact through the PIT join engine for one proposal.

    This intentionally small seam proves the research intake path can move from
    proposal metadata to typed semantic features while preserving point-in-time
    legality provenance. It does not adjudicate or write the ledger.
    """
    evaluation_time = proposal.evidence_bundle.evaluation_time_utc
    if evaluation_time is None:
        raise ValueError("proposal evidence_bundle.evaluation_time_utc is required for PIT materialization")

    resolved_asset_id = asset_id or proposal.evidence_bundle.market_data_subject_id
    if not resolved_asset_id:
        raise ValueError("asset_id or proposal evidence_bundle.market_data_subject_id is required")

    feature_row = adapt_tribunal_to_feature_row(
        artifact,
        asset_id=resolved_asset_id,
        published_at=published_at,
        available_at=available_at,
    )

    target_df = pd.DataFrame(
        [{"experiment_id": proposal.experiment_id, "asset_id": resolved_asset_id, "decision_time_utc": evaluation_time}]
    )
    feature_df = pd.DataFrame(
        [
            {
                "asset_id": resolved_asset_id,
                "available_at_utc": feature_row.available_at,
                "event_id": feature_row.event_id,
                "novelty_score": feature_row.novelty_score,
                "polarity_score": feature_row.polarity_score,
                "belief_conflict_score": feature_row.belief_conflict_score,
                "abstain_flag": feature_row.abstain_flag,
                "missingness_reason": feature_row.missingness_reason,
            }
        ]
    )
    target_df["decision_time_utc"] = pd.to_datetime(target_df["decision_time_utc"], utc=True)
    feature_df["available_at_utc"] = pd.to_datetime(feature_df["available_at_utc"], utc=True)

    joined, provenance = AsOfJoinEngine(
        decision_time_col="decision_time_utc",
        available_at_col="available_at_utc",
        group_keys=["asset_id"],
    ).execute(target_df, feature_df, dataset_id=dataset_id)

    return SemanticResearchFeatureMaterialization(
        experiment_id=proposal.experiment_id,
        asset_id=resolved_asset_id,
        feature_event_id=feature_row.event_id,
        joined_row_count=len(joined),
        feature_row=feature_row,
        pit_provenance=provenance,
    )


__all__ = ["materialize_semantic_feature_for_proposal"]
