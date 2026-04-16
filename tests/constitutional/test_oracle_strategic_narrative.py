from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.contracts.oracle import OracleAdvisoryInput, OracleInvestigationOutcomeInput
from strategy_validator.validator.oracle_briefing import build_oracle_briefing_pack
from strategy_validator.validator.oracle_doctrine_adaptation import build_oracle_doctrine_adaptation_report
from strategy_validator.validator.oracle_research_execution_memory import build_oracle_research_execution_memory_report
from strategy_validator.validator.oracle_research_planner import build_oracle_research_priority_report
from strategy_validator.validator.oracle_strategic_artifact_evidence import build_oracle_strategic_artifact_evidence_bundle, verify_oracle_strategic_artifact_evidence_bundle
from strategy_validator.validator.oracle_strategic_briefing import build_oracle_strategic_briefing
from strategy_validator.validator.oracle_strategic_narrative import build_oracle_strategic_narrative_report


_NOW = datetime(2026, 4, 14, 8, 0, tzinfo=timezone.utc)


def _payload(*, stressed: bool = False) -> OracleAdvisoryInput:
    return OracleAdvisoryInput.model_validate(
        {
            "generated_for_utc": "2026-04-14T08:00:00Z",
            "universe_label": "US_EQ_FACTORS",
            "sensors": {
                "semantic": {
                    "inflation_hawkishness_score": 0.72 if stressed else -0.18,
                    "geopolitical_risk_index": 0.84 if stressed else 0.16,
                    "narrative_contradiction_count": 7 if stressed else 1,
                    "tribunal_belief_conflict": 0.88 if stressed else 0.12,
                },
                "microstructure": {
                    "vpin": 0.81 if stressed else 0.19,
                    "order_flow_imbalance": -0.42 if stressed else 0.22,
                    "spread_variance_zscore": 2.1 if stressed else -0.30,
                    "liquidity_thinning_score": 0.86 if stressed else 0.09,
                },
                "macro": {
                    "yield_curve_slope_bps": -48.0 if stressed else 102.0,
                    "high_yield_credit_spread_bps": 512.0 if stressed else 268.0,
                    "equity_bond_correlation": 0.82 if stressed else -0.32,
                    "cross_asset_correlation_stress": 0.94 if stressed else 0.14,
                    "realized_volatility_zscore": 2.3 if stressed else -0.34,
                },
            },
            "strategies": [
                {
                    "strategy_id": "trend-b",
                    "strategy_type": "TREND_FOLLOWING",
                    "prior_edge_confidence": 0.75,
                    "deflated_sharpe_ratio": 0.96,
                    "cpcv_lower_bound": 0.32,
                    "realized_live_sharpe": -0.22 if stressed else 0.64,
                    "recent_win_rate": 0.34 if stressed else 0.61,
                    "drawdown_fraction": 0.22 if stressed else 0.04,
                    "expected_regimes": ["RISK_ON_LOW_VOL", "TRANSITION"],
                },
                {
                    "strategy_id": "carry-a",
                    "strategy_type": "CARRY",
                    "prior_edge_confidence": 0.64,
                    "deflated_sharpe_ratio": 0.77,
                    "cpcv_lower_bound": 0.20,
                    "realized_live_sharpe": -0.04 if stressed else 0.43,
                    "recent_win_rate": 0.43 if stressed else 0.57,
                    "drawdown_fraction": 0.11 if stressed else 0.03,
                    "expected_regimes": ["RISK_ON_LOW_VOL"],
                },
            ],
        }
    )


