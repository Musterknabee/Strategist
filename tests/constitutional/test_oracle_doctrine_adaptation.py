from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.contracts.oracle import OracleAdvisoryInput, OracleInvestigationOutcomeInput
from strategy_validator.validator.oracle_briefing import build_oracle_briefing_pack
from strategy_validator.validator.oracle_doctrine_adaptation import build_oracle_doctrine_adaptation_report, render_oracle_doctrine_adaptation_markdown
from strategy_validator.validator.oracle_research_execution_memory import build_oracle_research_execution_memory_report
from strategy_validator.validator.oracle_research_planner import build_oracle_research_priority_report
from strategy_validator.validator.oracle_strategic_artifact_evidence import build_oracle_strategic_artifact_evidence_bundle
from strategy_validator.validator.oracle_strategic_briefing import build_oracle_strategic_briefing
from strategy_validator.validator.oracle_strategic_memory_horizon import build_oracle_strategic_memory_horizon_report
from strategy_validator.validator.oracle_strategic_narrative import build_oracle_strategic_narrative_report


_NOW = datetime(2026, 4, 13, 8, 25, tzinfo=timezone.utc)


def _payload(*, stressed: bool = False) -> OracleAdvisoryInput:
    return OracleAdvisoryInput.model_validate(
        {
            "generated_for_utc": "2026-04-13T08:25:00Z",
            "universe_label": "US_EQ_FACTORS",
            "sensors": {
                "semantic": {
                    "inflation_hawkishness_score": 0.72 if stressed else -0.18,
                    "geopolitical_risk_index": 0.82 if stressed else 0.14,
                    "narrative_contradiction_count": 5 if stressed else 1,
                    "tribunal_belief_conflict": 0.88 if stressed else 0.10,
                },
                "microstructure": {
                    "vpin": 0.78 if stressed else 0.18,
                    "order_flow_imbalance": -0.36 if stressed else 0.16,
                    "spread_variance_zscore": 2.1 if stressed else -0.10,
                    "liquidity_thinning_score": 0.81 if stressed else 0.12,
                },
                "macro": {
                    "yield_curve_slope_bps": -42.0 if stressed else 92.0,
                    "high_yield_credit_spread_bps": 480.0 if stressed else 290.0,
                    "equity_bond_correlation": 0.76 if stressed else -0.30,
                    "cross_asset_correlation_stress": 0.90 if stressed else 0.11,
                    "realized_volatility_zscore": 2.2 if stressed else -0.30,
                },
            },
            "strategies": [
                {
                    "strategy_id": "trend-b",
                    "strategy_type": "TREND_FOLLOWING",
                    "prior_edge_confidence": 0.72,
                    "deflated_sharpe_ratio": 0.94,
                    "cpcv_lower_bound": 0.30,
                    "realized_live_sharpe": -0.14 if stressed else 0.62,
                    "recent_win_rate": 0.35 if stressed else 0.58,
                    "drawdown_fraction": 0.18 if stressed else 0.04,
                    "expected_regimes": ["RISK_ON_LOW_VOL", "TRANSITION"],
                },
                {
                    "strategy_id": "carry-a",
                    "strategy_type": "CARRY",
                    "prior_edge_confidence": 0.62,
                    "deflated_sharpe_ratio": 0.74,
                    "cpcv_lower_bound": 0.18,
                    "realized_live_sharpe": -0.06 if stressed else 0.40,
                    "recent_win_rate": 0.42 if stressed else 0.55,
                    "drawdown_fraction": 0.12 if stressed else 0.03,
                    "expected_regimes": ["RISK_ON_LOW_VOL"],
                },
            ],
        }
    )


@pytest.mark.constitutional
def test_doctrine_adaptation_builder_freezes_under_stress() -> None:
    report = build_oracle_doctrine_adaptation_report(_payload(stressed=True), now_utc=_NOW)

    assert report.schema_version == "oracle_doctrine_adaptation_report/v1"
    assert report.items
    assert report.top_review_clause_ids
    assert any(item.adaptation_state in {"ADAPT", "FREEZE"} for item in report.items)
    assert report.freeze_recommended or report.items[0].adaptation_state in {"ADAPT", "FREEZE"}


