from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from strategy_validator.contracts.oracle import OracleAdvisoryInput, OracleSensorIngestionInput
from strategy_validator.validator.oracle_regime_transition import compare_strategic_fusion_reports
from strategy_validator.validator.oracle_sensors import normalize_sensor_input
from strategy_validator.validator.oracle_signal_fusion import build_oracle_strategic_fusion_report
from strategy_validator.validator.oracle_doctrine_adaptation import build_oracle_doctrine_adaptation_report
from strategy_validator.validator.oracle_research_planner import build_oracle_research_priority_report
from strategy_validator.validator.oracle_strategic_briefing import build_oracle_strategic_briefing, render_oracle_strategic_briefing_markdown
from strategy_validator.validator.oracle_strategic_memory_horizon import build_oracle_strategic_memory_horizon_report
from strategy_validator.validator.oracle_strategic_narrative import build_oracle_strategic_narrative_report
from strategy_validator.validator.oracle_strategic_artifact_evidence import build_oracle_strategic_artifact_evidence_bundle, verify_oracle_strategic_artifact_evidence_bundle
from strategy_validator.validator.strategy_health_posterior import build_strategy_health_posterior_report


@pytest.mark.constitutional
def test_sensor_ingestion_normalizes_raw_payload_into_advisory_input() -> None:
    raw = OracleSensorIngestionInput.model_validate(
        {
            "generated_for_utc": "2026-04-13T08:10:00Z",
            "universe_label": "US_EQ_FACTORS",
            "macro_raw": {
                "yield_curve_slope_bps": 95.0,
                "high_yield_credit_spread_bps": 280.0,
                "equity_bond_correlation_20d": -0.35,
                "cross_asset_correlation_20d": -0.10,
                "realized_volatility_20d": 14.0,
                "realized_volatility_252d": 18.0,
            },
            "semantic_raw": {
                "hawkish_document_ratio": 0.22,
                "dovish_document_ratio": 0.41,
                "geopolitical_headline_share": 0.12,
                "contradiction_count": 0,
                "belief_conflict_score": 0.08,
            },
            "microstructure_raw": {
                "buy_volume": 110.0,
                "sell_volume": 90.0,
                "median_spread_bps": 9.5,
                "baseline_spread_bps": 11.0,
                "top_book_depth_usd": 950000.0,
                "baseline_top_book_depth_usd": 1000000.0,
                "toxic_flow_ratio": 0.18,
            },
            "strategies": [],
        }
    )
    report = normalize_sensor_input(raw)
    assert report.advisory_input.sensors.semantic.inflation_hawkishness_score < 0
    assert report.advisory_input.sensors.microstructure.order_flow_imbalance > 0
    assert report.advisory_input.sensors.macro.realized_volatility_zscore < 0
    assert report.quality_score > 0.8


@pytest.mark.constitutional
def test_signal_fusion_surfaces_opportunity_posture_for_supportive_stack() -> None:
    payload = OracleAdvisoryInput.model_validate(
        {
            "generated_for_utc": "2026-04-13T08:10:00Z",
            "universe_label": "US_EQ_FACTORS",
            "sensors": {
                "semantic": {
                    "inflation_hawkishness_score": -0.4,
                    "geopolitical_risk_index": 0.10,
                    "narrative_contradiction_count": 0,
                    "tribunal_belief_conflict": 0.05,
                },
                "microstructure": {
                    "vpin": 0.18,
                    "order_flow_imbalance": 0.22,
                    "spread_variance_zscore": -0.4,
                    "liquidity_thinning_score": 0.08,
                },
                "macro": {
                    "yield_curve_slope_bps": 105.0,
                    "high_yield_credit_spread_bps": 265.0,
                    "equity_bond_correlation": -0.30,
                    "cross_asset_correlation_stress": 0.12,
                    "realized_volatility_zscore": -0.55,
                },
            },
            "strategies": [
                {
                    "strategy_id": "trend-b",
                    "strategy_type": "TREND_FOLLOWING",
                    "prior_edge_confidence": 0.72,
                    "deflated_sharpe_ratio": 0.94,
                    "cpcv_lower_bound": 0.30,
                    "realized_live_sharpe": 0.72,
                    "recent_win_rate": 0.61,
                    "drawdown_fraction": 0.04,
                    "expected_regimes": ["RISK_ON_LOW_VOL", "TRANSITION"],
                }
            ],
        }
    )
    fusion = build_oracle_strategic_fusion_report(payload, now_utc=datetime(2026, 4, 13, 8, 15, tzinfo=timezone.utc))
    assert fusion.strategic_posture in {"OPPORTUNITY_BIASED", "BALANCED_OBSERVATION", "CAUTION_BIASED"}
    assert fusion.opportunity_score > fusion.caution_score
    assert fusion.caution_score < 0.55


