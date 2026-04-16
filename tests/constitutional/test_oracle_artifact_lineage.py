from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from strategy_validator.contracts.oracle import OracleAdvisoryInput, OracleDoctrineAdaptationReport, OracleStrategicArtifactEvidenceManifest
from strategy_validator.validator.oracle_advisory import build_oracle_morning_attestation
from strategy_validator.validator.oracle_briefing import build_oracle_briefing_pack
from strategy_validator.validator.oracle_signal_fusion import build_oracle_strategic_fusion_report


@pytest.mark.constitutional
def test_morning_attestation_records_input_and_policy_lineage(tmp_path: Path) -> None:
    repo_root = tmp_path
    (repo_root / "strategy_validator" / "policies").mkdir(parents=True)
    policy_src = Path("strategy_validator/policies/oracle_policy.json").read_text(encoding="utf-8")
    (repo_root / "strategy_validator" / "policies" / "oracle_policy.json").write_text(policy_src, encoding="utf-8")

    payload = OracleAdvisoryInput.model_validate(
        {
            "generated_for_utc": "2026-04-14T08:00:00Z",
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

    report = build_oracle_morning_attestation(payload, now_utc=datetime(2026, 4, 14, 8, 15, tzinfo=timezone.utc), repo_root=repo_root)

    labels = {item.artifact_label: item for item in report.artifact_lineage}
    assert set(labels) == {"advisory_input", "oracle_policy"}
    assert labels["advisory_input"].artifact_role == "INPUT"
    assert labels["advisory_input"].schema_version == "oracle_advisory_input"
    assert labels["oracle_policy"].artifact_role == "POLICY"
    assert labels["oracle_policy"].integrity_status == "VERIFIED"
    assert "Artifact lineage captured for 2 artifacts" in report.artifact_lineage_summary_line


@pytest.mark.constitutional
def test_strategic_fusion_records_preferred_evidence_manifest_in_lineage(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    artifacts_root = repo_root / "docs" / "artifacts"
    artifacts_root.mkdir(parents=True)
    (repo_root / "strategy_validator" / "policies").mkdir(parents=True)
    policy_src = Path("strategy_validator/policies/oracle_policy.json").read_text(encoding="utf-8")
    (repo_root / "strategy_validator" / "policies" / "oracle_policy.json").write_text(policy_src, encoding="utf-8")

    payload = OracleAdvisoryInput.model_validate(
        {
            "generated_for_utc": "2026-04-14T08:00:00Z",
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
    doctrine_report = OracleDoctrineAdaptationReport.model_validate(
        {
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
            "items": [
                {
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
                }
            ],
        }
    )
    doctrine_path = artifacts_root / "ORACLE_DOCTRINE_ADAPTATION_REPORT.json"
    doctrine_path.write_text(json.dumps(doctrine_report.model_dump(mode="json"), indent=2), encoding="utf-8")

    manifest = OracleStrategicArtifactEvidenceManifest(
        generated_at_utc=datetime(2026, 4, 14, 8, 6, tzinfo=timezone.utc),
        artifact_kind="doctrine_adaptation",
        report_schema_version="oracle_doctrine_adaptation_report/v1",
        oracle_run_id="oracle-run-1",
        universe_label="US_EQ_FACTORS",
        input_timestamp_utc=datetime(2026, 4, 14, 8, 0, tzinfo=timezone.utc),
        execution_authority="ADVISORY_ONLY",
        preferred_strategic_backing_source="SEALED_STRATEGIC_STACK",
        preferred_strategic_backing_classification="SEALED_STRATEGIC_STACK_BACKED",
        integrity_status="VERIFIED",
        subjects=[
            {
                "name": doctrine_path.name,
                "path": str(doctrine_path.relative_to(repo_root)).replace("\\", "/"),
                "digest": {"sha256": "a" * 64},
                "size_bytes": doctrine_path.stat().st_size,
                "media_type": "application/json",
            }
        ],
        missing_artifact_paths=[],
        summary_line="sealed doctrine evidence",
    )
    manifest_path = artifacts_root / "ORACLE_STRATEGIC_ARTIFACT_EVIDENCE.json"
    manifest_path.write_text(json.dumps(manifest.model_dump(mode="json"), indent=2), encoding="utf-8")
    verification_path = artifacts_root / "ORACLE_STRATEGIC_ARTIFACT_EVIDENCE.verification.json"
    verification_path.write_text(
        json.dumps(
            {
                "schema_version": "oracle_strategic_artifact_evidence_verification/v1",
                "generated_at_utc": "2026-04-14T08:07:00Z",
                "manifest_path": str(manifest_path.relative_to(repo_root)).replace("\\", "/"),
                "status": "VERIFIED",
                "verified_subject_count": 1,
                "missing_subjects": [],
                "summary_line": "verified",
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    report = build_oracle_strategic_fusion_report(
        payload,
        now_utc=datetime(2026, 4, 14, 8, 15, tzinfo=timezone.utc),
        doctrine_adaptation_report_path=doctrine_path,
        repo_root=repo_root,
        search_root=artifacts_root,
    )

    evidence_items = [item for item in report.artifact_lineage if item.artifact_role == "EVIDENCE"]
    assert len(evidence_items) == 1
    assert evidence_items[0].schema_version == "oracle_strategic_artifact_evidence_manifest/v1"
    assert evidence_items[0].integrity_status == "VERIFIED"
    assert evidence_items[0].source_path == str(manifest_path)


@pytest.mark.constitutional
def test_briefing_pack_records_policy_and_loaded_artifact_lineage(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    artifacts_root = repo_root / "docs" / "artifacts"
    artifacts_root.mkdir(parents=True)
    (repo_root / "strategy_validator" / "policies").mkdir(parents=True)
    policy_src = Path("strategy_validator/policies/oracle_policy.json").read_text(encoding="utf-8")
    (repo_root / "strategy_validator" / "policies" / "oracle_policy.json").write_text(policy_src, encoding="utf-8")

    strategic_briefing = {
        "schema_version": "oracle_strategic_briefing_report/v1",
        "generated_at_utc": "2026-04-14T08:00:00Z",
        "universe_label": "US_EQ_FACTORS",
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

    labels = {item.artifact_label: item for item in report.artifact_lineage}
    assert "oracle_policy" in labels
    assert labels["oracle_policy"].artifact_role == "POLICY"
    assert "status_pack" in labels
    assert labels["status_pack"].artifact_role == "STATUS"
    assert "strategic_briefing" in labels
    assert labels["strategic_briefing"].artifact_role == "DERIVED"
    assert labels["strategic_briefing"].schema_version == "oracle_strategic_briefing_report/v1"
