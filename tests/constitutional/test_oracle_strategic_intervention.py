from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.contracts.oracle import OracleAdvisoryInput
from strategy_validator.validator.oracle_briefing import build_oracle_briefing_pack
from strategy_validator.validator.oracle_contradiction_resolution import build_oracle_contradiction_resolution_report
from strategy_validator.validator.oracle_strategic_briefing import build_oracle_strategic_briefing
from strategy_validator.validator.oracle_intervention_simulator import build_oracle_strategic_intervention_report, render_oracle_strategic_intervention_markdown
from strategy_validator.validator.oracle_strategic_memory_horizon import build_oracle_strategic_memory_horizon_report
from strategy_validator.validator.oracle_strategic_narrative import build_oracle_strategic_narrative_report
from strategy_validator.validator.oracle_doctrine_adaptation import build_oracle_doctrine_adaptation_report
from strategy_validator.validator.oracle_research_planner import build_oracle_research_priority_report
from strategy_validator.validator.oracle_strategic_artifact_evidence import build_oracle_strategic_artifact_evidence_bundle


_NOW = datetime(2026, 4, 14, 8, 0, tzinfo=timezone.utc)


def _payload(*, stressed: bool = False) -> OracleAdvisoryInput:
    return OracleAdvisoryInput.model_validate(
        {
            "generated_for_utc": "2026-04-14T08:00:00Z",
            "universe_label": "US_EQ_FACTORS",
            "sensors": {
                "semantic": {
                    "inflation_hawkishness_score": 0.78 if stressed else -0.20,
                    "geopolitical_risk_index": 0.88 if stressed else 0.14,
                    "narrative_contradiction_count": 8 if stressed else 1,
                    "tribunal_belief_conflict": 0.92 if stressed else 0.11,
                },
                "microstructure": {
                    "vpin": 0.86 if stressed else 0.18,
                    "order_flow_imbalance": -0.48 if stressed else 0.26,
                    "spread_variance_zscore": 2.5 if stressed else -0.36,
                    "liquidity_thinning_score": 0.90 if stressed else 0.10,
                },
                "macro": {
                    "yield_curve_slope_bps": -58.0 if stressed else 112.0,
                    "high_yield_credit_spread_bps": 548.0 if stressed else 248.0,
                    "equity_bond_correlation": 0.86 if stressed else -0.38,
                    "cross_asset_correlation_stress": 0.97 if stressed else 0.15,
                    "realized_volatility_zscore": 2.7 if stressed else -0.28,
                },
            },
            "strategies": [
                {
                    "strategy_id": "trend-b",
                    "strategy_type": "TREND_FOLLOWING",
                    "prior_edge_confidence": 0.73,
                    "deflated_sharpe_ratio": 0.91,
                    "cpcv_lower_bound": 0.28,
                    "realized_live_sharpe": -0.34 if stressed else 0.66,
                    "recent_win_rate": 0.31 if stressed else 0.64,
                    "drawdown_fraction": 0.26 if stressed else 0.05,
                    "expected_regimes": ["RISK_ON_LOW_VOL", "TRANSITION"],
                },
                {
                    "strategy_id": "carry-a",
                    "strategy_type": "CARRY",
                    "prior_edge_confidence": 0.66,
                    "deflated_sharpe_ratio": 0.80,
                    "cpcv_lower_bound": 0.22,
                    "realized_live_sharpe": -0.11 if stressed else 0.46,
                    "recent_win_rate": 0.40 if stressed else 0.58,
                    "drawdown_fraction": 0.15 if stressed else 0.03,
                    "expected_regimes": ["RISK_ON_LOW_VOL"],
                },
            ],
        }
    )


def _narrative(*, stressed: bool, at_hour: int):
    return build_oracle_strategic_narrative_report(_payload(stressed=stressed), now_utc=_NOW.replace(hour=at_hour))


