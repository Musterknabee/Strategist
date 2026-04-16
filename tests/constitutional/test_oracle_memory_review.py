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
def test_oracle_memory_review_flags_repair_first_for_repeated_evidence_gaps(tmp_path: Path) -> None:
    repo_root = tmp_path
    day1 = repo_root / "day1"
    day2 = repo_root / "day2"
    day3 = repo_root / "day3"
    day1.mkdir()
    day2.mkdir()
    day3.mkdir()

    private_key = repo_root / "oracle_private.pem"
    public_key = repo_root / "oracle_public.pem"
    generate_snapshot_signing_keypair(private_key_path=private_key, public_key_path=public_key)

    base = {
        "universe_label": "US_EQ_FACTORS",
        "sensors": {
            "semantic": {
                "inflation_hawkishness_score": 0.0,
                "geopolitical_risk_index": 0.12,
                "narrative_contradiction_count": 0,
                "tribunal_belief_conflict": 0.05,
            },
            "microstructure": {
                "vpin": 0.22,
                "order_flow_imbalance": 0.05,
                "spread_variance_zscore": 0.0,
                "liquidity_thinning_score": 0.10,
            },
            "macro": {
                "yield_curve_slope_bps": 85.0,
                "high_yield_credit_spread_bps": 300.0,
                "equity_bond_correlation": -0.25,
                "cross_asset_correlation_stress": 0.12,
                "realized_volatility_zscore": -0.15,
            },
        },
        "strategies": [],
    }
    payloads = [
        {**base, "generated_for_utc": "2026-04-13T08:10:00Z"},
        {**base, "generated_for_utc": "2026-04-14T08:10:00Z"},
        {**base, "generated_for_utc": "2026-04-15T08:10:00Z"},
    ]

    manifest1, _ = _write_oracle_evidence(repo_root=repo_root, base_dir=day1, payload=payloads[0], private_key=None)
    manifest2, _ = _write_oracle_evidence(repo_root=repo_root, base_dir=day2, payload=payloads[1], private_key=None)
    manifest3, _ = _write_oracle_evidence(repo_root=repo_root, base_dir=day3, payload=payloads[2], private_key=None)

    lane_path = repo_root / "docs" / "artifacts" / "oracle" / "ORACLE_MEMORY_LANE.jsonl"
    trans1_manifest = repo_root / "transition1" / "ORACLE_TRANSITION_EVIDENCE.json"
    trans1_manifest.parent.mkdir()
    trans1_dsse = trans1_manifest.with_suffix(".dsse.json")
    rc = main([
        "oracle-transition-evidence",
        str(manifest1),
        str(manifest2),
        "--repo-root", str(repo_root),
        "--signing-private-key", str(private_key),
        "--public-key", str(public_key),
        "--output", str(trans1_manifest),
        "--dsse-output", str(trans1_dsse),
    ])
    assert rc == 0
    rc = main([
        "oracle-memory-append",
        str(trans1_manifest),
        "--repo-root", str(repo_root),
        "--dsse", str(trans1_dsse),
        "--public-key", str(public_key),
        "--lane-path", str(lane_path),
    ])
    assert rc == 0

    trans2_manifest = repo_root / "transition2" / "ORACLE_TRANSITION_EVIDENCE.json"
    trans2_manifest.parent.mkdir()
    trans2_dsse = trans2_manifest.with_suffix(".dsse.json")
    rc = main([
        "oracle-transition-evidence",
        str(manifest2),
        str(manifest3),
        "--repo-root", str(repo_root),
        "--signing-private-key", str(private_key),
        "--public-key", str(public_key),
        "--output", str(trans2_manifest),
        "--dsse-output", str(trans2_dsse),
    ])
    assert rc == 0
    rc = main([
        "oracle-memory-append",
        str(trans2_manifest),
        "--repo-root", str(repo_root),
        "--dsse", str(trans2_dsse),
        "--public-key", str(public_key),
        "--lane-path", str(lane_path),
    ])
    assert rc == 0

    review_output = lane_path.with_name("ORACLE_MEMORY_REVIEW_REPORT.json")
    review_md = lane_path.with_name("ORACLE_MEMORY_REVIEW_REPORT.md")
    rc = main([
        "oracle-memory-review",
        "--lane-path", str(lane_path),
        "--repo-root", str(repo_root),
        "--window-size", "2",
        "--output", str(review_output),
        "--markdown-output", str(review_md),
    ])
    assert rc == 0
    review = json.loads(review_output.read_text(encoding="utf-8"))
    assert review["review_classification"] == "REPAIR_FIRST"
    assert review["evidence_gap_count"] == 2
    assert "ORACLE MEMORY REVIEW REPORT" in review_md.read_text(encoding="utf-8")


