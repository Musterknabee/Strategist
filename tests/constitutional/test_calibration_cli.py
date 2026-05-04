"""CLI workflow for validating on-disk calibration artifacts."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from strategy_validator.cli.calibration import main


def _minimal_artifact(curve: bool) -> dict:
    base = {
        "calibration_schema_version": "1.0.0",
        "dataset_fingerprint": "abcd12345678",
        "model_version": "cli-test",
        "nonlinear_sqrt_multiplier": 400.0,
        "fitted_at_utc": datetime(2024, 1, 1, tzinfo=timezone.utc).isoformat(),
    }
    if curve:
        base["empirical_participation_curve"] = [
            {"participation_rate": 0.01, "impact_bps": 10.0},
            {"participation_rate": 0.05, "impact_bps": 50.0},
            {"participation_rate": 0.10, "impact_bps": 120.0},
        ]
    return base


def test_calibration_cli_load_ok(tmp_path: Path):
    p = tmp_path / "cal.json"
    p.write_text(json.dumps(_minimal_artifact(False)), encoding="utf-8")
    assert main(["--artifact", str(p)]) == 0


def test_calibration_cli_invalid_returns_2(tmp_path: Path):
    p = tmp_path / "bad.json"
    p.write_text("{", encoding="utf-8")
    assert main(["--artifact", str(p)]) == 2


def test_calibration_cli_samples_require_curve(tmp_path: Path):
    p = tmp_path / "cal.json"
    p.write_text(json.dumps(_minimal_artifact(False)), encoding="utf-8")
    assert main(["--artifact", str(p), "--participation", "0.05"]) == 3


def test_calibration_cli_check_governance_ok(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    p = tmp_path / "cal.json"
    p.write_text(json.dumps(_minimal_artifact(True)), encoding="utf-8")
    monkeypatch.delenv("STRATEGY_VALIDATOR_CALIBRATION_MINIMUM_VALIDATION_SCORE", raising=False)
    assert main(["--artifact", str(p), "--check-governance"]) == 0


def test_calibration_cli_samples_ok(tmp_path: Path):
    p = tmp_path / "cal.json"
    p.write_text(json.dumps(_minimal_artifact(True)), encoding="utf-8")
    code = main(["--artifact", str(p), "--participation", "0.05", "--json"])
    assert code == 0
