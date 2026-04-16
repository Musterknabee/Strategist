from __future__ import annotations

from strategy_validator.application.research_ingress import normalize_proposal_for_adjudication
from strategy_validator.application.source_registry import SourceRegistry
from strategy_validator.contracts.feature_lineage import FeatureLineageRecord
from strategy_validator.contracts.proposal_manifest import ProposalManifest
from strategy_validator.contracts.source_registry import SourceRegistryRecord


def test_normalized_proposal_uses_registered_sources() -> None:
    registry = SourceRegistry()
    registry.register(
        SourceRegistryRecord(
            source_id='src-1',
            source_system='market_data',
            snapshot_reference='snap-2026-01-01',
            schema_id='bars/v1',
            trust_posture='trusted',
        )
    )
    payload = normalize_proposal_for_adjudication(
        ProposalManifest(
            proposal_id='proposal-1',
            thesis='mean reversion with governance overlay',
            target_universe='SP500',
            intended_horizon='swing',
            required_evidence_class='institutional',
            feature_dependencies=('feature-1',),
            source_registry_references=('src-1',),
            evaluation_plan={'benchmark': 'cpcv'},
        ),
        source_registry=registry,
        feature_lineage=(
            FeatureLineageRecord(feature_id='feature-1', upstream_source_ids=('src-1',), transform_version='v1'),
        ),
    )
    assert payload['normalized_request']['ingestion']['ready_for_adjudication'] is True
    assert payload['idempotency_key']
