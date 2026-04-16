from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.contracts.oracle import OracleAdvisoryInput
from strategy_validator.validator.oracle_doctrine_adaptation import build_oracle_doctrine_adaptation_report
from strategy_validator.validator.oracle_opportunity_queue import build_oracle_opportunity_queue_report
from strategy_validator.validator.oracle_research_planner import build_oracle_research_priority_report
from strategy_validator.validator.oracle_strategic_artifact_evidence import build_oracle_strategic_artifact_evidence_bundle
from strategy_validator.validator.oracle_signal_fusion import build_oracle_strategic_fusion_report
from strategy_validator.validator.oracle_strategic_briefing import build_oracle_strategic_briefing
from strategy_validator.validator.oracle_strategic_memory_horizon import build_oracle_strategic_memory_horizon_report
from strategy_validator.validator.oracle_strategic_narrative import build_oracle_strategic_narrative_report
from strategy_validator.validator.oracle_thesis_memory import build_oracle_thesis_memory_report
from strategy_validator.validator.strategy_health_posterior import build_strategy_health_posterior_report


_NOW = datetime(2026, 4, 13, 8, 10, tzinfo=timezone.utc)


def _payload(*, stressed: bool = False) -> OracleAdvisoryInput:
    return OracleAdvisoryInput.model_validate(
        {
            "generated_for_utc": "2026-04-13T08:10:00Z",
            "universe_label": "US_EQ_FACTORS",
            "sensors": {
                "semantic": {
                    "inflation_hawkishness_score": 0.65 if stressed else -0.20,
                    "geopolitical_risk_index": 0.78 if stressed else 0.12,
                    "narrative_contradiction_count": 4 if stressed else 1,
                    "tribunal_belief_conflict": 0.82 if stressed else 0.08,
                },
                "microstructure": {
                    "vpin": 0.72 if stressed else 0.20,
                    "order_flow_imbalance": -0.28 if stressed else 0.18,
                    "spread_variance_zscore": 1.7 if stressed else -0.15,
                    "liquidity_thinning_score": 0.74 if stressed else 0.10,
                },
                "macro": {
                    "yield_curve_slope_bps": -30.0 if stressed else 95.0,
                    "high_yield_credit_spread_bps": 455.0 if stressed else 285.0,
                    "equity_bond_correlation": 0.72 if stressed else -0.32,
                    "cross_asset_correlation_stress": 0.88 if stressed else 0.10,
                    "realized_volatility_zscore": 1.9 if stressed else -0.35,
                },
            },
            "strategies": [
                {
                    "strategy_id": "trend-b",
                    "strategy_type": "TREND_FOLLOWING",
                    "prior_edge_confidence": 0.72,
                    "deflated_sharpe_ratio": 0.94,
                    "cpcv_lower_bound": 0.30,
                    "realized_live_sharpe": -0.08 if stressed else 0.62,
                    "recent_win_rate": 0.39 if stressed else 0.59,
                    "drawdown_fraction": 0.16 if stressed else 0.04,
                    "expected_regimes": ["RISK_ON_LOW_VOL", "TRANSITION"],
                },
                {
                    "strategy_id": "carry-a",
                    "strategy_type": "CARRY",
                    "prior_edge_confidence": 0.61,
                    "deflated_sharpe_ratio": 0.72,
                    "cpcv_lower_bound": 0.18,
                    "realized_live_sharpe": 0.05 if stressed else 0.41,
                    "recent_win_rate": 0.47 if stressed else 0.56,
                    "drawdown_fraction": 0.10 if stressed else 0.03,
                    "expected_regimes": ["RISK_ON_LOW_VOL"],
                },
            ],
        }
    )


@pytest.mark.constitutional
def test_opportunity_queue_ranks_both_opportunity_and_caution_items() -> None:
    payload = _payload(stressed=False)
    fusion = build_oracle_strategic_fusion_report(payload, now_utc=_NOW)
    posterior = build_strategy_health_posterior_report(payload, fusion, now_utc=_NOW)
    report = build_oracle_opportunity_queue_report(payload, fusion, posterior, now_utc=_NOW)

    assert report.items
    kinds = {item.queue_kind for item in report.items}
    assert "OPPORTUNITY" in kinds
    assert report.items[0].priority_score >= report.items[-1].priority_score
    assert any("research" in action.lower() or "validate" in action.lower() for action in report.operator_actions)




