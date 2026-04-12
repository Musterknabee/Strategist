"""Readiness fail-closed rules for calibration."""
from __future__ import annotations

import json

import pytest

from strategy_validator.validator.readiness import perform_readiness_check


@pytest.mark.constitutional
def test_production_calibrated_without_artifact_blocks_readiness(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    db = tmp_path / "ledger.sqlite3"
    monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "PRODUCTION")
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB_PATH", str(db.absolute()))
    monkeypatch.setenv("STRATEGY_VALIDATOR_CAPACITY_IMPACT_MODEL", "CALIBRATED")
    monkeypatch.delenv("STRATEGY_VALIDATOR_CALIBRATION_ARTIFACT_PATH", raising=False)

    report = perform_readiness_check()
    assert report.status == "BLOCKED"
    assert any(b.code == "CALIBRATION_ARTIFACT_MISSING" for b in report.blockers)


@pytest.mark.constitutional
def test_production_calibrated_with_invalid_artifact_blocks(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    bad = tmp_path / "bad_cal.json"
    bad.write_text(json.dumps({"not": "valid"}), encoding="utf-8")
    db = tmp_path / "ledger.sqlite3"
    monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "PRODUCTION")
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB_PATH", str(db.absolute()))
    monkeypatch.setenv("STRATEGY_VALIDATOR_CAPACITY_IMPACT_MODEL", "CALIBRATED")
    monkeypatch.setenv("STRATEGY_VALIDATOR_CALIBRATION_ARTIFACT_PATH", str(bad))

    report = perform_readiness_check()
    assert report.status == "BLOCKED"
    assert any(b.code == "CALIBRATION_ARTIFACT_INVALID" for b in report.blockers)


@pytest.mark.constitutional
@pytest.mark.constitutional
def test_production_calibrated_governance_validation_score_blocks(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    art_path = tmp_path / "cal.json"
    art_path.write_text(
        json.dumps(
            {
                "calibration_schema_version": "1.0.0",
                "dataset_fingerprint": "0" * 8,
                "model_version": "gov_v1",
                "nonlinear_sqrt_multiplier": 600.0,
                "fitted_at_utc": "2026-04-12T00:00:00+00:00",
                "validation_quality_score": 0.4,
                "empirical_participation_curve": [
                    {"participation_rate": 0.01, "impact_bps": 10.0},
                    {"participation_rate": 0.05, "impact_bps": 50.0},
                    {"participation_rate": 0.10, "impact_bps": 120.0},
                ],
            }
        ),
        encoding="utf-8",
    )
    db = tmp_path / "ledger.sqlite3"
    monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "PRODUCTION")
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB_PATH", str(db.absolute()))
    monkeypatch.setenv("STRATEGY_VALIDATOR_CAPACITY_IMPACT_MODEL", "CALIBRATED")
    monkeypatch.setenv("STRATEGY_VALIDATOR_CALIBRATION_ARTIFACT_PATH", str(art_path))
    monkeypatch.setenv("STRATEGY_VALIDATOR_CALIBRATION_MINIMUM_VALIDATION_SCORE", "0.9")

    report = perform_readiness_check()
    assert report.status == "BLOCKED"
    assert any(b.code == "CALIBRATION_GOVERNANCE_REJECTED" for b in report.blockers)


def test_production_calibrated_with_non_monotonic_curve_blocks(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    bad = tmp_path / "bad_curve.json"
    bad.write_text(
        json.dumps(
            {
                "calibration_schema_version": "1.0.0",
                "dataset_fingerprint": "0" * 8,
                "model_version": "empirical_curve_v1",
                "nonlinear_sqrt_multiplier": 600.0,
                "fitted_at_utc": "2026-04-12T00:00:00+00:00",
                "empirical_participation_curve": [
                    {"participation_rate": 0.02, "impact_bps": 10.0},
                    {"participation_rate": 0.01, "impact_bps": 20.0},
                    {"participation_rate": 0.03, "impact_bps": 30.0},
                ],
            }
        ),
        encoding="utf-8",
    )
    db = tmp_path / "ledger.sqlite3"
    monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "PRODUCTION")
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB_PATH", str(db.absolute()))
    monkeypatch.setenv("STRATEGY_VALIDATOR_CAPACITY_IMPACT_MODEL", "CALIBRATED")
    monkeypatch.setenv("STRATEGY_VALIDATOR_CALIBRATION_ARTIFACT_PATH", str(bad))

    report = perform_readiness_check()
    assert report.status == "BLOCKED"
    assert any(b.code == "CALIBRATION_ARTIFACT_INVALID" for b in report.blockers)
