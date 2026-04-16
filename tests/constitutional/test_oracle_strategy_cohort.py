from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.contracts.oracle import OracleAdvisoryInput
from strategy_validator.validator.oracle_briefing import build_oracle_briefing_pack
from strategy_validator.validator.oracle_doctrine_adaptation import build_oracle_doctrine_adaptation_report
from strategy_validator.validator.oracle_research_planner import build_oracle_research_priority_report
from strategy_validator.validator.oracle_strategic_artifact_evidence import build_oracle_strategic_artifact_evidence_bundle
from strategy_validator.validator.oracle_strategic_briefing import build_oracle_strategic_briefing
from strategy_validator.validator.oracle_strategic_memory_horizon import build_oracle_strategic_memory_horizon_report
from strategy_validator.validator.oracle_strategic_narrative import build_oracle_strategic_narrative_report
from strategy_validator.validator.oracle_strategy_cohort import build_oracle_strategy_cohort_report


_NOW = datetime(2026, 4, 13, 10, 0, tzinfo=timezone.utc)


def _payload() -> OracleAdvisoryInput:
    return OracleAdvisoryInput.model_validate(
        {
            "generated_for_utc": "2026-04-13T10:00:00Z",
            "universe_label": "US_EQ_FACTORS",
            "sensors": {
                "semantic": {
                    "inflation_hawkishness_score": -0.08,
                    "geopolitical_risk_index": 0.18,
                    "narrative_contradiction_count": 1,
                    "tribunal_belief_conflict": 0.10,
                },
                "microstructure": {
                    "vpin": 0.26,
                    "order_flow_imbalance": 0.14,
                    "spread_variance_zscore": 0.05,
                    "liquidity_thinning_score": 0.16,
                },
                "macro": {
                    "yield_curve_slope_bps": 88.0,
                    "high_yield_credit_spread_bps": 300.0,
                    "equity_bond_correlation": -0.22,
                    "cross_asset_correlation_stress": 0.18,
                    "realized_volatility_zscore": -0.20,
                },
            },
            "strategies": [
                {
                    "strategy_id": "trend-b",
                    "strategy_type": "TREND_FOLLOWING",
                    "prior_edge_confidence": 0.78,
                    "deflated_sharpe_ratio": 0.96,
                    "cpcv_lower_bound": 0.32,
                    "realized_live_sharpe": 0.66,
                    "recent_win_rate": 0.60,
                    "drawdown_fraction": 0.04,
                    "expected_regimes": ["RISK_ON_LOW_VOL", "TRANSITION"],
                },
                {
                    "strategy_id": "carry-a",
                    "strategy_type": "CARRY",
                    "prior_edge_confidence": 0.63,
                    "deflated_sharpe_ratio": 0.71,
                    "cpcv_lower_bound": 0.18,
                    "realized_live_sharpe": 0.24,
                    "recent_win_rate": 0.53,
                    "drawdown_fraction": 0.08,
                    "expected_regimes": ["RISK_ON_LOW_VOL"],
                },
                {
                    "strategy_id": "meanrev-x",
                    "strategy_type": "MEAN_REVERSION",
                    "prior_edge_confidence": 0.56,
                    "deflated_sharpe_ratio": 0.44,
                    "cpcv_lower_bound": 0.08,
                    "realized_live_sharpe": -0.22,
                    "recent_win_rate": 0.39,
                    "drawdown_fraction": 0.19,
                    "expected_regimes": ["RISK_ON_LOW_VOL"],
                },
            ],
        }
    )


@pytest.mark.constitutional
def test_strategy_cohort_ranks_resilient_strategy_above_pressured_one() -> None:
    report = build_oracle_strategy_cohort_report(_payload(), now_utc=_NOW)
    assert report.items
    assert report.items[0].strategy_id == "trend-b"
    assert report.items[-1].strategy_id == "meanrev-x"
    assert report.items[0].cohort_rank_score > report.items[-1].cohort_rank_score
    assert report.items[-1].cohort_bucket in {"PRESSURED", "RESEARCH_ONLY"}


@pytest.mark.constitutional
def test_strategy_cohort_cli_emits_report_and_markdown(tmp_path: Path) -> None:
    input_path = tmp_path / "ORACLE_ADVISORY_INPUT.json"
    input_path.write_text(json.dumps(_payload().model_dump(mode="json"), indent=2, default=str), encoding="utf-8")

    report_path = tmp_path / "ORACLE_STRATEGY_COHORT_REPORT.json"
    markdown_path = tmp_path / "ORACLE_STRATEGY_COHORT_REPORT.md"
    rc = main([
        "oracle-strategy-cohort",
        str(input_path),
        "--output", str(report_path),
        "--markdown-output", str(markdown_path),
    ])
    assert rc == 0
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "oracle_strategy_cohort_report/v1"
    assert payload["items"][0]["strategy_id"] == "trend-b"
    assert "ORACLE STRATEGY COHORT REPORT" in markdown_path.read_text(encoding="utf-8")


