from __future__ import annotations

from strategy_validator.application.source_registry import SourceRegistry
from strategy_validator.contracts.feature_lineage import FeatureLineageRecord
from strategy_validator.contracts.proposal_manifest import ProposalManifest


def ingest_proposal(
    manifest: ProposalManifest,
    *,
    source_registry: SourceRegistry,
    feature_lineage: tuple[FeatureLineageRecord, ...] = (),
) -> dict[str, object]:
    missing_sources = [source_id for source_id in manifest.source_registry_references if source_registry.get(source_id) is None]
    known_features = {item.feature_id for item in feature_lineage}
    unresolved_features = [feature_id for feature_id in manifest.feature_dependencies if feature_id not in known_features]
    return {
        'proposal_id': manifest.proposal_id,
        'source_reference_count': len(manifest.source_registry_references),
        'feature_dependency_count': len(manifest.feature_dependencies),
        'missing_sources': missing_sources,
        'unresolved_features': unresolved_features,
        'ready_for_adjudication': not missing_sources,
    }
