from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.contracts.oracle import OracleAdvisoryInput, OracleInvestigationOutcomeInput
from strategy_validator.validator.oracle_briefing import build_oracle_briefing_pack
from strategy_validator.validator.oracle_research_execution_memory import build_oracle_research_execution_memory_report
from strategy_validator.validator.oracle_research_planner import build_oracle_research_priority_report
from strategy_validator.validator.oracle_strategic_briefing import build_oracle_strategic_briefing
from strategy_validator.validator.oracle_strategic_memory_horizon import build_oracle_strategic_memory_horizon_report
from strategy_validator.validator.oracle_strategic_narrative import build_oracle_strategic_narrative_report
from strategy_validator.validator.oracle_thesis_graph import build_oracle_thesis_graph_report


_NOW = datetime(2026, 4, 14, 7, 30, tzinfo=timezone.utc)


def _payload(*, stressed: bool = False) -> OracleAdvisoryInput:
    return OracleAdvisoryInput.model_validate(
        {
            "generated_for_utc": "2026-04-14T07:30:00Z",
            "universe_label": "US_EQ_FACTORS",
            "sensors": {
                "semantic": {
                    "inflation_hawkishness_score": 0.72 if stressed else -0.16,
                    "geopolitical_risk_index": 0.80 if stressed else 0.18,
                    "narrative_contradiction_count": 5 if stressed else 1,
                    "tribunal_belief_conflict": 0.87 if stressed else 0.12,
                },
                "microstructure": {
                    "vpin": 0.77 if stressed else 0.22,
                    "order_flow_imbalance": -0.30 if stressed else 0.14,
                    "spread_variance_zscore": 1.8 if stressed else -0.12,
                    "liquidity_thinning_score": 0.79 if stressed else 0.12,
                },
                "macro": {
                    "yield_curve_slope_bps": -36.0 if stressed else 90.0,
                    "high_yield_credit_spread_bps": 475.0 if stressed else 282.0,
                    "equity_bond_correlation": 0.74 if stressed else -0.28,
                    "cross_asset_correlation_stress": 0.91 if stressed else 0.14,
                    "realized_volatility_zscore": 2.0 if stressed else -0.24,
                },
            },
            "strategies": [
                {
                    "strategy_id": "trend-b",
                    "strategy_type": "TREND_FOLLOWING",
                    "prior_edge_confidence": 0.74,
                    "deflated_sharpe_ratio": 0.95,
                    "cpcv_lower_bound": 0.31,
                    "realized_live_sharpe": -0.14 if stressed else 0.58,
                    "recent_win_rate": 0.37 if stressed else 0.57,
                    "drawdown_fraction": 0.19 if stressed else 0.04,
                    "expected_regimes": ["RISK_ON_LOW_VOL", "TRANSITION"],
                },
                {
                    "strategy_id": "carry-a",
                    "strategy_type": "CARRY",
                    "prior_edge_confidence": 0.62,
                    "deflated_sharpe_ratio": 0.74,
                    "cpcv_lower_bound": 0.18,
                    "realized_live_sharpe": -0.03 if stressed else 0.40,
                    "recent_win_rate": 0.45 if stressed else 0.55,
                    "drawdown_fraction": 0.11 if stressed else 0.03,
                    "expected_regimes": ["RISK_ON_LOW_VOL"],
                },
            ],
        }
    )