@pytest.mark.constitutional
def test_strategy_health_posterior_flags_degrading_strategy_under_caution_stack() -> None:
    payload = OracleAdvisoryInput.model_validate(
        {
            "generated_for_utc": "2026-04-13T08:00:00Z",
            "universe_label": "GLOBAL_MACRO",
            "sensors": {
                "semantic": {
                    "inflation_hawkishness_score": 0.6,
                    "geopolitical_risk_index": 0.78,
                    "narrative_contradiction_count": 4,
                    "tribunal_belief_conflict": 0.84,
                },
                "microstructure": {
                    "vpin": 0.72,
                    "order_flow_imbalance": -0.35,
                    "spread_variance_zscore": 1.8,
                    "liquidity_thinning_score": 0.76,
                },
                "macro": {
                    "yield_curve_slope_bps": -40.0,
                    "high_yield_credit_spread_bps": 445.0,
                    "equity_bond_correlation": 0.75,
                    "cross_asset_correlation_stress": 0.88,
                    "realized_volatility_zscore": 1.9,
                },
            },
            "strategies": [
                {
                    "strategy_id": "meanrev-a",
                    "strategy_type": "MEAN_REVERSION",
                    "prior_edge_confidence": 0.68,
                    "deflated_sharpe_ratio": 0.88,
                    "cpcv_lower_bound": 0.45,
                    "realized_live_sharpe": -0.15,
                    "recent_win_rate": 0.38,
                    "drawdown_fraction": 0.17,
                    "expected_regimes": ["RISK_ON_LOW_VOL", "TRANSITION"],
                }
            ],
        }
    )
    fusion = build_oracle_strategic_fusion_report(payload)
    posterior = build_strategy_health_posterior_report(payload, fusion)
    state = posterior.strategies[0]
    assert state.posterior_edge_confidence < state.prior_edge_confidence
    assert state.recommended_action in {"CANARY", "HIBERNATE"}
    assert posterior.degraded_strategy_ids == ["meanrev-a"]


@pytest.mark.constitutional
def test_regime_transition_detects_structural_break_candidate() -> None:
    previous = build_oracle_strategic_fusion_report(
        OracleAdvisoryInput.model_validate(
            {
                "generated_for_utc": "2026-04-13T06:00:00Z",
                "universe_label": "US_EQ",
                "sensors": {
                    "semantic": {
                        "inflation_hawkishness_score": -0.4,
                        "geopolitical_risk_index": 0.08,
                        "narrative_contradiction_count": 0,
                        "tribunal_belief_conflict": 0.04,
                    },
                    "microstructure": {
                        "vpin": 0.16,
                        "order_flow_imbalance": 0.20,
                        "spread_variance_zscore": -0.3,
                        "liquidity_thinning_score": 0.06,
                    },
                    "macro": {
                        "yield_curve_slope_bps": 110.0,
                        "high_yield_credit_spread_bps": 255.0,
                        "equity_bond_correlation": -0.42,
                        "cross_asset_correlation_stress": 0.10,
                        "realized_volatility_zscore": -0.60,
                    },
                },
                "strategies": [],
            }
        ),
        now_utc=datetime(2026, 4, 13, 6, 5, tzinfo=timezone.utc),
    )
    current = build_oracle_strategic_fusion_report(
        OracleAdvisoryInput.model_validate(
            {
                "generated_for_utc": "2026-04-13T09:00:00Z",
                "universe_label": "US_EQ",
                "sensors": {
                    "semantic": {
                        "inflation_hawkishness_score": 0.8,
                        "geopolitical_risk_index": 0.82,
                        "narrative_contradiction_count": 5,
                        "tribunal_belief_conflict": 0.94,
                    },
                    "microstructure": {
                        "vpin": 0.86,
                        "order_flow_imbalance": -0.52,
                        "spread_variance_zscore": 2.2,
                        "liquidity_thinning_score": 0.84,
                    },
                    "macro": {
                        "yield_curve_slope_bps": -65.0,
                        "high_yield_credit_spread_bps": 520.0,
                        "equity_bond_correlation": 0.91,
                        "cross_asset_correlation_stress": 0.96,
                        "realized_volatility_zscore": 2.5,
                    },
                },
                "strategies": [],
            }
        ),
        now_utc=datetime(2026, 4, 13, 9, 5, tzinfo=timezone.utc),
    )
    transition = compare_strategic_fusion_reports(previous, current)
    assert transition.transition_classification in {"STRUCTURAL_BREAK_CANDIDATE", "TRANSITIONING"}
    assert transition.previous_strategic_posture != transition.current_strategic_posture


