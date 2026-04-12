from datetime import datetime, timezone
import math
import sqlite3

import pytest

from strategy_validator.contracts.evidence import Evidence, EvidenceBundle, ReproducibilityManifest
from strategy_validator.contracts.experiments import ExperimentManifest
from strategy_validator.core.enums import EvidenceType, PromotionState
from strategy_validator.core.exceptions import (
    IllegalPromotionStateTransition,
    ImmutableViolation,
    LedgerAuthorizationError,
    LedgerPayloadViolation,
)
from strategy_validator.ledger import reader as ledger_reader
from strategy_validator.ledger._append_only import _execute_write, resolve_database_path
from strategy_validator.ledger.writer import (
    _validate_ledger_payload,
    _validate_state_transition,
    commit_state_transition,
    issue_write_authority,
)
from strategy_validator.validator.orchestrator import adjudicate


def _repro() -> ReproducibilityManifest:
    return ReproducibilityManifest(
        code_hash="a" * 64,
        data_snapshot_hash="b" * 64,
        universe_hash="c" * 64,
        feature_graph_hash="d" * 64,
        parameter_manifest_hash="e" * 64,
        benchmark_version="bench-v1",
        cost_model_version="cost-v1",
        calendar_version="cal-v1",
    )


def _bundle(**kw) -> EvidenceBundle:
    defaults = dict(
        reproducibility=_repro(),
        benchmark_rung="L1",
        search_breadth=3,
        decoy_survival_passed=True,
        decoy_suite_version="decoy-v1",
        decoy_coverage=1.0,
        cpcv_path_stability=0.1,
        dsr_estimate=0.5,
        pbo_estimate=0.1,
    )
    defaults.update(kw)
    return EvidenceBundle(**defaults)


def _evidence(experiment_id: str, **payload) -> Evidence:
    return Evidence(
        evidence_id=f"e-{experiment_id}-{len(payload)}",
        experiment_id=experiment_id,
        evidence_type=EvidenceType.COST_SUMMARY,
        timestamp=datetime.now(timezone.utc),
        payload=payload,
        source_module="tests",
        checksum="1" * 64,
    )


def _manifest(experiment_id: str) -> ExperimentManifest:
    return ExperimentManifest(
        experiment_id=experiment_id,
        strategy_name="baseline",
        version="1",
        proposer_id="proposer",
        evidence_bundle=_bundle(),
    )


def test_append_only_persistence_across_multiple_writes() -> None:
    experiment = _manifest("EXP-PERSIST")
    experiment.evidence_bundle.dsr_estimate = 0.5
    experiment.evidence_bundle.pbo_estimate = 0.1
    experiment.evidence_bundle.cpcv_passed = True
    experiment.evidence_bundle.cpcv_folds = 5
    experiment.evidence_bundle.cpcv_path_coverage = 1.0
    experiment.evidence_bundle.decoy_survival_passed = True
    experiment.evidence_bundle.decoy_suite_version = "decoy-v1"
    experiment.evidence_bundle.decoy_coverage = 1.0

    adjudicate(
        experiment,
        [
            _evidence(
                "EXP-PERSIST",
                pit_integrity_ok=True,
                benchmark_passed=True,
                benchmark_delta=0.05,
                benchmark_id="SPY",
                benchmark_version="bench-v1",
                cpcv_passed=True,
                cpcv_folds=5,
                cpcv_path_coverage=1.0,
                dsr_estimate=0.5,
                pbo_estimate=0.1,
                incrementality_p_value=0.01,
                incrementality_significant=True,
                decoy_survival_passed=True,
                decoy_coverage=1.0
            )
        ],
    )
    adjudicate(experiment, [_evidence("EXP-PERSIST", future_leakage_detected=True)])
    history = ledger_reader.get_history("EXP-PERSIST")
    assert [event.promotion_state for event in history] == ["PROMOTABLE", "INVALID"]


def test_hash_chain_continuity() -> None:
    experiment = _manifest("EXP-CHAIN")
    experiment.evidence_bundle.dsr_estimate = 0.5
    experiment.evidence_bundle.pbo_estimate = 0.1
    experiment.evidence_bundle.cpcv_passed = True
    experiment.evidence_bundle.cpcv_folds = 5
    experiment.evidence_bundle.cpcv_path_coverage = 1.0
    experiment.evidence_bundle.decoy_survival_passed = True
    experiment.evidence_bundle.decoy_coverage = 1.0

    experiment.evidence_bundle.decoy_suite_version = "decoy-v1"
    adjudicate(
        experiment,
        [
            _evidence(
                "EXP-CHAIN",
                pit_integrity_ok=True,
                benchmark_passed=True,
                benchmark_delta=0.1,
                benchmark_id="SPY",
                benchmark_version="bench-v1",
                cpcv_passed=True,
                cpcv_folds=5,
                cpcv_path_coverage=1.0,
                dsr_estimate=0.5,
                pbo_estimate=0.1,
                incrementality_p_value=0.01,
                incrementality_significant=True,
                decoy_survival_passed=True,
                decoy_suite_version="decoy-v1",
                decoy_coverage=1.0
            )
        ],
    )
    # The second write triggers INVALID via future_leakage_detected
    adjudicate(experiment, [_evidence("EXP-CHAIN", future_leakage_detected=True)])
    history = ledger_reader.get_history("EXP-CHAIN")
    assert [event.promotion_state for event in history] == ["PROMOTABLE", "INVALID"]