def _outcomes(priority_report) -> OracleInvestigationOutcomeInput:
    doctrine_priority = next(item for item in priority_report.items if item.priority_kind == "DOCTRINE_REVIEW")
    strategy_priority = next(item for item in priority_report.items if item.related_strategy_ids)
    return OracleInvestigationOutcomeInput.model_validate(
        {
            "generated_at_utc": "2026-04-14T08:05:00Z",
            "universe_label": priority_report.universe_label,
            "items": [
                {
                    "outcome_id": "outcome-narrative-1",
                    "priority_id": doctrine_priority.priority_id,
                    "execution_state": "COMPLETED",
                    "outcome_disposition": "ESCALATED",
                    "thesis_ids": ["doctrine:coherence"],
                    "doctrine_clause_ids": ["doctrine:regime-assumptions"],
                    "thesis_effect": "WEAKENS",
                    "doctrine_effect": "FREEZE_CANDIDATE",
                    "cohort_effect": "WATCH",
                    "confidence_impact": -0.24,
                    "urgency_impact": 0.28,
                    "finding_summary": "Doctrine contradiction remained elevated under the latest probe.",
                    "evidence": ["doctrine_conflict", "contradiction_load"],
                    "next_action": "Freeze doctrine expansion until contradiction pressure is resolved.",
                },
                {
                    "outcome_id": "outcome-narrative-2",
                    "priority_id": strategy_priority.priority_id,
                    "execution_state": "COMPLETED",
                    "outcome_disposition": "REFUTED",
                    "related_strategy_ids": strategy_priority.related_strategy_ids,
                    "thesis_ids": [f"strategy:{strategy_priority.related_strategy_ids[0]}"],
                    "doctrine_clause_ids": ["doctrine:strategy-alignment"],
                    "thesis_effect": "WEAKENS",
                    "doctrine_effect": "PRESSURES",
                    "cohort_effect": "DEMOTES",
                    "confidence_impact": -0.33,
                    "urgency_impact": 0.20,
                    "finding_summary": "The supposed lead strategy failed the downside probe.",
                    "evidence": ["downside_probe_failed", "lead_cohort_fragility"],
                    "next_action": "Demote the strategy until fragility is resolved.",
                },
            ],
        }
    )


@pytest.mark.constitutional
def test_strategic_narrative_report_surfaces_fragile_conviction_under_contradiction() -> None:
    payload = _payload(stressed=False)
    priorities = build_oracle_research_priority_report(payload, now_utc=_NOW)
    execution_memory = build_oracle_research_execution_memory_report(priorities, _outcomes(priorities), now_utc=_NOW)
    report = build_oracle_strategic_narrative_report(payload, research_priority_report=priorities, research_execution_memory_report=execution_memory, now_utc=_NOW)

    assert report.schema_version == "oracle_strategic_narrative_report/v1"
    assert report.items
    assert report.highest_ranked_narrative_id is not None
    assert report.conviction_state in {"FRAGILE_CONVICTION", "BROKEN_CONVICTION", "GUARDED_CONVICTION"}
    assert any(item.driver_kind == "CONTRADICTION_DRIVER" for item in report.items)
    assert report.fragility_score >= 0.20


@pytest.mark.constitutional
def test_strategic_narrative_report_can_surface_guarded_or_high_conviction_when_supportive() -> None:
    report = build_oracle_strategic_narrative_report(_payload(stressed=False), now_utc=_NOW)

    assert report.items
    assert report.conviction_state in {"HIGH_CONVICTION", "GUARDED_CONVICTION", "FRAGILE_CONVICTION"}
    assert any(item.driver_kind == "REGIME_DRIVER" for item in report.items)




