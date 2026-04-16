from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from strategy_validator.contracts.oracle import OracleAdvisoryInput, OracleStrategicArtifactEvidenceManifest
from strategy_validator.validator.oracle_advisory import build_oracle_morning_attestation
from strategy_validator.validator.oracle_briefing import build_oracle_briefing_pack
from strategy_validator.validator.oracle_signal_fusion import build_oracle_strategic_fusion_report


def _payload() -> OracleAdvisoryInput:
    return OracleAdvisoryInput.model_validate({
        "generated_for_utc": datetime(2026, 4, 14, 8, 0, tzinfo=UTC),
        "universe_label": "test-universe",
        "sensors": {
            "semantic": {"tribunal_belief_conflict": 0.15, "narrative_contradiction_count": 1},
            "microstructure": {"liquidity_thinning_score": 0.2, "spread_variance_zscore": 0.1},
            "macro": {
                "yield_curve_slope_bps": 12.0,
                "high_yield_credit_spread_bps": 310.0,
                "equity_bond_correlation": -0.2,
                "cross_asset_correlation_stress": 0.2,
                "realized_volatility_zscore": 0.1,
            },
        },
        "strategies": [],
    })


def test_morning_attestation_reports_complete_coverage() -> None:
    report = build_oracle_morning_attestation(_payload())
    assert report.evidence_coverage_status == "COMPLETE"
    assert report.missing_expected_artifact_count == 0
    assert report.missing_expected_artifact_labels == []
    assert "Artifact coverage status=COMPLETE" in report.evidence_coverage_summary_line


def test_fusion_reports_partial_coverage_when_manifest_expected_but_missing(tmp_path: Path) -> None:
    repo_root = tmp_path
    (repo_root / "strategy_validator" / "policies").mkdir(parents=True, exist_ok=True)
    policy_src = Path("strategy_validator/policies/oracle_policy.json").read_text(encoding="utf-8")
    (repo_root / "strategy_validator" / "policies" / "oracle_policy.json").write_text(policy_src, encoding="utf-8")
    missing_report_path = repo_root / "missing_doctrine_report.json"
    report = build_oracle_strategic_fusion_report(
        _payload(),
        repo_root=repo_root,
        search_root=repo_root,
        doctrine_adaptation_report_path=missing_report_path,
    )
    assert report.evidence_coverage_status == "PARTIAL"
    assert report.missing_expected_artifact_count == 1
    assert report.missing_expected_artifact_labels == ["preferred_strategic_artifact_evidence"]
    assert report.operator_readiness == "REVIEW_WITH_CAUTION"



def test_briefing_reports_complete_core_coverage(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    artifacts_root = repo_root / "docs" / "artifacts"
    artifacts_root.mkdir(parents=True, exist_ok=True)
    (repo_root / "strategy_validator" / "policies").mkdir(parents=True, exist_ok=True)
    policy_src = Path("strategy_validator/policies/oracle_policy.json").read_text(encoding="utf-8")
    (repo_root / "strategy_validator" / "policies" / "oracle_policy.json").write_text(policy_src, encoding="utf-8")
    strategic_briefing = {
        "schema_version": "oracle_strategic_briefing_report/v1",
        "generated_at_utc": "2026-04-14T08:00:00Z",
        "universe_label": "test-universe",
        "oracle_run_id": "run-1",
        "input_timestamp_utc": "2026-04-14T07:45:00Z",
        "dominant_regime": "RISK_ON_LOW_VOL",
        "strategic_posture": "OPPORTUNITY_BIASED",
        "transition_classification": None,
        "preferred_strategic_backing_source": None,
        "exact_feedback_confirmation_count": 0,
        "exact_feedback_relief_count": 0,
        "exact_cadence_signal_classification": "AMBIENT_DRIFT",
        "preferred_strategic_backing_classification": "NO_STRATEGIC_STACK_HISTORY",
        "summary_line": "briefing ok",
        "sections": [],
        "operator_actions": [],
    }
    (artifacts_root / "ORACLE_STRATEGIC_BRIEFING_REPORT.json").write_text(json.dumps(strategic_briefing, indent=2), encoding="utf-8")
    report = build_oracle_briefing_pack(repo_root=repo_root, search_root=artifacts_root)
    assert report.evidence_coverage_status == "COMPLETE"
    assert report.missing_expected_artifact_count == 0
