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
def test_oracle_transition_evidence_and_memory_lane_cli_round_trip(tmp_path: Path) -> None:
    repo_root = tmp_path
    prev_dir = repo_root / "prev"
    curr_dir = repo_root / "curr"
    nxt_dir = repo_root / "next"
    prev_dir.mkdir()
    curr_dir.mkdir()
    nxt_dir.mkdir()

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
            }
        ],
    }
    payload_prev = {
        **base,
        "generated_for_utc": "2026-04-13T08:10:00Z",
        "sensors": {
            "semantic": {"inflation_hawkishness_score": 0.0, "geopolitical_risk_index": 0.15, "narrative_contradiction_count": 0, "tribunal_belief_conflict": 0.05},
            "microstructure": {"vpin": 0.28, "order_flow_imbalance": 0.08, "spread_variance_zscore": 0.0, "liquidity_thinning_score": 0.12},
            "macro": {"yield_curve_slope_bps": 85.0, "high_yield_credit_spread_bps": 300.0, "equity_bond_correlation": -0.20, "cross_asset_correlation_stress": 0.10, "realized_volatility_zscore": -0.10},
        },
    }
    payload_curr = {
        **base,
        "generated_for_utc": "2026-04-14T08:10:00Z",
        "sensors": {
            "semantic": {"inflation_hawkishness_score": 1.1, "geopolitical_risk_index": 0.70, "narrative_contradiction_count": 3, "tribunal_belief_conflict": 0.62},
            "microstructure": {"vpin": 0.62, "order_flow_imbalance": -0.35, "spread_variance_zscore": 1.2, "liquidity_thinning_score": 0.55},
            "macro": {"yield_curve_slope_bps": 15.0, "high_yield_credit_spread_bps": 450.0, "equity_bond_correlation": 0.45, "cross_asset_correlation_stress": 0.55, "realized_volatility_zscore": 1.10},
        },
    }
    payload_next = {
        **base,
        "generated_for_utc": "2026-04-15T08:10:00Z",
        "sensors": {
            "semantic": {"inflation_hawkishness_score": 1.5, "geopolitical_risk_index": 0.88, "narrative_contradiction_count": 5, "tribunal_belief_conflict": 0.91},
            "microstructure": {"vpin": 0.84, "order_flow_imbalance": -0.60, "spread_variance_zscore": 2.1, "liquidity_thinning_score": 0.82},
            "macro": {"yield_curve_slope_bps": -10.0, "high_yield_credit_spread_bps": 620.0, "equity_bond_correlation": 0.72, "cross_asset_correlation_stress": 0.89, "realized_volatility_zscore": 2.40},
        },
    }

    prev_manifest, prev_dsse = _write_oracle_evidence(repo_root=repo_root, base_dir=prev_dir, payload=payload_prev, private_key=private_key)
    curr_manifest, curr_dsse = _write_oracle_evidence(repo_root=repo_root, base_dir=curr_dir, payload=payload_curr, private_key=private_key)
    next_manifest, next_dsse = _write_oracle_evidence(repo_root=repo_root, base_dir=nxt_dir, payload=payload_next, private_key=private_key)

    lane_path = repo_root / "docs" / "artifacts" / "oracle" / "ORACLE_MEMORY_LANE.jsonl"

    trans1_manifest = repo_root / "transition1" / "ORACLE_TRANSITION_EVIDENCE.json"
    trans1_manifest.parent.mkdir()
    trans1_dsse = trans1_manifest.with_suffix(".dsse.json")
    trans1_verify = trans1_manifest.with_name("ORACLE_TRANSITION_EVIDENCE.verification.json")
    rc = main([
        "oracle-transition-evidence",
        str(prev_manifest),
        str(curr_manifest),
        "--repo-root", str(repo_root),
        "--previous-dsse", str(prev_dsse),
        "--current-dsse", str(curr_dsse),
        "--previous-public-key", str(public_key),
        "--current-public-key", str(public_key),
        "--signing-private-key", str(private_key),
        "--public-key", str(public_key),
        "--output", str(trans1_manifest),
        "--dsse-output", str(trans1_dsse),
        "--verification-output", str(trans1_verify),
    ])
    assert rc == 0

    entry1_output = trans1_manifest.with_name("ORACLE_MEMORY_LANE_ENTRY.json")
    rc = main([
        "oracle-memory-append",
        str(trans1_manifest),
        "--repo-root", str(repo_root),
        "--dsse", str(trans1_dsse),
        "--public-key", str(public_key),
        "--lane-path", str(lane_path),
        "--output", str(entry1_output),
    ])
    assert rc == 0
    entry1 = json.loads(entry1_output.read_text(encoding="utf-8"))
    assert entry1["sequence_number"] == 0

    trans2_manifest = repo_root / "transition2" / "ORACLE_TRANSITION_EVIDENCE.json"
    trans2_manifest.parent.mkdir()
    trans2_dsse = trans2_manifest.with_suffix(".dsse.json")
    trans2_verify = trans2_manifest.with_name("ORACLE_TRANSITION_EVIDENCE.verification.json")
    rc = main([
        "oracle-transition-evidence",
        str(curr_manifest),
        str(next_manifest),
        "--repo-root", str(repo_root),
        "--previous-dsse", str(curr_dsse),
        "--current-dsse", str(next_dsse),
        "--previous-public-key", str(public_key),
        "--current-public-key", str(public_key),
        "--signing-private-key", str(private_key),
        "--public-key", str(public_key),
        "--output", str(trans2_manifest),
        "--dsse-output", str(trans2_dsse),
        "--verification-output", str(trans2_verify),
    ])
    assert rc == 0

    entry2_output = trans2_manifest.with_name("ORACLE_MEMORY_LANE_ENTRY.json")
    rc = main([
        "oracle-memory-append",
        str(trans2_manifest),
        "--repo-root", str(repo_root),
        "--dsse", str(trans2_dsse),
        "--public-key", str(public_key),
        "--lane-path", str(lane_path),
        "--output", str(entry2_output),
    ])
    assert rc == 0
    entry2 = json.loads(entry2_output.read_text(encoding="utf-8"))
    assert entry2["sequence_number"] == 1
    assert entry2["previous_entry_hash"] == entry1["entry_hash"]

    summary_output = lane_path.with_name("ORACLE_MEMORY_LANE_SUMMARY.json")
    summary_md = lane_path.with_name("ORACLE_MEMORY_LANE_SUMMARY.md")
    rc = main([
        "oracle-memory-summary",
        "--lane-path", str(lane_path),
        "--output", str(summary_output),
        "--markdown-output", str(summary_md),
    ])
    assert rc == 0
    summary = json.loads(summary_output.read_text(encoding="utf-8"))
    assert summary["entry_count"] == 2
    assert summary["latest_transition_classification"] in {"GLOBAL_ACTION_ESCALATION", "EPISTEMIC_ESCALATION", "REGIME_DRIFT"}
    assert summary["classification_counts"]
    assert "ORACLE MEMORY LANE SUMMARY" in summary_md.read_text(encoding="utf-8")


