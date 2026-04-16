from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from strategy_validator.validator.oracle_advisory import (
    build_oracle_evidence_bundle,
    build_oracle_morning_attestation,
    load_oracle_input,
    render_oracle_morning_attestation_markdown,
)
from strategy_validator.validator.oracle_transition import compare_oracle_evidence
from strategy_validator.validator.rollout_ops import generate_snapshot_signing_keypair


def _write_oracle_evidence(
    *,
    repo_root: Path,
    base_dir: Path,
    payload: dict,
    private_key: Path | None,
) -> tuple[Path, Path | None]:
    input_path = base_dir / "oracle_input.json"
    input_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    loaded = load_oracle_input(input_path)
    attestation = build_oracle_morning_attestation(
        payload=loaded,
        now_utc=datetime(2026, 4, 13, 8, 11, tzinfo=timezone.utc),
    )
    attestation_path = base_dir / "ORACLE_MORNING_ATTESTATION.json"
    attestation_path.write_text(json.dumps(attestation.model_dump(mode="json"), indent=2), encoding="utf-8")
    markdown_path = base_dir / "ORACLE_MORNING_ATTESTATION.md"
    markdown_path.write_text(render_oracle_morning_attestation_markdown(attestation), encoding="utf-8")
    manifest, envelope = build_oracle_evidence_bundle(
        input_path=input_path,
        attestation_path=attestation_path,
        markdown_path=markdown_path,
        repo_root=repo_root,
        signing_private_key_path=private_key,
        now_utc=datetime(2026, 4, 13, 8, 12, tzinfo=timezone.utc),
    )
    manifest_path = base_dir / "ORACLE_EVIDENCE.json"
    manifest_path.write_text(json.dumps(manifest.model_dump(mode="json"), indent=2), encoding="utf-8")
    dsse_path: Path | None = None
    if envelope is not None:
        dsse_path = base_dir / "ORACLE_EVIDENCE.dsse.json"
        dsse_path.write_text(json.dumps(envelope.model_dump(mode="json"), indent=2), encoding="utf-8")
    return manifest_path, dsse_path