@pytest.mark.constitutional
def test_oracle_strategic_briefing_cli_emits_forward_looking_report(tmp_path: Path) -> None:
    payload = {
        "generated_for_utc": "2026-04-13T08:10:00Z",
        "universe_label": "US_EQ_FACTORS",
        "sensors": {
            "semantic": {
                "inflation_hawkishness_score": -0.2,
                "geopolitical_risk_index": 0.10,
                "narrative_contradiction_count": 0,
                "tribunal_belief_conflict": 0.05,
            },
            "microstructure": {
                "vpin": 0.21,
                "order_flow_imbalance": 0.18,
                "spread_variance_zscore": -0.1,
                "liquidity_thinning_score": 0.12,
            },
            "macro": {
                "yield_curve_slope_bps": 95.0,
                "high_yield_credit_spread_bps": 280.0,
                "equity_bond_correlation": -0.35,
                "cross_asset_correlation_stress": 0.08,
                "realized_volatility_zscore": -0.45,
            },
        },
        "strategies": [
            {
                "strategy_id": "trend-b",
                "strategy_type": "TREND_FOLLOWING",
                "prior_edge_confidence": 0.72,
                "deflated_sharpe_ratio": 0.94,
                "cpcv_lower_bound": 0.30,
                "realized_live_sharpe": 0.58,
                "recent_win_rate": 0.57,
                "drawdown_fraction": 0.04,
                "expected_regimes": ["RISK_ON_LOW_VOL", "TRANSITION"],
            }
        ],
    }
    input_path = tmp_path / "oracle_input.json"
    input_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    from strategy_validator.cli.rollout_ops import main

    output_path = tmp_path / "ORACLE_STRATEGIC_BRIEFING_REPORT.json"
    markdown_path = tmp_path / "ORACLE_STRATEGIC_BRIEFING_REPORT.md"
    rc = main([
        "oracle-strategic-briefing",
        str(input_path),
        "--output",
        str(output_path),
        "--markdown-output",
        str(markdown_path),
    ])
    assert rc == 0
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["strategic_posture"] in {
        "OPPORTUNITY_BIASED",
        "BALANCED_OBSERVATION",
        "CAUTION_BIASED",
        "DEFENSIVE_RESEARCH",
        "RESEARCH_FREEZE",
    }
    assert any(section["section_id"] == "opportunity_queue" for section in report["sections"])
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "ORACLE STRATEGIC BRIEFING" in markdown
    assert "Strategic Posture" in markdown


@pytest.mark.constitutional
def test_strategic_briefing_surfaces_preferred_backing_source_across_sections() -> None:
    payload = OracleAdvisoryInput.model_validate(
        {
            "generated_for_utc": "2026-04-13T08:10:00Z",
            "universe_label": "US_EQ_FACTORS",
            "sensors": {
                "semantic": {
                    "inflation_hawkishness_score": -0.2,
                    "geopolitical_risk_index": 0.10,
                    "narrative_contradiction_count": 0,
                    "tribunal_belief_conflict": 0.05,
                },
                "microstructure": {
                    "vpin": 0.18,
                    "order_flow_imbalance": 0.24,
                    "spread_variance_zscore": -0.4,
                    "liquidity_thinning_score": 0.08,
                },
                "macro": {
                    "yield_curve_slope_bps": 105.0,
                    "high_yield_credit_spread_bps": 265.0,
                    "equity_bond_correlation": -0.30,
                    "cross_asset_correlation_stress": 0.12,
                    "realized_volatility_zscore": -0.55,
                },
            },
            "strategies": [],
        }
    )
    prior = build_oracle_strategic_briefing(payload, now_utc=datetime(2026, 4, 13, 7, 0, tzinfo=timezone.utc))
    current = build_oracle_strategic_briefing(
        payload,
        strategic_memory_horizon_report=build_oracle_strategic_memory_horizon_report(
            build_oracle_strategic_narrative_report(payload, now_utc=datetime(2026, 4, 13, 8, 15, tzinfo=timezone.utc)),
            sealed_history_reports=[build_oracle_strategic_narrative_report(payload, now_utc=datetime(2026, 4, 13, 7, 15, tzinfo=timezone.utc))],
            sealed_history_manifest_paths=["docs/artifacts/oracle/ORACLE_STRATEGIC_STACK_EVIDENCE_MANIFEST.json"],
            require_sealed_history=True,
            now_utc=datetime(2026, 4, 13, 8, 20, tzinfo=timezone.utc),
        ),
        previous_fusion_report=build_oracle_strategic_fusion_report(payload, now_utc=datetime(2026, 4, 13, 7, 5, tzinfo=timezone.utc)),
        now_utc=datetime(2026, 4, 13, 8, 25, tzinfo=timezone.utc),
    )

    assert current.preferred_strategic_backing_source == "strategic_stack_manifest"
    assert current.preferred_strategic_backing_classification == "SEALED_STRATEGIC_STACK_BACKED"
    for section_id in {"strategic_posture", "doctrine_adaptation", "research_priorities", "strategic_campaigns"}:
        section = next(item for item in current.sections if item.section_id == section_id)
        assert section.preferred_strategic_backing_source == "strategic_stack_manifest"
        assert section.preferred_strategic_backing_classification == "SEALED_STRATEGIC_STACK_BACKED"
        assert any(fact.startswith("preferred_backing_source=") for fact in section.facts)

    markdown = render_oracle_strategic_briefing_markdown(current)
    assert "Preferred strategic backing source: strategic_stack_manifest" in markdown
    assert "Preferred strategic backing classification: SEALED_STRATEGIC_STACK_BACKED" in markdown