def test_latest_state_reconstruction() -> None:
    experiment = _manifest("EXP-LATEST")
    adjudicate(
        experiment,
        [
            _evidence(
                "EXP-LATEST",
                pit_integrity_ok=True,
                benchmark_passed=True,
                benchmark_delta=0.02,
                benchmark_id="SPY",
                benchmark_version="bench-v1",
            )
        ],
    )
    adjudicate(
        experiment,
        [
            _evidence(
                "EXP-LATEST",
                benchmark_passed=False,
                benchmark_delta=0.0,
                benchmark_id="SPY",
                benchmark_version="bench-v1",
            )
        ],
    )
    latest = ledger_reader.get_experiment("EXP-LATEST")
    assert latest is not None
    assert latest.state == PromotionState.REJECTED


def test_attempted_update_delete_is_rejected() -> None:
    with pytest.raises(ImmutableViolation, match="append-only INSERT"):
        _execute_write("UPDATE ledger_events SET promotion_state = ? WHERE experiment_id = ?", ("PROMOTABLE", "EXP-1"))
    with pytest.raises(ImmutableViolation, match="append-only INSERT"):
        _execute_write("DELETE FROM ledger_events WHERE experiment_id = ?", ("EXP-1",))


def test_non_orchestrator_write_attempts_fail() -> None:
    experiment = _manifest("EXP-AUTH")
    with pytest.raises(LedgerAuthorizationError, match="acquire ledger write authority"):
        issue_write_authority()
    with pytest.raises(LedgerAuthorizationError, match="authority token"):
        commit_state_transition(experiment, authority=object())


def test_illegal_promotion_state_transition_rejected() -> None:
    with pytest.raises(IllegalPromotionStateTransition, match="REJECTED -> PROMOTABLE"):
        _validate_state_transition("REJECTED", "PROMOTABLE")


def test_promotable_payload_without_benchmark_delta_is_blocked() -> None:
    experiment = _manifest("EXP-PAYLOAD")
    experiment.state = PromotionState.PROMOTABLE
    experiment.evidence_bundle.cpcv_passed = True
    experiment.evidence_bundle.cpcv_folds = 3
    experiment.evidence_bundle.cpcv_path_coverage = 1.0
    experiment.evidence_bundle.decoy_survival_passed = True
    experiment.evidence_bundle.decoy_suite_version = "decoy-v1"
    experiment.evidence_bundle.decoy_coverage = 1.0

    payload = experiment.model_dump(mode="json")
    with pytest.raises(LedgerPayloadViolation):
        _validate_ledger_payload(payload, PromotionState.PROMOTABLE)


def test_promotable_payload_without_cpcv_coverage_is_blocked() -> None:
    experiment = _manifest("EXP-PAYLOAD-CPCV")
    experiment.state = PromotionState.PROMOTABLE
    experiment.evidence_bundle.evidence_items.append(
        _evidence(
            "EXP-PAYLOAD-CPCV",
            benchmark_delta=0.02,
            benchmark_passed=True,
            pit_integrity_ok=True,
            benchmark_id="SPY",
            benchmark_version="bench-v1",
        )
    )
    experiment.evidence_bundle.cpcv_passed = True
    experiment.evidence_bundle.cpcv_folds = 3
    experiment.evidence_bundle.decoy_survival_passed = True
    experiment.evidence_bundle.decoy_suite_version = "decoy-v1"
    experiment.evidence_bundle.decoy_coverage = 1.0

    payload = experiment.model_dump(mode="json")
    with pytest.raises(LedgerPayloadViolation, match="cpcv_path_coverage"):
        _validate_ledger_payload(payload, PromotionState.PROMOTABLE)


def test_promotable_payload_without_reproducibility_field_is_blocked() -> None:
    experiment = _manifest("EXP-PAYLOAD-REPRO")
    experiment.state = PromotionState.PROMOTABLE
    experiment.evidence_bundle.evidence_items.append(
        _evidence(
            "EXP-PAYLOAD-REPRO",
            benchmark_delta=0.02,
            benchmark_passed=True,
            pit_integrity_ok=True,
            benchmark_id="SPY",
            benchmark_version="bench-v1",
        )
    )
    experiment.evidence_bundle.cpcv_passed = True
    experiment.evidence_bundle.cpcv_folds = 3
    experiment.evidence_bundle.cpcv_path_coverage = 1.0
    experiment.evidence_bundle.decoy_survival_passed = True
    experiment.evidence_bundle.decoy_suite_version = "decoy-v1"
    experiment.evidence_bundle.decoy_coverage = 1.0

    payload = experiment.model_dump(mode="json")
    del payload["evidence_bundle"]["reproducibility"]["benchmark_version"]
    with pytest.raises(LedgerPayloadViolation, match="benchmark_version"):
        _validate_ledger_payload(payload, PromotionState.PROMOTABLE)


def test_promotable_payload_with_pbo_too_high_is_blocked() -> None:
    experiment = _manifest("EXP-PAYLOAD-PBO")
    experiment.state = PromotionState.PROMOTABLE
    experiment.evidence_bundle.evidence_items.append(
        _evidence(
            "EXP-PAYLOAD-PBO",
            benchmark_delta=0.02,
            benchmark_passed=True,
            pit_integrity_ok=True,
            benchmark_id="SPY",
            benchmark_version="bench-v1",
        )
    )
    experiment.evidence_bundle.cpcv_passed = True
    experiment.evidence_bundle.cpcv_folds = 3
    experiment.evidence_bundle.cpcv_path_coverage = 1.0
    experiment.evidence_bundle.cpcv_path_stability = 0.1
    experiment.evidence_bundle.dsr_estimate = 0.2
    experiment.evidence_bundle.pbo_estimate = 0.25
    experiment.evidence_bundle.decoy_survival_passed = True
    experiment.evidence_bundle.decoy_suite_version = "decoy-v1"
    experiment.evidence_bundle.decoy_coverage = 1.0

    payload = experiment.model_dump(mode="json")
    with pytest.raises(LedgerPayloadViolation, match="pbo_estimate <= 0.2"):
        _validate_ledger_payload(payload, PromotionState.PROMOTABLE)


