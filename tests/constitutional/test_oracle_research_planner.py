from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.contracts.oracle import OracleAdvisoryInput
from strategy_validator.validator.oracle_briefing import build_oracle_briefing_pack
from strategy_validator.validator.oracle_research_planner import build_oracle_research_priority_report, render_oracle_research_priority_markdown
from strategy_validator.validator.oracle_doctrine_adaptation import build_oracle_doctrine_adaptation_report
from strategy_validator.validator.oracle_strategic_artifact_evidence import build_oracle_strategic_artifact_evidence_bundle
from strategy_validator.validator.oracle_strategic_briefing import build_oracle_strategic_briefing
from strategy_validator.validator.oracle_strategic_memory_horizon import build_oracle_strategic_memory_horizon_report
from strategy_validator.validator.oracle_strategic_narrative import build_oracle_strategic_narrative_report


_NOW = datetime(2026, 4, 13, 8, 40, tzinfo=timezone.utc)


def _payload(*, stressed: bool = False) -> OracleAdvisoryInput:
    return OracleAdvisoryInput.model_validate(
        {
            "generated_for_utc": "2026-04-13T08:40:00Z",
            "universe_label": "US_EQ_FACTORS",
            "sensors": {
                "semantic": {
                    "inflation_hawkishness_score": 0.76 if stressed else -0.16,
                    "geopolitical_risk_index": 0.84 if stressed else 0.14,
                    "narrative_contradiction_count": 5 if stressed else 1,
                    "tribunal_belief_conflict": 0.90 if stressed else 0.10,
                },
                "microstructure": {
                    "vpin": 0.81 if stressed else 0.18,
                    "order_flow_imbalance": -0.34 if stressed else 0.14,
                    "spread_variance_zscore": 2.0 if stressed else -0.12,
                    "liquidity_thinning_score": 0.83 if stressed else 0.10,
                },
                "macro": {
                    "yield_curve_slope_bps": -44.0 if stressed else 88.0,
                    "high_yield_credit_spread_bps": 495.0 if stressed else 292.0,
                    "equity_bond_correlation": 0.78 if stressed else -0.28,
                    "cross_asset_correlation_stress": 0.92 if stressed else 0.12,
                    "realized_volatility_zscore": 2.3 if stressed else -0.25,
                },
            },
            "strategies": [
                {
                    "strategy_id": "trend-b",
                    "strategy_type": "TREND_FOLLOWING",
                    "prior_edge_confidence": 0.73,
                    "deflated_sharpe_ratio": 0.95,
                    "cpcv_lower_bound": 0.31,
                    "realized_live_sharpe": -0.16 if stressed else 0.60,
                    "recent_win_rate": 0.35 if stressed else 0.58,
                    "drawdown_fraction": 0.19 if stressed else 0.04,
                    "expected_regimes": ["RISK_ON_LOW_VOL", "TRANSITION"],
                },
                {
                    "strategy_id": "carry-a",
                    "strategy_type": "CARRY",
                    "prior_edge_confidence": 0.62,
                    "deflated_sharpe_ratio": 0.74,
                    "cpcv_lower_bound": 0.18,
                    "realized_live_sharpe": -0.05 if stressed else 0.39,
                    "recent_win_rate": 0.43 if stressed else 0.55,
                    "drawdown_fraction": 0.12 if stressed else 0.03,
                    "expected_regimes": ["RISK_ON_LOW_VOL"],
                },
            ],
        }
    )


@pytest.mark.constitutional
def test_research_planner_ranks_nonempty_investigation_plan_under_stress() -> None:
    report = build_oracle_research_priority_report(_payload(stressed=True), now_utc=_NOW)

    assert report.schema_version == "oracle_research_priority_report/v1"
    assert report.items
    assert report.highest_priority_id == report.items[0].priority_id
    assert report.items[0].urgency_score >= report.items[-1].urgency_score
    assert {item.priority_kind for item in report.items} & {"DOCTRINE_REVIEW", "THESIS_REVIEW", "SCENARIO_PROBE", "STRATEGY_VALIDATION"}




@pytest.mark.constitutional
def test_research_planner_penalizes_expansion_forward_moves_without_sealed_history() -> None:
    payload = _payload(stressed=False)
    current_narrative = build_oracle_strategic_narrative_report(payload, now_utc=_NOW)
    prior_narrative = build_oracle_strategic_narrative_report(payload, now_utc=_NOW.replace(hour=7))

    current_only = build_oracle_strategic_memory_horizon_report(current_narrative, now_utc=_NOW)
    sealed_history = build_oracle_strategic_memory_horizon_report(
        current_narrative,
        sealed_history_reports=[prior_narrative],
        sealed_history_manifest_paths=["docs/artifacts/oracle/STACK_07.json"],
        require_sealed_history=True,
        now_utc=_NOW,
    )

    unsealed_report = build_oracle_research_priority_report(payload, strategic_memory_horizon_report=current_only, now_utc=_NOW)
    sealed_report = build_oracle_research_priority_report(payload, strategic_memory_horizon_report=sealed_history, now_utc=_NOW)

    assert unsealed_report.history_integrity_status == "CURRENT_ONLY"
    assert sealed_report.history_integrity_status == "SEALED_HISTORY"
    assert unsealed_report.integrity_penalty_score > sealed_report.integrity_penalty_score
    unsealed_validation = next(item for item in unsealed_report.items if item.priority_kind == "STRATEGY_VALIDATION")
    sealed_validation = next(item for item in sealed_report.items if item.priority_kind == "STRATEGY_VALIDATION")
    assert unsealed_validation.integrity_penalty_score > 0.0
    assert sealed_validation.integrity_penalty_score == 0.0
    assert sealed_validation.urgency_score > unsealed_validation.urgency_score
    assert "sealed" in unsealed_validation.recommended_investigation.lower()

