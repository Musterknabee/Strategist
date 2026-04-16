from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.contracts.oracle import OracleAdvisoryInput
from strategy_validator.validator.oracle_briefing import build_oracle_briefing_pack
from strategy_validator.validator.oracle_contradiction_resolution import build_oracle_contradiction_resolution_report
from strategy_validator.validator.oracle_doctrine_adaptation import build_oracle_doctrine_adaptation_report
from strategy_validator.validator.oracle_research_planner import build_oracle_research_priority_report
from strategy_validator.validator.oracle_strategic_artifact_evidence import build_oracle_strategic_artifact_evidence_bundle
from strategy_validator.validator.oracle_strategic_briefing import build_oracle_strategic_briefing
from strategy_validator.validator.oracle_strategic_memory_horizon import build_oracle_strategic_memory_horizon_report
from strategy_validator.validator.oracle_strategic_narrative import build_oracle_strategic_narrative_report


_NOW = datetime(2026, 4, 14, 8, 0, tzinfo=timezone.utc)


def _payload(*, stressed: bool = False) -> OracleAdvisoryInput:
    return OracleAdvisoryInput.model_validate(
        {
            "generated_for_utc": "2026-04-14T08:00:00Z",
            "universe_label": "US_EQ_FACTORS",
            "sensors": {
                "semantic": {
                    "inflation_hawkishness_score": 0.74 if stressed else -0.22,
                    "geopolitical_risk_index": 0.86 if stressed else 0.14,
                    "narrative_contradiction_count": 8 if stressed else 1,
                    "tribunal_belief_conflict": 0.90 if stressed else 0.10,
                },
                "microstructure": {
                    "vpin": 0.83 if stressed else 0.18,
                    "order_flow_imbalance": -0.46 if stressed else 0.24,
                    "spread_variance_zscore": 2.4 if stressed else -0.38,
                    "liquidity_thinning_score": 0.88 if stressed else 0.10,
                },
                "macro": {
                    "yield_curve_slope_bps": -52.0 if stressed else 108.0,
                    "high_yield_credit_spread_bps": 534.0 if stressed else 258.0,
                    "equity_bond_correlation": 0.84 if stressed else -0.36,
                    "cross_asset_correlation_stress": 0.96 if stressed else 0.16,
                    "realized_volatility_zscore": 2.5 if stressed else -0.30,
                },
            },
            "strategies": [
                {
                    "strategy_id": "trend-b",
                    "strategy_type": "TREND_FOLLOWING",
                    "prior_edge_confidence": 0.74,
                    "deflated_sharpe_ratio": 0.94,
                    "cpcv_lower_bound": 0.30,
                    "realized_live_sharpe": -0.28 if stressed else 0.62,
                    "recent_win_rate": 0.33 if stressed else 0.63,
                    "drawdown_fraction": 0.24 if stressed else 0.05,
                    "expected_regimes": ["RISK_ON_LOW_VOL", "TRANSITION"],
                },
                {
                    "strategy_id": "carry-a",
                    "strategy_type": "CARRY",
                    "prior_edge_confidence": 0.65,
                    "deflated_sharpe_ratio": 0.78,
                    "cpcv_lower_bound": 0.20,
                    "realized_live_sharpe": -0.08 if stressed else 0.44,
                    "recent_win_rate": 0.41 if stressed else 0.57,
                    "drawdown_fraction": 0.13 if stressed else 0.03,
                    "expected_regimes": ["RISK_ON_LOW_VOL"],
                },
            ],
        }
    )


def _narrative(*, stressed: bool, at_hour: int):
    return build_oracle_strategic_narrative_report(_payload(stressed=stressed), now_utc=_NOW.replace(hour=at_hour))