def test_promotable_payload_with_decoy_coverage_below_one_is_blocked() -> None:
    experiment = _manifest("EXP-PAYLOAD-DECOY-COV")
    experiment.state = PromotionState.PROMOTABLE
    experiment.evidence_bundle.evidence_items.append(
        _evidence(
            "EXP-PAYLOAD-DECOY-COV",
            benchmark_delta=0.02,
            benchmark_passed=True,
            pit_integrity_ok=True,
            benchmark_id="SPY",
            benchmark_version="bench-v1",
        )
    )
    experiment.evidence_bundle.cpcv_passed = True
    experiment.evidence_bundle.cpcv_folds = 3
    experiment.evidence_bundle.cpcv_path_coverage = 1.0
    experiment.evidence_bundle.cpcv_path_stability = 0.1
    experiment.evidence_bundle.dsr_estimate = 0.2
    experiment.evidence_bundle.pbo_estimate = 0.1
    experiment.evidence_bundle.decoy_survival_passed = True
    experiment.evidence_bundle.decoy_suite_version = "decoy-v1"
    experiment.evidence_bundle.decoy_coverage = 0.9
    payload = experiment.model_dump(mode="json")
    with pytest.raises(LedgerPayloadViolation, match="decoy_coverage == 1.0"):
        _validate_ledger_payload(payload, PromotionState.PROMOTABLE)


def test_promotable_payload_without_dsr_is_blocked() -> None:
    experiment = _manifest("EXP-PAYLOAD-DSR")
    experiment.state = PromotionState.PROMOTABLE
    experiment.evidence_bundle.evidence_items.append(
        _evidence(
            "EXP-PAYLOAD-DSR",
            benchmark_delta=0.02,
            benchmark_passed=True,
            pit_integrity_ok=True,
            benchmark_id="SPY",
            benchmark_version="bench-v1",
        )
    )
    experiment.evidence_bundle.cpcv_passed = True
    experiment.evidence_bundle.cpcv_folds = 3
    experiment.evidence_bundle.cpcv_path_coverage = 1.0
    experiment.evidence_bundle.cpcv_path_stability = 0.1
    experiment.evidence_bundle.pbo_estimate = 0.1
    experiment.evidence_bundle.decoy_survival_passed = True
    experiment.evidence_bundle.decoy_suite_version = "decoy-v1"
    experiment.evidence_bundle.decoy_coverage = 1.0
    experiment.evidence_bundle.dsr_estimate = None

    payload = experiment.model_dump(mode="json")
    payload["promotion_history"] = [{
        "new_state": "PROMOTABLE", 
        "decided_at": "2026-04-12T00:00:00Z",
        "execution_report": {
            "total_post_cost_bps": 10.0,
            "passed": True,
            "impact_model_mode": "FIXED_BPS",
            "capacity": {"capacity_limit_passed": True, "estimated_participation_rate": 0.01},
            "borrow": {"shortability_passed": True}
        }
    }]
    with pytest.raises(LedgerPayloadViolation, match="dsr_estimate"):
        _validate_ledger_payload(payload, PromotionState.PROMOTABLE)


def test_promotable_payload_with_low_cpcv_coverage_is_blocked() -> None:
    experiment = _manifest("EXP-PAYLOAD-CPCV-LOW")
    experiment.state = PromotionState.PROMOTABLE
    experiment.evidence_bundle.evidence_items.append(
        _evidence(
            "EXP-PAYLOAD-CPCV-LOW",
            benchmark_delta=0.02,
            benchmark_passed=True,
            pit_integrity_ok=True,
            benchmark_id="SPY",
            benchmark_version="bench-v1",
        )
    )
    experiment.evidence_bundle.cpcv_passed = True
    experiment.evidence_bundle.cpcv_folds = 3
    experiment.evidence_bundle.cpcv_path_coverage = 0.6
    experiment.evidence_bundle.cpcv_path_stability = 0.1
    experiment.evidence_bundle.dsr_estimate = 0.2
    experiment.evidence_bundle.pbo_estimate = 0.1
    experiment.evidence_bundle.decoy_survival_passed = True
    experiment.evidence_bundle.decoy_suite_version = "decoy-v1"
    experiment.evidence_bundle.decoy_coverage = 1.0

    payload = experiment.model_dump(mode="json")
    with pytest.raises(LedgerPayloadViolation, match="cpcv_path_coverage >= 0.7"):
        _validate_ledger_payload(payload, PromotionState.PROMOTABLE)


