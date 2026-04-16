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
from strategy_validator.validator.oracle_strategic_artifact_evidence import build_oracle_strategic_artifact_evidence_bundle
from strategy_validator.validator.oracle_strategic_briefing import build_oracle_strategic_briefing
from strategy_validator.validator.oracle_strategic_memory_horizon import build_oracle_strategic_memory_horizon_report
from strategy_validator.validator.oracle_strategic_narrative import build_oracle_strategic_narrative_report
from strategy_validator.validator.oracle_strategy_cohort import build_oracle_strategy_cohort_report
from strategy_validator.validator.oracle_thesis_memory import build_oracle_thesis_memory_report


_NOW = datetime(2026, 4, 13, 9, 5, tzinfo=timezone.utc)


def _payload(*, stressed: bool = False) -> OracleAdvisoryInput:
    return OracleAdvisoryInput.model_validate(
        {
            "generated_for_utc": "2026-04-13T09:05:00Z",
            "universe_label": "US_EQ_FACTORS",
            "sensors": {
                "semantic": {
                    "inflation_hawkishness_score": 0.74 if stressed else -0.18,
                    "geopolitical_risk_index": 0.82 if stressed else 0.14,
                    "narrative_contradiction_count": 5 if stressed else 1,
                    "tribunal_belief_conflict": 0.88 if stressed else 0.10,
                },
                "microstructure": {
                    "vpin": 0.79 if stressed else 0.20,
                    "order_flow_imbalance": -0.32 if stressed else 0.16,
                    "spread_variance_zscore": 1.9 if stressed else -0.10,
                    "liquidity_thinning_score": 0.80 if stressed else 0.10,
                },
                "macro": {
                    "yield_curve_slope_bps": -40.0 if stressed else 96.0,
                    "high_yield_credit_spread_bps": 490.0 if stressed else 285.0,
                    "equity_bond_correlation": 0.76 if stressed else -0.30,
                    "cross_asset_correlation_stress": 0.90 if stressed else 0.12,
                    "realized_volatility_zscore": 2.1 if stressed else -0.28,
                },
            },
            "strategies": [
                {
                    "strategy_id": "trend-b",
                    "strategy_type": "TREND_FOLLOWING",
                    "prior_edge_confidence": 0.73,
                    "deflated_sharpe_ratio": 0.95,
                    "cpcv_lower_bound": 0.31,
                    "realized_live_sharpe": -0.15 if stressed else 0.60,
                    "recent_win_rate": 0.36 if stressed else 0.58,
                    "drawdown_fraction": 0.20 if stressed else 0.04,
                    "expected_regimes": ["RISK_ON_LOW_VOL", "TRANSITION"],
                },
                {
                    "strategy_id": "carry-a",
                    "strategy_type": "CARRY",
                    "prior_edge_confidence": 0.63,
                    "deflated_sharpe_ratio": 0.76,
                    "cpcv_lower_bound": 0.18,
                    "realized_live_sharpe": -0.04 if stressed else 0.42,
                    "recent_win_rate": 0.44 if stressed else 0.56,
                    "drawdown_fraction": 0.12 if stressed else 0.03,
                    "expected_regimes": ["RISK_ON_LOW_VOL"],
                },
            ],
        }
    )


def _outcomes(priority_report) -> OracleInvestigationOutcomeInput:
    top = priority_report.items[0]
    strategy_priority = next(item for item in priority_report.items if item.related_strategy_ids)
    doctrine_priority = next(item for item in priority_report.items if item.priority_kind == "DOCTRINE_REVIEW")
    return OracleInvestigationOutcomeInput.model_validate(
        {
            "generated_at_utc": "2026-04-13T09:10:00Z",
            "universe_label": priority_report.universe_label,
            "items": [
                {
                    "outcome_id": "outcome-thesis",
                    "priority_id": top.priority_id,
                    "execution_state": "COMPLETED",
                    "outcome_disposition": "CONFIRMED",
                    "thesis_ids": ["doctrine:coherence"],
                    "doctrine_clause_ids": ["doctrine:regime-assumptions"],
                    "thesis_effect": "WEAKENS",
                    "doctrine_effect": "PRESSURES",
                    "cohort_effect": "WATCH",
                    "confidence_impact": -0.40,
                    "urgency_impact": 0.30,
                    "finding_summary": "The highest-priority investigation confirmed doctrine contradictions were worsening.",
                    "evidence": ["confirmed_doctrine_contradiction", "regime_mismatch_persisted"],
                    "next_action": "Escalate doctrine review and refresh the affected thesis immediately.",
                },
                {
                    "outcome_id": "outcome-strategy",
                    "priority_id": strategy_priority.priority_id,
                    "execution_state": "COMPLETED",
                    "outcome_disposition": "ESCALATED",
                    "related_strategy_ids": strategy_priority.related_strategy_ids,
                    "thesis_ids": [f"strategy:{strategy_priority.related_strategy_ids[0]}"],
                    "doctrine_clause_ids": ["doctrine:strategy-alignment"],
                    "thesis_effect": "WEAKENS",
                    "doctrine_effect": "FREEZE_CANDIDATE",
                    "cohort_effect": "DEMOTES",
                    "confidence_impact": -0.55,
                    "urgency_impact": 0.44,
                    "finding_summary": "The strategy validation investigation found materially worse downside than expected.",
                    "evidence": ["downside_floor_failed", "transition_pressure_elevated"],
                    "next_action": "Demote the pressured strategy and freeze any doctrine clause that assumes resilience here.",
                },
                {
                    "outcome_id": "outcome-doctrine",
                    "priority_id": doctrine_priority.priority_id,
                    "execution_state": "DEFERRED",
                    "outcome_disposition": "INCONCLUSIVE",
                    "doctrine_clause_ids": ["doctrine:research-expansion"],
                    "thesis_effect": "REVIEW_REQUIRED",
                    "doctrine_effect": "PRESSURES",
                    "cohort_effect": "NO_CHANGE",
                    "confidence_impact": -0.10,
                    "urgency_impact": 0.20,
                    "finding_summary": "The expansion review remains open pending another stress window.",
                    "evidence": ["need_more_evidence"],
                    "next_action": "Keep the expansion review open into the next sensing cycle.",
                },
            ],
        }
    )