@pytest.mark.constitutional
def test_strategic_briefing_includes_doctrine_adaptation_section() -> None:
    report = build_oracle_strategic_briefing(_payload(stressed=True), now_utc=_NOW)

    section = next(section for section in report.sections if section.section_id == "doctrine_adaptation")
    assert section.facts
    assert section.provenance_refs == ["doctrine_adaptation:oracle_doctrine_adaptation_report/v1"]
    assert section.status in {"MONITOR", "REVIEW", "ADAPT", "FREEZE"}


@pytest.mark.constitutional
def test_doctrine_adaptation_cli_emits_report_and_markdown(tmp_path: Path) -> None:
    payload = _payload(stressed=True).model_dump(mode="json")
    input_path = tmp_path / "ORACLE_ADVISORY_INPUT.json"
    input_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    report_json = tmp_path / "ORACLE_DOCTRINE_ADAPTATION_REPORT.json"
    report_md = tmp_path / "ORACLE_DOCTRINE_ADAPTATION_REPORT.md"
    rc = main([
        "oracle-doctrine-adaptation",
        str(input_path),
        "--output", str(report_json),
        "--markdown-output", str(report_md),
    ])
    assert rc == 0
    artifact = json.loads(report_json.read_text(encoding="utf-8"))
    assert artifact["schema_version"] == "oracle_doctrine_adaptation_report/v1"
    assert artifact["items"]
    assert "ORACLE DOCTRINE ADAPTATION REPORT" in report_md.read_text(encoding="utf-8")


@pytest.mark.constitutional
def test_briefing_pack_absorbs_doctrine_adaptation_report(tmp_path: Path) -> None:
    repo_root = tmp_path
    oracle_root = repo_root / "docs" / "artifacts" / "oracle"
    oracle_root.mkdir(parents=True)

    adaptation = build_oracle_doctrine_adaptation_report(_payload(stressed=True), now_utc=_NOW)
    strategic = build_oracle_strategic_briefing(_payload(stressed=True), now_utc=_NOW)

    (oracle_root / "ORACLE_DOCTRINE_ADAPTATION_REPORT.json").write_text(
        json.dumps(adaptation.model_dump(mode="json"), indent=2, default=str),
        encoding="utf-8",
    )
    (oracle_root / "ORACLE_STRATEGIC_BRIEFING_REPORT.json").write_text(
        json.dumps(strategic.model_dump(mode="json"), indent=2, default=str),
        encoding="utf-8",
    )

    report = build_oracle_briefing_pack(repo_root=repo_root, search_root=repo_root / "docs" / "artifacts")
    section = next(section for section in report.sections if section.section_id == "doctrine_adaptation")
    assert section.status in {"MONITOR", "REVIEW", "ADAPT", "FREEZE"}
    assert section.provenance_refs == ["doctrine_adaptation:oracle_doctrine_adaptation_report/v1"]
    assert section.facts


@pytest.mark.constitutional
def test_doctrine_adaptation_report_surfaces_preferred_strategic_backing() -> None:
    current = build_oracle_strategic_narrative_report(_payload(stressed=True), now_utc=_NOW)
    prior = build_oracle_strategic_narrative_report(_payload(stressed=False), now_utc=_NOW.replace(hour=7))
    memory = build_oracle_strategic_memory_horizon_report(
        current,
        sealed_history_reports=[prior],
        sealed_history_manifest_paths=["docs/artifacts/oracle/STACK_07.json"],
        require_sealed_history=True,
        now_utc=_NOW,
    )
    report = build_oracle_doctrine_adaptation_report(_payload(stressed=True), strategic_memory_horizon_report=memory, now_utc=_NOW)
    markdown = render_oracle_doctrine_adaptation_markdown(report)

    assert report.preferred_strategic_backing_source == "strategic_stack_manifest"
    assert report.preferred_strategic_backing_classification == "SEALED_STRATEGIC_STACK_BACKED"
    assert report.history_integrity_status == "SEALED_HISTORY"
    assert "Preferred strategic backing source: strategic_stack_manifest" in markdown