def test_promotable_payload_with_high_cpcv_stability_is_blocked() -> None:
    experiment = _manifest("EXP-PAYLOAD-CPCV-STAB")
    experiment.state = PromotionState.PROMOTABLE
    experiment.evidence_bundle.evidence_items.append(
        _evidence(
            "EXP-PAYLOAD-CPCV-STAB",
            benchmark_delta=0.02,
            benchmark_passed=True,
            pit_integrity_ok=True,
            benchmark_id="SPY",
            benchmark_version="bench-v1",
        )
    )
    experiment.evidence_bundle.cpcv_passed = True
    experiment.evidence_bundle.cpcv_folds = 3
    experiment.evidence_bundle.cpcv_path_coverage = 1.0
    experiment.evidence_bundle.cpcv_path_stability = 2.0
    experiment.evidence_bundle.dsr_estimate = 0.2
    experiment.evidence_bundle.pbo_estimate = 0.1
    experiment.evidence_bundle.decoy_survival_passed = True
    experiment.evidence_bundle.decoy_suite_version = "decoy-v1"
    experiment.evidence_bundle.decoy_coverage = 1.0

    payload = experiment.model_dump(mode="json")
    with pytest.raises(LedgerPayloadViolation, match="cpcv_path_stability <= 1.0"):
        _validate_ledger_payload(payload, PromotionState.PROMOTABLE)


def test_promotable_payload_with_negative_pbo_is_blocked() -> None:
    experiment = _manifest("EXP-PAYLOAD-PBO-NEG")
    experiment.state = PromotionState.PROMOTABLE
    experiment.evidence_bundle.evidence_items.append(
        _evidence(
            "EXP-PAYLOAD-PBO-NEG",
            benchmark_delta=0.02,
            benchmark_passed=True,
            pit_integrity_ok=True,
            benchmark_id="SPY",
            benchmark_version="bench-v1",
        )
    )
    experiment.evidence_bundle.cpcv_passed = True
    experiment.evidence_bundle.cpcv_folds = 3
    experiment.evidence_bundle.cpcv_path_coverage = 1.0
    experiment.evidence_bundle.cpcv_path_stability = 0.1
    experiment.evidence_bundle.dsr_estimate = 0.2
    experiment.evidence_bundle.pbo_estimate = -0.1
    experiment.evidence_bundle.decoy_survival_passed = True
    experiment.evidence_bundle.decoy_suite_version = "decoy-v1"
    experiment.evidence_bundle.decoy_coverage = 1.0

    payload = experiment.model_dump(mode="json")
    with pytest.raises(LedgerPayloadViolation, match="pbo_estimate >= 0.0"):
        _validate_ledger_payload(payload, PromotionState.PROMOTABLE)


def test_promotable_payload_with_empty_benchmark_id_is_blocked() -> None:
    experiment = _manifest("EXP-PAYLOAD-BENCH-ID")
    experiment.state = PromotionState.PROMOTABLE
    experiment.evidence_bundle.evidence_items.append(
        _evidence(
            "EXP-PAYLOAD-BENCH-ID",
            benchmark_delta=0.02,
            benchmark_passed=True,
            pit_integrity_ok=True,
            benchmark_id="",
            benchmark_version="bench-v1",
        )
    )
    experiment.evidence_bundle.cpcv_passed = True
    experiment.evidence_bundle.cpcv_folds = 3
    experiment.evidence_bundle.cpcv_path_coverage = 1.0
    experiment.evidence_bundle.cpcv_path_stability = 0.1
    experiment.evidence_bundle.dsr_estimate = 0.2
    experiment.evidence_bundle.pbo_estimate = 0.1
    experiment.evidence_bundle.decoy_survival_passed = True
    experiment.evidence_bundle.decoy_suite_version = "decoy-v1"
    experiment.evidence_bundle.decoy_coverage = 1.0

    payload = experiment.model_dump(mode="json")
    with pytest.raises(LedgerPayloadViolation, match="typed benchmark evidence"):
        _validate_ledger_payload(payload, PromotionState.PROMOTABLE)


def test_promotable_payload_with_benchmark_version_mismatch_is_blocked() -> None:
    experiment = _manifest("EXP-PAYLOAD-BENCH-VER")
    experiment.state = PromotionState.PROMOTABLE
    experiment.evidence_bundle.evidence_items.append(
        _evidence(
            "EXP-PAYLOAD-BENCH-VER",
            benchmark_delta=0.02,
            benchmark_passed=True,
            pit_integrity_ok=True,
            benchmark_id="SPY",
            benchmark_version="bench-v999",
        )
    )
    experiment.evidence_bundle.cpcv_passed = True
    experiment.evidence_bundle.cpcv_folds = 3
    experiment.evidence_bundle.cpcv_path_coverage = 1.0
    experiment.evidence_bundle.cpcv_path_stability = 0.1
    experiment.evidence_bundle.dsr_estimate = 0.2
    experiment.evidence_bundle.pbo_estimate = 0.1
    experiment.evidence_bundle.decoy_survival_passed = True
    experiment.evidence_bundle.decoy_suite_version = "decoy-v1"
    experiment.evidence_bundle.decoy_coverage = 1.0

    payload = experiment.model_dump(mode="json")
    with pytest.raises(LedgerPayloadViolation, match="typed benchmark evidence"):
        _validate_ledger_payload(payload, PromotionState.PROMOTABLE)


