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
        "strategies": [{
            "strategy_id": "s1", "strategy_type": "swing", "prior_edge_confidence": 0.61, "deflated_sharpe_ratio": 0.34,
            "cpcv_lower_bound": 0.21, "realized_live_sharpe": 0.42, "recent_win_rate": 0.56, "drawdown_fraction": 0.05,
            "expected_regimes": ["RISK_ON_LOW_VOL"],
        }],
    })


def test_morning_attestation_reports_verified_integrity() -> None:
    report = build_oracle_morning_attestation(_payload())
    assert report.evidence_integrity_status == "VERIFIED"
    assert report.unverified_artifact_count == 0
    assert "Artifact integrity status=VERIFIED" in report.integrity_summary_line


def test_fusion_reports_mixed_integrity_when_manifest_is_incomplete(tmp_path: Path) -> None:
    repo_root = tmp_path
    (repo_root / "strategy_validator" / "policies").mkdir(parents=True, exist_ok=True)
    policy_src = Path("strategy_validator/policies/oracle_policy.json").read_text(encoding="utf-8")
    (repo_root / "strategy_validator" / "policies" / "oracle_policy.json").write_text(policy_src, encoding="utf-8")
    manifest_path = repo_root / "oracle_doctrine_adaptation.artifact_evidence_manifest.json"
    doctrine_report = repo_root / "oracle_doctrine_adaptation_report.json"
    doctrine_report.write_text(json.dumps({
        "schema_version": "oracle_doctrine_adaptation_report/v1",
        "generated_at_utc": "2026-04-14T07:00:00Z",
        "oracle_run_id": "run-1",
        "universe_label": "test-universe",
        "input_timestamp_utc": "2026-04-14T07:45:00Z",
        "dominant_regime": "RISK_ON_LOW_VOL",
        "history_integrity_status": "SEALED_HISTORY",
        "exact_evidence_support_score": 0.95,
        "exact_feedback_confirmation_count": 1,
        "exact_feedback_relief_count": 0,
        "exact_cadence_signal_classification": "EXACT_CONFIRMED_PRESSURE",
        "preferred_strategic_backing_source": "sealed_history",
        "preferred_strategic_backing_classification": "SEALED_STRATEGIC_STACK_BACKED",
        "doctrine_intensity_score": 0.2,
        "clauses": [],
        "operator_actions": [],
        "summary_line": "ok"
    }), encoding="utf-8")
    manifest = OracleStrategicArtifactEvidenceManifest(
        generated_at_utc=datetime(2026, 4, 13, 8, 0, tzinfo=UTC),
        artifact_kind="doctrine_adaptation",
        report_schema_version="oracle_doctrine_adaptation_report/v1",
        oracle_run_id="run-1",
        universe_label="test-universe",
        input_timestamp_utc=datetime(2026, 4, 14, 7, 45, tzinfo=UTC),
        preferred_strategic_backing_source="sealed_history",
        preferred_strategic_backing_classification="SEALED_STRATEGIC_STACK_BACKED",
        integrity_status="INCOMPLETE",
        subjects=[{"name": doctrine_report.name, "path": str(doctrine_report.relative_to(repo_root)), "digest": {"sha256": "0"*64}, "size_bytes": doctrine_report.stat().st_size, "media_type": "application/json"}],
        missing_artifact_paths=["missing.json"],
        summary_line="incomplete manifest",
    )
    manifest_path.write_text(json.dumps(manifest.model_dump(mode="json"), indent=2), encoding="utf-8")
    report = build_oracle_strategic_fusion_report(_payload(), repo_root=repo_root, search_root=repo_root, doctrine_adaptation_report_path=doctrine_report)
    assert report.evidence_integrity_status == "MIXED"
    assert report.unverified_artifact_count >= 1
    assert report.operator_readiness == "REVIEW_WITH_CAUTION"
    assert any("unverified" in reason or "incomplete" in reason for reason in report.operator_readiness_reasons)


def test_briefing_surfaces_integrity_summary(tmp_path: Path) -> None:
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
    assert report.evidence_integrity_status == "VERIFIED"
    assert "Artifact integrity status=VERIFIED" in report.integrity_summary_line