@pytest.mark.constitutional
def test_oracle_transition_detects_epistemic_escalation(tmp_path: Path) -> None:
    repo_root = tmp_path
    previous_dir = repo_root / "docs" / "artifacts" / "oracle_prev"
    current_dir = repo_root / "docs" / "artifacts" / "oracle_curr"
    previous_dir.mkdir(parents=True)
    current_dir.mkdir(parents=True)

    private_key = repo_root / "keys" / "oracle_private.pem"
    public_key = repo_root / "keys" / "oracle_public.pem"
    generate_snapshot_signing_keypair(private_key_path=private_key, public_key_path=public_key)

    previous_payload = {
        "generated_for_utc": "2026-04-13T08:10:00Z",
        "universe_label": "US_EQ_FACTORS",
        "sensors": {
            "semantic": {
                "inflation_hawkishness_score": -0.1,
                "geopolitical_risk_index": 0.12,
                "narrative_contradiction_count": 0,
                "tribunal_belief_conflict": 0.08,
            },
            "microstructure": {
                "vpin": 0.22,
                "order_flow_imbalance": 0.10,
                "spread_variance_zscore": -0.1,
                "liquidity_thinning_score": 0.10,
            },
            "macro": {
                "yield_curve_slope_bps": 92.0,
                "high_yield_credit_spread_bps": 290.0,
                "equity_bond_correlation": -0.35,
                "cross_asset_correlation_stress": 0.10,
                "realized_volatility_zscore": -0.30,
            },
        },
        "strategies": [
            {
                "strategy_id": "trend-b",
                "strategy_type": "TREND_FOLLOWING",
                "prior_edge_confidence": 0.70,
                "deflated_sharpe_ratio": 0.92,
                "cpcv_lower_bound": 0.25,
                "realized_live_sharpe": 0.60,
                "recent_win_rate": 0.58,
                "drawdown_fraction": 0.04,
                "expected_regimes": ["RISK_ON_LOW_VOL", "TRANSITION"],
            }
        ],
    }
    current_payload = {
        "generated_for_utc": "2026-04-14T08:10:00Z",
        "universe_label": "US_EQ_FACTORS",
        "sensors": {
            "semantic": {
                "inflation_hawkishness_score": 1.4,
                "geopolitical_risk_index": 0.88,
                "narrative_contradiction_count": 5,
                "tribunal_belief_conflict": 0.91,
            },
            "microstructure": {
                "vpin": 0.84,
                "order_flow_imbalance": -0.64,
                "spread_variance_zscore": 2.1,
                "liquidity_thinning_score": 0.82,
            },
            "macro": {
                "yield_curve_slope_bps": -10.0,
                "high_yield_credit_spread_bps": 610.0,
                "equity_bond_correlation": 0.72,
                "cross_asset_correlation_stress": 0.89,
                "realized_volatility_zscore": 2.4,
            },
        },
        "strategies": [
            {
                "strategy_id": "trend-b",
                "strategy_type": "TREND_FOLLOWING",
                "prior_edge_confidence": 0.70,
                "deflated_sharpe_ratio": 0.92,
                "cpcv_lower_bound": 0.25,
                "realized_live_sharpe": -0.40,
                "recent_win_rate": 0.31,
                "drawdown_fraction": 0.24,
                "expected_regimes": ["RISK_ON_LOW_VOL", "TRANSITION"],
            }
        ],
    }

    previous_manifest, previous_dsse = _write_oracle_evidence(
        repo_root=repo_root,
        base_dir=previous_dir,
        payload=previous_payload,
        private_key=private_key,
    )
    current_manifest, current_dsse = _write_oracle_evidence(
        repo_root=repo_root,
        base_dir=current_dir,
        payload=current_payload,
        private_key=private_key,
    )

    report = compare_oracle_evidence(
        previous_manifest_path=previous_manifest,
        current_manifest_path=current_manifest,
        repo_root=repo_root,
        previous_dsse_path=previous_dsse,
        current_dsse_path=current_dsse,
        previous_public_key_path=public_key,
        current_public_key_path=public_key,
        now_utc=datetime(2026, 4, 14, 8, 13, tzinfo=timezone.utc),
    )

    assert report.comparison_status == "VERIFIED"
    assert report.transition_classification == "EPISTEMIC_ESCALATION"
    assert report.current_recommended_global_action == "DEFENSIVE_POSTURE"
    assert report.current_epistemic_status == "UNKNOWN_UNKNOWNS"
    assert report.regime_transition.drift_level in {"MATERIAL", "SEVERE"}
    assert report.strategy_transitions[0].current_action == "HIBERNATE"


@pytest.mark.constitutional
def test_oracle_transition_marks_evidence_gap_without_verification(tmp_path: Path) -> None:
    repo_root = tmp_path
    previous_dir = repo_root / "prev"
    current_dir = repo_root / "curr"
    previous_dir.mkdir(parents=True)
    current_dir.mkdir(parents=True)

    shared_payload = {
        "generated_for_utc": "2026-04-13T08:10:00Z",
        "universe_label": "US_EQ_FACTORS",
        "sensors": {
            "semantic": {
                "inflation_hawkishness_score": 0.0,
                "geopolitical_risk_index": 0.20,
                "narrative_contradiction_count": 1,
                "tribunal_belief_conflict": 0.10,
            },
            "microstructure": {
                "vpin": 0.30,
                "order_flow_imbalance": 0.05,
                "spread_variance_zscore": 0.0,
                "liquidity_thinning_score": 0.15,
            },
            "macro": {
                "yield_curve_slope_bps": 70.0,
                "high_yield_credit_spread_bps": 310.0,
                "equity_bond_correlation": -0.20,
                "cross_asset_correlation_stress": 0.12,
                "realized_volatility_zscore": 0.10,
            },
        },
        "strategies": [],
    }

    previous_manifest, _ = _write_oracle_evidence(
        repo_root=repo_root,
        base_dir=previous_dir,
        payload=shared_payload,
        private_key=None,
    )
    current_manifest, _ = _write_oracle_evidence(
        repo_root=repo_root,
        base_dir=current_dir,
        payload={**shared_payload, "generated_for_utc": "2026-04-14T08:10:00Z"},
        private_key=None,
    )

    report = compare_oracle_evidence(
        previous_manifest_path=previous_manifest,
        current_manifest_path=current_manifest,
        repo_root=repo_root,
    )

    assert report.comparison_status == "UNVERIFIED"
    assert report.transition_classification == "EVIDENCE_GAP"
    assert any("Repair missing or unverified oracle evidence" in item for item in report.operator_actions)


