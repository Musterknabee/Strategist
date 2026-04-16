from __future__ import annotations

import json
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.validator.oracle_advisory import (
    build_oracle_evidence_bundle,
    build_oracle_morning_attestation,
    load_oracle_input,
    render_oracle_morning_attestation_markdown,
)
from strategy_validator.validator.oracle_event_log import query_oracle_event_log
from strategy_validator.contracts.oracle import OracleEventLogQuerySpec
from strategy_validator.validator.rollout_ops import generate_snapshot_signing_keypair


def _write_oracle_evidence(*, repo_root: Path, base_dir: Path, payload: dict, private_key: Path | None) -> tuple[Path, Path | None]:
    input_path = base_dir / "oracle_input.json"
    input_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    loaded = load_oracle_input(input_path)
    attestation = build_oracle_morning_attestation(payload=loaded)
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
    )
    manifest_path = base_dir / "ORACLE_EVIDENCE.json"
    manifest_path.write_text(json.dumps(manifest.model_dump(mode="json"), indent=2), encoding="utf-8")
    dsse_path = None
    if envelope is not None:
        dsse_path = base_dir / "ORACLE_EVIDENCE.dsse.json"
        dsse_path.write_text(json.dumps(envelope.model_dump(mode="json"), indent=2), encoding="utf-8")
    return manifest_path, dsse_path


@pytest.mark.constitutional
def test_oracle_event_log_and_checkpoint_cli_round_trip(tmp_path: Path) -> None:
    repo_root = tmp_path
    day1_dir = repo_root / "day1"
    day2_dir = repo_root / "day2"
    day1_dir.mkdir()
    day2_dir.mkdir()

    private_key = repo_root / "oracle_private.pem"
    public_key = repo_root / "oracle_public.pem"
    generate_snapshot_signing_keypair(private_key_path=private_key, public_key_path=public_key)

    base = {
        "universe_label": "US_EQ_FACTORS",
        "strategies": [
            {
                "strategy_id": "trend-a",
                "strategy_type": "TREND_FOLLOWING",
                "prior_edge_confidence": 0.70,
                "deflated_sharpe_ratio": 0.90,
                "cpcv_lower_bound": 0.20,
                "realized_live_sharpe": 0.60,
                "recent_win_rate": 0.58,
                "drawdown_fraction": 0.04,
                "expected_regimes": ["RISK_ON_LOW_VOL", "TRANSITION"],
            },
            {
                "strategy_id": "mr-a",
                "strategy_type": "MEAN_REVERSION",
                "prior_edge_confidence": 0.62,
                "deflated_sharpe_ratio": 0.50,
                "cpcv_lower_bound": 0.10,
                "realized_live_sharpe": 0.15,
                "recent_win_rate": 0.44,
                "drawdown_fraction": 0.10,
                "expected_regimes": ["RISK_ON_LOW_VOL"],
            },
        ],
    }
    payload_day1 = {
        **base,
        "generated_for_utc": "2026-04-13T08:10:00Z",
        "sensors": {
            "semantic": {"inflation_hawkishness_score": 0.1, "geopolitical_risk_index": 0.20, "narrative_contradiction_count": 0, "tribunal_belief_conflict": 0.05},
            "microstructure": {"vpin": 0.28, "order_flow_imbalance": 0.08, "spread_variance_zscore": 0.0, "liquidity_thinning_score": 0.12},
            "macro": {"yield_curve_slope_bps": 85.0, "high_yield_credit_spread_bps": 300.0, "equity_bond_correlation": -0.20, "cross_asset_correlation_stress": 0.10, "realized_volatility_zscore": -0.10},
        },
    }
    payload_day2 = {
        **base,
        "generated_for_utc": "2026-04-14T08:10:00Z",
        "sensors": {
            "semantic": {"inflation_hawkishness_score": 1.4, "geopolitical_risk_index": 0.75, "narrative_contradiction_count": 4, "tribunal_belief_conflict": 0.70},
            "microstructure": {"vpin": 0.72, "order_flow_imbalance": -0.30, "spread_variance_zscore": 1.6, "liquidity_thinning_score": 0.60},
            "macro": {"yield_curve_slope_bps": 10.0, "high_yield_credit_spread_bps": 470.0, "equity_bond_correlation": 0.30, "cross_asset_correlation_stress": 0.62, "realized_volatility_zscore": 1.2},
        },
    }

    manifest1, dsse1 = _write_oracle_evidence(repo_root=repo_root, base_dir=day1_dir, payload=payload_day1, private_key=private_key)
    manifest2, dsse2 = _write_oracle_evidence(repo_root=repo_root, base_dir=day2_dir, payload=payload_day2, private_key=private_key)
    assert dsse1 is not None and dsse2 is not None

    log_path = repo_root / "docs" / "artifacts" / "oracle" / "ORACLE_EVENT_LOG.jsonl"

    entry1_output = day1_dir / "ORACLE_EVENT_LOG_ENTRY.json"
    rc = main([
        "oracle-event-log-append",
        str(manifest1),
        "--repo-root", str(repo_root),
        "--dsse", str(dsse1),
        "--public-key", str(public_key),
        "--log-path", str(log_path),
        "--output", str(entry1_output),
    ])
    assert rc == 0
    entry1 = json.loads(entry1_output.read_text(encoding="utf-8"))
    assert entry1["sequence_number"] == 0

    entry2_output = day2_dir / "ORACLE_EVENT_LOG_ENTRY.json"
    rc = main([
        "oracle-event-log-append",
        str(manifest2),
        "--repo-root", str(repo_root),
        "--dsse", str(dsse2),
        "--public-key", str(public_key),
        "--log-path", str(log_path),
        "--output", str(entry2_output),
    ])
    assert rc == 0
    entry2 = json.loads(entry2_output.read_text(encoding="utf-8"))
    assert entry2["sequence_number"] == 1
    assert entry2["previous_entry_hash"] == entry1["entry_hash"]

    derived_json = log_path.with_name("ORACLE_DERIVED_VIEW.json")
    derived_md = log_path.with_name("ORACLE_DERIVED_VIEW.md")
    rc = main([
        "oracle-derived-view",
        "--log-path", str(log_path),
        "--view-label", "weekly",
        "--window-size", "2",
        "--output", str(derived_json),
        "--markdown-output", str(derived_md),
    ])
    assert rc == 0
    derived = json.loads(derived_json.read_text(encoding="utf-8"))
    assert derived["window_entry_count"] == 2
    assert derived["derived_classification"] in {"HEIGHTENED_WATCH", "DEFENSIVE_POSTURE", "RETRAIN_REVIEW"}
    assert "ORACLE DERIVED VIEW" in derived_md.read_text(encoding="utf-8")

    checkpoint_json = log_path.with_name("ORACLE_EVENT_CHECKPOINT.json")
    checkpoint_dsse = log_path.with_name("ORACLE_EVENT_CHECKPOINT.dsse.json")
    checkpoint_verify = log_path.with_name("ORACLE_EVENT_CHECKPOINT.verification.json")
    rc = main([
        "oracle-event-checkpoint",
        "--lane-path", str(log_path),
        "--repo-root", str(repo_root),
        "--view-label", "weekly",
        "--window-size", "2",
        "--signing-private-key", str(private_key),
        "--output", str(checkpoint_json),
        "--dsse-output", str(checkpoint_dsse),
        "--verification-output", str(checkpoint_verify),
    ])
    assert rc == 0
    verification = json.loads(checkpoint_verify.read_text(encoding="utf-8"))
    assert verification["status"] == "VERIFIED"

    verify_output = log_path.with_name("ORACLE_EVENT_CHECKPOINT.verify.json")
    rc = main([
        "verify-oracle-event-checkpoint",
        str(checkpoint_json),
        "--repo-root", str(repo_root),
        "--dsse", str(checkpoint_dsse),
        "--public-key", str(public_key),
        "--output", str(verify_output),
    ])
    assert rc == 0
    verified = json.loads(verify_output.read_text(encoding="utf-8"))
    assert verified["status"] == "VERIFIED"
    assert verified["signature_verified"] is True