@pytest.mark.constitutional
def test_strategic_briefing_prefers_exact_artifact_evidence_for_doctrine_section(tmp_path: Path) -> None:
    payload = OracleAdvisoryInput.model_validate(
        {
            "generated_for_utc": "2026-04-13T08:10:00Z",
            "universe_label": "US_EQ_FACTORS",
            "sensors": {
                "semantic": {
                    "inflation_hawkishness_score": 0.55,
                    "geopolitical_risk_index": 0.64,
                    "narrative_contradiction_count": 3,
                    "tribunal_belief_conflict": 0.68,
                },
                "microstructure": {
                    "vpin": 0.72,
                    "order_flow_imbalance": -0.35,
                    "spread_variance_zscore": 2.2,
                    "liquidity_thinning_score": 0.58,
                },
                "macro": {
                    "yield_curve_slope_bps": 38.0,
                    "high_yield_credit_spread_bps": 470.0,
                    "equity_bond_correlation": 0.34,
                    "cross_asset_correlation_stress": 0.66,
                    "realized_volatility_zscore": 1.8,
                },
            },
            "strategies": [],
        }
    )

    horizon = build_oracle_strategic_memory_horizon_report(
        build_oracle_strategic_narrative_report(payload, now_utc=datetime(2026, 4, 13, 8, 15, tzinfo=timezone.utc)),
        sealed_history_reports=[build_oracle_strategic_narrative_report(payload, now_utc=datetime(2026, 4, 13, 7, 15, tzinfo=timezone.utc))],
        sealed_history_manifest_paths=["docs/artifacts/oracle/ORACLE_STRATEGIC_STACK_EVIDENCE_MANIFEST.json"],
        require_sealed_history=True,
        now_utc=datetime(2026, 4, 13, 8, 20, tzinfo=timezone.utc),
    )
    doctrine = build_oracle_doctrine_adaptation_report(
        payload,
        fusion_report=build_oracle_strategic_fusion_report(payload, now_utc=datetime(2026, 4, 13, 8, 25, tzinfo=timezone.utc)),
        strategic_memory_horizon_report=horizon,
        now_utc=datetime(2026, 4, 13, 8, 25, tzinfo=timezone.utc),
    )

    report_dir = tmp_path / 'docs' / 'artifacts' / 'doctrine'
    report_dir.mkdir(parents=True)
    doctrine_path = report_dir / 'ORACLE_DOCTRINE_ADAPTATION_REPORT.json'
    doctrine_path.write_text(doctrine.model_dump_json(indent=2), encoding='utf-8')

    manifest, _ = build_oracle_strategic_artifact_evidence_bundle(
        report_path=doctrine_path,
        repo_root=tmp_path,
        now_utc=datetime(2026, 4, 13, 8, 30, tzinfo=timezone.utc),
    )
    manifest_path = report_dir / 'ORACLE_DOCTRINE_ADAPTATION_EVIDENCE_MANIFEST.json'
    manifest_path.write_text(manifest.model_dump_json(indent=2), encoding='utf-8')
    verification = verify_oracle_strategic_artifact_evidence_bundle(manifest_path=manifest_path, repo_root=tmp_path)
    verification_path = report_dir / 'ORACLE_DOCTRINE_ADAPTATION_EVIDENCE_MANIFEST.verification.json'
    verification_path.write_text(verification.model_dump_json(indent=2), encoding='utf-8')

    report = build_oracle_strategic_briefing(
        payload,
        doctrine_adaptation_report=doctrine,
        doctrine_adaptation_report_path=doctrine_path,
        strategic_memory_horizon_report=horizon,
        repo_root=tmp_path,
        search_root=tmp_path / 'docs' / 'artifacts',
        now_utc=datetime(2026, 4, 13, 8, 35, tzinfo=timezone.utc),
    )

    section = next(item for item in report.sections if item.section_id == 'doctrine_adaptation')
    assert report.preferred_strategic_backing_source == 'strategic_stack_manifest'
    assert section.preferred_strategic_backing_source == 'strategic_artifact_evidence_manifest'
    assert section.preferred_strategic_backing_classification == 'SEALED_STRATEGIC_STACK_BACKED'
    assert section.preferred_strategic_artifact_evidence_manifest == str(manifest_path)
    assert section.preferred_strategic_artifact_evidence_kind == 'doctrine_adaptation'
    assert section.preferred_strategic_artifact_evidence_status == 'VERIFIED'
    assert any(fact.startswith('strategic_artifact_evidence_manifest=') for fact in section.facts)
    assert 'strategic_artifact_evidence:doctrine_adaptation' in section.provenance_refs

    markdown = render_oracle_strategic_briefing_markdown(report)
    assert 'Preferred strategic artifact evidence kind: doctrine_adaptation' in markdown
    assert 'Preferred strategic artifact evidence status: VERIFIED' in markdown