@pytest.mark.constitutional
def test_oracle_transition_cli_writes_markdown(tmp_path: Path) -> None:
    repo_root = tmp_path
    previous_dir = repo_root / "prev"
    current_dir = repo_root / "curr"
    previous_dir.mkdir(parents=True)
    current_dir.mkdir(parents=True)

    private_key = repo_root / "keys" / "oracle_private.pem"
    public_key = repo_root / "keys" / "oracle_public.pem"
    generate_snapshot_signing_keypair(private_key_path=private_key, public_key_path=public_key)

    previous_manifest, previous_dsse = _write_oracle_evidence(
        repo_root=repo_root,
        base_dir=previous_dir,
        payload={
            "generated_for_utc": "2026-04-13T08:10:00Z",
            "universe_label": "US_EQ_FACTORS",
            "sensors": {
                "semantic": {
                    "inflation_hawkishness_score": 0.0,
                    "geopolitical_risk_index": 0.15,
                    "narrative_contradiction_count": 0,
                    "tribunal_belief_conflict": 0.05,
                },
                "microstructure": {
                    "vpin": 0.28,
                    "order_flow_imbalance": 0.09,
                    "spread_variance_zscore": 0.0,
                    "liquidity_thinning_score": 0.11,
                },
                "macro": {
                    "yield_curve_slope_bps": 88.0,
                    "high_yield_credit_spread_bps": 300.0,
                    "equity_bond_correlation": -0.30,
                    "cross_asset_correlation_stress": 0.10,
                    "realized_volatility_zscore": -0.20,
                },
            },
            "strategies": [],
        },
        private_key=private_key,
    )
    current_manifest, current_dsse = _write_oracle_evidence(
        repo_root=repo_root,
        base_dir=current_dir,
        payload={
            "generated_for_utc": "2026-04-14T08:10:00Z",
            "universe_label": "US_EQ_FACTORS",
            "sensors": {
                "semantic": {
                    "inflation_hawkishness_score": 0.3,
                    "geopolitical_risk_index": 0.40,
                    "narrative_contradiction_count": 2,
                    "tribunal_belief_conflict": 0.20,
                },
                "microstructure": {
                    "vpin": 0.45,
                    "order_flow_imbalance": -0.18,
                    "spread_variance_zscore": 0.4,
                    "liquidity_thinning_score": 0.28,
                },
                "macro": {
                    "yield_curve_slope_bps": 40.0,
                    "high_yield_credit_spread_bps": 365.0,
                    "equity_bond_correlation": 0.10,
                    "cross_asset_correlation_stress": 0.28,
                    "realized_volatility_zscore": 0.65,
                },
            },
            "strategies": [],
        },
        private_key=private_key,
    )

    from strategy_validator.cli.rollout_ops import main

    output_path = tmp_path / "ORACLE_STATE_TRANSITION_REPORT.json"
    markdown_path = tmp_path / "ORACLE_STATE_TRANSITION_REPORT.md"
    rc = main([
        "oracle-transition",
        str(previous_manifest),
        str(current_manifest),
        "--repo-root",
        str(repo_root),
        "--previous-dsse",
        str(previous_dsse),
        "--current-dsse",
        str(current_dsse),
        "--previous-public-key",
        str(public_key),
        "--current-public-key",
        str(public_key),
        "--output",
        str(output_path),
        "--markdown-output",
        str(markdown_path),
    ])
    assert rc == 0
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["comparison_status"] == "VERIFIED"
    assert markdown_path.exists()
    assert "ORACLE STATE TRANSITION REPORT" in markdown_path.read_text(encoding="utf-8")