def test_promotable_payload_with_non_numeric_benchmark_delta_is_blocked() -> None:
    experiment = _manifest("EXP-PAYLOAD-BENCH-NONNUM")
    experiment.state = PromotionState.PROMOTABLE
    experiment.evidence_bundle.evidence_items.append(
        _evidence(
            "EXP-PAYLOAD-BENCH-NONNUM",
            benchmark_delta="not-a-number",
            benchmark_passed=True,
            pit_integrity_ok=True,
            benchmark_id="SPY",
            benchmark_version="bench-v1",
        )
    )
    experiment.evidence_bundle.cpcv_passed = True
    experiment.evidence_bundle.cpcv_folds = 3
    experiment.evidence_bundle.cpcv_path_coverage = 1.0
    experiment.evidence_bundle.cpcv_path_stability = 0.1
    experiment.evidence_bundle.dsr_estimate = 0.2
    experiment.evidence_bundle.pbo_estimate = 0.1
    experiment.evidence_bundle.decoy_survival_passed = True
    experiment.evidence_bundle.decoy_suite_version = "decoy-v1"
    experiment.evidence_bundle.decoy_coverage = 1.0

    payload = experiment.model_dump(mode="json")
    with pytest.raises(LedgerPayloadViolation, match="benchmark_delta must be numeric"):
        _validate_ledger_payload(payload, PromotionState.PROMOTABLE)


def test_promotable_payload_with_nan_benchmark_delta_is_blocked() -> None:
    experiment = _manifest("EXP-PAYLOAD-BENCH-NAN")
    experiment.state = PromotionState.PROMOTABLE
    experiment.evidence_bundle.evidence_items.append(
        _evidence(
            "EXP-PAYLOAD-BENCH-NAN",
            benchmark_delta=math.nan,
            benchmark_passed=True,
            pit_integrity_ok=True,
            benchmark_id="SPY",
            benchmark_version="bench-v1",
        )
    )
    experiment.evidence_bundle.cpcv_passed = True
    experiment.evidence_bundle.cpcv_folds = 3
    experiment.evidence_bundle.cpcv_path_coverage = 1.0
    experiment.evidence_bundle.cpcv_path_stability = 0.1
    experiment.evidence_bundle.dsr_estimate = 0.2
    experiment.evidence_bundle.pbo_estimate = 0.1
    experiment.evidence_bundle.decoy_survival_passed = True
    experiment.evidence_bundle.decoy_suite_version = "decoy-v1"
    experiment.evidence_bundle.decoy_coverage = 1.0

    payload = experiment.model_dump(mode="json")
    with pytest.raises(LedgerPayloadViolation, match="benchmark_delta"):
        _validate_ledger_payload(payload, PromotionState.PROMOTABLE)


def test_promotable_payload_with_inf_benchmark_delta_is_blocked() -> None:
    experiment = _manifest("EXP-PAYLOAD-BENCH-INF")
    experiment.state = PromotionState.PROMOTABLE
    experiment.evidence_bundle.evidence_items.append(
        _evidence(
            "EXP-PAYLOAD-BENCH-INF",
            benchmark_delta=math.inf,
            benchmark_passed=True,
            pit_integrity_ok=True,
            benchmark_id="SPY",
            benchmark_version="bench-v1",
        )
    )
    experiment.evidence_bundle.cpcv_passed = True
    experiment.evidence_bundle.cpcv_folds = 3
    experiment.evidence_bundle.cpcv_path_coverage = 1.0
    experiment.evidence_bundle.cpcv_path_stability = 0.1
    experiment.evidence_bundle.dsr_estimate = 0.2
    experiment.evidence_bundle.pbo_estimate = 0.1
    experiment.evidence_bundle.decoy_survival_passed = True
    experiment.evidence_bundle.decoy_suite_version = "decoy-v1"
    experiment.evidence_bundle.decoy_coverage = 1.0

    payload = experiment.model_dump(mode="json")
    with pytest.raises(LedgerPayloadViolation, match="benchmark_delta"):
        _validate_ledger_payload(payload, PromotionState.PROMOTABLE)


def test_promotable_payload_with_evidence_experiment_id_mismatch_is_blocked() -> None:
    experiment = _manifest("EXP-PAYLOAD-EID-MISMATCH")
    experiment.state = PromotionState.PROMOTABLE
    mismatched = _evidence(
        "OTHER-EXPERIMENT",
        benchmark_delta=0.02,
        benchmark_passed=True,
        pit_integrity_ok=True,
        benchmark_id="SPY",
        benchmark_version="bench-v1",
    )
    experiment.evidence_bundle.evidence_items.append(mismatched)
    experiment.evidence_bundle.cpcv_passed = True
    experiment.evidence_bundle.cpcv_folds = 3
    experiment.evidence_bundle.cpcv_path_coverage = 1.0
    experiment.evidence_bundle.cpcv_path_stability = 0.1
    experiment.evidence_bundle.dsr_estimate = 0.2
    experiment.evidence_bundle.pbo_estimate = 0.1
    experiment.evidence_bundle.decoy_survival_passed = True
    experiment.evidence_bundle.decoy_suite_version = "decoy-v1"
    experiment.evidence_bundle.decoy_coverage = 1.0

    payload = experiment.model_dump(mode="json")
    with pytest.raises(LedgerPayloadViolation, match="experiment_id to match manifest"):
        _validate_ledger_payload(payload, PromotionState.PROMOTABLE)


def test_hash_chain_is_valid_for_unknown_experiment() -> None:
    assert ledger_reader.hash_chain_is_valid("EXP-DOES-NOT-EXIST") is True


def test_get_history_unknown_experiment_returns_empty() -> None:
    assert ledger_reader.get_history("EXP-DOES-NOT-EXIST") == []


