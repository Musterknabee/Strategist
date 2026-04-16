from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from strategy_validator.contracts.oracle import OracleAdvisoryInput
from strategy_validator.validator.oracle_advisory import build_oracle_morning_attestation
from strategy_validator.validator.oracle_briefing import build_oracle_briefing_pack
from strategy_validator.validator.oracle_signal_fusion import build_oracle_strategic_fusion_report
from strategy_validator.validator.oracle_support_chain_trust import assess_support_chain_trust


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


def test_support_chain_trust_is_untrusted_when_expected_artifacts_are_missing() -> None:
    status, _, reasons = assess_support_chain_trust(
        evidence_freshness_status="FRESH",
        stale_artifact_count=0,
        evidence_integrity_status="VERIFIED",
        unverified_artifact_count=0,
        evidence_coverage_status="MISSING",
        missing_expected_artifact_count=1,
        support_verification_status="ABSENT",
        formal_verification_required=False,
    )
    assert status == "UNTRUSTED"
    assert any("missing expected artifacts" in reason for reason in reasons)


def test_attestation_surfaces_trusted_support_chain_for_nominal_inputs() -> None:
    report = build_oracle_morning_attestation(_payload())
    assert report.support_chain_trust_status == "TRUSTED"
    assert "routine operator reliance" in report.support_chain_trust_summary_line.lower()
    assert report.support_chain_trust_reasons


def test_fusion_restricts_support_chain_trust_when_formal_verification_is_absent_for_complete_support() -> None:
    report = build_oracle_strategic_fusion_report(_payload())
    assert report.evidence_coverage_status == "COMPLETE"
    assert report.support_verification_status == "ABSENT"
    assert report.support_chain_trust_status in {"TRUST_RESTRICTED", "UNTRUSTED"}
    assert any("formal support verification" in reason for reason in report.support_chain_trust_reasons)


def test_briefing_surfaces_restricted_support_chain_when_formal_verification_is_absent(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    artifacts_root = repo_root / "docs" / "artifacts"
    (artifacts_root / "briefing").mkdir(parents=True)
    (repo_root / "strategy_validator" / "policies").mkdir(parents=True)
    policy_src = Path("strategy_validator/policies/oracle_policy.json").read_text(encoding="utf-8")
    (repo_root / "strategy_validator" / "policies" / "oracle_policy.json").write_text(policy_src, encoding="utf-8")
    (artifacts_root / "briefing" / "ORACLE_STRATEGIC_BRIEFING_REPORT.json").write_text(
        """
        {
          "schema_version": "oracle_strategic_briefing_report/v1",
          "generated_at_utc": "2026-01-10T09:00:00Z",
          "input_timestamp_utc": "2026-01-10T09:00:00Z",
          "oracle_run_id": "oracle-run-1",
          "universe_label": "core",
          "dominant_regime": "RISK_ON_LOW_VOL",
          "strategic_posture": "BALANCED_OBSERVATION",
          "summary_line": "summary",
          "sections": [],
          "operator_actions": []
        }
        """,
        encoding="utf-8",
    )
    report = build_oracle_briefing_pack(repo_root=repo_root, search_root=artifacts_root)
    assert report.support_verification_status == "ABSENT"
    assert report.support_chain_trust_status in {"TRUST_RESTRICTED", "UNTRUSTED"}
    assert any("formal support verification" in reason for reason in report.support_chain_trust_reasons)