def _outcomes(priority_report) -> OracleInvestigationOutcomeInput:
    strategy_priority = next(item for item in priority_report.items if item.related_strategy_ids)
    doctrine_priority = next(item for item in priority_report.items if item.priority_kind == "DOCTRINE_REVIEW")
    thesis_priority = next(item for item in priority_report.items if item.priority_kind == "THESIS_REVIEW")
    return OracleInvestigationOutcomeInput.model_validate(
        {
            "generated_at_utc": "2026-04-14T07:35:00Z",
            "universe_label": priority_report.universe_label,
            "items": [
                {
                    "outcome_id": "outcome-thesis-graph-1",
                    "priority_id": thesis_priority.priority_id,
                    "execution_state": "COMPLETED",
                    "outcome_disposition": "ESCALATED",
                    "thesis_ids": ["doctrine:coherence"],
                    "doctrine_clause_ids": ["doctrine:regime-assumptions"],
                    "thesis_effect": "WEAKENS",
                    "doctrine_effect": "PRESSURES",
                    "cohort_effect": "WATCH",
                    "confidence_impact": -0.32,
                    "urgency_impact": 0.26,
                    "finding_summary": "Doctrine coherence weakened across the stressed investigation window.",
                    "evidence": ["doctrine_conflict", "regime_mismatch"],
                    "next_action": "Escalate doctrine review before broadening conviction.",
                },
                {
                    "outcome_id": "outcome-thesis-graph-2",
                    "priority_id": strategy_priority.priority_id,
                    "execution_state": "COMPLETED",
                    "outcome_disposition": "REFUTED",
                    "related_strategy_ids": strategy_priority.related_strategy_ids,
                    "thesis_ids": [f"strategy:{strategy_priority.related_strategy_ids[0]}"],
                    "doctrine_clause_ids": ["doctrine:strategy-alignment"],
                    "thesis_effect": "WEAKENS",
                    "doctrine_effect": "FREEZE_CANDIDATE",
                    "cohort_effect": "DEMOTES",
                    "confidence_impact": -0.48,
                    "urgency_impact": 0.33,
                    "finding_summary": "The stressed downside probe refuted the expected resilience of the lead cohort.",
                    "evidence": ["downside_floor_failed", "transition_pressure"],
                    "next_action": "Demote the pressured strategy and freeze doctrine assumptions that still treat it as resilient.",
                },
                {
                    "outcome_id": "outcome-thesis-graph-3",
                    "priority_id": doctrine_priority.priority_id,
                    "execution_state": "IN_PROGRESS",
                    "outcome_disposition": "MIXED",
                    "doctrine_clause_ids": ["doctrine:research-expansion"],
                    "thesis_effect": "REVIEW_REQUIRED",
                    "doctrine_effect": "PRESSURES",
                    "cohort_effect": "NO_CHANGE",
                    "confidence_impact": -0.08,
                    "urgency_impact": 0.18,
                    "finding_summary": "Expansion review is still open under stressed macro conditions.",
                    "evidence": ["need_more_evidence"],
                    "next_action": "Keep the expansion clause under review through the next cycle.",
                },
            ],
        }
    )


@pytest.mark.constitutional
def test_thesis_graph_builds_nodes_edges_and_cascade_focus() -> None:
    payload = _payload(stressed=True)
    priorities = build_oracle_research_priority_report(payload, now_utc=_NOW)
    execution_memory = build_oracle_research_execution_memory_report(priorities, _outcomes(priorities))
    report = build_oracle_thesis_graph_report(payload, research_priority_report=priorities, research_execution_memory_report=execution_memory, now_utc=_NOW)

    assert report.nodes
    assert report.edges
    assert report.highest_cascade_risk_node_ids
    assert any(node.node_kind == "THESIS" for node in report.nodes)
    assert any(edge.relation_kind in {"PRESSURES", "WEAKENS", "DEMOTES"} for edge in report.edges)


@pytest.mark.constitutional
def test_cli_emits_thesis_graph_report_and_markdown(tmp_path: Path) -> None:
    payload = _payload(stressed=True).model_dump(mode="json")
    input_path = tmp_path / "ORACLE_ADVISORY_INPUT.json"
    input_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    graph_json = tmp_path / "ORACLE_THESIS_GRAPH_REPORT.json"
    graph_md = tmp_path / "ORACLE_THESIS_GRAPH_REPORT.md"
    rc = main([
        "oracle-thesis-graph",
        str(input_path),
        "--output", str(graph_json),
        "--markdown-output", str(graph_md),
    ])
    assert rc == 0
    graph_report = json.loads(graph_json.read_text(encoding="utf-8"))
    assert graph_report["schema_version"] == "oracle_thesis_graph_report/v1"
    assert graph_report["nodes"]
    assert "ORACLE THESIS GRAPH REPORT" in graph_md.read_text(encoding="utf-8")


@pytest.mark.constitutional
def test_strategic_briefing_includes_thesis_graph_section() -> None:
    payload = _payload(stressed=True)
    priorities = build_oracle_research_priority_report(payload, now_utc=_NOW)
    execution_memory = build_oracle_research_execution_memory_report(priorities, _outcomes(priorities))
    report = build_oracle_strategic_briefing(payload, research_execution_memory_report=execution_memory, now_utc=_NOW)

    section = next(section for section in report.sections if section.section_id == "thesis_graph")
    assert section.provenance_refs == ["thesis_graph:oracle_thesis_graph_report/v1"]
    assert section.facts


