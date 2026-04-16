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
from strategy_validator.validator.oracle_scenario_lab import build_oracle_scenario_lab_report
from strategy_validator.validator.oracle_strategic_artifact_evidence import build_oracle_strategic_artifact_evidence_bundle
from strategy_validator.validator.oracle_strategic_briefing import build_oracle_strategic_briefing
from strategy_validator.validator.oracle_strategic_memory_horizon import build_oracle_strategic_memory_horizon_report
from strategy_validator.validator.oracle_strategic_narrative import build_oracle_strategic_narrative_report


_NOW = datetime(2026, 4, 13, 8, 10, tzinfo=timezone.utc)


def _payload(*, stressed: bool = False) -> OracleAdvisoryInput:
    return OracleAdvisoryInput.model_validate(
        {
            "generated_for_utc": "2026-04-13T08:10:00Z",
            "universe_label": "US_EQ_FACTORS",
            "sensors": {
                "semantic": {
                    "inflation_hawkishness_score": 0.55 if stressed else -0.18,
                    "geopolitical_risk_index": 0.76 if stressed else 0.12,
                    "narrative_contradiction_count": 4 if stressed else 1,
                    "tribunal_belief_conflict": 0.82 if stressed else 0.08,
                },
                "microstructure": {
                    "vpin": 0.70 if stressed else 0.20,
                    "order_flow_imbalance": -0.24 if stressed else 0.18,
                    "spread_variance_zscore": 1.6 if stressed else -0.12,
                    "liquidity_thinning_score": 0.72 if stressed else 0.10,
                },
                "macro": {
                    "yield_curve_slope_bps": -25.0 if stressed else 98.0,
                    "high_yield_credit_spread_bps": 448.0 if stressed else 280.0,
                    "equity_bond_correlation": 0.68 if stressed else -0.30,
                    "cross_asset_correlation_stress": 0.86 if stressed else 0.10,
                    "realized_volatility_zscore": 1.8 if stressed else -0.35,
                },
            },
            "strategies": [
                {
                    "strategy_id": "trend-b",
                    "strategy_type": "TREND_FOLLOWING",
                    "prior_edge_confidence": 0.72,
                    "deflated_sharpe_ratio": 0.94,
                    "cpcv_lower_bound": 0.30,
                    "realized_live_sharpe": -0.04 if stressed else 0.62,
                    "recent_win_rate": 0.40 if stressed else 0.59,
                    "drawdown_fraction": 0.16 if stressed else 0.04,
                    "expected_regimes": ["RISK_ON_LOW_VOL", "TRANSITION"],
                },
                {
                    "strategy_id": "carry-a",
                    "strategy_type": "CARRY",
                    "prior_edge_confidence": 0.61,
                    "deflated_sharpe_ratio": 0.72,
                    "cpcv_lower_bound": 0.18,
                    "realized_live_sharpe": 0.03 if stressed else 0.40,
                    "recent_win_rate": 0.46 if stressed else 0.56,
                    "drawdown_fraction": 0.10 if stressed else 0.03,
                    "expected_regimes": ["RISK_ON_LOW_VOL"],
                },
            ],
        }
    )


@pytest.mark.constitutional
def test_scenario_lab_surfaces_upside_and_downside_paths() -> None:
    report = build_oracle_scenario_lab_report(_payload(stressed=False), now_utc=_NOW)
    assert report.scenarios
    assert report.highest_downside_scenario_id is not None
    assert report.highest_upside_scenario_id is not None
    downside = next(item for item in report.scenarios if item.scenario_id == report.highest_downside_scenario_id)
    upside = next(item for item in report.scenarios if item.scenario_id == report.highest_upside_scenario_id)
    assert downside.caution_delta > 0
    assert upside.opportunity_delta > 0
    assert any(item.transition_classification in {"TRANSITIONING", "HIGH_UNCERTAINTY", "STRUCTURAL_BREAK_CANDIDATE", "DRIFTING", "STABLE_REGIME"} for item in report.scenarios)