@pytest.mark.constitutional
def test_strategic_briefing_includes_research_priorities_section() -> None:
    report = build_oracle_strategic_briefing(_payload(stressed=True), now_utc=_NOW)

    section = next(section for section in report.sections if section.section_id == "research_priorities")
    assert section.facts
    assert section.provenance_refs == ["research_priorities:oracle_research_priority_report/v1"]
    assert section.status in {"REGIME_INVESTIGATION", "STRATEGY_VALIDATION", "DOCTRINE_REVIEW", "THESIS_REVIEW", "SCENARIO_PROBE"}


@pytest.mark.constitutional
def test_research_planner_cli_emits_report_and_markdown(tmp_path: Path) -> None:
    payload = _payload(stressed=True).model_dump(mode="json")
    input_path = tmp_path / "ORACLE_ADVISORY_INPUT.json"
    input_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    report_json = tmp_path / "ORACLE_RESEARCH_PRIORITY_REPORT.json"
    report_md = tmp_path / "ORACLE_RESEARCH_PRIORITY_REPORT.md"
    rc = main([
        "oracle-research-planner",
        str(input_path),
        "--output", str(report_json),
        "--markdown-output", str(report_md),
    ])
    assert rc == 0
    artifact = json.loads(report_json.read_text(encoding="utf-8"))
    assert artifact["schema_version"] == "oracle_research_priority_report/v1"
    assert artifact["items"]
    assert "ORACLE RESEARCH PRIORITY REPORT" in report_md.read_text(encoding="utf-8")


@pytest.mark.constitutional
def test_briefing_pack_absorbs_research_priority_report(tmp_path: Path) -> None:
    repo_root = tmp_path
    oracle_root = repo_root / "docs" / "artifacts" / "oracle"
    oracle_root.mkdir(parents=True)

    priorities = build_oracle_research_priority_report(_payload(stressed=True), now_utc=_NOW)
    strategic = build_oracle_strategic_briefing(_payload(stressed=True), now_utc=_NOW)

    (oracle_root / "ORACLE_RESEARCH_PRIORITY_REPORT.json").write_text(
        json.dumps(priorities.model_dump(mode="json"), indent=2, default=str),
        encoding="utf-8",
    )
    (oracle_root / "ORACLE_STRATEGIC_BRIEFING_REPORT.json").write_text(
        json.dumps(strategic.model_dump(mode="json"), indent=2, default=str),
        encoding="utf-8",
    )

    report = build_oracle_briefing_pack(repo_root=repo_root, search_root=repo_root / "docs" / "artifacts")
    section = next(section for section in report.sections if section.section_id == "research_priorities")
    assert section.provenance_refs == ["research_priorities:oracle_research_priority_report/v1"]
    assert section.facts
    assert section.status in {"REGIME_INVESTIGATION", "STRATEGY_VALIDATION", "DOCTRINE_REVIEW", "THESIS_REVIEW", "SCENARIO_PROBE"}


@pytest.mark.constitutional
def test_research_priority_report_is_self_describing_about_grounding() -> None:
    payload = _payload(stressed=False)
    current_narrative = build_oracle_strategic_narrative_report(payload, now_utc=_NOW)
    prior_narrative = build_oracle_strategic_narrative_report(payload, now_utc=_NOW.replace(hour=7))
    sealed_history = build_oracle_strategic_memory_horizon_report(
        current_narrative,
        sealed_history_reports=[prior_narrative],
        sealed_history_manifest_paths=["docs/artifacts/oracle/STACK_07.json"],
        require_sealed_history=True,
        now_utc=_NOW,
    )

    report = build_oracle_research_priority_report(payload, strategic_memory_horizon_report=sealed_history, now_utc=_NOW)
    markdown = render_oracle_research_priority_markdown(report)

    assert report.preferred_strategic_backing_source == "strategic_stack_manifest"
    assert report.preferred_strategic_backing_classification == "SEALED_STRATEGIC_STACK_BACKED"
    assert "Preferred strategic backing source: strategic_stack_manifest" in markdown