@pytest.mark.constitutional
def test_oracle_event_log_append_rejects_incomplete_evidence(tmp_path: Path) -> None:
    repo_root = tmp_path
    base_dir = repo_root / "day1"
    base_dir.mkdir()
    private_key = repo_root / "oracle_private.pem"
    public_key = repo_root / "oracle_public.pem"
    generate_snapshot_signing_keypair(private_key_path=private_key, public_key_path=public_key)

    payload = {
        "generated_for_utc": "2026-04-13T08:10:00Z",
        "universe_label": "US_EQ_FACTORS",
        "sensors": {
            "semantic": {"inflation_hawkishness_score": 0.0, "geopolitical_risk_index": 0.15, "narrative_contradiction_count": 0, "tribunal_belief_conflict": 0.05},
            "microstructure": {"vpin": 0.28, "order_flow_imbalance": 0.08, "spread_variance_zscore": 0.0, "liquidity_thinning_score": 0.12},
            "macro": {"yield_curve_slope_bps": 85.0, "high_yield_credit_spread_bps": 300.0, "equity_bond_correlation": -0.20, "cross_asset_correlation_stress": 0.10, "realized_volatility_zscore": -0.10},
        },
        "strategies": [],
    }
    manifest_path, dsse_path = _write_oracle_evidence(repo_root=repo_root, base_dir=base_dir, payload=payload, private_key=private_key)
    assert dsse_path is not None
    attestation_path = base_dir / "ORACLE_MORNING_ATTESTATION.json"
    attestation_path.unlink()

    rc = main([
        "oracle-event-log-append",
        str(manifest_path),
        "--repo-root", str(repo_root),
        "--dsse", str(dsse_path),
        "--public-key", str(public_key),
        "--log-path", str(repo_root / "ORACLE_EVENT_LOG.jsonl"),
    ])
    assert rc != 0