@pytest.mark.constitutional
def test_strategic_briefing_includes_scenario_lab_section() -> None:
    report = build_oracle_strategic_briefing(_payload(stressed=False), now_utc=_NOW)
    section_ids = {section.section_id for section in report.sections}
    assert "scenario_lab" in section_ids
    section = next(section for section in report.sections if section.section_id == "scenario_lab")
    assert section.facts
    assert section.provenance_refs == ["scenario_lab:oracle_scenario_lab_report/v1"]


@pytest.mark.constitutional
def test_scenario_lab_cli_emits_report_and_markdown(tmp_path: Path) -> None:
    input_path = tmp_path / "ORACLE_ADVISORY_INPUT.json"
    input_path.write_text(json.dumps(_payload(stressed=False).model_dump(mode="json"), indent=2, default=str), encoding="utf-8")

    report_path = tmp_path / "ORACLE_SCENARIO_LAB_REPORT.json"
    markdown_path = tmp_path / "ORACLE_SCENARIO_LAB_REPORT.md"
    rc = main([
        "oracle-scenario-lab",
        str(input_path),
        "--output", str(report_path),
        "--markdown-output", str(markdown_path),
    ])
    assert rc == 0
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "oracle_scenario_lab_report/v1"
    assert payload["scenarios"]
    assert "ORACLE SCENARIO LAB REPORT" in markdown_path.read_text(encoding="utf-8")


@pytest.mark.constitutional
def test_briefing_pack_absorbs_scenario_lab_when_present(tmp_path: Path) -> None:
    repo_root = tmp_path
    oracle_root = repo_root / "docs" / "artifacts" / "oracle"
    oracle_root.mkdir(parents=True)

    scenario_report = build_oracle_scenario_lab_report(_payload(stressed=False), now_utc=_NOW)
    strategic_report = build_oracle_strategic_briefing(_payload(stressed=False), now_utc=_NOW)

    (oracle_root / "ORACLE_SCENARIO_LAB_REPORT.json").write_text(
        json.dumps(scenario_report.model_dump(mode="json"), indent=2, default=str),
        encoding="utf-8",
    )
    (oracle_root / "ORACLE_STRATEGIC_BRIEFING_REPORT.json").write_text(
        json.dumps(strategic_report.model_dump(mode="json"), indent=2, default=str),
        encoding="utf-8",
    )

    report = build_oracle_briefing_pack(repo_root=repo_root, search_root=repo_root / "docs" / "artifacts")
    section_ids = {section.section_id for section in report.sections}
    assert "scenario_lab" in section_ids
    section = next(section for section in report.sections if section.section_id == "scenario_lab")
    assert section.status in {"DOWNSIDE_PRESSURE", "UPSIDE_OPTIONALITY", "BALANCED_SCENARIOS"}
    assert section.provenance_refs == ["scenario_lab:oracle_scenario_lab_report/v1"]


@pytest.mark.constitutional
def test_scenario_lab_prefers_exact_sealed_support_when_present(tmp_path: Path) -> None:
    payload = _payload(stressed=False)
    current = build_oracle_strategic_narrative_report(payload, now_utc=_NOW)
    sealed_history = build_oracle_strategic_memory_horizon_report(
        current,
        sealed_history_reports=[build_oracle_strategic_narrative_report(payload, now_utc=_NOW.replace(hour=7))],
        sealed_history_manifest_paths=["docs/artifacts/oracle/STACK_07.json"],
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

    report = build_oracle_scenario_lab_report(
        payload,
        doctrine_adaptation_report=doctrine,
        research_priority_report=priorities,
        doctrine_adaptation_report_path=doctrine_path,
        research_priority_report_path=priorities_path,
        repo_root=repo_root,
        search_root=repo_root / "docs" / "artifacts",
        now_utc=_NOW,
    )
    assert report.exact_evidence_support_score >= 0.99
    assert all(item.exact_evidence_support_score >= 0.99 for item in report.scenarios)
    assert any("scenario_support_artifact_evidence_manifest=" in entry for entry in report.scenarios[0].evidence)
