from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.contracts.oracle import OracleAdvisoryInput
from strategy_validator.validator.oracle_briefing import build_oracle_briefing_pack
from strategy_validator.validator.oracle_strategic_briefing import build_oracle_strategic_briefing
from strategy_validator.validator.oracle_strategic_memory_horizon import build_oracle_strategic_memory_horizon_report
from strategy_validator.validator.oracle_strategic_narrative import build_oracle_strategic_narrative_report


_NOW = datetime(2026, 4, 14, 8, 0, tzinfo=timezone.utc)


def _payload(*, stressed: bool = False) -> OracleAdvisoryInput:
    return OracleAdvisoryInput.model_validate(
        {
            "generated_for_utc": "2026-04-14T08:00:00Z",
            "universe_label": "US_EQ_FACTORS",
            "sensors": {
                "semantic": {
                    "inflation_hawkishness_score": 0.66 if stressed else -0.20,
                    "geopolitical_risk_index": 0.82 if stressed else 0.18,
                    "narrative_contradiction_count": 7 if stressed else 1,
                    "tribunal_belief_conflict": 0.84 if stressed else 0.10,
                },
                "microstructure": {
                    "vpin": 0.76 if stressed else 0.20,
                    "order_flow_imbalance": -0.38 if stressed else 0.26,
                    "spread_variance_zscore": 2.2 if stressed else -0.40,
                    "liquidity_thinning_score": 0.83 if stressed else 0.08,
                },
                "macro": {
                    "yield_curve_slope_bps": -46.0 if stressed else 110.0,
                    "high_yield_credit_spread_bps": 498.0 if stressed else 252.0,
                    "equity_bond_correlation": 0.74 if stressed else -0.34,
                    "cross_asset_correlation_stress": 0.90 if stressed else 0.16,
                    "realized_volatility_zscore": 2.0 if stressed else -0.28,
                },
            },
            "strategies": [
                {
                    "strategy_id": "trend-b",
                    "strategy_type": "TREND_FOLLOWING",
                    "prior_edge_confidence": 0.72,
                    "deflated_sharpe_ratio": 0.91,
                    "cpcv_lower_bound": 0.28,
                    "realized_live_sharpe": -0.18 if stressed else 0.61,
                    "recent_win_rate": 0.37 if stressed else 0.62,
                    "drawdown_fraction": 0.20 if stressed else 0.05,
                    "expected_regimes": ["RISK_ON_LOW_VOL", "TRANSITION"],
                },
                {
                    "strategy_id": "carry-a",
                    "strategy_type": "CARRY",
                    "prior_edge_confidence": 0.63,
                    "deflated_sharpe_ratio": 0.76,
                    "cpcv_lower_bound": 0.18,
                    "realized_live_sharpe": -0.02 if stressed else 0.41,
                    "recent_win_rate": 0.44 if stressed else 0.58,
                    "drawdown_fraction": 0.12 if stressed else 0.03,
                    "expected_regimes": ["RISK_ON_LOW_VOL"],
                },
            ],
        }
    )


def _narrative(*, stressed: bool, at_hour: int):
    report = build_oracle_strategic_narrative_report(_payload(stressed=stressed), now_utc=_NOW.replace(hour=at_hour))
    return report


@pytest.mark.constitutional
def test_memory_horizon_tracks_conviction_and_driver_drift() -> None:
    early = _narrative(stressed=False, at_hour=6)
    middle = _narrative(stressed=False, at_hour=7)
    current = _narrative(stressed=True, at_hour=8)

    report = build_oracle_strategic_memory_horizon_report(current, history_reports=[early, middle], now_utc=_NOW)

    assert report.schema_version == "oracle_strategic_memory_horizon_report/v1"
    assert report.horizon_observation_count == 3
    assert len(report.points) == 3
    assert report.driver_drifts
    assert report.drift_state in {"SOFTENING", "REVERSING", "VOLATILE", "STABLE", "STRENGTHENING"}
    assert report.strongest_rising_driver_kind is not None or report.strongest_falling_driver_kind is not None
    assert any(item.drift_direction in {"RISING", "FALLING"} for item in report.driver_drifts)


@pytest.mark.constitutional
def test_cli_emits_strategic_memory_horizon_report_and_markdown(tmp_path: Path) -> None:
    early = _narrative(stressed=False, at_hour=6)
    current = _narrative(stressed=True, at_hour=8)
    early_path = tmp_path / "ORACLE_STRATEGIC_NARRATIVE_REPORT.early.json"
    current_path = tmp_path / "ORACLE_STRATEGIC_NARRATIVE_REPORT.current.json"
    early_path.write_text(json.dumps(early.model_dump(mode="json"), indent=2, default=str), encoding="utf-8")
    current_path.write_text(json.dumps(current.model_dump(mode="json"), indent=2, default=str), encoding="utf-8")

    report_json = tmp_path / "ORACLE_STRATEGIC_MEMORY_HORIZON_REPORT.json"
    report_md = tmp_path / "ORACLE_STRATEGIC_MEMORY_HORIZON_REPORT.md"
    rc = main([
        "oracle-strategic-memory-horizon",
        str(current_path),
        "--history-report", str(early_path),
        "--output", str(report_json),
        "--markdown-output", str(report_md),
    ])
    assert rc == 0
    payload = json.loads(report_json.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "oracle_strategic_memory_horizon_report/v1"
    assert "ORACLE STRATEGIC MEMORY HORIZON REPORT" in report_md.read_text(encoding="utf-8")


@pytest.mark.constitutional
def test_strategic_briefing_includes_belief_drift_timeline_when_present() -> None:
    early = _narrative(stressed=False, at_hour=6)
    current = _narrative(stressed=True, at_hour=8)
    memory = build_oracle_strategic_memory_horizon_report(current, history_reports=[early], now_utc=_NOW)

    report = build_oracle_strategic_briefing(
        _payload(stressed=True),
        strategic_narrative_report=current,
        strategic_memory_horizon_report=memory,
        now_utc=_NOW,
    )

    section = next(section for section in report.sections if section.section_id == "belief_drift_timeline")
    assert section.provenance_refs == ["strategic_memory_horizon:oracle_strategic_memory_horizon_report/v1"]
    assert section.facts


@pytest.mark.constitutional
def test_briefing_pack_absorbs_strategic_memory_horizon_when_present(tmp_path: Path) -> None:
    repo_root = tmp_path
    oracle_root = repo_root / "docs" / "artifacts" / "oracle"
    oracle_root.mkdir(parents=True)

    early = _narrative(stressed=False, at_hour=6)
    current = _narrative(stressed=True, at_hour=8)
    memory = build_oracle_strategic_memory_horizon_report(current, history_reports=[early], now_utc=_NOW)

    (oracle_root / "ORACLE_STRATEGIC_MEMORY_HORIZON_REPORT.json").write_text(
        json.dumps(memory.model_dump(mode="json"), indent=2, default=str),
        encoding="utf-8",
    )

    report = build_oracle_briefing_pack(repo_root=repo_root, search_root=repo_root / "docs" / "artifacts")
    section = next(section for section in report.sections if section.section_id == "belief_drift_timeline")
    assert section.provenance_refs == ["strategic_memory_horizon:oracle_strategic_memory_horizon_report/v1"]
    assert section.facts