@pytest.mark.constitutional
def test_oracle_horizon_view_and_checkpoint_cli_round_trip(tmp_path: Path) -> None:
    repo_root = tmp_path
    day_dir = repo_root / "day"
    day_dir.mkdir()

    private_key = repo_root / "oracle_private.pem"
    public_key = repo_root / "oracle_public.pem"
    generate_snapshot_signing_keypair(private_key_path=private_key, public_key_path=public_key)

    payload = {
        "generated_for_utc": "2026-04-13T08:10:00Z",
        "universe_label": "US_EQ_FACTORS",
        "sensors": {
            "semantic": {"inflation_hawkishness_score": 0.2, "geopolitical_risk_index": 0.18, "narrative_contradiction_count": 0, "tribunal_belief_conflict": 0.04},
            "microstructure": {"vpin": 0.20, "order_flow_imbalance": 0.05, "spread_variance_zscore": 0.1, "liquidity_thinning_score": 0.09},
            "macro": {"yield_curve_slope_bps": 72.0, "high_yield_credit_spread_bps": 310.0, "equity_bond_correlation": -0.25, "cross_asset_correlation_stress": 0.08, "realized_volatility_zscore": -0.2},
        },
        "strategies": [
            {
                "strategy_id": "trend-a",
                "strategy_type": "TREND_FOLLOWING",
                "prior_edge_confidence": 0.72,
                "deflated_sharpe_ratio": 0.88,
                "cpcv_lower_bound": 0.22,
                "realized_live_sharpe": 0.61,
                "recent_win_rate": 0.57,
                "drawdown_fraction": 0.03,
                "expected_regimes": ["RISK_ON_LOW_VOL", "TRANSITION"],
            }
        ],
    }
    manifest, dsse = _write_oracle_evidence(repo_root=repo_root, base_dir=day_dir, payload=payload, private_key=private_key)
    assert dsse is not None

    log_path = repo_root / "docs" / "artifacts" / "oracle" / "ORACLE_EVENT_LOG.jsonl"
    rc = main([
        "oracle-event-log-append",
        str(manifest),
        "--repo-root", str(repo_root),
        "--dsse", str(dsse),
        "--public-key", str(public_key),
        "--log-path", str(log_path),
    ])
    assert rc == 0

    derived_json = log_path.with_name("ORACLE_HORIZON_WEEKLY.json")
    derived_md = log_path.with_name("ORACLE_HORIZON_WEEKLY.md")
    rc = main([
        "oracle-horizon-view",
        "--log-path", str(log_path),
        "--horizon", "weekly",
        "--output", str(derived_json),
        "--markdown-output", str(derived_md),
    ])
    assert rc == 0
    derived = json.loads(derived_json.read_text(encoding="utf-8"))
    assert derived["view_label"] == "weekly"
    assert derived["window_entry_count"] == 1
    derived_markdown = derived_md.read_text(encoding="utf-8")
    assert "Trust banner:" in derived_markdown
    assert "Lineage reason:" in derived_markdown

    checkpoint_json = log_path.with_name("ORACLE_HORIZON_WEEKLY_CHECKPOINT.json")
    checkpoint_dsse = log_path.with_name("ORACLE_HORIZON_WEEKLY_CHECKPOINT.dsse.json")
    checkpoint_verify = log_path.with_name("ORACLE_HORIZON_WEEKLY_CHECKPOINT.verification.json")
    rc = main([
        "oracle-horizon-checkpoint",
        "--log-path", str(log_path),
        "--repo-root", str(repo_root),
        "--horizon", "weekly",
        "--signing-private-key", str(private_key),
        "--output", str(checkpoint_json),
        "--dsse-output", str(checkpoint_dsse),
        "--verification-output", str(checkpoint_verify),
    ])
    assert rc == 0
    verification = json.loads(checkpoint_verify.read_text(encoding="utf-8"))
    assert verification["status"] == "VERIFIED"


@pytest.mark.constitutional
def test_oracle_horizon_view_rejects_unknown_horizon(tmp_path: Path) -> None:
    log_path = tmp_path / "docs" / "artifacts" / "oracle" / "ORACLE_EVENT_LOG.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    rc = main([
        "oracle-horizon-view",
        "--log-path", str(log_path),
        "--horizon", "nonsense",
    ])
    assert rc != 0


