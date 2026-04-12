from datetime import datetime, timezone

from strategy_validator.contracts.evidence import Evidence
from strategy_validator.core.enums import EvidenceType
from strategy_validator.validator.decoys import evaluate_decoy_survival_hook


def _ev(**payload) -> Evidence:
    return Evidence(
        evidence_id="d2",
        experiment_id="EXP-D2",
        evidence_type=EvidenceType.COST_SUMMARY,
        timestamp=datetime.now(timezone.utc),
        payload=payload,
        source_module="tests",
        checksum="e" * 64,
    )


def test_decoy_survival_battery_placeholder() -> None:
    outcome = evaluate_decoy_survival_hook(
        [
            _ev(
                decoy_suite_version="decoy-v1",
                decoy_battery_results=[
                    {"decoy_type": "randomized_labels", "strategy_metric": 0.58, "decoy_metric": 0.50, "required_margin": 0.02},
                    {"decoy_type": "timestamp_jitter", "strategy_metric": 0.57, "decoy_metric": 0.50, "required_margin": 0.02},
                    {"decoy_type": "shuffled_cross_section", "strategy_metric": 0.56, "decoy_metric": 0.50, "required_margin": 0.02},
                    {"decoy_type": "regime_mismatch", "strategy_metric": 0.55, "decoy_metric": 0.50, "required_margin": 0.02},
                ],
            )
        ]
    )
    assert outcome.passed is True
    assert outcome.coverage == 1.0