@pytest.mark.constitutional
def test_research_planner_prefers_exact_sealed_doctrine_evidence_when_present(tmp_path: Path) -> None:
    payload = _payload(stressed=False)
    current_narrative = build_oracle_strategic_narrative_report(payload, now_utc=_NOW)
    current_only = build_oracle_strategic_memory_horizon_report(current_narrative, now_utc=_NOW)
    sealed_memory = build_oracle_strategic_memory_horizon_report(
        current_narrative,
        sealed_history_reports=[build_oracle_strategic_narrative_report(payload, now_utc=_NOW.replace(hour=max(0, _NOW.hour - 1)))],
        sealed_history_manifest_paths=["docs/artifacts/oracle/STACK_PREV.json"],
        require_sealed_history=True,
        now_utc=_NOW,
    )
    doctrine = build_oracle_doctrine_adaptation_report(payload, strategic_memory_horizon_report=sealed_memory, now_utc=_NOW)

    repo_root = tmp_path
    artifacts = repo_root / "docs" / "artifacts" / "oracle"
    artifacts.mkdir(parents=True)
    doctrine_path = artifacts / "ORACLE_DOCTRINE_ADAPTATION_REPORT.json"
    doctrine_path.write_text(json.dumps(doctrine.model_dump(mode="json"), indent=2, default=str), encoding="utf-8")
    manifest, _ = build_oracle_strategic_artifact_evidence_bundle(report_path=doctrine_path, repo_root=repo_root)
    manifest_path = artifacts / "ORACLE_STRATEGIC_ARTIFACT_EVIDENCE_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest.model_dump(mode="json"), indent=2, default=str), encoding="utf-8")
    verification_path = artifacts / "ORACLE_STRATEGIC_ARTIFACT_EVIDENCE_MANIFEST.verification.json"
    verification_path.write_text(json.dumps({
        "schema_version": "oracle_strategic_artifact_evidence_verification/v1",
        "status": "VERIFIED",
        "integrity_status": "VERIFIED",
        "manifest_path": str(manifest_path),
        "verified_at_utc": _NOW.isoformat().replace("+00:00", "Z"),
        "subject_results": [],
        "verification_notes": [],
    }, indent=2), encoding="utf-8")

    plain = build_oracle_research_priority_report(payload, doctrine_adaptation_report=doctrine, strategic_memory_horizon_report=current_only, now_utc=_NOW)
    exact = build_oracle_research_priority_report(
        payload,
        doctrine_adaptation_report=doctrine,
        doctrine_adaptation_report_path=doctrine_path,
        strategic_memory_horizon_report=current_only,
        repo_root=repo_root,
        search_root=artifacts,
        now_utc=_NOW,
    )

    plain_doctrine = next(item for item in plain.items if item.priority_kind == "DOCTRINE_REVIEW")
    exact_doctrine = next(item for item in exact.items if item.priority_kind == "DOCTRINE_REVIEW")
    plain_validation = next(item for item in plain.items if item.priority_kind == "STRATEGY_VALIDATION")
    exact_validation = next(item for item in exact.items if item.priority_kind == "STRATEGY_VALIDATION")

    assert exact.exact_evidence_support_score >= 0.85
    assert exact_doctrine.exact_evidence_support_score >= 0.85
    assert exact_doctrine.integrity_penalty_score < plain_doctrine.integrity_penalty_score
    assert exact_doctrine.urgency_score > plain_doctrine.urgency_score
    assert exact_validation.integrity_penalty_score < plain_validation.integrity_penalty_score
    assert "exact sealed doctrine subject" in exact_doctrine.recommended_investigation.lower()


def _write_cadence_doctrine_report(tmp_path: Path, payload: OracleAdvisoryInput, *, confirmation: bool) -> Path:
    artifacts_root = tmp_path / "docs" / "artifacts" / "oracle"
    artifacts_root.mkdir(parents=True, exist_ok=True)
    report = build_oracle_doctrine_adaptation_report(payload, now_utc=_NOW)
    item = report.items[0].model_copy(update={
        "exact_evidence_support_score": 0.99,
        "stress_score": 0.74 if confirmation else 0.30,
        "review_priority_score": 0.72 if confirmation else 0.28,
    })
    report = report.model_copy(update={
        "exact_evidence_support_score": 0.99,
        "items": [item] + report.items[1:],
    })
    path = artifacts_root / ("ORACLE_DOCTRINE_ADAPTATION_REPORT_CONFIRMED.json" if confirmation else "ORACLE_DOCTRINE_ADAPTATION_REPORT_RELIEF.json")
    path.write_text(json.dumps(report.model_dump(mode="json"), indent=2, default=str), encoding="utf-8")
    return path


@pytest.mark.constitutional
def test_research_planner_operator_actions_change_under_exact_confirmed_pressure(tmp_path: Path) -> None:
    payload = _payload(stressed=False)
    _write_cadence_doctrine_report(tmp_path, payload, confirmation=True)

    report = build_oracle_research_priority_report(
        payload,
        repo_root=tmp_path,
        search_root=tmp_path / "docs" / "artifacts",
        now_utc=_NOW,
    )

    assert report.exact_cadence_signal_classification == "EXACT_CONFIRMED_PRESSURE"
    assert any("compress the decision loop" in action.lower() for action in report.operator_actions)
    assert any("repeated exact sealed confirmations" in item.recommended_investigation.lower() for item in report.items)