@pytest.mark.constitutional
def test_oracle_rolling_review_and_checkpoint_round_trip(tmp_path: Path) -> None:
    repo_root = tmp_path
    day_dir = repo_root / "day"
    day_dir.mkdir()

    private_key = repo_root / "oracle_private.pem"
    public_key = repo_root / "oracle_public.pem"
    generate_snapshot_signing_keypair(private_key_path=private_key, public_key_path=public_key)

    payload = {
        "generated_for_utc": "2026-04-13T08:10:00Z",
        "universe_label": "US_EQ_FACTORS",
        "sensors": {
            "semantic": {"inflation_hawkishness_score": 0.25, "geopolitical_risk_index": 0.22, "narrative_contradiction_count": 0, "tribunal_belief_conflict": 0.05},
            "microstructure": {"vpin": 0.24, "order_flow_imbalance": 0.06, "spread_variance_zscore": 0.0, "liquidity_thinning_score": 0.10},
            "macro": {"yield_curve_slope_bps": 78.0, "high_yield_credit_spread_bps": 305.0, "equity_bond_correlation": -0.21, "cross_asset_correlation_stress": 0.10, "realized_volatility_zscore": -0.15},
        },
        "strategies": [{
            "strategy_id": "trend-a",
            "strategy_type": "TREND_FOLLOWING",
            "prior_edge_confidence": 0.71,
            "deflated_sharpe_ratio": 0.84,
            "cpcv_lower_bound": 0.20,
            "realized_live_sharpe": 0.59,
            "recent_win_rate": 0.56,
            "drawdown_fraction": 0.03,
            "expected_regimes": ["RISK_ON_LOW_VOL", "TRANSITION"],
        }],
    }
    manifest, dsse = _write_oracle_evidence(repo_root=repo_root, base_dir=day_dir, payload=payload, private_key=private_key)
    assert dsse is not None

    log_path = repo_root / "docs" / "artifacts" / "oracle" / "ORACLE_EVENT_LOG.jsonl"
    rc = main([
        "oracle-event-log-append",
        str(manifest),
        "--repo-root", str(repo_root),
        "--dsse", str(dsse),
        "--public-key", str(public_key),
        "--log-path", str(log_path),
    ])
    assert rc == 0

    review_json = log_path.with_name("ORACLE_ROLLING_REVIEW.json")
    review_md = log_path.with_name("ORACLE_ROLLING_REVIEW.md")
    rc = main([
        "oracle-rolling-review",
        "--log-path", str(log_path),
        "--horizon", "weekly",
        "--output", str(review_json),
        "--markdown-output", str(review_md),
    ])
    assert rc == 0
    review = json.loads(review_json.read_text(encoding="utf-8"))
    assert review["view_label"] == "weekly"
    review_markdown = review_md.read_text(encoding="utf-8")
    assert "ORACLE ROLLING REVIEW" in review_markdown
    assert "Trust banner:" in review_markdown

    checkpoint_json = log_path.with_name("ORACLE_ROLLING_REVIEW_CHECKPOINT.json")
    checkpoint_dsse = log_path.with_name("ORACLE_ROLLING_REVIEW_CHECKPOINT.dsse.json")
    checkpoint_verify = log_path.with_name("ORACLE_ROLLING_REVIEW_CHECKPOINT.verification.json")
    rc = main([
        "oracle-rolling-review-checkpoint",
        "--log-path", str(log_path),
        "--repo-root", str(repo_root),
        "--horizon", "weekly",
        "--signing-private-key", str(private_key),
        "--output", str(checkpoint_json),
        "--dsse-output", str(checkpoint_dsse),
        "--verification-output", str(checkpoint_verify),
    ])
    assert rc == 0
    verification = json.loads(checkpoint_verify.read_text(encoding="utf-8"))
    assert verification["status"] == "VERIFIED"


@pytest.mark.constitutional
def test_legacy_weekly_digest_markdown_contains_banner(tmp_path: Path) -> None:
    lane_path = tmp_path / "docs" / "artifacts" / "oracle" / "ORACLE_REVIEW_LANE.jsonl"
    lane_path.parent.mkdir(parents=True, exist_ok=True)
    lane_path.write_text(
        json.dumps({
            "schema_version": "oracle_review_lane_entry/v1",
            "appended_at_utc": "2026-04-13T08:10:00Z",
            "lane_id": "ORACLE_REVIEW_LANE",
            "sequence_number": 0,
            "entry_id": "review:0",
            "review_id": "review-0",
            "previous_entry_hash": None,
            "entry_hash": "abc123",
            "manifest_path": "docs/artifacts/oracle/ORACLE_MEMORY_REVIEW_EVIDENCE.json",
            "manifest_sha256": "deadbeef",
            "review_classification": "STABLE_RESEARCH_POSTURE",
            "window_end_sequence_number": 0,
            "latest_global_action": "OBSERVE",
            "latest_epistemic_status": "NOMINAL",
            "evidence_status": "VERIFIED",
            "summary_line": "stable review"
        }) + "\n",
        encoding="utf-8",
    )
    markdown_path = lane_path.with_name("ORACLE_WEEKLY_DIGEST.md")
    rc = main([
        "oracle-weekly-digest",
        "--lane-path", str(lane_path),
        "--allow-legacy-lane-read",
        "--window-size", "1",
        "--markdown-output", str(markdown_path),
    ])
    assert rc == 0
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "Legacy compatibility surface" in markdown
    assert "oracle-rolling-review / oracle-horizon-view" in markdown
    assert "Trust banner:" in markdown
    assert "Lineage reason:" in markdown


