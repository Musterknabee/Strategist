from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from strategy_validator.contracts.oracle import OracleAdvisoryInput, OracleDoctrineAdaptationReport, OracleStrategicArtifactEvidenceManifest
from strategy_validator.validator.oracle_advisory import build_oracle_morning_attestation
from strategy_validator.validator.oracle_automation_posture import assess_automation_posture
from strategy_validator.validator.oracle_briefing import build_oracle_briefing_pack
from strategy_validator.validator.oracle_signal_fusion import build_oracle_strategic_fusion_report


def _payload() -> OracleAdvisoryInput:
    return OracleAdvisoryInput.model_validate({
        "generated_for_utc": datetime(2026, 4, 14, 8, 0, tzinfo=UTC),
        "universe_label": "US_EQ_FACTORS",
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


def _write_policy(repo_root: Path) -> None:
    (repo_root / "strategy_validator" / "policies").mkdir(parents=True, exist_ok=True)
    policy_src = Path("strategy_validator/policies/oracle_policy.json").read_text(encoding="utf-8")
    (repo_root / "strategy_validator" / "policies" / "oracle_policy.json").write_text(policy_src, encoding="utf-8")


def _write_doctrine_report(artifacts_root: Path) -> Path:
    doctrine_report = OracleDoctrineAdaptationReport.model_validate({
        "schema_version": "oracle_doctrine_adaptation_report/v1",
        "generated_at_utc": "2026-04-14T08:05:00Z",
        "input_timestamp_utc": "2026-04-14T08:00:00Z",
        "oracle_run_id": "oracle-run-1",
        "universe_label": "US_EQ_FACTORS",
        "dominant_regime": "TRANSITION",
        "strategic_posture": "CAUTION_BIASED",
        "transition_classification": "DRIFTING",
        "history_integrity_status": "SEALED_HISTORY",
        "sealed_history_observation_count": 2,
        "unsealed_history_excluded_count": 0,
        "preferred_strategic_backing_source": "SEALED_STRATEGIC_STACK",
        "preferred_strategic_backing_classification": "SEALED_STRATEGIC_STACK_BACKED",
        "exact_evidence_support_score": 0.93,
        "summary_line": "doctrine is supported",
        "top_review_clause_ids": ["doctrine:stress-window"],
        "freeze_recommended": False,
        "operator_actions": [],
        "items": [{
            "clause_id": "doctrine:stress-window",
            "clause_label": "Stress window",
            "adaptation_state": "ADAPT",
            "stress_score": 0.55,
            "review_priority_score": 0.61,
            "exact_evidence_support_score": 0.93,
            "weakening_assumptions": [],
            "pressure_sources": ["queue_pressure"],
            "recommended_adaptation": "review now",
            "summary_line": "pressure persists",
        }],
    })
    doctrine_path = artifacts_root / "ORACLE_DOCTRINE_ADAPTATION_REPORT.json"
    doctrine_path.write_text(json.dumps(doctrine_report.model_dump(mode="json"), indent=2), encoding="utf-8")
    return doctrine_path


def _write_manifest(repo_root: Path, artifacts_root: Path, doctrine_path: Path) -> Path:
    manifest = OracleStrategicArtifactEvidenceManifest(
        generated_at_utc=datetime(2026, 4, 14, 8, 6, tzinfo=UTC),
        artifact_kind="doctrine_adaptation",
        report_schema_version="oracle_doctrine_adaptation_report/v1",
        oracle_run_id="oracle-run-1",
        universe_label="US_EQ_FACTORS",
        input_timestamp_utc=datetime(2026, 4, 14, 8, 0, tzinfo=UTC),
        execution_authority="ADVISORY_ONLY",
        preferred_strategic_backing_source="SEALED_STRATEGIC_STACK",
        preferred_strategic_backing_classification="SEALED_STRATEGIC_STACK_BACKED",
        integrity_status="VERIFIED",
        subjects=[{
            "name": doctrine_path.name,
            "path": str(doctrine_path.relative_to(repo_root)).replace("\\", "/"),
            "digest": {"sha256": "a" * 64},
            "size_bytes": doctrine_path.stat().st_size,
            "media_type": "application/json",
        }],
        missing_artifact_paths=[],
        summary_line="sealed doctrine evidence",
    )
    manifest_path = artifacts_root / "ORACLE_STRATEGIC_ARTIFACT_EVIDENCE.json"
    manifest_path.write_text(json.dumps(manifest.model_dump(mode="json"), indent=2), encoding="utf-8")
    return manifest_path


def test_assess_automation_posture_blocks_local_only_surfaces() -> None:
    posture, _, reasons = assess_automation_posture(
        propagation_posture="LOCAL_ONLY_DO_NOT_PROPAGATE",
        operator_escalation_lane="CONSTITUTIONAL_REPAIR_ESCALATION",
        operator_reliance_posture="REPAIR_FIRST",
    )
    assert posture == "HUMAN_ONLY_NO_AUTOMATION"
    assert any("automation" in reason.lower() or "local-only" in reason.lower() for reason in reasons)


def test_attestation_is_automation_eligible_for_nominal_inputs() -> None:
    report = build_oracle_morning_attestation(_payload())
    assert report.automation_posture == "AUTOMATION_ELIGIBLE"
    assert "automation eligible" in report.automation_summary_line.lower()
    assert report.automation_reasons


def test_fusion_requires_review_before_automation_when_verification_is_absent_for_complete_support(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    artifacts_root = repo_root / "docs" / "artifacts"
    artifacts_root.mkdir(parents=True)
    _write_policy(repo_root)
    doctrine_path = _write_doctrine_report(artifacts_root)
    _write_manifest(repo_root, artifacts_root, doctrine_path)

    report = build_oracle_strategic_fusion_report(
        _payload(),
        repo_root=repo_root,
        search_root=artifacts_root,
        doctrine_adaptation_report_path=doctrine_path,
        now_utc=datetime(2026, 4, 14, 8, 15, tzinfo=UTC),
    )

    assert report.automation_posture == "AUTOMATION_REVIEW_REQUIRED"
    assert any("review" in reason.lower() or "heightened" in reason.lower() for reason in report.automation_reasons)
    assert any("automated advisory workflows" in action.lower() for action in report.operator_actions)


def test_briefing_blocks_automation_when_support_requires_repair(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    artifacts_root = repo_root / "docs" / "artifacts"
    (artifacts_root / "briefing").mkdir(parents=True)
    _write_policy(repo_root)
    (artifacts_root / "briefing" / "ORACLE_STRATEGIC_BRIEFING_REPORT.json").write_text(
        json.dumps({
            "schema_version": "oracle_strategic_briefing_report/v1",
            "generated_at_utc": "2026-01-10T09:00:00Z",
            "input_timestamp_utc": "2026-01-10T09:00:00Z",
            "oracle_run_id": "oracle-run-1",
            "universe_label": "core",
            "dominant_regime": "RISK_ON_LOW_VOL",
            "strategic_posture": "BALANCED_OBSERVATION",
            "summary_line": "summary",
            "sections": [],
            "operator_actions": [],
        }, indent=2),
        encoding="utf-8",
    )
    report = build_oracle_briefing_pack(repo_root=repo_root, search_root=artifacts_root)
    assert report.automation_posture == "HUMAN_ONLY_NO_AUTOMATION"
    assert any("automation" in reason.lower() or "repair" in reason.lower() for reason in report.automation_reasons)
    assert any("out of automated advisory workflows" in action.lower() for action in report.operator_actions)