@pytest.mark.constitutional
def test_strategic_narrative_report_surfaces_exact_sealed_support_in_driver_interpretation(tmp_path: Path) -> None:
    payload = _payload(stressed=False)
    doctrine = build_oracle_doctrine_adaptation_report(payload, now_utc=_NOW).model_copy(update={
        "preferred_strategic_backing_source": "strategic_stack_manifest",
        "preferred_strategic_backing_classification": "SEALED_STRATEGIC_STACK_BACKED",
    })
    priorities = build_oracle_research_priority_report(payload, doctrine_adaptation_report=doctrine, now_utc=_NOW)

    repo_root = tmp_path
    doctrine_path = repo_root / "DOCTRINE.json"
    doctrine_path.write_text(json.dumps(doctrine.model_dump(mode="json"), indent=2, default=str), encoding="utf-8")
    manifest, _ = build_oracle_strategic_artifact_evidence_bundle(report_path=doctrine_path, repo_root=repo_root, now_utc=_NOW)
    manifest_path = repo_root / "DOCTRINE_EVIDENCE.json"
    manifest_path.write_text(json.dumps(manifest.model_dump(mode="json"), indent=2, default=str), encoding="utf-8")
    verification = verify_oracle_strategic_artifact_evidence_bundle(manifest_path=manifest_path, repo_root=repo_root)
    verification_path = repo_root / "DOCTRINE_EVIDENCE.verification.json"
    verification_path.write_text(json.dumps(verification.model_dump(mode="json"), indent=2, default=str), encoding="utf-8")

    report = build_oracle_strategic_narrative_report(
        payload,
        doctrine_adaptation_report=doctrine,
        research_priority_report=priorities,
        doctrine_adaptation_report_path=doctrine_path,
        repo_root=repo_root,
        search_root=repo_root,
        now_utc=_NOW,
    )

    assert report.exact_evidence_support_score > 0.9
    assert report.preferred_strategic_backing_classification == "SEALED_STRATEGIC_STACK_BACKED"
    assert any(item.exact_evidence_support_score > 0.9 for item in report.items)


@pytest.mark.constitutional
def test_cli_emits_strategic_narrative_report_and_markdown(tmp_path: Path) -> None:
    input_path = tmp_path / "ORACLE_ADVISORY_INPUT.json"
    input_path.write_text(json.dumps(_payload(stressed=False).model_dump(mode="json"), indent=2, default=str), encoding="utf-8")

    report_json = tmp_path / "ORACLE_STRATEGIC_NARRATIVE_REPORT.json"
    report_md = tmp_path / "ORACLE_STRATEGIC_NARRATIVE_REPORT.md"
    rc = main([
        "oracle-strategic-narrative",
        str(input_path),
        "--output", str(report_json),
        "--markdown-output", str(report_md),
    ])
    assert rc == 0
    payload = json.loads(report_json.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "oracle_strategic_narrative_report/v1"
    assert "ORACLE STRATEGIC NARRATIVE REPORT" in report_md.read_text(encoding="utf-8")


@pytest.mark.constitutional
def test_strategic_briefing_includes_strategic_narrative_section() -> None:
    payload = _payload(stressed=False)
    priorities = build_oracle_research_priority_report(payload, now_utc=_NOW)
    execution_memory = build_oracle_research_execution_memory_report(priorities, _outcomes(priorities), now_utc=_NOW)
    report = build_oracle_strategic_briefing(payload, research_execution_memory_report=execution_memory, now_utc=_NOW)

    section = next(section for section in report.sections if section.section_id == "strategic_narrative")
    assert section.provenance_refs == ["strategic_narrative:oracle_strategic_narrative_report/v1"]
    assert section.facts


@pytest.mark.constitutional
def test_briefing_pack_absorbs_strategic_narrative_when_present(tmp_path: Path) -> None:
    repo_root = tmp_path
    oracle_root = repo_root / "docs" / "artifacts" / "oracle"
    oracle_root.mkdir(parents=True)

    payload = _payload(stressed=False)
    priorities = build_oracle_research_priority_report(payload, now_utc=_NOW)
    execution_memory = build_oracle_research_execution_memory_report(priorities, _outcomes(priorities), now_utc=_NOW)
    narrative_report = build_oracle_strategic_narrative_report(payload, research_priority_report=priorities, research_execution_memory_report=execution_memory, now_utc=_NOW)

    (oracle_root / "ORACLE_STRATEGIC_NARRATIVE_REPORT.json").write_text(
        json.dumps(narrative_report.model_dump(mode="json"), indent=2, default=str),
        encoding="utf-8",
    )

    report = build_oracle_briefing_pack(repo_root=repo_root, search_root=repo_root / "docs" / "artifacts")
    section = next(section for section in report.sections if section.section_id == "strategic_narrative")
    assert section.provenance_refs == ["strategic_narrative:oracle_strategic_narrative_report/v1"]
    assert section.facts