@pytest.mark.constitutional
def test_legacy_weekly_digest_can_proxy_to_event_log(tmp_path: Path) -> None:
    repo_root = tmp_path
    day_dir = repo_root / "day"
    day_dir.mkdir()
    private_key = repo_root / "oracle_private.pem"
    public_key = repo_root / "oracle_public.pem"
    generate_snapshot_signing_keypair(private_key_path=private_key, public_key_path=public_key)
    payload = {
        "generated_for_utc": "2026-04-13T08:10:00Z",
        "universe_label": "US_EQ_FACTORS",
        "sensors": {
            "semantic": {"inflation_hawkishness_score": 0.9, "geopolitical_risk_index": 0.4, "narrative_contradiction_count": 1, "tribunal_belief_conflict": 0.15},
            "microstructure": {"vpin": 0.35, "order_flow_imbalance": -0.02, "spread_variance_zscore": 0.4, "liquidity_thinning_score": 0.22},
            "macro": {"yield_curve_slope_bps": 40.0, "high_yield_credit_spread_bps": 360.0, "equity_bond_correlation": 0.05, "cross_asset_correlation_stress": 0.22, "realized_volatility_zscore": 0.35},
        },
        "strategies": [{
            "strategy_id": "trend-a",
            "strategy_type": "TREND_FOLLOWING",
            "prior_edge_confidence": 0.72,
            "deflated_sharpe_ratio": 0.88,
            "cpcv_lower_bound": 0.22,
            "realized_live_sharpe": 0.61,
            "recent_win_rate": 0.57,
            "drawdown_fraction": 0.03,
            "expected_regimes": ["RISK_ON_LOW_VOL", "TRANSITION"],
        }],
    }
    manifest, dsse = _write_oracle_evidence(repo_root=repo_root, base_dir=day_dir, payload=payload, private_key=private_key)
    assert dsse is not None
    log_path = repo_root / "docs" / "artifacts" / "oracle" / "ORACLE_EVENT_LOG.jsonl"
    rc = main(["oracle-event-log-append", str(manifest), "--repo-root", str(repo_root), "--dsse", str(dsse), "--public-key", str(public_key), "--log-path", str(log_path)])
    assert rc == 0
    weekly_json = log_path.with_name("ORACLE_WEEKLY_DIGEST.json")
    weekly_md = log_path.with_name("ORACLE_WEEKLY_DIGEST.md")
    rc = main(["oracle-weekly-digest", "--log-path", str(log_path), "--window-size", "1", "--output", str(weekly_json), "--markdown-output", str(weekly_md)])
    assert rc == 0
    payload = json.loads(weekly_json.read_text(encoding="utf-8"))
    assert payload["view_label"] == "weekly"
    assert payload["window_entry_count"] == 1
    markdown = weekly_md.read_text(encoding="utf-8")
    assert "Legacy compatibility surface" in markdown
    assert "ORACLE ROLLING REVIEW" in markdown




@pytest.mark.constitutional
def test_oracle_event_log_query_layer_filters_strategy_regime_epistemic_and_time(tmp_path: Path) -> None:
    log_path = tmp_path / "docs" / "artifacts" / "oracle" / "ORACLE_EVENT_LOG.jsonl"
    _write_jsonl(
        log_path,
        [
            {
                'schema_version': 'oracle_event_log_entry/v1',
                'appended_at_utc': '2026-04-13T08:10:00Z',
                'lane_id': 'ORACLE_EVENT_LOG',
                'sequence_number': 0,
                'entry_id': 'evidence-0:0',
                'evidence_id': 'evidence-0',
                'previous_entry_hash': None,
                'entry_hash': '1' * 64,
                'manifest_path': 'docs/artifacts/oracle/ORACLE_EVIDENCE_0.json',
                'manifest_sha256': '2' * 64,
                'linked_closure_id': None,
                'input_timestamp_utc': '2026-04-13T08:10:00Z',
                'dominant_regime': 'RISK_ON_LOW_VOL',
                'recommended_global_action': 'OBSERVE',
                'epistemic_status': 'NOMINAL',
                'average_posterior_edge_confidence': 0.70,
                'maintain_count': 1,
                'canary_count': 0,
                'hibernate_count': 0,
                'strategy_ids': ['trend-a'],
                'evidence_status': 'VERIFIED',
                'summary_line': 'baseline entry',
            },
            {
                'schema_version': 'oracle_event_log_entry/v1',
                'appended_at_utc': '2026-04-14T08:10:00Z',
                'lane_id': 'ORACLE_EVENT_LOG',
                'sequence_number': 1,
                'entry_id': 'evidence-1:1',
                'evidence_id': 'evidence-1',
                'previous_entry_hash': '1' * 64,
                'entry_hash': '3' * 64,
                'manifest_path': 'docs/artifacts/oracle/ORACLE_EVIDENCE_1.json',
                'manifest_sha256': '4' * 64,
                'linked_closure_id': None,
                'input_timestamp_utc': '2026-04-14T08:10:00Z',
                'dominant_regime': 'TRANSITION',
                'recommended_global_action': 'CANARY_REVIEW',
                'epistemic_status': 'ELEVATED',
                'average_posterior_edge_confidence': 0.51,
                'maintain_count': 0,
                'canary_count': 1,
                'hibernate_count': 0,
                'strategy_ids': ['trend-a', 'mr-a'],
                'evidence_status': 'VERIFIED',
                'summary_line': 'elevated transition entry',
            },
            {
                'schema_version': 'oracle_event_log_entry/v1',
                'appended_at_utc': '2026-04-15T08:10:00Z',
                'lane_id': 'ORACLE_EVENT_LOG',
                'sequence_number': 2,
                'entry_id': 'evidence-2:2',
                'evidence_id': 'evidence-2',
                'previous_entry_hash': '3' * 64,
                'entry_hash': '5' * 64,
                'manifest_path': 'docs/artifacts/oracle/ORACLE_EVIDENCE_2.json',
                'manifest_sha256': '6' * 64,
                'linked_closure_id': None,
                'input_timestamp_utc': '2026-04-15T08:10:00Z',
                'dominant_regime': 'RISK_OFF_HIGH_VOL',
                'recommended_global_action': 'DEFENSIVE_POSTURE',
                'epistemic_status': 'UNKNOWN_UNKNOWNS',
                'average_posterior_edge_confidence': 0.31,
                'maintain_count': 0,
                'canary_count': 0,
                'hibernate_count': 1,
                'strategy_ids': ['carry-a'],
                'evidence_status': 'VERIFIED',
                'summary_line': 'crisis entry',
            },
        ],
    )
    rows, metadata = query_oracle_event_log(
        lane_path=log_path,
        query_spec=OracleEventLogQuerySpec(
            start_input_timestamp_utc='2026-04-14T00:00:00Z',
            end_input_timestamp_utc='2026-04-15T00:00:00Z',
            strategy_ids=['mr-a'],
            dominant_regimes=['TRANSITION'],
            epistemic_statuses=['ELEVATED'],
            max_entries=5,
        ),
        checkpoint_metadata_path=log_path.with_name('ORACLE_QUERY_FILTER.checkpoint.metadata.json'),
        view_label='transition-filter',
    )
    assert [row.entry_id for row in rows] == ['evidence-1:1']
    assert metadata is not None
    assert metadata.cached_window_entries[0].entry_id == 'evidence-1:1'