@pytest.mark.constitutional
def test_execution_memory_feedback_changes_thesis_cohort_and_doctrine() -> None:
    payload = _payload(stressed=True)
    priority_report = build_oracle_research_priority_report(payload, now_utc=_NOW)
    outcomes = _outcomes(priority_report)
    execution = build_oracle_research_execution_memory_report(priority_report, outcomes, now_utc=_NOW)

    assert execution.schema_version == "oracle_research_execution_memory_report/v1"
    assert execution.completed_priority_ids
    assert execution.escalated_priority_ids

    thesis_base = build_oracle_thesis_memory_report(payload, now_utc=_NOW)
    thesis_adjusted = build_oracle_thesis_memory_report(payload, execution_memory_report=execution, now_utc=_NOW)
    doctrine_base = build_oracle_doctrine_adaptation_report(payload, now_utc=_NOW)
    doctrine_adjusted = build_oracle_doctrine_adaptation_report(payload, execution_memory_report=execution, now_utc=_NOW)
    cohort_base = build_oracle_strategy_cohort_report(payload, now_utc=_NOW)
    cohort_adjusted = build_oracle_strategy_cohort_report(payload, execution_memory_report=execution, now_utc=_NOW)

    base_doctrine = next(item for item in thesis_base.items if item.thesis_id == "doctrine:coherence")
    adjusted_doctrine = next(item for item in thesis_adjusted.items if item.thesis_id == "doctrine:coherence")
    assert adjusted_doctrine.confidence_score < base_doctrine.confidence_score
    assert any("investigation:" in entry for entry in adjusted_doctrine.evidence_against)

    base_clause = next(item for item in doctrine_base.items if item.clause_id == "doctrine:regime-assumptions")
    adjusted_clause = next(item for item in doctrine_adjusted.items if item.clause_id == "doctrine:regime-assumptions")
    assert adjusted_clause.stress_score >= base_clause.stress_score
    assert any("investigation:" in entry for entry in adjusted_clause.pressure_sources)

    impacted_strategy_id = next(item for item in execution.items if item.related_strategy_ids).related_strategy_ids[0]
    base_strategy = next(item for item in cohort_base.items if item.strategy_id == impacted_strategy_id)
    adjusted_strategy = next(item for item in cohort_adjusted.items if item.strategy_id == impacted_strategy_id)
    assert adjusted_strategy.cohort_rank_score <= base_strategy.cohort_rank_score
    assert any("investigation:" in entry for entry in adjusted_strategy.evidence)


