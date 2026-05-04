from __future__ import annotations

from datetime import datetime, timezone

from strategy_validator.contracts.evidence import EvidenceBundle, ReproducibilityManifest
from strategy_validator.contracts.experiments import ExperimentManifest

_ZERO_SHA256 = "0" * 64


def build_strategy_proposal(
    *,
    experiment_id: str,
    strategy_name: str,
    version: str = "1.0.0",
    proposer_id: str = "AGENT_001",
    benchmark_rung: str = "core-equity",
    search_breadth: int = 1,
    evaluation_time_utc: datetime | None = None,
    market_data_subject_id: str | None = None,
    code_hash: str = _ZERO_SHA256,
    data_snapshot_hash: str = _ZERO_SHA256,
    universe_hash: str = _ZERO_SHA256,
    feature_graph_hash: str = _ZERO_SHA256,
    parameter_manifest_hash: str = _ZERO_SHA256,
    benchmark_version: str = "v1",
    cost_model_version: str = "v1",
    calendar_version: str = "v1",
) -> ExperimentManifest:
    """Build a deterministic experiment proposal manifest.

    The previous public helper returned a single hard-coded sample. This
    builder keeps a tiny bounded API while making the proposer usable by
    integration fixtures and future governed intake commands.
    """
    evaluation_time = evaluation_time_utc or datetime.now(timezone.utc)
    return ExperimentManifest(
        experiment_id=experiment_id,
        strategy_name=strategy_name,
        version=version,
        proposer_id=proposer_id,
        evidence_bundle=EvidenceBundle(
            reproducibility=ReproducibilityManifest(
                code_hash=code_hash,
                data_snapshot_hash=data_snapshot_hash,
                universe_hash=universe_hash,
                feature_graph_hash=feature_graph_hash,
                parameter_manifest_hash=parameter_manifest_hash,
                benchmark_version=benchmark_version,
                cost_model_version=cost_model_version,
                calendar_version=calendar_version,
            ),
            benchmark_rung=benchmark_rung,
            search_breadth=search_breadth,
            evaluation_time_utc=evaluation_time,
            market_data_subject_id=market_data_subject_id,
        ),
    )


def propose_new_strategy() -> ExperimentManifest:
    """Backward-compatible sample proposal used by early examples/tests."""
    return build_strategy_proposal(
        experiment_id="EXP-001",
        strategy_name="TrendFollowing_Alpha",
        version="1.0.0",
        proposer_id="AGENT_001",
        benchmark_rung="core-equity",
        search_breadth=1,
    )