@pytest.mark.constitutional
def test_intervention_report_ranks_highest_impact_downstream_relief() -> None:
    current = _narrative(stressed=True, at_hour=8)
    history = [_narrative(stressed=False, at_hour=6), _narrative(stressed=False, at_hour=7)]
    memory = build_oracle_strategic_memory_horizon_report(current, history_reports=history, now_utc=_NOW)
    contradiction = build_oracle_contradiction_resolution_report(
        _payload(stressed=True),
        strategic_narrative_report=current,
        strategic_memory_horizon_report=memory,
        now_utc=_NOW,
    )

    report = build_oracle_strategic_intervention_report(
        _payload(stressed=True),
        strategic_narrative_report=current,
        strategic_memory_horizon_report=memory,
        contradiction_resolution_report=contradiction,
        now_utc=_NOW,
    )

    assert report.schema_version == "oracle_strategic_intervention_report/v1"
    assert report.items
    assert report.highest_impact_intervention_id is not None
    assert report.items[0].projected_conviction_gain_score >= report.items[-1].projected_conviction_gain_score or report.items[0].projected_fragility_reduction_score >= report.items[-1].projected_fragility_reduction_score
    assert report.items[0].projected_conviction_state in {"HIGH_CONVICTION", "GUARDED_CONVICTION", "FRAGILE_CONVICTION", "BROKEN_CONVICTION"}
    assert report.items[0].projected_queue_pressure_relief_score > 0.0