@pytest.mark.constitutional
def test_opportunity_queue_gates_expansion_when_history_is_unsealed() -> None:
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

    unsealed_report = build_oracle_opportunity_queue_report(payload, strategic_memory_horizon_report=current_only, now_utc=_NOW)
    sealed_report = build_oracle_opportunity_queue_report(payload, strategic_memory_horizon_report=sealed_history, now_utc=_NOW)

    assert unsealed_report.history_integrity_status == "CURRENT_ONLY"
    assert sealed_report.history_integrity_status == "SEALED_HISTORY"
    assert sealed_report.integrity_operator_friction_score < unsealed_report.integrity_operator_friction_score
    sealed_top_opportunity = next(item for item in sealed_report.items if item.queue_kind == "OPPORTUNITY")
    unsealed_top_opportunity = next(item for item in unsealed_report.items if item.queue_kind == "OPPORTUNITY")
    assert sealed_top_opportunity.priority_score > unsealed_top_opportunity.priority_score
    assert "seal" in unsealed_top_opportunity.operator_action.lower()



@pytest.mark.constitutional
def test_opportunity_queue_prefers_exact_sealed_support_when_history_is_current_only(tmp_path: Path) -> None:
    payload = _payload(stressed=False)
    current_narrative = build_oracle_strategic_narrative_report(payload, now_utc=_NOW)
    current_only = build_oracle_strategic_memory_horizon_report(current_narrative, now_utc=_NOW)
    sealed_history = build_oracle_strategic_memory_horizon_report(
        current_narrative,
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

    plain = build_oracle_opportunity_queue_report(payload, strategic_memory_horizon_report=current_only, now_utc=_NOW)
    supported = build_oracle_opportunity_queue_report(
        payload,
        strategic_memory_horizon_report=current_only,
        doctrine_adaptation_report=doctrine,
        research_priority_report=priorities,
        doctrine_adaptation_report_path=doctrine_path,
        research_priority_report_path=priorities_path,
        repo_root=repo_root,
        search_root=repo_root / "docs" / "artifacts",
        now_utc=_NOW,
    )

    plain_top = next(item for item in plain.items if item.queue_kind == "OPPORTUNITY")
    supported_top = next(item for item in supported.items if item.queue_kind == "OPPORTUNITY")
    assert supported.exact_evidence_support_score >= 0.99
    assert supported_top.exact_evidence_support_score >= 0.99
    assert supported_top.priority_score > plain_top.priority_score
    assert "exact sealed support exists" in supported_top.operator_action.lower()


@pytest.mark.constitutional
def test_thesis_memory_detects_weakening_when_stack_turns_stressed() -> None:
    previous_payload = _payload(stressed=False)
    current_payload = _payload(stressed=True)

    previous_fusion = build_oracle_strategic_fusion_report(previous_payload, now_utc=_NOW)
    previous_posterior = build_strategy_health_posterior_report(previous_payload, previous_fusion, now_utc=_NOW)
    previous_report = build_oracle_thesis_memory_report(
        previous_payload,
        fusion_report=previous_fusion,
        posterior_report=previous_posterior,
        now_utc=_NOW,
    )

    current_fusion = build_oracle_strategic_fusion_report(current_payload, now_utc=_NOW)
    current_posterior = build_strategy_health_posterior_report(current_payload, current_fusion, now_utc=_NOW)
    current_report = build_oracle_thesis_memory_report(
        current_payload,
        fusion_report=current_fusion,
        posterior_report=current_posterior,
        previous_report=previous_report,
        now_utc=_NOW,
    )

    assert current_report.weakening_thesis_ids
    assert any(item.evolution_state in {"WEAKENING", "REVERSING"} for item in current_report.items)
    assert any(item.current_state in {"AT_RISK", "BROKEN"} for item in current_report.items)


@pytest.mark.constitutional
def test_strategic_briefing_includes_thesis_evolution_section() -> None:
    payload = _payload(stressed=True)
    report = build_oracle_strategic_briefing(payload, now_utc=_NOW)
    section_ids = {section.section_id for section in report.sections}
    assert {"opportunity_queue", "caution_queue", "thesis_evolution"} <= section_ids
    thesis_section = next(section for section in report.sections if section.section_id == "thesis_evolution")
    assert thesis_section.facts
    assert thesis_section.provenance_refs == ["thesis:oracle_thesis_memory_report/v1"]


@pytest.mark.constitutional
def test_cli_emits_queue_and_thesis_reports(tmp_path: Path) -> None:
    payload = _payload(stressed=True).model_dump(mode="json")
    input_path = tmp_path / "ORACLE_ADVISORY_INPUT.json"
    input_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    queue_json = tmp_path / "ORACLE_OPPORTUNITY_QUEUE_REPORT.json"
    queue_md = tmp_path / "ORACLE_OPPORTUNITY_QUEUE_REPORT.md"
    rc = main([
        "oracle-opportunity-queue",
        str(input_path),
        "--output", str(queue_json),
        "--markdown-output", str(queue_md),
    ])
    assert rc == 0
    queue_report = json.loads(queue_json.read_text(encoding="utf-8"))
    assert queue_report["schema_version"] == "oracle_opportunity_queue_report/v1"
    assert queue_report["items"]

    previous_report = build_oracle_thesis_memory_report(_payload(stressed=False), now_utc=_NOW)
    previous_path = tmp_path / "ORACLE_THESIS_MEMORY_PREVIOUS.json"
    previous_path.write_text(json.dumps(previous_report.model_dump(mode="json"), indent=2, default=str), encoding="utf-8")

    thesis_json = tmp_path / "ORACLE_THESIS_MEMORY_REPORT.json"
    thesis_md = tmp_path / "ORACLE_THESIS_MEMORY_REPORT.md"
    rc = main([
        "oracle-thesis-memory",
        str(input_path),
        "--previous-thesis-memory-report", str(previous_path),
        "--output", str(thesis_json),
        "--markdown-output", str(thesis_md),
    ])
    assert rc == 0
    thesis_report = json.loads(thesis_json.read_text(encoding="utf-8"))
    assert thesis_report["schema_version"] == "oracle_thesis_memory_report/v1"
    assert thesis_report["items"]
    assert "ORACLE THESIS MEMORY REPORT" in thesis_md.read_text(encoding="utf-8")


@pytest.mark.constitutional
def test_briefing_pack_absorbs_strategic_reports_when_present(tmp_path: Path) -> None:
    from strategy_validator.validator.oracle_briefing import build_oracle_briefing_pack

    repo_root = tmp_path
    oracle_root = repo_root / "docs" / "artifacts" / "oracle"
    oracle_root.mkdir(parents=True)

    payload = _payload(stressed=False)
    thesis_report = build_oracle_thesis_memory_report(payload, now_utc=_NOW)
    strategic_report = build_oracle_strategic_briefing(payload, thesis_memory_report=thesis_report, now_utc=_NOW)

    (oracle_root / "ORACLE_THESIS_MEMORY_REPORT.json").write_text(
        json.dumps(thesis_report.model_dump(mode="json"), indent=2, default=str),
        encoding="utf-8",
    )
    (oracle_root / "ORACLE_STRATEGIC_BRIEFING_REPORT.json").write_text(
        json.dumps(strategic_report.model_dump(mode="json"), indent=2, default=str),
        encoding="utf-8",
    )

    report = build_oracle_briefing_pack(repo_root=repo_root, search_root=repo_root / "docs" / "artifacts")
    section_ids = {section.section_id for section in report.sections}
    assert {"strategic_posture", "opportunity_queue", "thesis_evolution"} <= section_ids
    strategic_section = next(section for section in report.sections if section.section_id == "strategic_posture")
    thesis_section = next(section for section in report.sections if section.section_id == "thesis_evolution")
    assert strategic_section.status == strategic_report.strategic_posture
    assert thesis_section.status in {"STRENGTHENING", "UNDER_REVIEW", "STABLE"}


@pytest.mark.constitutional
def test_thesis_memory_prefers_exact_sealed_support_when_history_is_current_only(tmp_path: Path) -> None:
    payload = _payload(stressed=False)
    current_narrative = build_oracle_strategic_narrative_report(payload, now_utc=_NOW)
    current_only = build_oracle_strategic_memory_horizon_report(current_narrative, now_utc=_NOW)
    sealed_history = build_oracle_strategic_memory_horizon_report(
        current_narrative,
        sealed_history_reports=[build_oracle_strategic_narrative_report(payload, now_utc=_NOW.replace(hour=7))],
        sealed_history_manifest_paths=["docs/artifacts/oracle/STACK_07.json"],
        require_sealed_history=True,
        now_utc=_NOW,
    )
    doctrine = build_oracle_doctrine_adaptation_report(payload, strategic_memory_horizon_report=sealed_history, now_utc=_NOW)
    priorities = build_oracle_research_priority_report(
        payload,
        strategic_memory_horizon_report=sealed_history,
        doctrine_adaptation_report=doctrine,
        now_utc=_NOW,
    )

    repo_root = tmp_path
    artifacts_root = repo_root / "docs" / "artifacts" / "oracle"
    artifacts_root.mkdir(parents=True)
    doctrine_path = artifacts_root / "ORACLE_DOCTRINE_ADAPTATION_REPORT.json"
    doctrine_path.write_text(json.dumps(doctrine.model_dump(mode="json"), indent=2, default=str), encoding="utf-8")
    priorities_path = artifacts_root / "ORACLE_RESEARCH_PRIORITY_REPORT.json"
    priorities_path.write_text(json.dumps(priorities.model_dump(mode="json"), indent=2, default=str), encoding="utf-8")

    for idx, report_path in enumerate((doctrine_path, priorities_path), start=1):
        manifest, _ = build_oracle_strategic_artifact_evidence_bundle(report_path=report_path, repo_root=repo_root)
        manifest_path = artifacts_root / f"ORACLE_STRATEGIC_ARTIFACT_EVIDENCE_THESIS_{idx}.json"
        manifest_path.write_text(json.dumps(manifest.model_dump(mode="json"), indent=2, default=str), encoding="utf-8")
        (artifacts_root / f"ORACLE_STRATEGIC_ARTIFACT_EVIDENCE_THESIS_{idx}.verification.json").write_text(json.dumps({
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

    plain = build_oracle_thesis_memory_report(payload, now_utc=_NOW)
    supported = build_oracle_thesis_memory_report(
        payload,
        doctrine_adaptation_report=doctrine,
        research_priority_report=priorities,
        doctrine_adaptation_report_path=doctrine_path,
        research_priority_report_path=priorities_path,
        repo_root=repo_root,
        search_root=repo_root / "docs" / "artifacts",
        now_utc=_NOW,
    )

    plain_doctrine = next(item for item in plain.items if item.thesis_kind == "DOCTRINE")
    supported_doctrine = next(item for item in supported.items if item.thesis_kind == "DOCTRINE")
    assert supported.exact_evidence_support_score >= 0.99
    assert supported_doctrine.exact_evidence_support_score >= 0.99
    assert supported_doctrine.confidence_score > plain_doctrine.confidence_score
    assert any(fact.startswith("thesis_support_artifact_evidence_manifest=") for fact in supported_doctrine.evidence_for)


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
def test_opportunity_queue_operator_actions_change_under_exact_relief(tmp_path: Path) -> None:
    payload = _payload(stressed=False)
    _write_cadence_doctrine_report(tmp_path, payload, confirmation=False)

    report = build_oracle_opportunity_queue_report(
        payload,
        repo_root=tmp_path,
        search_root=tmp_path / "docs" / "artifacts",
        now_utc=_NOW,
    )

    assert report.exact_cadence_signal_classification == "EXACT_RELIEF_PRESSURE"
    assert any("softening signal" in action.lower() for action in report.operator_actions)
    assert any("repeated exact sealed relief" in item.operator_action.lower() for item in report.items)