@pytest.mark.constitutional
def test_oracle_memory_append_rejects_incomplete_transition_evidence(tmp_path: Path) -> None:
    repo_root = tmp_path
    prev_dir = repo_root / "prev"
    curr_dir = repo_root / "curr"
    prev_dir.mkdir()
    curr_dir.mkdir()
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
    prev_manifest, prev_dsse = _write_oracle_evidence(repo_root=repo_root, base_dir=prev_dir, payload=payload, private_key=private_key)
    curr_manifest, curr_dsse = _write_oracle_evidence(repo_root=repo_root, base_dir=curr_dir, payload={**payload, "generated_for_utc": "2026-04-14T08:10:00Z"}, private_key=private_key)

    manifest_path = repo_root / "ORACLE_TRANSITION_EVIDENCE.json"
    dsse_path = manifest_path.with_suffix(".dsse.json")
    rc = main([
        "oracle-transition-evidence",
        str(prev_manifest),
        str(curr_manifest),
        "--repo-root", str(repo_root),
        "--previous-dsse", str(prev_dsse),
        "--current-dsse", str(curr_dsse),
        "--previous-public-key", str(public_key),
        "--current-public-key", str(public_key),
        "--signing-private-key", str(private_key),
        "--public-key", str(public_key),
        "--output", str(manifest_path),
        "--dsse-output", str(dsse_path),
    ])
    assert rc == 0
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    report_subject = next(item for item in manifest["subjects"] if item["name"] == "ORACLE_STATE_TRANSITION_REPORT.json")
    report_path = repo_root / Path(report_subject["path"])
    report_path.unlink()

    rc = main([
        "oracle-memory-append",
        str(manifest_path),
        "--repo-root", str(repo_root),
        "--dsse", str(dsse_path),
        "--public-key", str(public_key),
        "--lane-path", str(repo_root / "ORACLE_MEMORY_LANE.jsonl"),
    ])
    assert rc != 0