@pytest.mark.constitutional
def test_signal_fusion_surfaces_exact_sealed_support_when_present(tmp_path: Path) -> None:
    payload = OracleAdvisoryInput.model_validate(
        {
            "generated_for_utc": "2026-04-13T08:10:00Z",
            "universe_label": "US_EQ_FACTORS",
            "sensors": {
                "semantic": {
                    "inflation_hawkishness_score": 0.25,
                    "geopolitical_risk_index": 0.42,
                    "narrative_contradiction_count": 2,
                    "tribunal_belief_conflict": 0.48,
                },
                "microstructure": {
                    "vpin": 0.51,
                    "order_flow_imbalance": 0.08,
                    "spread_variance_zscore": 0.4,
                    "liquidity_thinning_score": 0.34,
                },
                "macro": {
                    "yield_curve_slope_bps": 42.0,
                    "high_yield_credit_spread_bps": 350.0,
                    "equity_bond_correlation": 0.18,
                    "cross_asset_correlation_stress": 0.44,
                    "realized_volatility_zscore": 0.6,
                },
            },
            "strategies": [
                {
                    "strategy_id": "trend-b",
                    "strategy_type": "TREND_FOLLOWING",
                    "prior_edge_confidence": 0.66,
                    "deflated_sharpe_ratio": 0.91,
                    "cpcv_lower_bound": 0.30,
                    "realized_live_sharpe": 0.48,
                    "recent_win_rate": 0.56,
                    "drawdown_fraction": 0.06,
                    "expected_regimes": ["RISK_ON_LOW_VOL", "TRANSITION"],
                }
            ],
        }
    )
    current_narrative = build_oracle_strategic_narrative_report(payload, now_utc=datetime(2026, 4, 13, 8, 12, tzinfo=timezone.utc))
    sealed_history = build_oracle_strategic_memory_horizon_report(
        current_narrative,
        sealed_history_reports=[build_oracle_strategic_narrative_report(payload, now_utc=datetime(2026, 4, 13, 7, 12, tzinfo=timezone.utc))],
        sealed_history_manifest_paths=["docs/artifacts/oracle/STACK_07.json"],
        require_sealed_history=True,
        now_utc=datetime(2026, 4, 13, 8, 13, tzinfo=timezone.utc),
    )
    doctrine = build_oracle_doctrine_adaptation_report(payload, strategic_memory_horizon_report=sealed_history, now_utc=datetime(2026, 4, 13, 8, 14, tzinfo=timezone.utc))
    priorities = build_oracle_research_priority_report(payload, strategic_memory_horizon_report=sealed_history, doctrine_adaptation_report=doctrine, now_utc=datetime(2026, 4, 13, 8, 15, tzinfo=timezone.utc))

    artifacts_root = tmp_path / "docs" / "artifacts" / "oracle"
    artifacts_root.mkdir(parents=True)
    doctrine_path = artifacts_root / "ORACLE_DOCTRINE_ADAPTATION_REPORT.json"
    doctrine_path.write_text(doctrine.model_dump_json(indent=2), encoding="utf-8")
    priorities_path = artifacts_root / "ORACLE_RESEARCH_PRIORITY_REPORT.json"
    priorities_path.write_text(priorities.model_dump_json(indent=2), encoding="utf-8")
    for idx, report_path in enumerate((doctrine_path, priorities_path), start=1):
        manifest, _ = build_oracle_strategic_artifact_evidence_bundle(report_path=report_path, repo_root=tmp_path, now_utc=datetime(2026, 4, 13, 8, 16, tzinfo=timezone.utc))
        manifest_path = artifacts_root / f"ORACLE_STRATEGIC_ARTIFACT_EVIDENCE_{idx}.json"
        manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
        (artifacts_root / f"ORACLE_STRATEGIC_ARTIFACT_EVIDENCE_{idx}.verification.json").write_text(json.dumps({
            "verified_at_utc": datetime(2026, 4, 13, 8, 17, tzinfo=timezone.utc).isoformat(),
            "manifest_path": str(manifest_path),
            "status": "VERIFIED",
            "artifact_digests_verified": True,
            "signature_verified": False,
            "verified_subject_count": len(manifest.subjects),
            "digest_mismatches": [],
            "missing_artifact_paths": [],
            "notes": [],
        }, indent=2), encoding="utf-8")

    plain = build_oracle_strategic_fusion_report(payload, now_utc=datetime(2026, 4, 13, 8, 18, tzinfo=timezone.utc))
    supported = build_oracle_strategic_fusion_report(
        payload,
        doctrine_adaptation_report_path=doctrine_path,
        research_priority_report_path=priorities_path,
        repo_root=tmp_path,
        search_root=tmp_path / "docs" / "artifacts",
        now_utc=datetime(2026, 4, 13, 8, 18, tzinfo=timezone.utc),
    )
    assert supported.exact_evidence_support_score >= 0.99
    assert supported.preferred_strategic_backing_source == "strategic_artifact_evidence_manifest"
    assert supported.preferred_strategic_backing_classification == "SEALED_STRATEGIC_STACK_BACKED"
    assert supported.caution_score < plain.caution_score
    assert any("exact sealed strategist support" in item for item in supported.opportunity_factors)


