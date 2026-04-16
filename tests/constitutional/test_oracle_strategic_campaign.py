from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.contracts.oracle import OracleAdvisoryInput
from strategy_validator.validator.oracle_briefing import build_oracle_briefing_pack
from strategy_validator.validator.oracle_campaign_planner import build_oracle_strategic_campaign_report, render_oracle_strategic_campaign_markdown
from strategy_validator.validator.oracle_doctrine_adaptation import build_oracle_doctrine_adaptation_report
from strategy_validator.validator.oracle_research_planner import build_oracle_research_priority_report
from strategy_validator.validator.oracle_strategic_artifact_evidence import build_oracle_strategic_artifact_evidence_bundle
from strategy_validator.validator.oracle_intervention_simulator import build_oracle_strategic_intervention_report
from strategy_validator.validator.oracle_strategic_briefing import build_oracle_strategic_briefing
from strategy_validator.validator.oracle_strategic_memory_horizon import build_oracle_strategic_memory_horizon_report
from strategy_validator.validator.oracle_strategic_narrative import build_oracle_strategic_narrative_report


_NOW = datetime(2026, 4, 14, 9, 0, tzinfo=timezone.utc)


def _payload(*, stressed: bool = False) -> OracleAdvisoryInput:
    return OracleAdvisoryInput.model_validate(
        {
            "generated_for_utc": "2026-04-14T09:00:00Z",
            "universe_label": "US_EQ_FACTORS",
            "sensors": {
                "semantic": {
                    "inflation_hawkishness_score": 0.79 if stressed else -0.18,
                    "geopolitical_risk_index": 0.90 if stressed else 0.18,
                    "narrative_contradiction_count": 9 if stressed else 1,
                    "tribunal_belief_conflict": 0.93 if stressed else 0.12,
                },
                "microstructure": {
                    "vpin": 0.88 if stressed else 0.17,
                    "order_flow_imbalance": -0.44 if stressed else 0.22,
                    "spread_variance_zscore": 2.7 if stressed else -0.40,
                    "liquidity_thinning_score": 0.91 if stressed else 0.09,
                },
                "macro": {
                    "yield_curve_slope_bps": -60.0 if stressed else 118.0,
                    "high_yield_credit_spread_bps": 560.0 if stressed else 238.0,
                    "equity_bond_correlation": 0.88 if stressed else -0.41,
                    "cross_asset_correlation_stress": 0.98 if stressed else 0.14,
                    "realized_volatility_zscore": 2.8 if stressed else -0.35,
                },
            },
            "strategies": [
                {
                    "strategy_id": "trend-b",
                    "strategy_type": "TREND_FOLLOWING",
                    "prior_edge_confidence": 0.72,
                    "deflated_sharpe_ratio": 0.90,
                    "cpcv_lower_bound": 0.28,
                    "realized_live_sharpe": -0.38 if stressed else 0.64,
                    "recent_win_rate": 0.29 if stressed else 0.65,
                    "drawdown_fraction": 0.28 if stressed else 0.05,
                    "expected_regimes": ["RISK_ON_LOW_VOL", "TRANSITION"],
                },
                {
                    "strategy_id": "carry-a",
                    "strategy_type": "CARRY",
                    "prior_edge_confidence": 0.65,
                    "deflated_sharpe_ratio": 0.78,
                    "cpcv_lower_bound": 0.19,
                    "realized_live_sharpe": -0.12 if stressed else 0.42,
                    "recent_win_rate": 0.39 if stressed else 0.56,
                    "drawdown_fraction": 0.16 if stressed else 0.03,
                    "expected_regimes": ["RISK_ON_LOW_VOL"],
                },
            ],
        }
    )


def _narrative(*, stressed: bool, at_hour: int):
    return build_oracle_strategic_narrative_report(_payload(stressed=stressed), now_utc=_NOW.replace(hour=at_hour))