def _outcomes(priority_report):
    strategy_priority = next(item for item in priority_report.items if item.priority_kind == "STRATEGY_VALIDATION")
    return OracleInvestigationOutcomeInput.model_validate(
        {
            "generated_at_utc": _NOW.isoformat().replace("+00:00", "Z"),
            "universe_label": priority_report.universe_label,
            "items": [
                {
                    "outcome_id": "outcome-regime-support",
                    "priority_id": strategy_priority.priority_id,
                    "execution_state": "COMPLETED",
                    "outcome_disposition": "CONFIRMED",
                    "related_strategy_ids": strategy_priority.related_strategy_ids,
                    "doctrine_clause_ids": ["doctrine:regime-assumptions"],
                    "thesis_effect": "STRENGTHENS",
                    "doctrine_effect": "RELIEVES",
                    "cohort_effect": "PROMOTES",
                    "confidence_impact": 0.24,
                    "urgency_impact": -0.16,
                    "finding_summary": "A sealed regime-validation outcome relieved the doctrine assumption under direct replayable evidence.",
                    "evidence": ["regime_support_confirmed"],
                    "next_action": "Relax the clause freeze and compare the next cycle before broadening doctrine changes.",
                }
            ],
        }
    )


@pytest.mark.constitutional
def test_doctrine_adaptation_prefers_exact_execution_support_when_present(tmp_path: Path) -> None:
    payload = _payload(stressed=False)
    current = build_oracle_strategic_narrative_report(payload, now_utc=_NOW)
    sealed_memory = build_oracle_strategic_memory_horizon_report(
        current,
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

    plain_execution = build_oracle_research_execution_memory_report(priorities, outcomes, now_utc=_NOW)
    exact_execution = build_oracle_research_execution_memory_report(
        priorities,
        outcomes,
        research_priority_report_path=priority_path,
        repo_root=repo_root,
        search_root=artifacts,
        now_utc=_NOW,
    )
    plain = build_oracle_doctrine_adaptation_report(payload, execution_memory_report=plain_execution, now_utc=_NOW)
    exact = build_oracle_doctrine_adaptation_report(payload, execution_memory_report=exact_execution, strategic_memory_horizon_report=sealed_memory, now_utc=_NOW)
    exact_markdown = render_oracle_doctrine_adaptation_markdown(exact)

    plain_clause = next(item for item in plain.items if item.clause_id == "doctrine:regime-assumptions")
    exact_clause = next(item for item in exact.items if item.clause_id == "doctrine:regime-assumptions")

    assert exact.exact_evidence_support_score >= 0.99
    assert exact_clause.exact_evidence_support_score >= 0.99
    assert exact_clause.stress_score < plain_clause.stress_score
    assert exact_clause.review_priority_score < plain_clause.review_priority_score
    assert any("exact_execution_support=" in entry for entry in exact_clause.pressure_sources)
    assert any("exact sealed execution" in action.lower() or "exact sealed" in action.lower() for action in exact.operator_actions)
    assert "Exact evidence support score" in exact_markdown


@pytest.mark.constitutional
def test_doctrine_adaptation_cli_absorbs_execution_memory_report(tmp_path: Path) -> None:
    payload = _payload(stressed=False)
    priorities = build_oracle_research_priority_report(payload, now_utc=_NOW)
    outcomes = _outcomes(priorities)
    execution = build_oracle_research_execution_memory_report(priorities, outcomes, now_utc=_NOW)

    input_path = tmp_path / "ORACLE_ADVISORY_INPUT.json"
    input_path.write_text(json.dumps(payload.model_dump(mode="json"), indent=2, default=str), encoding="utf-8")
    execution_path = tmp_path / "ORACLE_RESEARCH_EXECUTION_MEMORY_REPORT.json"
    execution_path.write_text(json.dumps(execution.model_dump(mode="json"), indent=2, default=str), encoding="utf-8")
    report_json = tmp_path / "ORACLE_DOCTRINE_ADAPTATION_REPORT.json"

    rc = main([
        "oracle-doctrine-adaptation",
        str(input_path),
        "--research-execution-memory-report", str(execution_path),
        "--output", str(report_json),
    ])
    assert rc == 0
    artifact = json.loads(report_json.read_text(encoding="utf-8"))
    clause = next(item for item in artifact["items"] if item["clause_id"] == "doctrine:regime-assumptions")
    assert any("investigation:" in entry for entry in clause["pressure_sources"])