@pytest.mark.constitutional
def test_strategy_health_posterior_prefers_exact_sealed_support_when_present(tmp_path: Path) -> None:
    payload = OracleAdvisoryInput.model_validate(
        {
            "generated_for_utc": "2026-04-13T08:10:00Z",
            "universe_label": "GLOBAL_MACRO",
            "sensors": {
                "semantic": {
                    "inflation_hawkishness_score": 0.45,
                    "geopolitical_risk_index": 0.58,
                    "narrative_contradiction_count": 2,
                    "tribunal_belief_conflict": 0.52,
                },
                "microstructure": {
                    "vpin": 0.44,
                    "order_flow_imbalance": -0.08,
                    "spread_variance_zscore": 0.8,
                    "liquidity_thinning_score": 0.35,
                },
                "macro": {
                    "yield_curve_slope_bps": 18.0,
                    "high_yield_credit_spread_bps": 360.0,
                    "equity_bond_correlation": 0.22,
                    "cross_asset_correlation_stress": 0.48,
                    "realized_volatility_zscore": 0.7,
                },
            },
            "strategies": [
                {
                    "strategy_id": "macro-a",
                    "strategy_type": "GLOBAL_MACRO",
                    "prior_edge_confidence": 0.58,
                    "deflated_sharpe_ratio": 0.85,
                    "cpcv_lower_bound": 0.35,
                    "realized_live_sharpe": 0.16,
                    "recent_win_rate": 0.53,
                    "drawdown_fraction": 0.09,
                    "expected_regimes": ["TRANSITION", "RISK_OFF_HIGH_VOL"],
                }
            ],
        }
    )
    current_narrative = build_oracle_strategic_narrative_report(payload, now_utc=datetime(2026, 4, 13, 8, 20, tzinfo=timezone.utc))
    sealed_history = build_oracle_strategic_memory_horizon_report(
        current_narrative,
        sealed_history_reports=[build_oracle_strategic_narrative_report(payload, now_utc=datetime(2026, 4, 13, 7, 20, tzinfo=timezone.utc))],
        sealed_history_manifest_paths=["docs/artifacts/oracle/STACK_07.json"],
        require_sealed_history=True,
        now_utc=datetime(2026, 4, 13, 8, 21, tzinfo=timezone.utc),
    )
    doctrine = build_oracle_doctrine_adaptation_report(payload, strategic_memory_horizon_report=sealed_history, now_utc=datetime(2026, 4, 13, 8, 22, tzinfo=timezone.utc))
    priorities = build_oracle_research_priority_report(payload, strategic_memory_horizon_report=sealed_history, doctrine_adaptation_report=doctrine, now_utc=datetime(2026, 4, 13, 8, 23, tzinfo=timezone.utc))
    fusion = build_oracle_strategic_fusion_report(payload, now_utc=datetime(2026, 4, 13, 8, 24, tzinfo=timezone.utc))

    artifacts_root = tmp_path / "docs" / "artifacts" / "oracle"
    artifacts_root.mkdir(parents=True)
    doctrine_path = artifacts_root / "ORACLE_DOCTRINE_ADAPTATION_REPORT.json"
    doctrine_path.write_text(doctrine.model_dump_json(indent=2), encoding="utf-8")
    priorities_path = artifacts_root / "ORACLE_RESEARCH_PRIORITY_REPORT.json"
    priorities_path.write_text(priorities.model_dump_json(indent=2), encoding="utf-8")
    for idx, report_path in enumerate((doctrine_path, priorities_path), start=1):
        manifest, _ = build_oracle_strategic_artifact_evidence_bundle(report_path=report_path, repo_root=tmp_path, now_utc=datetime(2026, 4, 13, 8, 25, tzinfo=timezone.utc))
        manifest_path = artifacts_root / f"ORACLE_STRATEGIC_ARTIFACT_EVIDENCE_{idx}.json"
        manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
        (artifacts_root / f"ORACLE_STRATEGIC_ARTIFACT_EVIDENCE_{idx}.verification.json").write_text(json.dumps({
            "verified_at_utc": datetime(2026, 4, 13, 8, 26, tzinfo=timezone.utc).isoformat(),
            "manifest_path": str(manifest_path),
            "status": "VERIFIED",
            "artifact_digests_verified": True,
            "signature_verified": False,
            "verified_subject_count": len(manifest.subjects),
            "digest_mismatches": [],
            "missing_artifact_paths": [],
            "notes": [],
        }, indent=2), encoding="utf-8")

    plain = build_strategy_health_posterior_report(payload, fusion, now_utc=datetime(2026, 4, 13, 8, 27, tzinfo=timezone.utc))
    supported = build_strategy_health_posterior_report(
        payload,
        fusion,
        doctrine_adaptation_report=doctrine,
        research_priority_report=priorities,
        doctrine_adaptation_report_path=doctrine_path,
        research_priority_report_path=priorities_path,
        repo_root=tmp_path,
        search_root=tmp_path / "docs" / "artifacts",
        now_utc=datetime(2026, 4, 13, 8, 27, tzinfo=timezone.utc),
    )
    assert supported.exact_evidence_support_score >= 0.99
    assert supported.strategies[0].exact_evidence_support_score >= 0.99
    assert supported.strategies[0].posterior_edge_confidence > plain.strategies[0].posterior_edge_confidence
    assert any("posterior_support_artifact_evidence_manifest=" in reason for reason in supported.strategies[0].reasons)


