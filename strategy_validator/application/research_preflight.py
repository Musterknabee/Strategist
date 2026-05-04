from __future__ import annotations

from datetime import datetime

from strategy_validator.application.research_evidence_bridge import (
    attach_semantic_materialization_evidence,
    build_semantic_materialization_evidence,
    verify_semantic_materialization_evidence,
)
from strategy_validator.application.research_feature_materialization import materialize_semantic_feature_for_proposal
from strategy_validator.contracts.experiments import ExperimentManifest
from strategy_validator.contracts.semantic import FeatureFactoryArtifact, SemanticResearchPreflightReport


def run_semantic_research_preflight(
    proposal: ExperimentManifest,
    artifact: FeatureFactoryArtifact,
    *,
    published_at: str | datetime,
    available_at: str | datetime,
    asset_id: str | None = None,
    dataset_id: str = "semantic_tribunal_features/v1",
    attach_to_proposal: bool = True,
) -> SemanticResearchPreflightReport:
    """Run one semantic research intake preflight without adjudicating or writing the ledger."""
    materialization = materialize_semantic_feature_for_proposal(
        proposal,
        artifact,
        asset_id=asset_id,
        published_at=published_at,
        available_at=available_at,
        dataset_id=dataset_id,
    )
    if attach_to_proposal:
        evidence = attach_semantic_materialization_evidence(proposal, materialization)
    else:
        evidence = build_semantic_materialization_evidence(materialization)

    verification = verify_semantic_materialization_evidence(
        evidence,
        materialization=materialization,
        proposal=proposal,
    )
    data_spine_fingerprint = None
    if proposal.evidence_bundle.data_spine_seal is not None:
        data_spine_fingerprint = proposal.evidence_bundle.data_spine_seal.fingerprint

    issue_codes = [issue.code for issue in verification.issues]
    return SemanticResearchPreflightReport(
        experiment_id=proposal.experiment_id,
        strategy_name=proposal.strategy_name,
        asset_id=materialization.asset_id,
        feature_event_id=materialization.feature_event_id,
        evidence_id=evidence.evidence_id,
        evidence_checksum=evidence.checksum,
        evidence_verified=verification.verified,
        issue_count=verification.issue_count,
        issue_codes=issue_codes,
        joined_row_count=materialization.joined_row_count,
        pit_dataset_id=materialization.pit_provenance.dataset_id,
        pit_row_count_after=materialization.pit_provenance.row_count_after,
        data_spine_fingerprint=data_spine_fingerprint,
        attached_evidence_count=len(proposal.evidence_bundle.evidence_items),
        recommended_action=(
            "ATTACH_TO_ADJUDICATION_EVIDENCE" if verification.verified else "BLOCK_RESEARCH_INTAKE"
        ),
    )


__all__ = ["run_semantic_research_preflight"]