@pytest.mark.constitutional
def test_execution_memory_cli_and_briefings_absorb_report(tmp_path: Path) -> None:
    payload = _payload(stressed=True)
    priority_report = build_oracle_research_priority_report(payload, now_utc=_NOW)
    outcomes = _outcomes(priority_report)

    repo_root = tmp_path
    oracle_root = repo_root / "docs" / "artifacts" / "oracle"
    oracle_root.mkdir(parents=True)

    priority_path = oracle_root / "ORACLE_RESEARCH_PRIORITY_REPORT.json"
    priority_path.write_text(json.dumps(priority_report.model_dump(mode="json"), indent=2, default=str), encoding="utf-8")
    outcome_path = oracle_root / "ORACLE_INVESTIGATION_OUTCOME_INPUT.json"
    outcome_path.write_text(json.dumps(outcomes.model_dump(mode="json"), indent=2, default=str), encoding="utf-8")

    execution_json = oracle_root / "ORACLE_RESEARCH_EXECUTION_MEMORY_REPORT.json"
    execution_md = oracle_root / "ORACLE_RESEARCH_EXECUTION_MEMORY_REPORT.md"
    rc = main([
        "oracle-research-execution-memory",
        str(priority_path),
        "--outcome-input", str(outcome_path),
        "--output", str(execution_json),
        "--markdown-output", str(execution_md),
    ])
    assert rc == 0
    payload_json = json.loads(execution_json.read_text(encoding="utf-8"))
    assert payload_json["schema_version"] == "oracle_research_execution_memory_report/v1"
    assert "ORACLE RESEARCH EXECUTION MEMORY REPORT" in execution_md.read_text(encoding="utf-8")

    strategic = build_oracle_strategic_briefing(payload, research_execution_memory_report=build_oracle_research_execution_memory_report(priority_report, outcomes, now_utc=_NOW), now_utc=_NOW)
    section = next(section for section in strategic.sections if section.section_id == "investigation_outcomes")
    assert section.provenance_refs == ["research_execution_memory:oracle_research_execution_memory_report/v1"]
    assert section.facts

    (oracle_root / "ORACLE_STRATEGIC_BRIEFING_REPORT.json").write_text(json.dumps(strategic.model_dump(mode="json"), indent=2, default=str), encoding="utf-8")
    report = build_oracle_briefing_pack(repo_root=repo_root, search_root=repo_root / "docs" / "artifacts")
    briefing_section = next(section for section in report.sections if section.section_id == "investigation_outcomes")
    assert briefing_section.provenance_refs == ["research_execution_memory:oracle_research_execution_memory_report/v1"]
    assert briefing_section.facts


@pytest.mark.constitutional
def test_execution_memory_prefers_exact_sealed_support_when_present(tmp_path: Path) -> None:
    payload = _payload(stressed=False)
    current_narrative = build_oracle_strategic_narrative_report(payload, now_utc=_NOW)
    sealed_memory = build_oracle_strategic_memory_horizon_report(
        current_narrative,
        sealed_history_reports=[build_oracle_strategic_narrative_report(payload, now_utc=_NOW.replace(hour=max(0, _NOW.hour - 1)))],
        sealed_history_manifest_paths=["docs/artifacts/oracle/STACK_PREV.json"],
        require_sealed_history=True,
        now_utc=_NOW,
    )
    priorities = build_oracle_research_priority_report(payload, strategic_memory_horizon_report=sealed_memory, now_utc=_NOW)
    outcomes = _outcomes(priorities)

    repo_root = tmp_path
    artifacts = repo_root / "docs" / "artifacts" / "oracle"
    artifacts.mkdir(parents=True)
    priority_path = artifacts / "ORACLE_RESEARCH_PRIORITY_REPORT.json"
    priority_path.write_text(json.dumps(priorities.model_dump(mode="json"), indent=2, default=str), encoding="utf-8")
    manifest, _ = build_oracle_strategic_artifact_evidence_bundle(report_path=priority_path, repo_root=repo_root)
    manifest_path = artifacts / "ORACLE_RESEARCH_PRIORITY_EVIDENCE.json"
    manifest_path.write_text(json.dumps(manifest.model_dump(mode="json"), indent=2, default=str), encoding="utf-8")
    verification_path = artifacts / "ORACLE_RESEARCH_PRIORITY_EVIDENCE.verification.json"
    verification_path.write_text(json.dumps({
        "schema_version": "oracle_strategic_artifact_evidence_verification/v1",
        "status": "VERIFIED",
        "integrity_status": "VERIFIED",
        "manifest_path": str(manifest_path),
        "verified_at_utc": _NOW.isoformat().replace("+00:00", "Z"),
        "subject_results": [],
        "verification_notes": [],
    }, indent=2), encoding="utf-8")

    plain = build_oracle_research_execution_memory_report(priorities, outcomes, now_utc=_NOW)
    exact = build_oracle_research_execution_memory_report(
        priorities,
        outcomes,
        research_priority_report_path=priority_path,
        repo_root=repo_root,
        search_root=artifacts,
        now_utc=_NOW,
    )

    plain_strategy = next(item for item in plain.items if item.priority_kind == "STRATEGY_VALIDATION")
    exact_strategy = next(item for item in exact.items if item.priority_kind == "STRATEGY_VALIDATION")

    assert exact.exact_evidence_support_score >= 0.99
    assert exact_strategy.exact_evidence_support_score >= 0.99
    assert any("research_artifact_evidence_manifest=" in entry for entry in exact_strategy.evidence)
    assert "exact sealed supporting subject" in exact_strategy.next_action.lower()
    assert exact.preferred_strategic_backing_classification == "SEALED_STRATEGIC_STACK_BACKED"
