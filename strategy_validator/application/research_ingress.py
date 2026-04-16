from __future__ import annotations

from strategy_validator.application.idempotency import derive_idempotency_key
from strategy_validator.application.proposal_ingest import ingest_proposal
from strategy_validator.application.source_registry import SourceRegistry
from strategy_validator.contracts.feature_lineage import FeatureLineageRecord
from strategy_validator.contracts.proposal_manifest import ProposalManifest


def normalize_proposal_for_adjudication(
    manifest: ProposalManifest,
    *,
    source_registry: SourceRegistry,
    feature_lineage: tuple[FeatureLineageRecord, ...] = (),
) -> dict[str, object]:
    ingestion = ingest_proposal(manifest, source_registry=source_registry, feature_lineage=feature_lineage)
    payload = {
        'proposal_id': manifest.proposal_id,
        'thesis': manifest.thesis,
        'target_universe': manifest.target_universe,
        'intended_horizon': manifest.intended_horizon,
        'required_evidence_class': manifest.required_evidence_class,
        'evaluation_plan': manifest.evaluation_plan,
        'ingestion': ingestion,
    }
    return {
        'idempotency_key': derive_idempotency_key(command_name='normalize_proposal_for_adjudication', payload=payload),
        'normalized_request': payload,
    }