@pytest.mark.constitutional
def test_briefing_pack_absorbs_thesis_graph_when_present(tmp_path: Path) -> None:
    repo_root = tmp_path
    oracle_root = repo_root / "docs" / "artifacts" / "oracle"
    oracle_root.mkdir(parents=True)

    payload = _payload(stressed=True)
    priorities = build_oracle_research_priority_report(payload, now_utc=_NOW)
    execution_memory = build_oracle_research_execution_memory_report(priorities, _outcomes(priorities))
    graph_report = build_oracle_thesis_graph_report(payload, research_priority_report=priorities, research_execution_memory_report=execution_memory, now_utc=_NOW)

    (oracle_root / "ORACLE_THESIS_GRAPH_REPORT.json").write_text(
        json.dumps(graph_report.model_dump(mode="json"), indent=2, default=str),
        encoding="utf-8",
    )
    report = build_oracle_briefing_pack(repo_root=repo_root, search_root=repo_root / "docs" / "artifacts")
    section = next(section for section in report.sections if section.section_id == "thesis_graph")
    assert section.provenance_refs == ["thesis_graph:oracle_thesis_graph_report/v1"]
    assert section.facts

from strategy_validator.validator.oracle_doctrine_adaptation import build_oracle_doctrine_adaptation_report
from strategy_validator.validator.oracle_strategic_artifact_evidence import build_oracle_strategic_artifact_evidence_bundle
from strategy_validator.validator.oracle_thesis_memory import build_oracle_thesis_memory_report


@pytest.mark.constitutional
def test_thesis_graph_prefers_exact_sealed_support_when_present(tmp_path: Path) -> None:
    payload = _payload(stressed=False)
    current_narrative = build_oracle_strategic_narrative_report(payload, now_utc=_NOW)
    sealed_history = build_oracle_strategic_memory_horizon_report(
        current_narrative,
        sealed_history_reports=[build_oracle_strategic_narrative_report(payload, now_utc=_NOW.replace(hour=6))],
        sealed_history_manifest_paths=["docs/artifacts/oracle/STACK_06.json"],
        require_sealed_history=True,
        now_utc=_NOW,
    )
    thesis = build_oracle_thesis_memory_report(payload, now_utc=_NOW)
    doctrine = build_oracle_doctrine_adaptation_report(payload, thesis_memory_report=thesis, strategic_memory_horizon_report=sealed_history, now_utc=_NOW)
    priorities = build_oracle_research_priority_report(payload, thesis_memory_report=thesis, doctrine_adaptation_report=doctrine, strategic_memory_horizon_report=sealed_history, now_utc=_NOW)

    repo_root = tmp_path
    artifacts_root = repo_root / "docs" / "artifacts" / "oracle"
    artifacts_root.mkdir(parents=True)
    doctrine_path = artifacts_root / "ORACLE_DOCTRINE_ADAPTATION_REPORT.json"
    doctrine_path.write_text(json.dumps(doctrine.model_dump(mode="json"), indent=2, default=str), encoding="utf-8")
    priorities_path = artifacts_root / "ORACLE_RESEARCH_PRIORITY_REPORT.json"
    priorities_path.write_text(json.dumps(priorities.model_dump(mode="json"), indent=2, default=str), encoding="utf-8")

    for idx, report_path in enumerate((doctrine_path, priorities_path), start=1):
        manifest, _ = build_oracle_strategic_artifact_evidence_bundle(report_path=report_path, repo_root=repo_root)
        manifest_path = artifacts_root / f"ORACLE_STRATEGIC_ARTIFACT_EVIDENCE_GRAPH_{idx}.json"
        manifest_path.write_text(json.dumps(manifest.model_dump(mode="json"), indent=2, default=str), encoding="utf-8")
        (artifacts_root / f"ORACLE_STRATEGIC_ARTIFACT_EVIDENCE_GRAPH_{idx}.verification.json").write_text(json.dumps({
            "schema_version": "oracle_strategic_artifact_evidence_verification/v1",
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

    plain = build_oracle_thesis_graph_report(payload, thesis_memory_report=thesis, doctrine_adaptation_report=doctrine, research_priority_report=priorities, now_utc=_NOW)
    supported = build_oracle_thesis_graph_report(
        payload,
        thesis_memory_report=thesis,
        doctrine_adaptation_report=doctrine,
        research_priority_report=priorities,
        doctrine_adaptation_report_path=doctrine_path,
        research_priority_report_path=priorities_path,
        repo_root=repo_root,
        search_root=repo_root / "docs" / "artifacts",
        now_utc=_NOW,
    )

    plain_doctrine_node = next(node for node in plain.nodes if node.node_id == "doctrine:regime-assumptions")
    supported_doctrine_node = next(node for node in supported.nodes if node.node_id == "doctrine:regime-assumptions")
    assert supported.exact_evidence_support_score >= 0.99
    assert supported_doctrine_node.exact_evidence_support_score >= 0.99
    assert supported_doctrine_node.cascade_risk_score < plain_doctrine_node.cascade_risk_score
    assert any(fact.startswith("graph_support_artifact_evidence_manifest=") for fact in supported_doctrine_node.evidence)