@pytest.mark.constitutional
def test_oracle_memory_review_flags_strategy_retrain_review(tmp_path: Path) -> None:
    repo_root = tmp_path
    day1 = repo_root / "day1"
    day2 = repo_root / "day2"
    day3 = repo_root / "day3"
    day1.mkdir()
    day2.mkdir()
    day3.mkdir()

    private_key = repo_root / "oracle_private.pem"
    public_key = repo_root / "oracle_public.pem"
    generate_snapshot_signing_keypair(private_key_path=private_key, public_key_path=public_key)

    sensors = {
        "semantic": {
            "inflation_hawkishness_score": 0.0,
            "geopolitical_risk_index": 0.10,
            "narrative_contradiction_count": 0,
            "tribunal_belief_conflict": 0.05,
        },
        "microstructure": {
            "vpin": 0.20,
            "order_flow_imbalance": 0.10,
            "spread_variance_zscore": 0.0,
            "liquidity_thinning_score": 0.10,
        },
        "macro": {
            "yield_curve_slope_bps": 80.0,
            "high_yield_credit_spread_bps": 300.0,
            "equity_bond_correlation": -0.20,
            "cross_asset_correlation_stress": 0.10,
            "realized_volatility_zscore": -0.20,
        },
    }
    strategy_days = [
        {"realized_live_sharpe": 0.9, "recent_win_rate": 0.70, "drawdown_fraction": 0.02},
        {"realized_live_sharpe": 0.0, "recent_win_rate": 0.35, "drawdown_fraction": 0.18},
        {"realized_live_sharpe": -1.2, "recent_win_rate": 0.15, "drawdown_fraction": 0.35},
    ]
    payloads: list[dict] = []
    for day, ts in enumerate(["2026-04-13T08:10:00Z", "2026-04-14T08:10:00Z", "2026-04-15T08:10:00Z"]):
        metrics = strategy_days[day]
        payloads.append(
            {
                "generated_for_utc": ts,
                "universe_label": "US_EQ_FACTORS",
                "sensors": sensors,
                "strategies": [
                    {
                        "strategy_id": "trend-a",
                        "strategy_type": "TREND_FOLLOWING",
                        "prior_edge_confidence": 0.35,
                        "deflated_sharpe_ratio": 0.20,
                        "cpcv_lower_bound": 0.20,
                        "expected_regimes": ["RISK_OFF_HIGH_VOL"],
                        **metrics,
                    }
                ],
            }
        )

    manifest1, dsse1 = _write_oracle_evidence(repo_root=repo_root, base_dir=day1, payload=payloads[0], private_key=private_key)
    manifest2, dsse2 = _write_oracle_evidence(repo_root=repo_root, base_dir=day2, payload=payloads[1], private_key=private_key)
    manifest3, dsse3 = _write_oracle_evidence(repo_root=repo_root, base_dir=day3, payload=payloads[2], private_key=private_key)

    lane_path = repo_root / "docs" / "artifacts" / "oracle" / "ORACLE_MEMORY_LANE.jsonl"
    for idx, (prev_manifest, prev_dsse, curr_manifest, curr_dsse) in enumerate([
        (manifest1, dsse1, manifest2, dsse2),
        (manifest2, dsse2, manifest3, dsse3),
    ], start=1):
        trans_manifest = repo_root / f"transition{idx}" / "ORACLE_TRANSITION_EVIDENCE.json"
        trans_manifest.parent.mkdir()
        trans_dsse = trans_manifest.with_suffix(".dsse.json")
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
            "--output", str(trans_manifest),
            "--dsse-output", str(trans_dsse),
        ])
        assert rc == 0
        rc = main([
            "oracle-memory-append",
            str(trans_manifest),
            "--repo-root", str(repo_root),
            "--dsse", str(trans_dsse),
            "--public-key", str(public_key),
            "--lane-path", str(lane_path),
        ])
        assert rc == 0

    review_output = lane_path.with_name("ORACLE_MEMORY_REVIEW_REPORT.json")
    rc = main([
        "oracle-memory-review",
        "--lane-path", str(lane_path),
        "--repo-root", str(repo_root),
        "--window-size", "2",
        "--output", str(review_output),
    ])
    assert rc == 0
    review = json.loads(review_output.read_text(encoding="utf-8"))
    assert review["review_classification"] == "STRATEGY_RETRAIN_REVIEW"
    assert review["strategy_retrain_candidate_ids"] == ["trend-a"]
    assert any("repeated posterior-confidence decay" in item for item in review["triggers"])