@pytest.mark.constitutional
def test_regime_transition_signal_surfaces_exact_sealed_support_when_present(tmp_path: Path) -> None:
    previous = build_oracle_strategic_fusion_report(
        OracleAdvisoryInput.model_validate(
            {
                "generated_for_utc": "2026-04-13T06:00:00Z",
                "universe_label": "US_EQ",
                "sensors": {
                    "semantic": {
                        "inflation_hawkishness_score": -0.25,
                        "geopolitical_risk_index": 0.10,
                        "narrative_contradiction_count": 0,
                        "tribunal_belief_conflict": 0.06,
                    },
                    "microstructure": {
                        "vpin": 0.18,
                        "order_flow_imbalance": 0.18,
                        "spread_variance_zscore": -0.2,
                        "liquidity_thinning_score": 0.08,
                    },
                    "macro": {
                        "yield_curve_slope_bps": 95.0,
                        "high_yield_credit_spread_bps": 260.0,
                        "equity_bond_correlation": -0.20,
                        "cross_asset_correlation_stress": 0.15,
                        "realized_volatility_zscore": -0.35,
                    },
                },
                "strategies": [],
            }
        ),
        now_utc=datetime(2026, 4, 13, 6, 5, tzinfo=timezone.utc),
    )
    payload = OracleAdvisoryInput.model_validate(
        {
            "generated_for_utc": "2026-04-13T09:00:00Z",
            "universe_label": "US_EQ",
            "sensors": {
                "semantic": {
                    "inflation_hawkishness_score": 0.40,
                    "geopolitical_risk_index": 0.50,
                    "narrative_contradiction_count": 2,
                    "tribunal_belief_conflict": 0.58,
                },
                "microstructure": {
                    "vpin": 0.46,
                    "order_flow_imbalance": -0.20,
                    "spread_variance_zscore": 0.9,
                    "liquidity_thinning_score": 0.36,
                },
                "macro": {
                    "yield_curve_slope_bps": 20.0,
                    "high_yield_credit_spread_bps": 350.0,
                    "equity_bond_correlation": 0.18,
                    "cross_asset_correlation_stress": 0.44,
                    "realized_volatility_zscore": 0.55,
                },
            },
            "strategies": [
                {
                    "strategy_id": "trend-a",
                    "strategy_type": "TREND_FOLLOWING",
                    "prior_edge_confidence": 0.62,
                    "deflated_sharpe_ratio": 0.84,
                    "cpcv_lower_bound": 0.28,
                    "realized_live_sharpe": 0.25,
                    "recent_win_rate": 0.54,
                    "drawdown_fraction": 0.08,
                    "expected_regimes": ["TRANSITION", "RISK_ON_LOW_VOL"],
                }
            ],
        }
    )
    current = build_oracle_strategic_fusion_report(payload, now_utc=datetime(2026, 4, 13, 9, 5, tzinfo=timezone.utc))
    current_narrative = build_oracle_strategic_narrative_report(payload, now_utc=datetime(2026, 4, 13, 9, 7, tzinfo=timezone.utc))
    sealed_history = build_oracle_strategic_memory_horizon_report(
        current_narrative,
        sealed_history_reports=[build_oracle_strategic_narrative_report(payload, now_utc=datetime(2026, 4, 13, 8, 7, tzinfo=timezone.utc))],
        sealed_history_manifest_paths=["docs/artifacts/oracle/STACK_08.json"],
        require_sealed_history=True,
        now_utc=datetime(2026, 4, 13, 9, 8, tzinfo=timezone.utc),
    )
    doctrine = build_oracle_doctrine_adaptation_report(payload, strategic_memory_horizon_report=sealed_history, now_utc=datetime(2026, 4, 13, 9, 9, tzinfo=timezone.utc))
    priorities = build_oracle_research_priority_report(payload, strategic_memory_horizon_report=sealed_history, doctrine_adaptation_report=doctrine, now_utc=datetime(2026, 4, 13, 9, 10, tzinfo=timezone.utc))

    artifacts_root = tmp_path / "docs" / "artifacts" / "oracle"
    artifacts_root.mkdir(parents=True)
    doctrine_path = artifacts_root / "ORACLE_DOCTRINE_ADAPTATION_REPORT.json"
    doctrine_path.write_text(doctrine.model_dump_json(indent=2), encoding="utf-8")
    priorities_path = artifacts_root / "ORACLE_RESEARCH_PRIORITY_REPORT.json"
    priorities_path.write_text(priorities.model_dump_json(indent=2), encoding="utf-8")
    for idx, report_path in enumerate((doctrine_path, priorities_path), start=1):
        manifest, _ = build_oracle_strategic_artifact_evidence_bundle(report_path=report_path, repo_root=tmp_path, now_utc=datetime(2026, 4, 13, 9, 11, tzinfo=timezone.utc))
        manifest_path = artifacts_root / f"ORACLE_STRATEGIC_ARTIFACT_EVIDENCE_{idx}.json"
        manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
        (artifacts_root / f"ORACLE_STRATEGIC_ARTIFACT_EVIDENCE_{idx}.verification.json").write_text(json.dumps({
            "verified_at_utc": datetime(2026, 4, 13, 9, 12, tzinfo=timezone.utc).isoformat(),
            "manifest_path": str(manifest_path),
            "status": "VERIFIED",
            "artifact_digests_verified": True,
            "signature_verified": False,
            "verified_subject_count": len(manifest.subjects),
            "digest_mismatches": [],
            "missing_artifact_paths": [],
            "notes": [],
        }, indent=2), encoding="utf-8")

    report = compare_strategic_fusion_reports(
        previous,
        current,
        doctrine_adaptation_report_path=doctrine_path,
        research_priority_report_path=priorities_path,
        repo_root=tmp_path,
        search_root=tmp_path / "docs" / "artifacts",
        now_utc=datetime(2026, 4, 13, 9, 13, tzinfo=timezone.utc),
    )
    assert report.exact_evidence_support_score >= 0.99
    assert report.preferred_strategic_backing_source == "strategic_artifact_evidence_manifest"
    assert report.preferred_strategic_backing_classification == "SEALED_STRATEGIC_STACK_BACKED"
    assert any("transition_support_artifact_evidence_manifest=" in driver for driver in report.drivers)


