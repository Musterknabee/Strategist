from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from strategy_validator.contracts.oracle import OracleAdvisoryInput
from strategy_validator.validator.oracle_advisory import build_oracle_morning_attestation
from strategy_validator.validator.oracle_briefing import build_oracle_briefing_pack
from strategy_validator.validator.oracle_signal_fusion import build_oracle_strategic_fusion_report


@pytest.mark.constitutional
def test_morning_attestation_surfaces_stale_input_freshness() -> None:
    payload = OracleAdvisoryInput.model_validate(
        {
            "generated_for_utc": "2026-04-10T08:00:00Z",
            "universe_label": "US_EQ_FACTORS",
            "sensors": {
                "semantic": {
                    "inflation_hawkishness_score": 0.1,
                    "geopolitical_risk_index": 0.2,
                    "narrative_contradiction_count": 0,
                    "tribunal_belief_conflict": 0.1,
                },
                "microstructure": {
                    "vpin": 0.2,
                    "order_flow_imbalance": 0.05,
                    "spread_variance_zscore": 0.0,
                    "liquidity_thinning_score": 0.15,
                },
                "macro": {
                    "yield_curve_slope_bps": 15.0,
                    "high_yield_credit_spread_bps": 300.0,
                    "equity_bond_correlation": 0.1,
                    "cross_asset_correlation_stress": 0.15,
                    "realized_volatility_zscore": 0.2,
                },
            },
            "strategies": [],
        }
    )
    report = build_oracle_morning_attestation(payload, now_utc=datetime(2026, 4, 13, 8, 0, tzinfo=timezone.utc))
    assert report.evidence_freshness_status == "STALE"
    assert report.stale_artifact_count == 1
    assert report.artifact_freshness[0].artifact_label == "advisory_input"
    assert any("stale" in item.lower() for item in report.operator_actions)


@pytest.mark.constitutional
def test_briefing_pack_surfaces_stale_artifact_chain(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    artifacts_root = repo_root / "docs" / "artifacts"
    artifacts_root.mkdir(parents=True)
    (repo_root / "strategy_validator" / "policies").mkdir(parents=True)
    policy_src = Path("strategy_validator/policies/oracle_policy.json").resolve()
    (repo_root / "strategy_validator" / "policies" / "oracle_policy.json").write_text(policy_src.read_text(encoding="utf-8"), encoding="utf-8")

    stale_briefing = {
        "schema_version": "oracle_strategic_briefing_report/v1",
        "generated_at_utc": "2026-03-20T08:00:00Z",
        "universe_label": "US_EQ_FACTORS",
        "oracle_run_id": "run-1",
        "input_timestamp_utc": "2026-03-20T07:45:00Z",
        "dominant_regime": "RISK_ON_LOW_VOL",
        "strategic_posture": "OPPORTUNITY_BIASED",
        "transition_classification": None,
        "preferred_strategic_backing_source": None,
        "exact_feedback_confirmation_count": 0,
        "exact_feedback_relief_count": 0,
        "exact_cadence_signal_classification": "AMBIENT_DRIFT",
        "preferred_strategic_backing_classification": "NO_STRATEGIC_STACK_HISTORY",
        "summary_line": "stale strategic briefing",
        "sections": [],
        "operator_actions": ["refresh this briefing"],
    }
    (artifacts_root / "ORACLE_STRATEGIC_BRIEFING_REPORT.json").write_text(json.dumps(stale_briefing, indent=2), encoding="utf-8")

    report = build_oracle_briefing_pack(repo_root=repo_root, search_root=artifacts_root)
    assert report.evidence_freshness_status == "STALE"
    assert report.stale_artifact_count >= 1
    assert any(item.artifact_label == "strategic_briefing" and item.freshness_status == "STALE" for item in report.artifact_freshness)
    assert any("stale strategist artifacts" in item.lower() for item in report.operator_actions)


@pytest.mark.constitutional
def test_morning_attestation_sets_hold_for_refresh_readiness_on_stale_input() -> None:
    payload = OracleAdvisoryInput.model_validate(
        {
            "generated_for_utc": "2026-04-10T08:00:00Z",
            "universe_label": "US_EQ_FACTORS",
            "sensors": {
                "semantic": {
                    "inflation_hawkishness_score": 0.1,
                    "geopolitical_risk_index": 0.2,
                    "narrative_contradiction_count": 0,
                    "tribunal_belief_conflict": 0.1,
                },
                "microstructure": {
                    "vpin": 0.2,
                    "order_flow_imbalance": 0.05,
                    "spread_variance_zscore": 0.0,
                    "liquidity_thinning_score": 0.15,
                },
                "macro": {
                    "yield_curve_slope_bps": 15.0,
                    "high_yield_credit_spread_bps": 300.0,
                    "equity_bond_correlation": 0.1,
                    "cross_asset_correlation_stress": 0.15,
                    "realized_volatility_zscore": 0.2,
                },
            },
            "strategies": [],
        }
    )
    report = build_oracle_morning_attestation(payload, now_utc=datetime(2026, 4, 13, 8, 0, tzinfo=timezone.utc))
    assert report.operator_readiness == "HOLD_FOR_REFRESH"
    assert "blocked on freshness" in report.operator_readiness_summary_line.lower()
    assert report.operator_readiness_reasons


@pytest.mark.constitutional
def test_briefing_pack_sets_hold_for_refresh_readiness_on_stale_chain(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    artifacts_root = repo_root / "docs" / "artifacts"
    artifacts_root.mkdir(parents=True)
    (repo_root / "strategy_validator" / "policies").mkdir(parents=True)
    policy_src = Path("strategy_validator/policies/oracle_policy.json").resolve()
    (repo_root / "strategy_validator" / "policies" / "oracle_policy.json").write_text(policy_src.read_text(encoding="utf-8"), encoding="utf-8")

    stale_briefing = {
        "schema_version": "oracle_strategic_briefing_report/v1",
        "generated_at_utc": "2026-03-20T08:00:00Z",
        "universe_label": "US_EQ_FACTORS",
        "oracle_run_id": "run-1",
        "input_timestamp_utc": "2026-03-20T07:45:00Z",
        "dominant_regime": "RISK_ON_LOW_VOL",
        "strategic_posture": "OPPORTUNITY_BIASED",
        "transition_classification": None,
        "preferred_strategic_backing_source": None,
        "exact_feedback_confirmation_count": 0,
        "exact_feedback_relief_count": 0,
        "exact_cadence_signal_classification": "AMBIENT_DRIFT",
        "preferred_strategic_backing_classification": "NO_STRATEGIC_STACK_HISTORY",
        "summary_line": "stale strategic briefing",
        "sections": [],
        "operator_actions": ["refresh this briefing"],
    }
    (artifacts_root / "ORACLE_STRATEGIC_BRIEFING_REPORT.json").write_text(json.dumps(stale_briefing, indent=2), encoding="utf-8")

    report = build_oracle_briefing_pack(repo_root=repo_root, search_root=artifacts_root)
    assert report.operator_readiness == "HOLD_FOR_REFRESH"
    assert "repair trust or freshness gaps" in report.operator_readiness_summary_line.lower()
    assert report.operator_readiness_reasons