@pytest.mark.constitutional
def test_oracle_rolling_review_writes_and_refreshes_checkpoint_metadata(tmp_path: Path) -> None:
    repo_root = tmp_path
    log_path = repo_root / 'docs' / 'artifacts' / 'oracle' / 'ORACLE_EVENT_LOG.jsonl'
    metadata_path = repo_root / 'docs' / 'artifacts' / 'oracle' / 'ORACLE_WEEKLY.checkpoint.metadata.json'
    output = repo_root / 'docs' / 'artifacts' / 'oracle' / 'ORACLE_WEEKLY.json'
    _write_jsonl(
        log_path,
        [
            {
                'schema_version': 'oracle_event_log_entry/v1',
                'appended_at_utc': '2026-04-13T08:10:00Z',
                'lane_id': 'ORACLE_EVENT_LOG',
                'sequence_number': 0,
                'entry_id': 'evidence-0:0',
                'evidence_id': 'evidence-0',
                'previous_entry_hash': None,
                'entry_hash': '7' * 64,
                'manifest_path': 'docs/artifacts/oracle/ORACLE_EVIDENCE_0.json',
                'manifest_sha256': '8' * 64,
                'linked_closure_id': None,
                'input_timestamp_utc': '2026-04-13T08:10:00Z',
                'dominant_regime': 'RISK_ON_LOW_VOL',
                'recommended_global_action': 'OBSERVE',
                'epistemic_status': 'NOMINAL',
                'average_posterior_edge_confidence': 0.70,
                'maintain_count': 1,
                'canary_count': 0,
                'hibernate_count': 0,
                'strategy_ids': ['trend-a'],
                'evidence_status': 'VERIFIED',
                'summary_line': 'baseline entry',
            },
            {
                'schema_version': 'oracle_event_log_entry/v1',
                'appended_at_utc': '2026-04-14T08:10:00Z',
                'lane_id': 'ORACLE_EVENT_LOG',
                'sequence_number': 1,
                'entry_id': 'evidence-1:1',
                'evidence_id': 'evidence-1',
                'previous_entry_hash': '7' * 64,
                'entry_hash': '9' * 64,
                'manifest_path': 'docs/artifacts/oracle/ORACLE_EVIDENCE_1.json',
                'manifest_sha256': 'a' * 64,
                'linked_closure_id': None,
                'input_timestamp_utc': '2026-04-14T08:10:00Z',
                'dominant_regime': 'TRANSITION',
                'recommended_global_action': 'CANARY_REVIEW',
                'epistemic_status': 'ELEVATED',
                'average_posterior_edge_confidence': 0.58,
                'maintain_count': 0,
                'canary_count': 1,
                'hibernate_count': 0,
                'strategy_ids': ['trend-a'],
                'evidence_status': 'VERIFIED',
                'summary_line': 'watch entry',
            },
        ],
    )
    rc = main([
        'oracle-rolling-review',
        '--log-path', str(log_path),
        '--horizon', 'weekly',
        '--window-size', '2',
        '--output', str(output),
        '--checkpoint-metadata-output', str(metadata_path),
    ])
    assert rc == 0
    metadata1 = json.loads(metadata_path.read_text(encoding='utf-8'))
    assert metadata1['last_event_log_sequence_number'] == 1
    assert [row['entry_id'] for row in metadata1['cached_window_entries']] == ['evidence-0:0', 'evidence-1:1']

    with log_path.open('a', encoding='utf-8') as handle:
        handle.write(json.dumps({
            'schema_version': 'oracle_event_log_entry/v1',
            'appended_at_utc': '2026-04-15T08:10:00Z',
            'lane_id': 'ORACLE_EVENT_LOG',
            'sequence_number': 2,
            'entry_id': 'evidence-2:2',
            'evidence_id': 'evidence-2',
            'previous_entry_hash': '9' * 64,
            'entry_hash': 'b' * 64,
            'manifest_path': 'docs/artifacts/oracle/ORACLE_EVIDENCE_2.json',
            'manifest_sha256': 'c' * 64,
            'linked_closure_id': None,
            'input_timestamp_utc': '2026-04-15T08:10:00Z',
            'dominant_regime': 'RISK_OFF_HIGH_VOL',
            'recommended_global_action': 'DEFENSIVE_POSTURE',
            'epistemic_status': 'UNKNOWN_UNKNOWNS',
            'average_posterior_edge_confidence': 0.33,
            'maintain_count': 0,
            'canary_count': 0,
            'hibernate_count': 1,
            'strategy_ids': ['trend-a'],
            'evidence_status': 'VERIFIED',
            'summary_line': 'defensive entry',
        }, separators=(',', ':')) + '\n')


    rc = main([
        'oracle-rolling-review',
        '--log-path', str(log_path),
        '--horizon', 'weekly',
        '--window-size', '2',
        '--output', str(output),
        '--checkpoint-metadata-output', str(metadata_path),
    ])
    assert rc == 0
    metadata2 = json.loads(metadata_path.read_text(encoding='utf-8'))
    assert metadata2['last_event_log_sequence_number'] == 2
    assert [row['entry_id'] for row in metadata2['cached_window_entries']] == ['evidence-1:1', 'evidence-2:2']
    assert 'Incrementally refreshed weekly checkpoint metadata' in metadata2['summary_line']


