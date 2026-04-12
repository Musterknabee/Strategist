from datetime import datetime, timezone

from strategy_validator.contracts.evidence import Evidence
from strategy_validator.core.enums import EvidenceType
from strategy_validator.validator.decoys import evaluate_decoy_survival_hook


def _ev(**payload) -> Evidence:
    return Evidence(
        evidence_id="d1",
        experiment_id="EXP-D",
        evidence_type=EvidenceType.COST_SUMMARY,
        timestamp=datetime.now(timezone.utc),
        payload=payload,
        source_module="tests",
        checksum="d" * 64,
    )


def test_decoy_hook_uses_explicit_boolean() -> None:
    outcome = evaluate_decoy_survival_hook([_ev(decoy_survival_passed=False)])
    assert outcome.passed is False


def test_decoy_hook_accepts_full_battery_v1() -> None:
    outcome = evaluate_decoy_survival_hook(
        [
            _ev(
                decoy_suite_version="decoy-v1",
                decoy_battery_results=[
                    {"decoy_type": "randomized_labels", "strategy_metric": 0.54, "decoy_metric": 0.50},
                    {"decoy_type": "timestamp_jitter", "strategy_metric": 0.53, "decoy_metric": 0.50},
                    {"decoy_type": "shuffled_cross_section", "strategy_metric": 0.52, "decoy_metric": 0.50},
                    {"decoy_type": "regime_mismatch", "strategy_metric": 0.51, "decoy_metric": 0.50},
                ],
            )
        ]
    )
    assert outcome.passed is True
    assert outcome.coverage == 1.0


def test_decoy_hook_fails_when_required_decoy_type_missing() -> None:
    outcome = evaluate_decoy_survival_hook(
        [
            _ev(
                decoy_suite_version="decoy-v1",
                decoy_battery_results=[
                    {"decoy_type": "randomized_labels", "strategy_metric": 0.54, "decoy_metric": 0.50},
                    {"decoy_type": "timestamp_jitter", "strategy_metric": 0.53, "decoy_metric": 0.50},
                    {"decoy_type": "shuffled_cross_section", "strategy_metric": 0.52, "decoy_metric": 0.50},
                ],
            )
        ]
    )
    assert outcome.passed is False
    assert outcome.coverage is not None and outcome.coverage < 1.0


def test_decoy_hook_fails_without_suite_version() -> None:
    outcome = evaluate_decoy_survival_hook(
        [
            _ev(
                decoy_battery_results=[
                    {"decoy_type": "randomized_labels", "strategy_metric": 0.54, "decoy_metric": 0.50},
                    {"decoy_type": "timestamp_jitter", "strategy_metric": 0.53, "decoy_metric": 0.50},
                    {"decoy_type": "shuffled_cross_section", "strategy_metric": 0.52, "decoy_metric": 0.50},
                    {"decoy_type": "regime_mismatch", "strategy_metric": 0.51, "decoy_metric": 0.50},
                ],
            )
        ]
    )
    assert outcome.passed is False


def test_decoy_hook_fails_on_empty_battery_rows() -> None:
    outcome = evaluate_decoy_survival_hook(
        [_ev(decoy_suite_version="decoy-v1", decoy_battery_results=[])]
    )
    assert outcome.passed is False
    assert outcome.coverage == 0.0


def test_decoy_hook_explicit_payload_invalid_coverage_fails() -> None:
    outcome = evaluate_decoy_survival_hook(
        [_ev(decoy_survival_passed=True, decoy_suite_version="decoy-v1", decoy_coverage=1.2)]
    )
    assert outcome.passed is False


def test_decoy_hook_explicit_true_without_suite_version_defers_structural_rejection() -> None:
    outcome = evaluate_decoy_survival_hook([_ev(decoy_survival_passed=True, decoy_coverage=1.0)])
    assert outcome.passed is True
    assert outcome.suite_version is None


def test_decoy_hook_explicit_negative_coverage_fails() -> None:
    outcome = evaluate_decoy_survival_hook(
        [_ev(decoy_survival_passed=True, decoy_suite_version="decoy-v1", decoy_coverage=-0.1)]
    )
    assert outcome.passed is False


def test_decoy_hook_fails_when_required_margin_not_met() -> None:
    outcome = evaluate_decoy_survival_hook(
        [
            _ev(
                decoy_suite_version="decoy-v1",
                decoy_battery_results=[
                    {"decoy_type": "randomized_labels", "strategy_metric": 0.51, "decoy_metric": 0.50, "required_margin": 0.02},
                    {"decoy_type": "timestamp_jitter", "strategy_metric": 0.53, "decoy_metric": 0.50, "required_margin": 0.02},
                    {"decoy_type": "shuffled_cross_section", "strategy_metric": 0.52, "decoy_metric": 0.50, "required_margin": 0.02},
                    {"decoy_type": "regime_mismatch", "strategy_metric": 0.51, "decoy_metric": 0.50, "required_margin": 0.02},
                ],
            )
        ]
    )
    assert outcome.passed is False
    assert outcome.coverage == 1.0
