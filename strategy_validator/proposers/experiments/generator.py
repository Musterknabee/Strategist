from strategy_validator.contracts.evidence import EvidenceBundle, ReproducibilityManifest
from strategy_validator.contracts.experiments import ExperimentManifest


def propose_new_strategy() -> ExperimentManifest:
    return ExperimentManifest(
        experiment_id="EXP-001",
        strategy_name="TrendFollowing_Alpha",
        version="1.0.0",
        proposer_id="AGENT_001",
        evidence_bundle=EvidenceBundle(
            reproducibility=ReproducibilityManifest(
                code_hash="0" * 64,
                data_snapshot_hash="0" * 64,
                universe_hash="0" * 64,
                feature_graph_hash="0" * 64,
                parameter_manifest_hash="0" * 64,
                benchmark_version="v1",
                cost_model_version="v1",
                calendar_version="v1",
            ),
            benchmark_rung="core-equity",
            search_breadth=1,
        ),
    )