def test_promotable_payload_with_cpcv_coverage_above_one_is_blocked() -> None:
    experiment = _manifest("EXP-PAYLOAD-CPCV-HI")
    experiment.state = PromotionState.PROMOTABLE
    experiment.evidence_bundle.evidence_items.append(
        _evidence(
            "EXP-PAYLOAD-CPCV-HI",
            benchmark_delta=0.02,
            benchmark_passed=True,
            pit_integrity_ok=True,
            benchmark_id="SPY",
            benchmark_version="bench-v1",
        )
    )
    experiment.evidence_bundle.cpcv_passed = True
    experiment.evidence_bundle.cpcv_folds = 3
    experiment.evidence_bundle.cpcv_path_coverage = 1.2
    experiment.evidence_bundle.cpcv_path_stability = 0.1
    experiment.evidence_bundle.dsr_estimate = 0.2
    experiment.evidence_bundle.pbo_estimate = 0.1
    experiment.evidence_bundle.decoy_survival_passed = True
    experiment.evidence_bundle.decoy_suite_version = "decoy-v1"
    experiment.evidence_bundle.decoy_coverage = 1.0

    payload = experiment.model_dump(mode="json")
    with pytest.raises(LedgerPayloadViolation, match="cpcv_path_coverage <= 1.0"):
        _validate_ledger_payload(payload, PromotionState.PROMOTABLE)


def test_promotable_payload_with_negative_cpcv_stability_is_blocked() -> None:
    experiment = _manifest("EXP-PAYLOAD-CPCV-STAB-NEG")
    experiment.state = PromotionState.PROMOTABLE
    experiment.evidence_bundle.evidence_items.append(
        _evidence(
            "EXP-PAYLOAD-CPCV-STAB-NEG",
            benchmark_delta=0.02,
            benchmark_passed=True,
            pit_integrity_ok=True,
            benchmark_id="SPY",
            benchmark_version="bench-v1",
        )
    )
    experiment.evidence_bundle.cpcv_passed = True
    experiment.evidence_bundle.cpcv_folds = 3
    experiment.evidence_bundle.cpcv_path_coverage = 1.0
    experiment.evidence_bundle.cpcv_path_stability = -0.1
    experiment.evidence_bundle.dsr_estimate = 0.2
    experiment.evidence_bundle.pbo_estimate = 0.1
    experiment.evidence_bundle.decoy_survival_passed = True
    experiment.evidence_bundle.decoy_suite_version = "decoy-v1"
    experiment.evidence_bundle.decoy_coverage = 1.0

    payload = experiment.model_dump(mode="json")
    with pytest.raises(LedgerPayloadViolation, match="cpcv_path_stability >= 0.0"):
        _validate_ledger_payload(payload, PromotionState.PROMOTABLE)


def test_promotable_payload_with_decoy_coverage_above_one_is_blocked() -> None:
    experiment = _manifest("EXP-PAYLOAD-DECOY-HI")
    experiment.state = PromotionState.PROMOTABLE
    experiment.evidence_bundle.evidence_items.append(
        _evidence(
            "EXP-PAYLOAD-DECOY-HI",
            benchmark_delta=0.02,
            benchmark_passed=True,
            pit_integrity_ok=True,
            benchmark_id="SPY",
            benchmark_version="bench-v1",
        )
    )
    experiment.evidence_bundle.cpcv_passed = True
    experiment.evidence_bundle.cpcv_folds = 3
    experiment.evidence_bundle.cpcv_path_coverage = 1.0
    experiment.evidence_bundle.cpcv_path_stability = 0.1
    experiment.evidence_bundle.dsr_estimate = 0.2
    experiment.evidence_bundle.pbo_estimate = 0.1
    experiment.evidence_bundle.decoy_survival_passed = True
    experiment.evidence_bundle.decoy_suite_version = "decoy-v1"
    experiment.evidence_bundle.decoy_coverage = 1.2
    payload = experiment.model_dump(mode="json")
    with pytest.raises(LedgerPayloadViolation, match="decoy_coverage <= 1.0"):
        _validate_ledger_payload(payload, PromotionState.PROMOTABLE)


def test_payload_state_mismatch_is_blocked() -> None:
    experiment = _manifest("EXP-PAYLOAD-STATE")
    experiment.state = PromotionState.PROMOTABLE
    experiment.evidence_bundle.evidence_items.append(
        _evidence(
            "EXP-PAYLOAD-STATE",
            benchmark_delta=0.02,
            benchmark_passed=True,
            pit_integrity_ok=True,
            benchmark_id="SPY",
            benchmark_version="bench-v1",
        )
    )
    experiment.evidence_bundle.cpcv_passed = True
    experiment.evidence_bundle.cpcv_folds = 3
    experiment.evidence_bundle.cpcv_path_coverage = 1.0
    experiment.evidence_bundle.cpcv_path_stability = 0.1
    experiment.evidence_bundle.dsr_estimate = 0.2
    experiment.evidence_bundle.pbo_estimate = 0.1
    experiment.evidence_bundle.decoy_survival_passed = True
    experiment.evidence_bundle.decoy_suite_version = "decoy-v1"
    experiment.evidence_bundle.decoy_coverage = 1.0

    payload = experiment.model_dump(mode="json")
    payload["state"] = "REJECTED"
    with pytest.raises(LedgerPayloadViolation, match="Payload state mismatch"):
        _validate_ledger_payload(payload, PromotionState.PROMOTABLE)