@pytest.mark.constitutional
def test_oracle_horizon_checkpoint_includes_metadata_subject(tmp_path: Path) -> None:
    repo_root = tmp_path
    oracle_root = repo_root / 'docs' / 'artifacts' / 'oracle'
    log_path = oracle_root / 'ORACLE_EVENT_LOG.jsonl'
    report_path = oracle_root / 'ORACLE_DERIVED_VIEW.json'
    metadata_path = oracle_root / 'ORACLE_DERIVED_VIEW.checkpoint.metadata.json'
    checkpoint_json = oracle_root / 'ORACLE_EVENT_CHECKPOINT.json'
    _write_jsonl(
        log_path,
        [{
            'schema_version': 'oracle_event_log_entry/v1',
            'appended_at_utc': '2026-04-13T08:10:00Z',
            'lane_id': 'ORACLE_EVENT_LOG',
            'sequence_number': 0,
            'entry_id': 'evidence-0:0',
            'evidence_id': 'evidence-0',
            'previous_entry_hash': None,
            'entry_hash': 'd' * 64,
            'manifest_path': 'docs/artifacts/oracle/ORACLE_EVIDENCE.json',
            'manifest_sha256': 'e' * 64,
            'linked_closure_id': None,
            'input_timestamp_utc': '2026-04-13T08:10:00Z',
            'dominant_regime': 'RISK_ON_LOW_VOL',
            'recommended_global_action': 'OBSERVE',
            'epistemic_status': 'NOMINAL',
            'average_posterior_edge_confidence': 0.71,
            'maintain_count': 1,
            'canary_count': 0,
            'hibernate_count': 0,
            'strategy_ids': ['trend-a'],
            'evidence_status': 'VERIFIED',
            'summary_line': 'stable event log entry',
        }],
    )
    rc = main([
        'oracle-horizon-checkpoint',
        '--log-path', str(log_path),
        '--horizon', 'weekly',
        '--report-output', str(report_path),
        '--checkpoint-metadata-output', str(metadata_path),
        '--output', str(checkpoint_json),
    ])
    assert rc == 0
    manifest = json.loads(checkpoint_json.read_text(encoding='utf-8'))
    subject_paths = {subject['path'] for subject in manifest['subjects']}
    assert metadata_path.name in {Path(p).name for p in subject_paths}

def _write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding='utf-8')



def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


_REQUIRED_LINEAGE_FILENAMES = [
    'ORACLE_EVIDENCE.json',
    'ORACLE_TRANSITION_EVIDENCE.json',
    'ORACLE_MEMORY_REVIEW_EVIDENCE.json',
    'ORACLE_WEEKLY_DIGEST_EVIDENCE.json',
    'ORACLE_DOCTRINE_DRIFT_EVIDENCE.json',
    'ORACLE_MONTHLY_DIGEST_EVIDENCE.json',
    'ORACLE_QUARTERLY_REVIEW_EVIDENCE.json',
    'ORACLE_SEMIANNUAL_AUDIT_EVIDENCE.json',
    'ORACLE_ANNUAL_REVIEW_EVIDENCE.json',
    'ORACLE_CONSTITUTIONAL_DIGEST_EVIDENCE.json',
]