@pytest.mark.constitutional
def test_contradiction_resolution_prefers_exact_sealed_support_over_generic_history_penalty(tmp_path: Path) -> None:
    payload = _payload(stressed=True)
    current = build_oracle_strategic_narrative_report(payload, now_utc=_NOW)
    mixed_memory = build_oracle_strategic_memory_horizon_report(
        current,
        history_reports=[build_oracle_strategic_narrative_report(_payload(stressed=False), now_utc=_NOW.replace(hour=7))],
        now_utc=_NOW,
    )
    sealed_memory = build_oracle_strategic_memory_horizon_report(
        current,
        sealed_history_reports=[build_oracle_strategic_narrative_report(_payload(stressed=False), now_utc=_NOW.replace(hour=7))],
        sealed_history_manifest_paths=["docs/artifacts/oracle/STACK_07.json"],
        require_sealed_history=True,
        now_utc=_NOW,
    )
    doctrine = build_oracle_doctrine_adaptation_report(payload, strategic_memory_horizon_report=sealed_memory, now_utc=_NOW)
    priorities = build_oracle_research_priority_report(payload, strategic_memory_horizon_report=sealed_memory, doctrine_adaptation_report=doctrine, now_utc=_NOW)

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

    plain = build_oracle_contradiction_resolution_report(
        payload,
        strategic_narrative_report=current,
        strategic_memory_horizon_report=mixed_memory,
        doctrine_adaptation_report=doctrine,
        research_priority_report=priorities,
        now_utc=_NOW,
    )
    supported = build_oracle_contradiction_resolution_report(
        payload,
        strategic_narrative_report=current,
        strategic_memory_horizon_report=mixed_memory,
        doctrine_adaptation_report=doctrine,
        research_priority_report=priorities,
        doctrine_adaptation_report_path=doctrine_path,
        research_priority_report_path=priorities_path,
        repo_root=repo_root,
        search_root=repo_root / "docs" / "artifacts",
        now_utc=_NOW,
    )

    assert supported.exact_evidence_support_score >= 0.99
    assert supported.integrity_penalty_score < plain.integrity_penalty_score
    assert supported.items[0].exact_evidence_support_score >= 0.99
    assert supported.items[0].resolution_priority_score > plain.items[0].resolution_priority_score
    assert "exact sealed supporting subject" in supported.items[0].recommended_resolution.lower()


@pytest.mark.constitutional
def test_contradiction_resolution_report_ranks_highest_leverage_contradictions() -> None:
    current = _narrative(stressed=True, at_hour=8)
    history = [_narrative(stressed=False, at_hour=6), _narrative(stressed=False, at_hour=7)]
    memory = build_oracle_strategic_memory_horizon_report(current, history_reports=history, now_utc=_NOW)

    report = build_oracle_contradiction_resolution_report(
        _payload(stressed=True),
        strategic_narrative_report=current,
        strategic_memory_horizon_report=memory,
        now_utc=_NOW,
    )

    assert report.schema_version == "oracle_contradiction_resolution_report/v1"
    assert report.items
    assert report.highest_priority_resolution_id is not None
    assert report.items[0].resolution_priority_score >= report.items[-1].resolution_priority_score
    assert report.items[0].expected_conviction_gain_score > 0.0
    assert report.drift_state in {"REVERSING", "VOLATILE", "SOFTENING", "STABLE", "FIRST_OBSERVATION", "STRENGTHENING"}