@pytest.mark.constitutional
def test_strategic_briefing_includes_strategy_cohorts_section() -> None:
    report = build_oracle_strategic_briefing(_payload(), now_utc=_NOW)
    section = next(section for section in report.sections if section.section_id == "strategy_cohorts")
    assert section.facts
    assert section.provenance_refs == ["strategy_cohort:oracle_strategy_cohort_report/v1"]


@pytest.mark.constitutional
def test_briefing_pack_absorbs_strategy_cohort_report(tmp_path: Path) -> None:
    repo_root = tmp_path
    oracle_root = repo_root / "docs" / "artifacts" / "oracle"
    oracle_root.mkdir(parents=True)

    cohort_report = build_oracle_strategy_cohort_report(_payload(), now_utc=_NOW)
    strategic_report = build_oracle_strategic_briefing(_payload(), now_utc=_NOW)

    (oracle_root / "ORACLE_STRATEGY_COHORT_REPORT.json").write_text(
        json.dumps(cohort_report.model_dump(mode="json"), indent=2, default=str),
        encoding="utf-8",
    )
    (oracle_root / "ORACLE_STRATEGIC_BRIEFING_REPORT.json").write_text(
        json.dumps(strategic_report.model_dump(mode="json"), indent=2, default=str),
        encoding="utf-8",
    )

    report = build_oracle_briefing_pack(repo_root=repo_root, search_root=repo_root / "docs" / "artifacts")
    section = next(section for section in report.sections if section.section_id == "strategy_cohorts")
    assert section.status in {"LEAD", "WATCH", "PRESSURED", "RESEARCH_ONLY", "UNKNOWN"}
    assert section.provenance_refs == ["strategy_cohort:oracle_strategy_cohort_report/v1"]


@pytest.mark.constitutional
def test_strategy_cohort_prefers_exact_sealed_support_when_present(tmp_path: Path) -> None:
    payload = _payload()
    current = build_oracle_strategic_narrative_report(payload, now_utc=_NOW)
    sealed_history = build_oracle_strategic_memory_horizon_report(
        current,
        sealed_history_reports=[build_oracle_strategic_narrative_report(payload, now_utc=_NOW.replace(hour=9))],
        sealed_history_manifest_paths=["docs/artifacts/oracle/STACK_09.json"],
        require_sealed_history=True,
        now_utc=_NOW,
    )
    doctrine = build_oracle_doctrine_adaptation_report(payload, strategic_memory_horizon_report=sealed_history, now_utc=_NOW)
    priorities = build_oracle_research_priority_report(payload, strategic_memory_horizon_report=sealed_history, doctrine_adaptation_report=doctrine, now_utc=_NOW)

    repo_root = tmp_path
    artifacts_root = repo_root / "docs" / "artifacts" / "oracle"
    artifacts_root.mkdir(parents=True)
    doctrine_path = artifacts_root / "ORACLE_DOCTRINE_ADAPTATION_REPORT.json"
    doctrine_path.write_text(json.dumps(doctrine.model_dump(mode="json"), indent=2, default=str), encoding="utf-8")
    priorities_path = artifacts_root / "ORACLE_RESEARCH_PRIORITY_REPORT.json"
    priorities_path.write_text(json.dumps(priorities.model_dump(mode="json"), indent=2, default=str), encoding="utf-8")
    for idx, report_path in enumerate((doctrine_path, priorities_path), start=1):
        manifest, _ = build_oracle_strategic_artifact_evidence_bundle(report_path=report_path, repo_root=repo_root)
        manifest_path = artifacts_root / f"ORACLE_STRATEGIC_ARTIFACT_EVIDENCE_{idx}.json"
        manifest_path.write_text(json.dumps(manifest.model_dump(mode="json"), indent=2, default=str), encoding="utf-8")
        (artifacts_root / f"ORACLE_STRATEGIC_ARTIFACT_EVIDENCE_{idx}.verification.json").write_text(json.dumps({
            "verified_at_utc": _NOW.isoformat(),
            "manifest_path": str(manifest_path),
            "status": "VERIFIED",
            "artifact_digests_verified": True,
            "signature_verified": False,
            "verified_subject_count": len(manifest.subjects),
            "digest_mismatches": [],
            "missing_artifact_paths": [],
            "notes": [],
        }, indent=2), encoding="utf-8")

    plain = build_oracle_strategy_cohort_report(payload, now_utc=_NOW)
    supported = build_oracle_strategy_cohort_report(
        payload,
        doctrine_adaptation_report=doctrine,
        research_priority_report=priorities,
        doctrine_adaptation_report_path=doctrine_path,
        research_priority_report_path=priorities_path,
        repo_root=repo_root,
        search_root=repo_root / "docs" / "artifacts",
        now_utc=_NOW,
    )
    assert supported.exact_evidence_support_score >= 0.99
    assert supported.items[0].exact_evidence_support_score >= 0.59
    assert supported.items[0].cohort_rank_score > plain.items[0].cohort_rank_score
    assert any("cohort_support_artifact_evidence_manifest=" in entry for entry in supported.items[0].evidence)
