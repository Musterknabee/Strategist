from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.contracts.oracle import OracleAdvisoryInput, OracleStrategicCampaignExecutionInput
from strategy_validator.validator.oracle_briefing import build_oracle_briefing_pack
from strategy_validator.validator.oracle_campaign_execution import build_oracle_strategic_campaign_execution_report, render_oracle_strategic_campaign_execution_markdown
from strategy_validator.validator.oracle_campaign_planner import build_oracle_strategic_campaign_report
from strategy_validator.validator.oracle_research_execution_memory import build_oracle_research_execution_memory_report
from strategy_validator.validator.oracle_research_planner import build_oracle_research_priority_report
from strategy_validator.validator.oracle_doctrine_adaptation import build_oracle_doctrine_adaptation_report
from strategy_validator.contracts.oracle import OracleInvestigationOutcomeInput
from strategy_validator.validator.oracle_strategic_briefing import build_oracle_strategic_briefing
from strategy_validator.validator.oracle_strategic_memory_horizon import build_oracle_strategic_memory_horizon_report
from strategy_validator.validator.oracle_strategic_artifact_evidence import build_oracle_strategic_artifact_evidence_bundle
from strategy_validator.validator.oracle_strategic_narrative import build_oracle_strategic_narrative_report


_NOW = datetime(2026, 4, 14, 10, 0, tzinfo=timezone.utc)


def _payload(*, stressed: bool = False) -> OracleAdvisoryInput:
    return OracleAdvisoryInput.model_validate(
        {
            "generated_for_utc": "2026-04-14T10:00:00Z",
            "universe_label": "US_EQ_FACTORS",
            "sensors": {
                "semantic": {
                    "inflation_hawkishness_score": 0.76 if stressed else -0.10,
                    "geopolitical_risk_index": 0.84 if stressed else 0.18,
                    "narrative_contradiction_count": 8 if stressed else 1,
                    "tribunal_belief_conflict": 0.88 if stressed else 0.12,
                },
                "microstructure": {
                    "vpin": 0.82 if stressed else 0.18,
                    "order_flow_imbalance": -0.35 if stressed else 0.24,
                    "spread_variance_zscore": 2.2 if stressed else -0.20,
                    "liquidity_thinning_score": 0.86 if stressed else 0.12,
                },
                "macro": {
                    "yield_curve_slope_bps": -52.0 if stressed else 102.0,
                    "high_yield_credit_spread_bps": 530.0 if stressed else 255.0,
                    "equity_bond_correlation": 0.81 if stressed else -0.33,
                    "cross_asset_correlation_stress": 0.94 if stressed else 0.15,
                    "realized_volatility_zscore": 2.4 if stressed else -0.30,
                },
            },
            "strategies": [
                {
                    "strategy_id": "trend-b",
                    "strategy_type": "TREND_FOLLOWING",
                    "prior_edge_confidence": 0.72,
                    "deflated_sharpe_ratio": 0.90,
                    "cpcv_lower_bound": 0.27,
                    "realized_live_sharpe": -0.28 if stressed else 0.58,
                    "recent_win_rate": 0.31 if stressed else 0.61,
                    "drawdown_fraction": 0.26 if stressed else 0.05,
                    "expected_regimes": ["RISK_ON_LOW_VOL", "TRANSITION"],
                },
                {
                    "strategy_id": "carry-a",
                    "strategy_type": "CARRY",
                    "prior_edge_confidence": 0.64,
                    "deflated_sharpe_ratio": 0.77,
                    "cpcv_lower_bound": 0.18,
                    "realized_live_sharpe": -0.10 if stressed else 0.40,
                    "recent_win_rate": 0.40 if stressed else 0.55,
                    "drawdown_fraction": 0.15 if stressed else 0.03,
                    "expected_regimes": ["RISK_ON_LOW_VOL"],
                },
            ],
        }
    )


def _narrative(*, stressed: bool, at_hour: int):
    return build_oracle_strategic_narrative_report(_payload(stressed=stressed), now_utc=_NOW.replace(hour=at_hour))