@pytest.mark.constitutional
def test_campaign_report_groups_multi_step_objectives() -> None:
    current = _narrative(stressed=True, at_hour=9)
    history = [_narrative(stressed=False, at_hour=7), _narrative(stressed=False, at_hour=8)]
    memory = build_oracle_strategic_memory_horizon_report(current, history_reports=history, now_utc=_NOW)
    intervention = build_oracle_strategic_intervention_report(
        _payload(stressed=True),
        strategic_narrative_report=current,
        strategic_memory_horizon_report=memory,
        now_utc=_NOW,
    )

    report = build_oracle_strategic_campaign_report(
        _payload(stressed=True),
        strategic_narrative_report=current,
        strategic_memory_horizon_report=memory,
        intervention_report=intervention,
        now_utc=_NOW,
    )

    assert report.schema_version == "oracle_strategic_campaign_report/v1"
    assert report.items
    assert report.highest_priority_campaign_id is not None
    assert report.items[0].priority_score >= report.items[-1].priority_score
    assert any(len(item.steps) >= 2 for item in report.items)
    assert report.items[0].recommended_campaign


@pytest.mark.constitutional
def test_cli_emits_campaign_report_and_markdown(tmp_path: Path) -> None:
    input_path = tmp_path / "ORACLE_ADVISORY_INPUT.json"
    input_path.write_text(json.dumps(_payload(stressed=True).model_dump(mode="json"), indent=2, default=str), encoding="utf-8")

    report_json = tmp_path / "ORACLE_STRATEGIC_CAMPAIGN_REPORT.json"
    report_md = tmp_path / "ORACLE_STRATEGIC_CAMPAIGN_REPORT.md"
    rc = main([
        "oracle-strategic-campaign",
        str(input_path),
        "--output", str(report_json),
        "--markdown-output", str(report_md),
    ])
    assert rc == 0
    payload = json.loads(report_json.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "oracle_strategic_campaign_report/v1"
    assert "ORACLE STRATEGIC CAMPAIGN REPORT" in report_md.read_text(encoding="utf-8")


@pytest.mark.constitutional
def test_strategic_briefing_includes_campaign_section() -> None:
    current = _narrative(stressed=True, at_hour=9)
    memory = build_oracle_strategic_memory_horizon_report(current, history_reports=[_narrative(stressed=False, at_hour=8)], now_utc=_NOW)
    campaign = build_oracle_strategic_campaign_report(
        _payload(stressed=True),
        strategic_narrative_report=current,
        strategic_memory_horizon_report=memory,
        now_utc=_NOW,
    )

    report = build_oracle_strategic_briefing(
        _payload(stressed=True),
        strategic_narrative_report=current,
        strategic_memory_horizon_report=memory,
        strategic_campaign_report=campaign,
        now_utc=_NOW,
    )

    section = next(section for section in report.sections if section.section_id == "strategic_campaigns")
    assert section.provenance_refs == ["strategic_campaigns:oracle_strategic_campaign_report/v1"]
    assert section.facts


@pytest.mark.constitutional
def test_briefing_pack_absorbs_campaign_report_when_present(tmp_path: Path) -> None:
    repo_root = tmp_path
    oracle_root = repo_root / "docs" / "artifacts" / "oracle"
    oracle_root.mkdir(parents=True)

    current = _narrative(stressed=True, at_hour=9)
    memory = build_oracle_strategic_memory_horizon_report(current, history_reports=[_narrative(stressed=False, at_hour=8)], now_utc=_NOW)
    campaign = build_oracle_strategic_campaign_report(
        _payload(stressed=True),
        strategic_narrative_report=current,
        strategic_memory_horizon_report=memory,
        now_utc=_NOW,
    )

    (oracle_root / "ORACLE_STRATEGIC_CAMPAIGN_REPORT.json").write_text(
        json.dumps(campaign.model_dump(mode="json"), indent=2, default=str),
        encoding="utf-8",
    )

    report = build_oracle_briefing_pack(repo_root=repo_root, search_root=repo_root / "docs" / "artifacts")
    section = next(section for section in report.sections if section.section_id == "strategic_campaigns")
    assert section.provenance_refs == ["strategic_campaigns:oracle_strategic_campaign_report/v1"]
    assert section.facts


@pytest.mark.constitutional
def test_campaign_opportunity_expansion_is_penalized_without_sealed_history() -> None:
    current = _narrative(stressed=False, at_hour=9)
    prior = _narrative(stressed=False, at_hour=8)
    current_only_memory = build_oracle_strategic_memory_horizon_report(current, history_reports=[], now_utc=_NOW)
    sealed_memory = build_oracle_strategic_memory_horizon_report(current, history_reports=[prior], now_utc=_NOW)

    current_only = build_oracle_strategic_campaign_report(
        _payload(stressed=False),
        strategic_narrative_report=current,
        strategic_memory_horizon_report=current_only_memory,
        now_utc=_NOW,
    )
    sealed = build_oracle_strategic_campaign_report(
        _payload(stressed=False),
        strategic_narrative_report=current,
        strategic_memory_horizon_report=sealed_memory,
        now_utc=_NOW,
    )

    current_opportunity = next(item for item in current_only.items if item.objective_kind == "OPPORTUNITY_EXPANSION")
    sealed_opportunity = next(item for item in sealed.items if item.objective_kind == "OPPORTUNITY_EXPANSION")

    assert current_only.history_integrity_status == "CURRENT_ONLY"
    assert sealed.history_integrity_status == "MIXED_HISTORY"
    assert current_only.integrity_penalty_score > sealed.integrity_penalty_score
    assert current_opportunity.integrity_penalty_score > sealed_opportunity.integrity_penalty_score
    assert current_opportunity.integrity_penalty_score > sealed_opportunity.integrity_penalty_score
    assert "Verified sealed history is required" in current_opportunity.recommended_campaign


@pytest.mark.constitutional
def test_campaign_report_surfaces_preferred_strategic_backing() -> None:
    current = _narrative(stressed=True, at_hour=9)
    sealed_memory = build_oracle_strategic_memory_horizon_report(
        current,
        sealed_history_reports=[_narrative(stressed=False, at_hour=8)],
        sealed_history_manifest_paths=["docs/artifacts/oracle/STACK_08.json"],
        require_sealed_history=True,
        now_utc=_NOW,
    )
    report = build_oracle_strategic_campaign_report(
        _payload(stressed=True),
        strategic_narrative_report=current,
        strategic_memory_horizon_report=sealed_memory,
        now_utc=_NOW,
    )
    markdown = render_oracle_strategic_campaign_markdown(report)

    assert report.preferred_strategic_backing_source == "strategic_stack_manifest"
    assert report.preferred_strategic_backing_classification == "SEALED_STRATEGIC_STACK_BACKED"
    assert "Preferred strategic backing source: strategic_stack_manifest" in markdown


@pytest.mark.constitutional
def test_campaign_planner_prefers_exact_sealed_supporting_subjects_when_present(tmp_path: Path) -> None:
    payload = _payload(stressed=False)
    current = _narrative(stressed=False, at_hour=9)
    current_only_memory = build_oracle_strategic_memory_horizon_report(current, history_reports=[], now_utc=_NOW)
    sealed_memory = build_oracle_strategic_memory_horizon_report(
        current,
        sealed_history_reports=[_narrative(stressed=False, at_hour=8)],
        sealed_history_manifest_paths=["docs/artifacts/oracle/STACK_08.json"],
        require_sealed_history=True,
        now_utc=_NOW,
    )
    doctrine = build_oracle_doctrine_adaptation_report(payload, strategic_memory_horizon_report=sealed_memory, now_utc=_NOW)
    priorities = build_oracle_research_priority_report(payload, doctrine_adaptation_report=doctrine, strategic_memory_horizon_report=sealed_memory, now_utc=_NOW)

    repo_root = tmp_path
    artifacts = repo_root / "docs" / "artifacts" / "oracle"
    artifacts.mkdir(parents=True)
    paths = {
        "doctrine": artifacts / "ORACLE_DOCTRINE_ADAPTATION_REPORT.json",
        "research": artifacts / "ORACLE_RESEARCH_PRIORITY_REPORT.json",
    }
    paths["doctrine"].write_text(json.dumps(doctrine.model_dump(mode="json"), indent=2, default=str), encoding="utf-8")
    paths["research"].write_text(json.dumps(priorities.model_dump(mode="json"), indent=2, default=str), encoding="utf-8")
    for key, path in paths.items():
        manifest, _ = build_oracle_strategic_artifact_evidence_bundle(report_path=path, repo_root=repo_root)
        manifest_path = artifacts / f"{key.upper()}_ARTIFACT_EVIDENCE_MANIFEST.json"
        manifest_path.write_text(json.dumps(manifest.model_dump(mode="json"), indent=2, default=str), encoding="utf-8")
        verification_path = artifacts / f"{key.upper()}_ARTIFACT_EVIDENCE_MANIFEST.verification.json"
        verification_path.write_text(json.dumps({
            "schema_version": "oracle_strategic_artifact_evidence_verification/v1",
            "status": "VERIFIED",
            "integrity_status": "VERIFIED",
            "manifest_path": str(manifest_path),
            "verified_at_utc": _NOW.isoformat().replace("+00:00", "Z"),
            "subject_results": [],
            "verification_notes": [],
        }, indent=2), encoding="utf-8")

    plain = build_oracle_strategic_campaign_report(
        payload,
        strategic_narrative_report=current,
        strategic_memory_horizon_report=current_only_memory,
        doctrine_adaptation_report=doctrine,
        research_priority_report=priorities,
        now_utc=_NOW,
    )
    exact = build_oracle_strategic_campaign_report(
        payload,
        strategic_narrative_report=current,
        strategic_memory_horizon_report=current_only_memory,
        doctrine_adaptation_report=doctrine,
        doctrine_adaptation_report_path=paths["doctrine"],
        research_priority_report=priorities,
        research_priority_report_path=paths["research"],
        repo_root=repo_root,
        search_root=artifacts,
        now_utc=_NOW,
    )

    plain_doctrine = next(item for item in plain.items if item.objective_kind == "DOCTRINE_STABILIZATION")
    exact_doctrine = next(item for item in exact.items if item.objective_kind == "DOCTRINE_STABILIZATION")
    plain_expansion = next(item for item in plain.items if item.objective_kind == "OPPORTUNITY_EXPANSION")
    exact_expansion = next(item for item in exact.items if item.objective_kind == "OPPORTUNITY_EXPANSION")

    assert exact.exact_evidence_support_score >= 0.85
    assert exact_doctrine.exact_evidence_support_score >= 0.85
    assert exact_doctrine.integrity_penalty_score < plain_doctrine.integrity_penalty_score
    assert exact_doctrine.priority_score > plain_doctrine.priority_score
    assert exact_expansion.integrity_penalty_score < plain_expansion.integrity_penalty_score
    assert "exact sealed" in exact_doctrine.recommended_campaign.lower()


@pytest.mark.constitutional
def test_campaign_summary_surfaces_exact_cadence_driver(tmp_path: Path) -> None:
    repo_root = tmp_path
    artifacts = repo_root / "docs" / "artifacts" / "oracle"
    artifacts.mkdir(parents=True)

    payload = _payload(stressed=True)
    current = _narrative(stressed=True, at_hour=9)
    sealed_memory = build_oracle_strategic_memory_horizon_report(
        current,
        sealed_history_reports=[_narrative(stressed=False, at_hour=8)],
        sealed_history_manifest_paths=["docs/artifacts/oracle/STACK_08.json"],
        require_sealed_history=True,
        now_utc=_NOW,
    )
    doctrine = build_oracle_doctrine_adaptation_report(payload, strategic_memory_horizon_report=sealed_memory, now_utc=_NOW)
    stressed_items = [
        item.model_copy(update={"exact_evidence_support_score": 1.0, "stress_score": max(item.stress_score, 0.78), "review_priority_score": max(item.review_priority_score, 0.81)})
        for item in doctrine.items
    ]
    doctrine = doctrine.model_copy(update={"exact_evidence_support_score": 1.0, "items": stressed_items})
    doctrine_path = artifacts / "ORACLE_DOCTRINE_ADAPTATION_REPORT.json"
    doctrine_path.write_text(json.dumps(doctrine.model_dump(mode="json"), indent=2, default=str), encoding="utf-8")

    report = build_oracle_strategic_campaign_report(
        payload,
        strategic_narrative_report=current,
        strategic_memory_horizon_report=sealed_memory,
        doctrine_adaptation_report=doctrine,
        doctrine_adaptation_report_path=doctrine_path,
        repo_root=repo_root,
        search_root=artifacts,
        now_utc=_NOW,
    )
    markdown = render_oracle_strategic_campaign_markdown(report)

    assert report.exact_cadence_signal_classification == "EXACT_CONFIRMED_PRESSURE"
    assert report.exact_feedback_confirmation_count >= 1
    assert "cadence=EXACT_CONFIRMED_PRESSURE" in report.summary_line
    assert "Exact cadence signal: EXACT_CONFIRMED_PRESSURE" in markdown
    assert any(item.exact_cadence_signal_classification == "EXACT_CONFIRMED_PRESSURE" for item in report.items)


@pytest.mark.constitutional
def test_campaign_recommendation_changes_under_exact_confirmed_pressure(tmp_path: Path) -> None:
    repo_root = tmp_path
    artifacts = repo_root / "docs" / "artifacts" / "oracle"
    artifacts.mkdir(parents=True)

    payload = _payload(stressed=True)
    current = _narrative(stressed=True, at_hour=9)
    sealed_memory = build_oracle_strategic_memory_horizon_report(
        current,
        sealed_history_reports=[_narrative(stressed=False, at_hour=8)],
        sealed_history_manifest_paths=["docs/artifacts/oracle/STACK_08.json"],
        require_sealed_history=True,
        now_utc=_NOW,
    )
    doctrine = build_oracle_doctrine_adaptation_report(payload, strategic_memory_horizon_report=sealed_memory, now_utc=_NOW)
    stressed_items = [
        item.model_copy(update={"exact_evidence_support_score": 1.0, "stress_score": max(item.stress_score, 0.78), "review_priority_score": max(item.review_priority_score, 0.81)})
        for item in doctrine.items
    ]
    doctrine = doctrine.model_copy(update={"exact_evidence_support_score": 1.0, "items": stressed_items})
    doctrine_path = artifacts / "ORACLE_DOCTRINE_ADAPTATION_REPORT.json"
    doctrine_path.write_text(json.dumps(doctrine.model_dump(mode="json"), indent=2, default=str), encoding="utf-8")

    report = build_oracle_strategic_campaign_report(
        payload,
        strategic_narrative_report=current,
        strategic_memory_horizon_report=sealed_memory,
        doctrine_adaptation_report=doctrine,
        doctrine_adaptation_report_path=doctrine_path,
        repo_root=repo_root,
        search_root=artifacts,
        now_utc=_NOW,
    )

    assert report.exact_cadence_signal_classification == "EXACT_CONFIRMED_PRESSURE"
    assert any("Repeated exact sealed confirmations" in item.recommended_campaign for item in report.items)
    assert any("active pressure" in action for action in report.operator_actions)
