from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.validator.oracle_briefing import build_oracle_briefing_pack
from strategy_validator.validator.oracle_operator_readiness import (
    assess_attestation_operator_readiness,
    assess_briefing_operator_readiness,
    assess_fusion_operator_readiness,
)


def test_attestation_does_not_penalize_absent_formal_support_verification() -> None:
    readiness, _, reasons = assess_attestation_operator_readiness(
        epistemic_status="NOMINAL",
        recommended_global_action="OBSERVE",
        evidence_freshness_status="FRESH",
        stale_artifact_count=0,
        evidence_integrity_status="VERIFIED",
        unverified_artifact_count=0,
        evidence_coverage_status="COMPLETE",
        missing_expected_artifact_count=0,
        support_verification_status="ABSENT",
    )
    assert readiness == "READY_FOR_REVIEW"
    assert not any("formal support verification" in reason for reason in reasons)


def test_fusion_penalizes_absent_formal_support_verification_when_support_is_otherwise_complete() -> None:
    readiness, _, reasons = assess_fusion_operator_readiness(
        epistemic_status="NOMINAL",
        strategic_posture="OPPORTUNITY_BIASED",
        evidence_freshness_status="FRESH",
        stale_artifact_count=0,
        evidence_integrity_status="VERIFIED",
        unverified_artifact_count=0,
        evidence_coverage_status="COMPLETE",
        missing_expected_artifact_count=0,
        support_verification_status="ABSENT",
    )
    assert readiness == "REVIEW_WITH_CAUTION"
    assert any("formal support verification" in reason for reason in reasons)


def test_briefing_penalizes_incomplete_formal_support_verification() -> None:
    readiness, _, reasons = assess_briefing_operator_readiness(
        trust_status="TRUSTED",
        evidence_freshness_status="FRESH",
        stale_artifact_count=0,
        evidence_integrity_status="VERIFIED",
        unverified_artifact_count=0,
        evidence_coverage_status="COMPLETE",
        missing_expected_artifact_count=0,
        support_verification_status="INCOMPLETE",
    )
    assert readiness == "REVIEW_WITH_CAUTION"
    assert any("incomplete" in reason and "verification" in reason for reason in reasons)


def test_briefing_builder_surfaces_missing_formal_support_verification_as_operator_action(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    artifacts_root = repo_root / "docs" / "artifacts"
    artifacts_root.mkdir(parents=True, exist_ok=True)
    (repo_root / "strategy_validator" / "policies").mkdir(parents=True, exist_ok=True)
    policy_src = Path("strategy_validator/policies/oracle_policy.json").read_text(encoding="utf-8")
    (repo_root / "strategy_validator" / "policies" / "oracle_policy.json").write_text(policy_src, encoding="utf-8")
    (artifacts_root / "ORACLE_STRATEGIC_BRIEFING_REPORT.json").write_text(
        json.dumps(
            {
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
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    report = build_oracle_briefing_pack(repo_root=repo_root, search_root=artifacts_root)

    assert report.support_verification_status == "ABSENT"
    assert report.operator_readiness in {"REVIEW_WITH_CAUTION", "HOLD_FOR_REFRESH"}
    assert any("formal support verification" in reason for reason in report.operator_readiness_reasons)
    assert any("formal support verification artifacts" in action for action in report.operator_actions)