def _execution_input(campaign_report) -> OracleStrategicCampaignExecutionInput:
    first, second, third = campaign_report.items[:3]
    return OracleStrategicCampaignExecutionInput.model_validate(
        {
            "generated_at_utc": "2026-04-14T10:05:00Z",
            "universe_label": campaign_report.universe_label,
            "items": [
                {
                    "campaign_id": first.campaign_id,
                    "execution_state": "ACTIVE",
                    "completed_step_ids": [first.steps[0].step_id] if first.steps else [],
                    "note": "Conviction repair is already underway.",
                    "evidence": ["operator_started_campaign"],
                    "recommended_next_step": "Advance the next unresolved conviction-repair step.",
                },
                {
                    "campaign_id": second.campaign_id,
                    "execution_state": "BLOCKED",
                    "blocked_step_ids": [second.steps[0].step_id] if second.steps else [],
                    "note": "Doctrine review is blocked on missing confirmation.",
                    "evidence": ["missing_confirmation_window"],
                    "recommended_next_step": "Unblock the doctrine review before continuing.",
                },
                {
                    "campaign_id": third.campaign_id,
                    "execution_state": "COMPLETED",
                    "completed_step_ids": [step.step_id for step in third.steps],
                    "note": "The cohort recovery campaign already completed successfully.",
                    "evidence": ["campaign_closed"],
                    "recommended_next_step": "Archive the completed cohort campaign and monitor for drift.",
                },
            ],
        }
    )


def _outcomes(priority_report) -> OracleInvestigationOutcomeInput:
    top = priority_report.items[0]
    return OracleInvestigationOutcomeInput.model_validate(
        {
            "generated_at_utc": "2026-04-14T10:05:00Z",
            "universe_label": priority_report.universe_label,
            "items": [
                {
                    "outcome_id": "outcome-top",
                    "priority_id": top.priority_id,
                    "execution_state": "COMPLETED",
                    "outcome_disposition": "CONFIRMED",
                    "related_strategy_ids": top.related_strategy_ids,
                    "thesis_ids": ["strategy:" + (top.related_strategy_ids[0] if top.related_strategy_ids else "trend-b")],
                    "doctrine_clause_ids": ["doctrine:strategy-alignment"],
                    "thesis_effect": "STRENGTHENS",
                    "doctrine_effect": "RELIEVES",
                    "cohort_effect": "PROMOTES",
                    "confidence_impact": 0.32,
                    "urgency_impact": -0.10,
                    "finding_summary": "The highest-priority investigation confirmed the supporting thesis remains intact.",
                    "evidence": ["validated_primary_hypothesis"],
                    "next_action": "Advance the matching campaign step.",
                }
            ],
        }
    )


@pytest.mark.constitutional
def test_campaign_execution_report_tracks_states() -> None:
    current = _narrative(stressed=True, at_hour=10)
    history = [_narrative(stressed=False, at_hour=8), _narrative(stressed=False, at_hour=9)]
    memory = build_oracle_strategic_memory_horizon_report(current, history_reports=history, now_utc=_NOW)
    campaign = build_oracle_strategic_campaign_report(
        _payload(stressed=True),
        strategic_narrative_report=current,
        strategic_memory_horizon_report=memory,
        now_utc=_NOW,
    )
    execution = build_oracle_strategic_campaign_execution_report(
        campaign,
        execution_input=_execution_input(campaign),
        strategic_memory_horizon_report=memory,
        now_utc=_NOW,
    )

    assert execution.schema_version == "oracle_strategic_campaign_execution_report/v1"
    assert execution.items
    assert execution.active_campaign_ids
    assert execution.blocked_campaign_ids
    assert execution.completed_campaign_ids
    assert execution.items[0].recommended_next_step