@pytest.mark.constitutional
def test_strategic_summaries_surface_exact_cadence_driver(tmp_path: Path) -> None:
    payload = OracleAdvisoryInput.model_validate(
        {
            "generated_for_utc": "2026-04-13T09:00:00Z",
            "universe_label": "US_EQ",
            "sensors": {
                "semantic": {
                    "inflation_hawkishness_score": 0.25,
                    "geopolitical_risk_index": 0.42,
                    "narrative_contradiction_count": 2,
                    "tribunal_belief_conflict": 0.36,
                },
                "microstructure": {
                    "vpin": 0.35,
                    "order_flow_imbalance": 0.08,
                    "spread_variance_zscore": 0.25,
                    "liquidity_thinning_score": 0.22,
                },
                "macro": {
                    "yield_curve_slope_bps": 35.0,
                    "high_yield_credit_spread_bps": 310.0,
                    "equity_bond_correlation": 0.10,
                    "cross_asset_correlation_stress": 0.30,
                    "realized_volatility_zscore": 0.15,
                },
            },
            "strategies": [
                {
                    "strategy_id": "carry-a",
                    "strategy_type": "CARRY",
                    "prior_edge_confidence": 0.64,
                    "deflated_sharpe_ratio": 0.82,
                    "cpcv_lower_bound": 0.24,
                    "realized_live_sharpe": 0.31,
                    "recent_win_rate": 0.55,
                    "drawdown_fraction": 0.07,
                    "expected_regimes": ["TRANSITION", "RISK_ON_LOW_VOL"],
                }
            ],
        }
    )
    doctrine = build_oracle_doctrine_adaptation_report(payload, now_utc=datetime(2026, 4, 13, 9, 5, tzinfo=timezone.utc))
    stressed_items = [
        item.model_copy(update={"exact_evidence_support_score": 1.0, "stress_score": max(item.stress_score, 0.78), "review_priority_score": max(item.review_priority_score, 0.81)})
        for item in doctrine.items
    ]
    doctrine1 = doctrine.model_copy(update={"generated_at_utc": datetime(2026, 4, 13, 9, 5, tzinfo=timezone.utc), "exact_evidence_support_score": 1.0, "items": stressed_items})
    doctrine2 = doctrine.model_copy(update={"generated_at_utc": datetime(2026, 4, 13, 9, 6, tzinfo=timezone.utc), "exact_evidence_support_score": 1.0, "items": stressed_items})
    artifacts_root = tmp_path / "docs" / "artifacts" / "oracle"
    artifacts_root.mkdir(parents=True)
    (artifacts_root / "DOCTRINE_1.json").write_text(doctrine1.model_dump_json(indent=2), encoding="utf-8")
    (artifacts_root / "DOCTRINE_2.json").write_text(doctrine2.model_dump_json(indent=2), encoding="utf-8")

    fusion = build_oracle_strategic_fusion_report(payload, repo_root=tmp_path, search_root=artifacts_root, now_utc=datetime(2026, 4, 13, 9, 7, tzinfo=timezone.utc))
    narrative = build_oracle_strategic_narrative_report(payload, repo_root=tmp_path, search_root=artifacts_root, now_utc=datetime(2026, 4, 13, 9, 8, tzinfo=timezone.utc))
    briefing = build_oracle_strategic_briefing(payload, repo_root=tmp_path, search_root=artifacts_root, now_utc=datetime(2026, 4, 13, 9, 9, tzinfo=timezone.utc))
    markdown = render_oracle_strategic_briefing_markdown(briefing)

    assert fusion.exact_cadence_signal_classification == "EXACT_CONFIRMED_PRESSURE"
    assert fusion.exact_feedback_confirmation_count >= 2
    assert "cadence=EXACT_CONFIRMED_PRESSURE" in fusion.summary_line

    assert narrative.exact_cadence_signal_classification == "EXACT_CONFIRMED_PRESSURE"
    assert narrative.exact_feedback_confirmation_count >= 2
    assert "cadence=EXACT_CONFIRMED_PRESSURE" in narrative.summary_line

    posture_section = next(section for section in briefing.sections if section.section_id == "strategic_posture")
    narrative_section = next(section for section in briefing.sections if section.section_id == "strategic_narrative")
    assert briefing.exact_cadence_signal_classification == "EXACT_CONFIRMED_PRESSURE"
    assert posture_section.exact_cadence_signal_classification == "EXACT_CONFIRMED_PRESSURE"
    assert narrative_section.exact_cadence_signal_classification == "EXACT_CONFIRMED_PRESSURE"
    assert "Exact cadence signal: EXACT_CONFIRMED_PRESSURE" in markdown