@pytest.mark.constitutional
def test_oracle_horizon_view_upgrades_trust_banner_when_lineage_is_fully_sealed(tmp_path: Path) -> None:
    repo_root = tmp_path
    artifacts = repo_root / 'docs' / 'artifacts'
    oracle_root = artifacts / 'oracle'
    log_path = oracle_root / 'ORACLE_EVENT_LOG.jsonl'

    _write_json(artifacts / 'final_rollout_closure' / 'CLOSURE_SNAPSHOT.json', {})
    for filename in _REQUIRED_LINEAGE_FILENAMES:
        _write_json(oracle_root / filename, {})
    _write_jsonl(oracle_root / 'ORACLE_ANNUAL_LANE.jsonl', [{'sequence_number': 0, 'entry_hash': 'a' * 64}])
    _write_jsonl(oracle_root / 'ORACLE_CONSTITUTIONAL_LANE.jsonl', [{'sequence_number': 0, 'entry_hash': 'b' * 64}])
    _write_jsonl(
        log_path,
        [{
            'schema_version': 'oracle_event_log_entry/v1',
            'appended_at_utc': '2026-04-13T08:10:00Z',
            'lane_id': 'ORACLE_EVENT_LOG',
            'sequence_number': 0,
            'entry_id': 'evidence-0:0',
            'evidence_id': 'evidence-0',
            'previous_entry_hash': None,
            'entry_hash': 'c' * 64,
            'manifest_path': 'docs/artifacts/oracle/ORACLE_EVIDENCE.json',
            'manifest_sha256': 'd' * 64,
            'linked_closure_id': None,
            'input_timestamp_utc': '2026-04-13T08:10:00Z',
            'dominant_regime': 'RISK_ON_LOW_VOL',
            'recommended_global_action': 'OBSERVE',
            'epistemic_status': 'NOMINAL',
            'average_posterior_edge_confidence': 0.71,
            'maintain_count': 1,
            'canary_count': 0,
            'hibernate_count': 0,
            'strategy_ids': ['trend-a'],
            'evidence_status': 'VERIFIED',
            'summary_line': 'stable event log entry',
        }],
    )

    output = oracle_root / 'ORACLE_HORIZON_WEEKLY.json'
    markdown = oracle_root / 'ORACLE_HORIZON_WEEKLY.md'
    rc = main([
        'oracle-horizon-view',
        '--log-path', str(log_path),
        '--output', str(output),
        '--markdown-output', str(markdown),
    ])
    assert rc == 0
    rendered = markdown.read_text(encoding='utf-8')
    assert 'Trust banner: `TRUSTED`' in rendered
    assert 'fully sealed doctrine lineage' in rendered


@pytest.mark.constitutional
def test_legacy_weekly_digest_auto_detects_canonical_event_log(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root = tmp_path
    log_path = repo_root / 'docs' / 'artifacts' / 'oracle' / 'ORACLE_EVENT_LOG.jsonl'
    _write_jsonl(
        log_path,
        [{
            'schema_version': 'oracle_event_log_entry/v1',
            'appended_at_utc': '2026-04-13T08:10:00Z',
            'lane_id': 'ORACLE_EVENT_LOG',
            'sequence_number': 0,
            'entry_id': 'evidence-0:0',
            'evidence_id': 'evidence-0',
            'previous_entry_hash': None,
            'entry_hash': 'e' * 64,
            'manifest_path': 'docs/artifacts/oracle/ORACLE_EVIDENCE.json',
            'manifest_sha256': 'f' * 64,
            'linked_closure_id': None,
            'input_timestamp_utc': '2026-04-13T08:10:00Z',
            'dominant_regime': 'RISK_ON_LOW_VOL',
            'recommended_global_action': 'OBSERVE',
            'epistemic_status': 'NOMINAL',
            'average_posterior_edge_confidence': 0.69,
            'maintain_count': 1,
            'canary_count': 0,
            'hibernate_count': 0,
            'strategy_ids': ['trend-a'],
            'evidence_status': 'VERIFIED',
            'summary_line': 'stable event log entry',
        }],
    )
    output = log_path.with_name('ORACLE_WEEKLY_DIGEST.json')
    markdown = log_path.with_name('ORACLE_WEEKLY_DIGEST.md')
    monkeypatch.chdir(repo_root)
    rc = main([
        'oracle-weekly-digest',
        '--window-size', '1',
        '--output', str(output),
        '--markdown-output', str(markdown),
    ])
    assert rc == 0
    payload = json.loads(output.read_text(encoding='utf-8'))
    assert payload['view_label'] == 'weekly'
    rendered = markdown.read_text(encoding='utf-8')
    assert 'ORACLE ROLLING REVIEW' in rendered
    assert 'Legacy compatibility surface' in rendered
    assert 'canonical Oracle Event Log' in rendered