def test_hash_chain_validation_detects_storage_tamper() -> None:
    experiment = _manifest("EXP-TAMPER")
    experiment.evidence_bundle.dsr_estimate = 0.2
    experiment.evidence_bundle.pbo_estimate = 0.1
    experiment.evidence_bundle.cpcv_passed = True
    experiment.evidence_bundle.cpcv_folds = 3
    experiment.evidence_bundle.cpcv_path_coverage = 1.0
    experiment.evidence_bundle.cpcv_path_stability = 0.1
    experiment.evidence_bundle.decoy_survival_passed = True
    experiment.evidence_bundle.decoy_suite_version = "decoy-v1"
    experiment.evidence_bundle.decoy_coverage = 1.0

    adjudicate(
        experiment,
        [
            _evidence(
                "EXP-TAMPER",
                pit_integrity_ok=True,
                benchmark_passed=True,
                benchmark_delta=0.1,
                benchmark_id="SPY",
                benchmark_version="bench-v1",
            )
        ],
    )
    db_path = resolve_database_path()
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "UPDATE ledger_events SET event_payload_json = ? WHERE experiment_id = ? AND sequence_number = 1",
            ('{"tampered":true}', "EXP-TAMPER"),
        )
        conn.commit()
    assert ledger_reader.hash_chain_is_valid("EXP-TAMPER") is False
    assert ledger_reader.get_experiment("EXP-TAMPER") is None


def test_hash_chain_validation_detects_previous_hash_link_tamper() -> None:
    experiment = _manifest("EXP-LINK-TAMPER")
    experiment.evidence_bundle.dsr_estimate = 0.2
    experiment.evidence_bundle.pbo_estimate = 0.1
    experiment.evidence_bundle.cpcv_passed = True
    experiment.evidence_bundle.cpcv_folds = 3
    experiment.evidence_bundle.cpcv_path_coverage = 1.0
    experiment.evidence_bundle.cpcv_path_stability = 0.1
    experiment.evidence_bundle.decoy_survival_passed = True
    experiment.evidence_bundle.decoy_suite_version = "decoy-v1"
    experiment.evidence_bundle.decoy_coverage = 1.0

    adjudicate(
        experiment,
        [
            _evidence(
                "EXP-LINK-TAMPER",
                pit_integrity_ok=True,
                benchmark_passed=True,
                benchmark_delta=0.1,
                benchmark_id="SPY",
                benchmark_version="bench-v1",
            )
        ],
    )
    adjudicate(
        experiment,
        [
            _evidence(
                "EXP-LINK-TAMPER",
                benchmark_passed=False,
                benchmark_delta=0.0,
                benchmark_id="SPY",
                benchmark_version="bench-v1",
            )
        ],
    )
    db_path = resolve_database_path()
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "UPDATE ledger_events SET previous_event_hash = ? WHERE experiment_id = ? AND sequence_number = 2",
            ("deadbeef", "EXP-LINK-TAMPER"),
        )
        conn.commit()
    assert ledger_reader.hash_chain_is_valid("EXP-LINK-TAMPER") is False
    assert ledger_reader.get_experiment("EXP-LINK-TAMPER") is None


def test_hash_chain_validation_detects_sequence_number_tamper() -> None:
    experiment = _manifest("EXP-SEQ-TAMPER")
    experiment.evidence_bundle.dsr_estimate = 0.2
    experiment.evidence_bundle.pbo_estimate = 0.1
    experiment.evidence_bundle.cpcv_passed = True
    experiment.evidence_bundle.cpcv_folds = 3
    experiment.evidence_bundle.cpcv_path_coverage = 1.0
    experiment.evidence_bundle.cpcv_path_stability = 0.1
    experiment.evidence_bundle.decoy_survival_passed = True
    experiment.evidence_bundle.decoy_suite_version = "decoy-v1"
    experiment.evidence_bundle.decoy_coverage = 1.0

    adjudicate(
        experiment,
        [
            _evidence(
                "EXP-SEQ-TAMPER",
                pit_integrity_ok=True,
                benchmark_passed=True,
                benchmark_delta=0.1,
                benchmark_id="SPY",
                benchmark_version="bench-v1",
            )
        ],
    )
    adjudicate(
        experiment,
        [
            _evidence(
                "EXP-SEQ-TAMPER",
                benchmark_passed=False,
                benchmark_delta=0.0,
                benchmark_id="SPY",
                benchmark_version="bench-v1",
            )
        ],
    )
    db_path = resolve_database_path()
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "UPDATE ledger_events SET sequence_number = ? WHERE experiment_id = ? AND sequence_number = 2",
            (3, "EXP-SEQ-TAMPER"),
        )
        conn.commit()
    assert ledger_reader.hash_chain_is_valid("EXP-SEQ-TAMPER") is False
    assert ledger_reader.get_experiment("EXP-SEQ-TAMPER") is None