@pytest.mark.constitutional
def test_cli_emits_intervention_report_and_markdown(tmp_path: Path) -> None:
    input_path = tmp_path / "ORACLE_ADVISORY_INPUT.json"
    input_path.write_text(json.dumps(_payload(stressed=True).model_dump(mode="json"), indent=2, default=str), encoding="utf-8")

    report_json = tmp_path / "ORACLE_STRATEGIC_INTERVENTION_REPORT.json"
    report_md = tmp_path / "ORACLE_STRATEGIC_INTERVENTION_REPORT.md"
    rc = main([
        "oracle-strategic-intervention",
        str(input_path),
        "--output", str(report_json),
        "--markdown-output", str(report_md),
    ])
    assert rc == 0
    payload = json.loads(report_json.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "oracle_strategic_intervention_report/v1"
    assert "ORACLE STRATEGIC INTERVENTION REPORT" in report_md.read_text(encoding="utf-8")


@pytest.mark.constitutional
def test_strategic_briefing_includes_intervention_simulation_section() -> None:
    current = _narrative(stressed=True, at_hour=8)
    memory = build_oracle_strategic_memory_horizon_report(current, history_reports=[_narrative(stressed=False, at_hour=6)], now_utc=_NOW)
    contradiction = build_oracle_contradiction_resolution_report(
        _payload(stressed=True),
        strategic_narrative_report=current,
        strategic_memory_horizon_report=memory,
        now_utc=_NOW,
    )
    intervention = build_oracle_strategic_intervention_report(
        _payload(stressed=True),
        strategic_narrative_report=current,
        strategic_memory_horizon_report=memory,
        contradiction_resolution_report=contradiction,
        now_utc=_NOW,
    )

    report = build_oracle_strategic_briefing(
        _payload(stressed=True),
        strategic_narrative_report=current,
        strategic_memory_horizon_report=memory,
        contradiction_resolution_report=contradiction,
        intervention_simulation_report=intervention,
        now_utc=_NOW,
    )

    section = next(section for section in report.sections if section.section_id == "intervention_simulation")
    assert section.provenance_refs == ["intervention_simulation:oracle_strategic_intervention_report/v1"]
    assert section.facts


@pytest.mark.constitutional
def test_briefing_pack_absorbs_intervention_report_when_present(tmp_path: Path) -> None:
    repo_root = tmp_path
    oracle_root = repo_root / "docs" / "artifacts" / "oracle"
    oracle_root.mkdir(parents=True)

    current = _narrative(stressed=True, at_hour=8)
    memory = build_oracle_strategic_memory_horizon_report(current, history_reports=[_narrative(stressed=False, at_hour=6)], now_utc=_NOW)
    contradiction = build_oracle_contradiction_resolution_report(
        _payload(stressed=True),
        strategic_narrative_report=current,
        strategic_memory_horizon_report=memory,
        now_utc=_NOW,
    )
    intervention = build_oracle_strategic_intervention_report(
        _payload(stressed=True),
        strategic_narrative_report=current,
        strategic_memory_horizon_report=memory,
        contradiction_resolution_report=contradiction,
        now_utc=_NOW,
    )

    (oracle_root / "ORACLE_STRATEGIC_INTERVENTION_REPORT.json").write_text(
        json.dumps(intervention.model_dump(mode="json"), indent=2, default=str),
        encoding="utf-8",
    )

    report = build_oracle_briefing_pack(repo_root=repo_root, search_root=repo_root / "docs" / "artifacts")
    section = next(section for section in report.sections if section.section_id == "intervention_simulation")
    assert section.provenance_refs == ["intervention_simulation:oracle_strategic_intervention_report/v1"]
    assert section.facts


@pytest.mark.constitutional
def test_intervention_integrity_penalty_relaxes_when_history_is_sealed() -> None:
    current = _narrative(stressed=True, at_hour=8)
    prior = _narrative(stressed=False, at_hour=6)
    current_only_memory = build_oracle_strategic_memory_horizon_report(current, history_reports=[], now_utc=_NOW)
    sealed_memory = build_oracle_strategic_memory_horizon_report(current, history_reports=[prior], now_utc=_NOW)

    current_only = build_oracle_strategic_intervention_report(
        _payload(stressed=True),
        strategic_narrative_report=current,
        strategic_memory_horizon_report=current_only_memory,
        now_utc=_NOW,
    )
    sealed = build_oracle_strategic_intervention_report(
        _payload(stressed=True),
        strategic_narrative_report=current,
        strategic_memory_horizon_report=sealed_memory,
        now_utc=_NOW,
    )

    assert current_only.history_integrity_status == "CURRENT_ONLY"
    assert sealed.history_integrity_status == "MIXED_HISTORY"
    assert current_only.integrity_penalty_score > sealed.integrity_penalty_score
    assert any(item.integrity_penalty_score > 0.0 for item in current_only.items)
    assert max(item.integrity_penalty_score for item in sealed.items) < max(item.integrity_penalty_score for item in current_only.items)


@pytest.mark.constitutional
def test_intervention_report_surfaces_preferred_strategic_backing() -> None:
    current = _narrative(stressed=True, at_hour=8)
    sealed_memory = build_oracle_strategic_memory_horizon_report(
        current,
        sealed_history_reports=[_narrative(stressed=False, at_hour=6)],
        sealed_history_manifest_paths=["docs/artifacts/oracle/STACK_06.json"],
        require_sealed_history=True,
        now_utc=_NOW,
    )
    report = build_oracle_strategic_intervention_report(
        _payload(stressed=True),
        strategic_narrative_report=current,
        strategic_memory_horizon_report=sealed_memory,
        now_utc=_NOW,
    )
    markdown = render_oracle_strategic_intervention_markdown(report)

    assert report.preferred_strategic_backing_source == "strategic_stack_manifest"
    assert report.preferred_strategic_backing_classification == "SEALED_STRATEGIC_STACK_BACKED"
    assert "Preferred strategic backing source: strategic_stack_manifest" in markdown


@pytest.mark.constitutional
def test_intervention_prefers_exact_sealed_subjects_for_doctrine_and_consensus(tmp_path: Path) -> None:
    repo_root = tmp_path
    artifacts_root = repo_root / "docs" / "artifacts" / "oracle"
    artifacts_root.mkdir(parents=True)

    current = _narrative(stressed=True, at_hour=8)
    sealed_memory = build_oracle_strategic_memory_horizon_report(
        current,
        sealed_history_reports=[_narrative(stressed=False, at_hour=6)],
        sealed_history_manifest_paths=["docs/artifacts/oracle/STACK_06.json"],
        require_sealed_history=True,
        now_utc=_NOW,
    )
    doctrine = build_oracle_doctrine_adaptation_report(_payload(stressed=True), strategic_memory_horizon_report=sealed_memory, now_utc=_NOW)
    priorities = build_oracle_research_priority_report(_payload(stressed=True), strategic_memory_horizon_report=sealed_memory, now_utc=_NOW)
    doctrine_path = artifacts_root / "ORACLE_DOCTRINE_ADAPTATION_REPORT.json"
    research_path = artifacts_root / "ORACLE_RESEARCH_PRIORITY_REPORT.json"
    doctrine_path.write_text(json.dumps(doctrine.model_dump(mode="json"), indent=2), encoding="utf-8")
    research_path.write_text(json.dumps(priorities.model_dump(mode="json"), indent=2), encoding="utf-8")

    for path in (doctrine_path, research_path):
        manifest, _ = build_oracle_strategic_artifact_evidence_bundle(report_path=path, repo_root=repo_root)
        out = path.with_name(path.stem + "_EVIDENCE.json")
        out.write_text(json.dumps(manifest.model_dump(mode="json"), indent=2), encoding="utf-8")
        verification = {
            "schema_version": "oracle_strategic_artifact_evidence_verification/v1",
            "status": "VERIFIED",
            "manifest_path": str(out),
            "verified_subject_count": len(manifest.subjects),
            "missing_subject_count": 0,
            "signature_verified": False,
            "subject_results": [],
            "generated_at_utc": _NOW.isoformat().replace("+00:00", "Z"),
        }
        out.with_name(out.stem + ".verification.json").write_text(json.dumps(verification, indent=2), encoding="utf-8")

    report = build_oracle_strategic_intervention_report(
        _payload(stressed=True),
        doctrine_adaptation_report=doctrine,
        research_priority_report=priorities,
        strategic_narrative_report=current,
        strategic_memory_horizon_report=sealed_memory,
        doctrine_adaptation_report_path=doctrine_path,
        research_priority_report_path=research_path,
        repo_root=repo_root,
        search_root=repo_root / "docs" / "artifacts",
        now_utc=_NOW,
    )

    assert report.exact_evidence_support_score >= 0.85
    assert any(item.intervention_kind in {"DOCTRINE_RELIEF", "VALIDATE_CONSENSUS"} and item.exact_evidence_support_score >= 0.85 for item in report.items)
    assert any("exact sealed subject" in item.recommended_intervention.lower() for item in report.items if item.intervention_kind in {"DOCTRINE_RELIEF", "VALIDATE_CONSENSUS"})


@pytest.mark.constitutional
def test_intervention_summary_surfaces_exact_cadence_driver(tmp_path: Path) -> None:
    repo_root = tmp_path
    artifacts_root = repo_root / "docs" / "artifacts" / "oracle"
    artifacts_root.mkdir(parents=True)

    payload = _payload(stressed=True)
    sealed_memory = build_oracle_strategic_memory_horizon_report(
        _narrative(stressed=True, at_hour=9),
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
    doctrine_path = artifacts_root / "ORACLE_DOCTRINE_ADAPTATION_REPORT.json"
    doctrine_path.write_text(json.dumps(doctrine.model_dump(mode="json"), indent=2, default=str), encoding="utf-8")

    report = build_oracle_strategic_intervention_report(
        payload,
        doctrine_adaptation_report=doctrine,
        strategic_memory_horizon_report=sealed_memory,
        doctrine_adaptation_report_path=doctrine_path,
        repo_root=repo_root,
        search_root=artifacts_root,
        now_utc=_NOW,
    )
    markdown = render_oracle_strategic_intervention_markdown(report)

    assert report.exact_cadence_signal_classification == "EXACT_CONFIRMED_PRESSURE"
    assert report.exact_feedback_confirmation_count >= 1
    assert "cadence=EXACT_CONFIRMED_PRESSURE" in report.summary_line
    assert "Exact cadence signal: EXACT_CONFIRMED_PRESSURE" in markdown
    assert any(item.exact_cadence_signal_classification == "EXACT_CONFIRMED_PRESSURE" for item in report.items)


@pytest.mark.constitutional
def test_intervention_recommendation_changes_under_exact_relief_pressure(tmp_path: Path) -> None:
    repo_root = tmp_path
    artifacts_root = repo_root / "docs" / "artifacts" / "oracle"
    artifacts_root.mkdir(parents=True)

    payload = _payload(stressed=False)
    sealed_memory = build_oracle_strategic_memory_horizon_report(
        _narrative(stressed=False, at_hour=9),
        sealed_history_reports=[_narrative(stressed=False, at_hour=8)],
        sealed_history_manifest_paths=["docs/artifacts/oracle/STACK_08.json"],
        require_sealed_history=True,
        now_utc=_NOW,
    )
    doctrine = build_oracle_doctrine_adaptation_report(payload, strategic_memory_horizon_report=sealed_memory, now_utc=_NOW)
    relieved_items = [
        item.model_copy(update={
            "exact_evidence_support_score": 1.0,
            "stress_score": min(item.stress_score, 0.22),
            "review_priority_score": min(item.review_priority_score, 0.24),
        })
        for item in doctrine.items
    ]
    doctrine = doctrine.model_copy(update={"exact_evidence_support_score": 1.0, "items": relieved_items})
    doctrine_path = artifacts_root / "ORACLE_DOCTRINE_ADAPTATION_REPORT.json"
    doctrine_path.write_text(json.dumps(doctrine.model_dump(mode="json"), indent=2, default=str), encoding="utf-8")

    report = build_oracle_strategic_intervention_report(
        payload,
        doctrine_adaptation_report=doctrine,
        strategic_memory_horizon_report=sealed_memory,
        doctrine_adaptation_report_path=doctrine_path,
        repo_root=repo_root,
        search_root=artifacts_root,
        now_utc=_NOW,
    )

    assert report.exact_cadence_signal_classification == "EXACT_RELIEF_PRESSURE"
    assert any("Repeated exact sealed relief" in item.recommended_intervention for item in report.items)
    assert any("softening signal" in action for action in report.operator_actions)