@pytest.mark.constitutional
def test_cli_emits_contradiction_resolution_report_and_markdown(tmp_path: Path) -> None:
    input_path = tmp_path / "ORACLE_ADVISORY_INPUT.json"
    input_path.write_text(json.dumps(_payload(stressed=True).model_dump(mode="json"), indent=2, default=str), encoding="utf-8")

    report_json = tmp_path / "ORACLE_CONTRADICTION_RESOLUTION_REPORT.json"
    report_md = tmp_path / "ORACLE_CONTRADICTION_RESOLUTION_REPORT.md"
    rc = main([
        "oracle-contradiction-resolution",
        str(input_path),
        "--output", str(report_json),
        "--markdown-output", str(report_md),
    ])
    assert rc == 0
    payload = json.loads(report_json.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "oracle_contradiction_resolution_report/v1"
    assert "ORACLE CONTRADICTION RESOLUTION REPORT" in report_md.read_text(encoding="utf-8")


@pytest.mark.constitutional
def test_strategic_briefing_includes_contradiction_resolution_section() -> None:
    current = _narrative(stressed=True, at_hour=8)
    memory = build_oracle_strategic_memory_horizon_report(current, history_reports=[_narrative(stressed=False, at_hour=6)], now_utc=_NOW)
    contradiction = build_oracle_contradiction_resolution_report(
        _payload(stressed=True),
        strategic_narrative_report=current,
        strategic_memory_horizon_report=memory,
        now_utc=_NOW,
    )

    report = build_oracle_strategic_briefing(
        _payload(stressed=True),
        strategic_narrative_report=current,
        strategic_memory_horizon_report=memory,
        contradiction_resolution_report=contradiction,
        now_utc=_NOW,
    )

    section = next(section for section in report.sections if section.section_id == "contradiction_resolution")
    assert section.provenance_refs == ["contradiction_resolution:oracle_contradiction_resolution_report/v1"]
    assert section.facts


@pytest.mark.constitutional
def test_briefing_pack_absorbs_contradiction_resolution_when_present(tmp_path: Path) -> None:
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

    (oracle_root / "ORACLE_CONTRADICTION_RESOLUTION_REPORT.json").write_text(
        json.dumps(contradiction.model_dump(mode="json"), indent=2, default=str),
        encoding="utf-8",
    )

    report = build_oracle_briefing_pack(repo_root=repo_root, search_root=repo_root / "docs" / "artifacts")
    section = next(section for section in report.sections if section.section_id == "contradiction_resolution")
    assert section.provenance_refs == ["contradiction_resolution:oracle_contradiction_resolution_report/v1"]
    assert section.facts


@pytest.mark.constitutional
def test_contradiction_resolution_downgrades_unsealed_history() -> None:
    payload = _payload(stressed=True)
    current = build_oracle_strategic_narrative_report(payload, now_utc=_NOW)
    mixed_memory = build_oracle_strategic_memory_horizon_report(
        current,
        history_reports=[build_oracle_strategic_narrative_report(_payload(stressed=False), now_utc=_NOW.replace(hour=7))],
        now_utc=_NOW,
    )
    sealed_memory = build_oracle_strategic_memory_horizon_report(
        current,
        sealed_history_reports=[build_oracle_strategic_narrative_report(_payload(stressed=False), now_utc=_NOW.replace(hour=7))],
        sealed_history_manifest_paths=["docs/artifacts/oracle/STACK_07.json"],
        require_sealed_history=True,
        now_utc=_NOW,
    )

    mixed = build_oracle_contradiction_resolution_report(
        payload,
        strategic_narrative_report=current,
        strategic_memory_horizon_report=mixed_memory,
        now_utc=_NOW,
    )
    sealed = build_oracle_contradiction_resolution_report(
        payload,
        strategic_narrative_report=current,
        strategic_memory_horizon_report=sealed_memory,
        now_utc=_NOW,
    )

    assert mixed.history_integrity_status == "MIXED_HISTORY"
    assert mixed.integrity_penalty_score > 0.0
    assert sealed.history_integrity_status == "SEALED_HISTORY"
    assert sealed.integrity_penalty_score == 0.0
    assert mixed.items[0].resolution_priority_score < sealed.items[0].resolution_priority_score


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
def test_contradiction_resolution_operator_actions_change_under_exact_confirmed_pressure(tmp_path: Path) -> None:
    payload = _payload(stressed=True)
    _write_cadence_doctrine_report(tmp_path, payload, confirmation=True)
    current = build_oracle_strategic_narrative_report(payload, now_utc=_NOW)
    memory = build_oracle_strategic_memory_horizon_report(current, history_reports=[build_oracle_strategic_narrative_report(_payload(stressed=False), now_utc=_NOW.replace(hour=7))], now_utc=_NOW)

    report = build_oracle_contradiction_resolution_report(
        payload,
        strategic_narrative_report=current,
        strategic_memory_horizon_report=memory,
        repo_root=tmp_path,
        search_root=tmp_path / "docs" / "artifacts",
        now_utc=_NOW,
    )

    assert report.exact_cadence_signal_classification == "EXACT_CONFIRMED_PRESSURE"
    assert any("compress the decision loop" in action.lower() for action in report.operator_actions)
    assert any("repeated exact sealed confirmations" in item.recommended_resolution.lower() for item in report.items)
