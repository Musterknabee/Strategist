from datetime import datetime, timezone

import pytest

from strategy_validator.contracts.evidence import Evidence, EvidenceBundle, ReproducibilityManifest
from strategy_validator.contracts.experiments import ExperimentManifest
from strategy_validator.core.enums import EvidenceType, PromotionState
from strategy_validator.core.exceptions import LedgerAuthorizationError
from strategy_validator.ledger.writer import issue_write_authority
from strategy_validator.validator.orchestrator import adjudicate


def _bundle() -> EvidenceBundle:
    return EvidenceBundle(
        reproducibility=ReproducibilityManifest(
            code_hash="a" * 64,
            data_snapshot_hash="b" * 64,
            universe_hash="c" * 64,
            feature_graph_hash="d" * 64,
            parameter_manifest_hash="e" * 64,
            benchmark_version="bench-v1",
            cost_model_version="cost-v1",
            calendar_version="cal-v1",
        ),
        benchmark_rung="L1",
        search_breadth=4,
    )


def _ev(experiment_id: str, **payload) -> Evidence:
    return Evidence(
        evidence_id=f"m-{experiment_id}-{len(payload)}",
        experiment_id=experiment_id,
        evidence_type=EvidenceType.COST_SUMMARY,
        timestamp=datetime.now(timezone.utc),
        payload=payload,
        source_module="tests",
        checksum="f" * 64,
    )


def _exp(experiment_id: str) -> ExperimentManifest:
    return ExperimentManifest(
        experiment_id=experiment_id,
        strategy_name="s",
        version="1",
        proposer_id="p",
        evidence_bundle=_bundle(),
    )


def test_mutation_future_leakage_forces_invalid() -> None:
    exp = _exp("MUT-PIT")
    state = adjudicate(
        exp,
        [_ev("MUT-PIT", future_leakage_detected=True, benchmark_delta=0.02, benchmark_id="SPY", benchmark_version="bench-v1")],
    )
    assert state == PromotionState.INVALID


def test_mutation_missing_benchmark_delta_blocks_promotable() -> None:
    exp = _exp("MUT-BENCH")
    state = adjudicate(exp, [_ev("MUT-BENCH", pit_integrity_ok=True, benchmark_passed=True)])
    assert state != PromotionState.PROMOTABLE


def test_mutation_cpcv_claim_without_metadata_forces_invalid() -> None:
    exp = _exp("MUT-CPCV")
    state = adjudicate(
        exp,
        [
            _ev(
                "MUT-CPCV",
                pit_integrity_ok=True,
                benchmark_passed=True,
                benchmark_delta=0.02,
                benchmark_id="SPY",
                benchmark_version="bench-v1",
                cpcv_passed=True,
            )
        ],
    )
    assert state == PromotionState.INVALID


def test_mutation_decoy_claim_without_suite_forces_invalid() -> None:
    exp = _exp("MUT-DECOY")
    state = adjudicate(
        exp,
        [
            _ev(
                "MUT-DECOY",
                pit_integrity_ok=True,
                benchmark_passed=True,
                benchmark_delta=0.02,
                benchmark_id="SPY",
                benchmark_version="bench-v1",
                decoy_survival_passed=True,
            )
        ],
    )
    assert state == PromotionState.INVALID


def test_mutation_partial_benchmark_payload_forces_rejected() -> None:
    exp = _exp("MUT-BENCH-TYPED")
    state = adjudicate(
        exp,
        [_ev("MUT-BENCH-TYPED", pit_integrity_ok=True, benchmark_passed=True, benchmark_delta=0.02)],
    )
    assert state == PromotionState.REJECTED


def test_mutation_direct_writer_authority_request_is_blocked() -> None:
    with pytest.raises(LedgerAuthorizationError):
        issue_write_authority()