def test_list_promoted_strategies_excludes_tampered_experiments() -> None:
    clean = _manifest("EXP-CLEAN-PROMO")
    clean.evidence_bundle.dsr_estimate = 0.2
    clean.evidence_bundle.pbo_estimate = 0.1
    clean.evidence_bundle.cpcv_passed = True
    clean.evidence_bundle.cpcv_folds = 3
    clean.evidence_bundle.cpcv_path_coverage = 1.0
    clean.evidence_bundle.cpcv_path_stability = 0.1
    clean.evidence_bundle.decoy_suite_version = "decoy-v1"
    clean.evidence_bundle.decoy_coverage = 1.0
    clean.evidence_bundle.search_breadth = 3
    adjudicate(
        clean,
        [
            _evidence(
                "EXP-CLEAN-PROMO",
                pit_integrity_ok=True,
                benchmark_passed=True,
                benchmark_delta=0.1,
                benchmark_id="SPY",
                benchmark_version="bench-v1",
                cpcv_passed=True,
                cpcv_folds=5,
                cpcv_path_coverage=1.0,
                dsr_estimate=0.5,
                pbo_estimate=0.1,
                incrementality_p_value=0.01,
                incrementality_significant=True,
                decoy_survival_passed=True,
                decoy_suite_version="decoy-v1",
                decoy_coverage=1.0
            )
        ],
    )

    tampered = _manifest("EXP-TAMPERED-PROMO")
    tampered.evidence_bundle.dsr_estimate = 0.5
    tampered.evidence_bundle.pbo_estimate = 0.1
    tampered.evidence_bundle.cpcv_passed = True
    tampered.evidence_bundle.cpcv_folds = 5
    tampered.evidence_bundle.cpcv_path_coverage = 1.0
    tampered.evidence_bundle.decoy_suite_version = "decoy-v1"
    tampered.evidence_bundle.decoy_coverage = 1.0
    tampered.evidence_bundle.decoy_suite_version = "decoy-v1"
    adjudicate(
        tampered,
        [
            _evidence(
                "EXP-TAMPERED-PROMO",
                pit_integrity_ok=True,
                benchmark_passed=True,
                benchmark_delta=0.1,
                benchmark_id="SPY",
                benchmark_version="bench-v1",
                cpcv_passed=True,
                cpcv_folds=5,
                cpcv_path_coverage=1.0,
                dsr_estimate=0.5,
                pbo_estimate=0.1,
                incrementality_p_value=0.01,
                incrementality_significant=True,
                decoy_survival_passed=True,
                decoy_suite_version="decoy-v1",
                decoy_coverage=1.0
            )
        ],
    )
    db_path = resolve_database_path()
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "UPDATE ledger_events SET event_payload_json = ? WHERE experiment_id = ? AND sequence_number = 1",
            ('{"tampered":true}', "EXP-TAMPERED-PROMO"),
        )
        conn.commit()

    promoted_ids = {m.experiment_id for m in ledger_reader.list_promoted_strategies()}
    assert "EXP-CLEAN-PROMO" in promoted_ids
    assert "EXP-TAMPERED-PROMO" not in promoted_ids


def test_list_promoted_strategies_skips_malformed_payload_rows() -> None:
    experiment = _manifest("EXP-MALFORMED-PROMO")
    experiment.evidence_bundle.dsr_estimate = 0.2
    experiment.evidence_bundle.pbo_estimate = 0.1
    experiment.evidence_bundle.cpcv_passed = True
    experiment.evidence_bundle.cpcv_folds = 3
    experiment.evidence_bundle.cpcv_path_coverage = 1.0
    experiment.evidence_bundle.cpcv_path_stability = 0.1
    experiment.evidence_bundle.decoy_survival_passed = True
    experiment.evidence_bundle.decoy_suite_version = "decoy-v1"
    experiment.evidence_bundle.decoy_coverage = 1.0

    adjudicate(
        experiment,
        [
            _evidence(
                "EXP-MALFORMED-PROMO",
                pit_integrity_ok=True,
                benchmark_passed=True,
                benchmark_delta=0.1,
                benchmark_id="SPY",
                benchmark_version="bench-v1",
            )
        ],
    )
    db_path = resolve_database_path()
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "UPDATE ledger_events SET event_payload_json = ? WHERE experiment_id = ? AND sequence_number = 1",
            ('{"experiment_id":"EXP-MALFORMED-PROMO","state":"NOT_A_REAL_STATE"}', "EXP-MALFORMED-PROMO"),
        )
        conn.commit()
    promoted_ids = {m.experiment_id for m in ledger_reader.list_promoted_strategies()}
    assert "EXP-MALFORMED-PROMO" not in promoted_ids


def test_list_promoted_strategies_excludes_rows_tampered_to_non_promotable_state() -> None:
    experiment = _manifest("EXP-NONPROMO-TAMPER")
    experiment.evidence_bundle.dsr_estimate = 0.2
    experiment.evidence_bundle.pbo_estimate = 0.1
    experiment.evidence_bundle.cpcv_passed = True
    experiment.evidence_bundle.cpcv_folds = 3
    experiment.evidence_bundle.cpcv_path_coverage = 1.0
    experiment.evidence_bundle.cpcv_path_stability = 0.1
    experiment.evidence_bundle.decoy_survival_passed = True
    experiment.evidence_bundle.decoy_suite_version = "decoy-v1"
    experiment.evidence_bundle.decoy_coverage = 1.0

    adjudicate(
        experiment,
        [
            _evidence(
                "EXP-NONPROMO-TAMPER",
                pit_integrity_ok=True,
                benchmark_passed=True,
                benchmark_delta=0.1,
                benchmark_id="SPY",
                benchmark_version="bench-v1",
            )
        ],
    )
    db_path = resolve_database_path()
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT event_payload_json FROM ledger_events WHERE experiment_id = ? AND sequence_number = 1",
            ("EXP-NONPROMO-TAMPER",),
        ).fetchone()
        payload = row[0]
        payload = payload.replace('"state":6', '"state":2')
        conn.execute(
            "UPDATE ledger_events SET event_payload_json = ? WHERE experiment_id = ? AND sequence_number = 1",
            (payload, "EXP-NONPROMO-TAMPER"),
        )
        conn.commit()
    promoted_ids = {m.experiment_id for m in ledger_reader.list_promoted_strategies()}
    assert "EXP-NONPROMO-TAMPER" not in promoted_ids