@pytest.mark.constitutional
def test_cli_emits_campaign_execution_report_and_markdown(tmp_path: Path) -> None:
    current = _narrative(stressed=True, at_hour=10)
    memory = build_oracle_strategic_memory_horizon_report(current, history_reports=[_narrative(stressed=False, at_hour=9)], now_utc=_NOW)
    campaign = build_oracle_strategic_campaign_report(
        _payload(stressed=True),
        strategic_narrative_report=current,
        strategic_memory_horizon_report=memory,
        now_utc=_NOW,
    )
    campaign_path = tmp_path / "ORACLE_STRATEGIC_CAMPAIGN_REPORT.json"
    campaign_path.write_text(json.dumps(campaign.model_dump(mode="json"), indent=2, default=str), encoding="utf-8")

    execution_input = _execution_input(campaign)
    execution_input_path = tmp_path / "ORACLE_STRATEGIC_CAMPAIGN_EXECUTION_INPUT.json"
    execution_input_path.write_text(json.dumps(execution_input.model_dump(mode="json"), indent=2, default=str), encoding="utf-8")

    report_json = tmp_path / "ORACLE_STRATEGIC_CAMPAIGN_EXECUTION_REPORT.json"
    report_md = tmp_path / "ORACLE_STRATEGIC_CAMPAIGN_EXECUTION_REPORT.md"
    rc = main([
        "oracle-strategic-campaign-state",
        str(campaign_path),
        "--execution-input", str(execution_input_path),
        "--output", str(report_json),
        "--markdown-output", str(report_md),
    ])
    assert rc == 0
    payload = json.loads(report_json.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "oracle_strategic_campaign_execution_report/v1"
    assert "ORACLE STRATEGIC CAMPAIGN EXECUTION REPORT" in report_md.read_text(encoding="utf-8")


@pytest.mark.constitutional
def test_strategic_briefing_includes_campaign_execution_section() -> None:
    current = _narrative(stressed=True, at_hour=10)
    memory = build_oracle_strategic_memory_horizon_report(current, history_reports=[_narrative(stressed=False, at_hour=9)], now_utc=_NOW)
    campaign = build_oracle_strategic_campaign_report(
        _payload(stressed=True),
        strategic_narrative_report=current,
        strategic_memory_horizon_report=memory,
        now_utc=_NOW,
    )
    execution = build_oracle_strategic_campaign_execution_report(
        campaign,
        execution_input=_execution_input(campaign),
        strategic_memory_horizon_report=memory,
        now_utc=_NOW,
    )

    report = build_oracle_strategic_briefing(
        _payload(stressed=True),
        strategic_narrative_report=current,
        strategic_memory_horizon_report=memory,
        strategic_campaign_report=campaign,
        campaign_execution_report=execution,
        now_utc=_NOW,
    )

    section = next(section for section in report.sections if section.section_id == "campaign_execution")
    assert section.provenance_refs == ["campaign_execution:oracle_strategic_campaign_execution_report/v1"]
    assert section.facts


@pytest.mark.constitutional
def test_briefing_pack_absorbs_campaign_execution_report_when_present(tmp_path: Path) -> None:
    repo_root = tmp_path
    oracle_root = repo_root / "docs" / "artifacts" / "oracle"
    oracle_root.mkdir(parents=True)

    current = _narrative(stressed=True, at_hour=10)
    memory = build_oracle_strategic_memory_horizon_report(current, history_reports=[_narrative(stressed=False, at_hour=9)], now_utc=_NOW)
    campaign = build_oracle_strategic_campaign_report(
        _payload(stressed=True),
        strategic_narrative_report=current,
        strategic_memory_horizon_report=memory,
        now_utc=_NOW,
    )
    execution = build_oracle_strategic_campaign_execution_report(
        campaign,
        execution_input=_execution_input(campaign),
        strategic_memory_horizon_report=memory,
        now_utc=_NOW,
    )

    (oracle_root / "ORACLE_STRATEGIC_CAMPAIGN_EXECUTION_REPORT.json").write_text(
        json.dumps(execution.model_dump(mode="json"), indent=2, default=str),
        encoding="utf-8",
    )

    report = build_oracle_briefing_pack(repo_root=repo_root, search_root=repo_root / "docs" / "artifacts")
    section = next(section for section in report.sections if section.section_id == "campaign_execution")
    assert section.provenance_refs == ["campaign_execution:oracle_strategic_campaign_execution_report/v1"]
    assert section.facts


@pytest.mark.constitutional
def test_campaign_execution_raises_friction_without_sealed_history() -> None:
    current = _narrative(stressed=True, at_hour=10)
    current_only_memory = build_oracle_strategic_memory_horizon_report(current, history_reports=[], now_utc=_NOW)
    sealed_memory = build_oracle_strategic_memory_horizon_report(
        current,
        sealed_history_reports=[_narrative(stressed=False, at_hour=9)],
        sealed_history_manifest_paths=["docs/artifacts/oracle/STACK_09.json"],
        require_sealed_history=True,
        now_utc=_NOW,
    )
    campaign = build_oracle_strategic_campaign_report(
        _payload(stressed=True),
        strategic_narrative_report=current,
        strategic_memory_horizon_report=current_only_memory,
        now_utc=_NOW,
    )
    unsealed_execution = build_oracle_strategic_campaign_execution_report(
        campaign,
        strategic_memory_horizon_report=current_only_memory,
        now_utc=_NOW,
    )
    sealed_execution = build_oracle_strategic_campaign_execution_report(
        campaign,
        strategic_memory_horizon_report=sealed_memory,
        now_utc=_NOW,
    )

    assert unsealed_execution.history_integrity_status == "CURRENT_ONLY"
    assert unsealed_execution.integrity_operator_friction_score > sealed_execution.integrity_operator_friction_score
    assert any(item.operator_friction_score > 0.5 for item in unsealed_execution.items)
    assert any(
        item.objective_kind in {"OPPORTUNITY_EXPANSION", "THESIS_VALIDATION"}
        and item.recommended_next_step.startswith("Seal and verify prior strategic stack history")
        for item in unsealed_execution.items
    )


@pytest.mark.constitutional
def test_campaign_execution_report_surfaces_preferred_strategic_backing() -> None:
    current = _narrative(stressed=True, at_hour=10)
    sealed_memory = build_oracle_strategic_memory_horizon_report(
        current,
        sealed_history_reports=[_narrative(stressed=False, at_hour=9)],
        sealed_history_manifest_paths=["docs/artifacts/oracle/STACK_09.json"],
        require_sealed_history=True,
        now_utc=_NOW,
    )
    campaign = build_oracle_strategic_campaign_report(
        _payload(stressed=True),
        strategic_narrative_report=current,
        strategic_memory_horizon_report=sealed_memory,
        now_utc=_NOW,
    )
    execution = build_oracle_strategic_campaign_execution_report(
        campaign,
        strategic_memory_horizon_report=sealed_memory,
        now_utc=_NOW,
    )
    markdown = render_oracle_strategic_campaign_execution_markdown(execution)

    assert execution.preferred_strategic_backing_source == "strategic_stack_manifest"
    assert execution.preferred_strategic_backing_classification == "SEALED_STRATEGIC_STACK_BACKED"
    assert "Preferred strategic backing source: strategic_stack_manifest" in markdown


@pytest.mark.constitutional
def test_campaign_execution_prefers_exact_sealed_campaign_subject(tmp_path: Path) -> None:
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
    campaign = build_oracle_strategic_campaign_report(_payload(stressed=True), strategic_memory_horizon_report=sealed_memory, now_utc=_NOW)
    campaign_path = artifacts_root / "ORACLE_STRATEGIC_CAMPAIGN_REPORT.json"
    campaign_path.write_text(json.dumps(campaign.model_dump(mode="json"), indent=2), encoding="utf-8")
    manifest, _ = build_oracle_strategic_artifact_evidence_bundle(report_path=campaign_path, repo_root=repo_root)
    manifest_path = artifacts_root / "ORACLE_STRATEGIC_CAMPAIGN_EVIDENCE.json"
    manifest_path.write_text(json.dumps(manifest.model_dump(mode="json"), indent=2), encoding="utf-8")
    verification = {
        "schema_version": "oracle_strategic_artifact_evidence_verification/v1",
        "status": "VERIFIED",
        "manifest_path": str(manifest_path),
        "verified_subject_count": len(manifest.subjects),
        "missing_subject_count": 0,
        "signature_verified": False,
        "subject_results": [],
        "generated_at_utc": _NOW.isoformat().replace("+00:00", "Z"),
    }
    manifest_path.with_name(manifest_path.stem + ".verification.json").write_text(json.dumps(verification, indent=2), encoding="utf-8")

    report = build_oracle_strategic_campaign_execution_report(
        campaign,
        strategic_memory_horizon_report=sealed_memory,
        campaign_report_path=campaign_path,
        repo_root=repo_root,
        search_root=repo_root / "docs" / "artifacts",
        now_utc=_NOW,
    )

    assert report.exact_evidence_support_score >= 0.85
    assert any(item.exact_evidence_support_score >= 0.85 for item in report.items)
    assert any("exact sealed campaign subject" in item.recommended_next_step.lower() for item in report.items if item.objective_kind in {"OPPORTUNITY_EXPANSION", "THESIS_VALIDATION", "DOCTRINE_STABILIZATION"})


@pytest.mark.constitutional
def test_campaign_execution_prefers_exact_execution_feedback_when_present(tmp_path: Path) -> None:
    repo_root = tmp_path
    artifacts = repo_root / "docs" / "artifacts" / "oracle"
    artifacts.mkdir(parents=True)
    current = _narrative(stressed=True, at_hour=10)
    current_only_memory = build_oracle_strategic_memory_horizon_report(current, history_reports=[], now_utc=_NOW)
    sealed_memory = build_oracle_strategic_memory_horizon_report(
        current,
        sealed_history_reports=[_narrative(stressed=False, at_hour=9)],
        sealed_history_manifest_paths=["docs/artifacts/oracle/STACK_09.json"],
        require_sealed_history=True,
        now_utc=_NOW,
    )
    priorities = build_oracle_research_priority_report(_payload(stressed=True), strategic_memory_horizon_report=sealed_memory, now_utc=_NOW)
    priority_path = artifacts / "ORACLE_RESEARCH_PRIORITY_REPORT.json"
    priority_path.write_text(json.dumps(priorities.model_dump(mode="json"), indent=2, default=str), encoding="utf-8")
    manifest, _ = build_oracle_strategic_artifact_evidence_bundle(report_path=priority_path, repo_root=repo_root)
    manifest_path = artifacts / "ORACLE_RESEARCH_PRIORITY_EVIDENCE.json"
    manifest_path.write_text(json.dumps(manifest.model_dump(mode="json"), indent=2, default=str), encoding="utf-8")
    manifest_path.with_name(manifest_path.stem + ".verification.json").write_text(json.dumps({
        "schema_version": "oracle_strategic_artifact_evidence_verification/v1",
        "status": "VERIFIED",
        "integrity_status": "VERIFIED",
        "manifest_path": str(manifest_path),
        "verified_at_utc": _NOW.isoformat().replace("+00:00", "Z"),
        "subject_results": [],
        "verification_notes": [],
    }, indent=2), encoding="utf-8")

    execution_memory = build_oracle_research_execution_memory_report(
        priorities,
        _outcomes(priorities),
        research_priority_report_path=priority_path,
        repo_root=repo_root,
        search_root=artifacts,
        now_utc=_NOW,
    )
    campaign = build_oracle_strategic_campaign_report(
        _payload(stressed=True),
        strategic_narrative_report=current,
        strategic_memory_horizon_report=current_only_memory,
        research_priority_report=priorities,
        research_execution_memory_report=execution_memory,
        research_priority_report_path=priority_path,
        repo_root=repo_root,
        search_root=artifacts,
        now_utc=_NOW,
    )
    plain = build_oracle_strategic_campaign_execution_report(campaign, strategic_memory_horizon_report=current_only_memory, now_utc=_NOW)
    exact = build_oracle_strategic_campaign_execution_report(
        campaign,
        research_execution_memory_report=execution_memory,
        strategic_memory_horizon_report=current_only_memory,
        campaign_report_path=artifacts / "ORACLE_STRATEGIC_CAMPAIGN_REPORT.json",
        repo_root=repo_root,
        search_root=artifacts,
        now_utc=_NOW,
    )

    assert exact.exact_evidence_support_score >= 0.99
    assert max(item.exact_evidence_support_score for item in exact.items) >= 0.99
    assert min(item.blocker_score for item in exact.items if item.objective_kind in {"THESIS_VALIDATION", "OPPORTUNITY_EXPANSION", "DOCTRINE_STABILIZATION"}) <= min(item.blocker_score for item in plain.items if item.objective_kind in {"THESIS_VALIDATION", "OPPORTUNITY_EXPANSION", "DOCTRINE_STABILIZATION"})
    assert any("execution_memory_exact_evidence_support=" in entry for item in exact.items for entry in item.evidence)


@pytest.mark.constitutional
def test_campaign_execution_surfaces_exact_cadence_signal_from_doctrine_feedback(tmp_path: Path) -> None:
    repo_root = tmp_path
    artifacts = repo_root / "docs" / "artifacts" / "oracle"
    artifacts.mkdir(parents=True)
    current = _narrative(stressed=True, at_hour=10)
    current_only_memory = build_oracle_strategic_memory_horizon_report(current, history_reports=[], now_utc=_NOW)
    sealed_memory = build_oracle_strategic_memory_horizon_report(
        current,
        sealed_history_reports=[_narrative(stressed=False, at_hour=9)],
        sealed_history_manifest_paths=["docs/artifacts/oracle/STACK_09.json"],
        require_sealed_history=True,
        now_utc=_NOW,
    )
    priorities = build_oracle_research_priority_report(
        _payload(stressed=True),
        strategic_memory_horizon_report=sealed_memory,
        now_utc=_NOW,
    )
    priority_path = artifacts / "ORACLE_RESEARCH_PRIORITY_REPORT.json"
    priority_path.write_text(json.dumps(priorities.model_dump(mode="json"), indent=2, default=str), encoding="utf-8")
    manifest, _ = build_oracle_strategic_artifact_evidence_bundle(report_path=priority_path, repo_root=repo_root)
    manifest_path = artifacts / "ORACLE_RESEARCH_PRIORITY_EVIDENCE.json"
    manifest_path.write_text(json.dumps(manifest.model_dump(mode="json"), indent=2, default=str), encoding="utf-8")
    manifest_path.with_name(manifest_path.stem + ".verification.json").write_text(json.dumps({
        "schema_version": "oracle_strategic_artifact_evidence_verification/v1",
        "status": "VERIFIED",
        "integrity_status": "VERIFIED",
        "manifest_path": str(manifest_path),
        "verified_at_utc": _NOW.isoformat().replace("+00:00", "Z"),
        "subject_results": [],
        "verification_notes": [],
    }, indent=2), encoding="utf-8")
    execution_memory = build_oracle_research_execution_memory_report(
        priorities,
        _outcomes(priorities),
        research_priority_report_path=priority_path,
        repo_root=repo_root,
        search_root=artifacts,
        now_utc=_NOW,
    )
    doctrine = build_oracle_doctrine_adaptation_report(
        _payload(stressed=True),
        execution_memory_report=execution_memory,
        strategic_memory_horizon_report=current_only_memory,
        now_utc=_NOW,
    )
    doctrine_payload = doctrine.model_dump(mode="json")
    doctrine_payload["exact_evidence_support_score"] = 0.99
    if doctrine_payload.get("items"):
        doctrine_payload["items"][0]["exact_evidence_support_score"] = 0.99
        doctrine_payload["items"][0]["stress_score"] = max(0.62, float(doctrine_payload["items"][0].get("stress_score", 0.0) or 0.0))
        doctrine_payload["items"][0]["review_priority_score"] = max(0.64, float(doctrine_payload["items"][0].get("review_priority_score", 0.0) or 0.0))
    doctrine_path = artifacts / "ORACLE_DOCTRINE_ADAPTATION_REPORT.json"
    doctrine_path.write_text(json.dumps(doctrine_payload, indent=2, default=str), encoding="utf-8")
    doctrine = type(doctrine).model_validate(doctrine_payload)

    campaign = build_oracle_strategic_campaign_report(
        _payload(stressed=True),
        strategic_narrative_report=current,
        strategic_memory_horizon_report=current_only_memory,
        research_priority_report=priorities,
        research_execution_memory_report=execution_memory,
        research_priority_report_path=priority_path,
        repo_root=repo_root,
        search_root=artifacts,
        now_utc=_NOW,
    )
    campaign_path = artifacts / "ORACLE_STRATEGIC_CAMPAIGN_REPORT.json"
    campaign_path.write_text(json.dumps(campaign.model_dump(mode="json"), indent=2, default=str), encoding="utf-8")

    report = build_oracle_strategic_campaign_execution_report(
        campaign,
        research_execution_memory_report=execution_memory,
        strategic_memory_horizon_report=current_only_memory,
        doctrine_adaptation_report=doctrine,
        campaign_report_path=campaign_path,
        repo_root=repo_root,
        search_root=artifacts,
        now_utc=_NOW,
    )
    markdown = render_oracle_strategic_campaign_execution_markdown(report)
    briefing = build_oracle_strategic_briefing(
        _payload(stressed=True),
        strategic_narrative_report=current,
        strategic_memory_horizon_report=current_only_memory,
        research_priority_report=priorities,
        research_execution_memory_report=execution_memory,
        doctrine_adaptation_report=doctrine,
        strategic_campaign_report=campaign,
        campaign_execution_report=report,
        repo_root=repo_root,
        search_root=artifacts,
        now_utc=_NOW,
    )
    execution_section = next(section for section in briefing.sections if section.section_id == "campaign_execution")

    assert report.exact_cadence_signal_classification == "EXACT_CONFIRMED_PRESSURE"
    assert report.exact_feedback_confirmation_count >= 1
    assert all(item.exact_cadence_signal_classification == "EXACT_CONFIRMED_PRESSURE" for item in report.items)
    assert "Exact cadence signal: EXACT_CONFIRMED_PRESSURE" in markdown
    assert execution_section.exact_cadence_signal_classification == "EXACT_CONFIRMED_PRESSURE"
    assert any("exact_cadence_signal_classification=EXACT_CONFIRMED_PRESSURE" in fact for fact in execution_section.facts)


@pytest.mark.constitutional
def test_campaign_execution_next_step_changes_under_exact_relief_pressure(tmp_path: Path) -> None:
    repo_root = tmp_path
    artifacts = repo_root / "docs" / "artifacts" / "oracle"
    artifacts.mkdir(parents=True)

    payload = _payload(stressed=False)
    current = _narrative(stressed=False, at_hour=10)
    sealed_memory = build_oracle_strategic_memory_horizon_report(
        current,
        sealed_history_reports=[_narrative(stressed=False, at_hour=9)],
        sealed_history_manifest_paths=["docs/artifacts/oracle/STACK_09.json"],
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
    doctrine_path = artifacts / "ORACLE_DOCTRINE_ADAPTATION_REPORT.json"
    doctrine_path.write_text(json.dumps(doctrine.model_dump(mode="json"), indent=2, default=str), encoding="utf-8")

    campaign = build_oracle_strategic_campaign_report(
        payload,
        strategic_narrative_report=current,
        strategic_memory_horizon_report=sealed_memory,
        doctrine_adaptation_report=doctrine,
        doctrine_adaptation_report_path=doctrine_path,
        repo_root=repo_root,
        search_root=artifacts,
        now_utc=_NOW,
    )
    campaign_path = artifacts / "ORACLE_STRATEGIC_CAMPAIGN_REPORT.json"
    campaign_path.write_text(json.dumps(campaign.model_dump(mode="json"), indent=2, default=str), encoding="utf-8")

    report = build_oracle_strategic_campaign_execution_report(
        campaign,
        doctrine_adaptation_report=doctrine,
        strategic_memory_horizon_report=sealed_memory,
        campaign_report_path=campaign_path,
        repo_root=repo_root,
        search_root=artifacts,
        now_utc=_NOW,
    )

    assert report.exact_cadence_signal_classification == "EXACT_RELIEF_PRESSURE"
    assert any("Repeated exact sealed relief" in item.recommended_next_step for item in report.items)
    assert any("softening signal" in action for action in report.operator_actions)
