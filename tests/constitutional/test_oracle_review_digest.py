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
def test_oracle_memory_review_evidence_and_weekly_digest_round_trip(tmp_path: Path) -> None:
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

    memory_lane = repo_root / "docs" / "artifacts" / "oracle" / "ORACLE_MEMORY_LANE.jsonl"
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
            "--lane-path", str(memory_lane),
        ])
        assert rc == 0

    review_manifest = repo_root / "docs" / "artifacts" / "oracle" / "ORACLE_MEMORY_REVIEW_EVIDENCE.json"
    review_dsse = review_manifest.with_suffix(".dsse.json")
    review_verify = review_manifest.with_name("ORACLE_MEMORY_REVIEW_EVIDENCE.verification.json")
    review_report = review_manifest.with_name("ORACLE_MEMORY_REVIEW_REPORT.json")
    review_md = review_manifest.with_name("ORACLE_MEMORY_REVIEW_REPORT.md")
    rc = main([
        "oracle-memory-review-evidence",
        "--lane-path", str(memory_lane),
        "--repo-root", str(repo_root),
        "--window-size", "2",
        "--signing-private-key", str(private_key),
        "--public-key", str(public_key),
        "--report-output", str(review_report),
        "--markdown-output", str(review_md),
        "--output", str(review_manifest),
        "--dsse-output", str(review_dsse),
        "--verification-output", str(review_verify),
    ])
    assert rc == 0
    review = json.loads(review_report.read_text(encoding="utf-8"))
    assert review["review_classification"] == "STRATEGY_RETRAIN_REVIEW"

    review_lane = repo_root / "docs" / "artifacts" / "oracle" / "ORACLE_REVIEW_LANE.jsonl"
    review_entry = review_lane.with_name("ORACLE_REVIEW_LANE_ENTRY.json")
    rc = main([
        "oracle-review-lane-append",
        str(review_manifest),
        "--repo-root", str(repo_root),
        "--dsse", str(review_dsse),
        "--public-key", str(public_key),
        "--lane-path", str(review_lane),
        "--output", str(review_entry),
    ])
    assert rc == 0
    entry = json.loads(review_entry.read_text(encoding="utf-8"))
    assert entry["sequence_number"] == 0
    assert entry["review_classification"] == "STRATEGY_RETRAIN_REVIEW"

    digest_output = review_lane.with_name("ORACLE_WEEKLY_DIGEST.json")
    digest_md = review_lane.with_name("ORACLE_WEEKLY_DIGEST.md")
    rc = main([
        "oracle-weekly-digest",
        "--lane-path", str(review_lane),
        "--allow-legacy-lane-read",
        "--window-size", "7",
        "--output", str(digest_output),
        "--markdown-output", str(digest_md),
    ])
    assert rc == 0
    digest = json.loads(digest_output.read_text(encoding="utf-8"))
    assert digest["doctrine_posture"] == "STRATEGY_RETRAIN_REVIEW"
    assert digest["classification_counts"]["STRATEGY_RETRAIN_REVIEW"] == 1
    assert "ORACLE WEEKLY DIGEST" in digest_md.read_text(encoding="utf-8")


@pytest.mark.constitutional
def test_oracle_review_lane_append_rejects_incomplete_review_evidence(tmp_path: Path) -> None:
    repo_root = tmp_path
    lane_path = repo_root / "docs" / "artifacts" / "oracle" / "ORACLE_MEMORY_LANE.jsonl"
    lane_path.parent.mkdir(parents=True)
    lane_path.write_text("", encoding="utf-8")

    private_key = repo_root / "oracle_private.pem"
    public_key = repo_root / "oracle_public.pem"
    generate_snapshot_signing_keypair(private_key_path=private_key, public_key_path=public_key)

    review_manifest = repo_root / "ORACLE_MEMORY_REVIEW_EVIDENCE.json"
    review_dsse = review_manifest.with_suffix(".dsse.json")
    review_verify = review_manifest.with_name("ORACLE_MEMORY_REVIEW_EVIDENCE.verification.json")
    review_report = review_manifest.with_name("ORACLE_MEMORY_REVIEW_REPORT.json")
    review_md = review_manifest.with_name("ORACLE_MEMORY_REVIEW_REPORT.md")

    rc = main([
        "oracle-memory-review-evidence",
        "--lane-path", str(lane_path),
        "--repo-root", str(repo_root),
        "--window-size", "7",
        "--signing-private-key", str(private_key),
        "--public-key", str(public_key),
        "--report-output", str(review_report),
        "--markdown-output", str(review_md),
        "--output", str(review_manifest),
        "--dsse-output", str(review_dsse),
        "--verification-output", str(review_verify),
    ])
    assert rc == 0
    manifest = json.loads(review_manifest.read_text(encoding="utf-8"))
    report_subject = next(item for item in manifest["subjects"] if item["name"] == "ORACLE_MEMORY_REVIEW_REPORT.json")
    (repo_root / Path(report_subject["path"])).unlink()

    rc = main([
        "oracle-review-lane-append",
        str(review_manifest),
        "--repo-root", str(repo_root),
        "--dsse", str(review_dsse),
        "--public-key", str(public_key),
        "--lane-path", str(repo_root / "ORACLE_REVIEW_LANE.jsonl"),
    ])
    assert rc != 0


def _write_review_lane(path: Path, entries: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(item, separators=(",", ":")) for item in entries]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


@pytest.mark.constitutional
def test_oracle_weekly_digest_evidence_and_doctrine_drift_round_trip(tmp_path: Path) -> None:
    repo_root = tmp_path
    private_key = repo_root / "oracle_private.pem"
    public_key = repo_root / "oracle_public.pem"
    generate_snapshot_signing_keypair(private_key_path=private_key, public_key_path=public_key)

    previous_lane = repo_root / "week1" / "ORACLE_REVIEW_LANE.jsonl"
    current_lane = repo_root / "week2" / "ORACLE_REVIEW_LANE.jsonl"
    _write_review_lane(previous_lane, [
        {
            "schema_version": "oracle_review_lane_entry/v1",
            "appended_at_utc": "2026-04-13T08:00:00Z",
            "lane_id": "ORACLE_REVIEW_LANE",
            "sequence_number": 0,
            "entry_id": "entry-0",
            "review_id": "review-stable-0",
            "previous_entry_hash": None,
            "entry_hash": "hash-0",
            "manifest_path": "week1/ORACLE_MEMORY_REVIEW_EVIDENCE.json",
            "manifest_sha256": "a" * 64,
            "review_classification": "STABLE_RESEARCH_POSTURE",
            "window_end_sequence_number": 0,
            "latest_global_action": "OBSERVE",
            "latest_epistemic_status": "NOMINAL",
            "evidence_status": "VERIFIED",
            "summary_line": "stable review lane"
        },
        {
            "schema_version": "oracle_review_lane_entry/v1",
            "appended_at_utc": "2026-04-14T08:00:00Z",
            "lane_id": "ORACLE_REVIEW_LANE",
            "sequence_number": 1,
            "entry_id": "entry-1",
            "review_id": "review-heightened-1",
            "previous_entry_hash": "hash-0",
            "entry_hash": "hash-1",
            "manifest_path": "week1/ORACLE_MEMORY_REVIEW_EVIDENCE_1.json",
            "manifest_sha256": "b" * 64,
            "review_classification": "HEIGHTENED_RESEARCH_POSTURE",
            "window_end_sequence_number": 1,
            "latest_global_action": "CANARY_REVIEW",
            "latest_epistemic_status": "ELEVATED",
            "evidence_status": "VERIFIED",
            "summary_line": "heightened review lane"
        }
    ])
    _write_review_lane(current_lane, [
        {
            "schema_version": "oracle_review_lane_entry/v1",
            "appended_at_utc": "2026-04-20T08:00:00Z",
            "lane_id": "ORACLE_REVIEW_LANE",
            "sequence_number": 0,
            "entry_id": "entry-0",
            "review_id": "review-repair-0",
            "previous_entry_hash": None,
            "entry_hash": "hash-0",
            "manifest_path": "week2/ORACLE_MEMORY_REVIEW_EVIDENCE.json",
            "manifest_sha256": "c" * 64,
            "review_classification": "REPAIR_FIRST",
            "window_end_sequence_number": 0,
            "latest_global_action": "DEFENSIVE_POSTURE",
            "latest_epistemic_status": "UNKNOWN_UNKNOWNS",
            "evidence_status": "VERIFIED",
            "summary_line": "repair review lane"
        },
        {
            "schema_version": "oracle_review_lane_entry/v1",
            "appended_at_utc": "2026-04-21T08:00:00Z",
            "lane_id": "ORACLE_REVIEW_LANE",
            "sequence_number": 1,
            "entry_id": "entry-1",
            "review_id": "review-repair-1",
            "previous_entry_hash": "hash-0",
            "entry_hash": "hash-1",
            "manifest_path": "week2/ORACLE_MEMORY_REVIEW_EVIDENCE_1.json",
            "manifest_sha256": "d" * 64,
            "review_classification": "REPAIR_FIRST",
            "window_end_sequence_number": 1,
            "latest_global_action": "DEFENSIVE_POSTURE",
            "latest_epistemic_status": "UNKNOWN_UNKNOWNS",
            "evidence_status": "VERIFIED",
            "summary_line": "repair review lane sustained"
        }
    ])

    prev_manifest = previous_lane.with_name("ORACLE_WEEKLY_DIGEST_EVIDENCE.json")
    prev_dsse = previous_lane.with_name("ORACLE_WEEKLY_DIGEST_EVIDENCE.dsse.json")
    prev_verify = previous_lane.with_name("ORACLE_WEEKLY_DIGEST_EVIDENCE.verification.json")
    prev_digest = previous_lane.with_name("ORACLE_WEEKLY_DIGEST.json")
    prev_md = previous_lane.with_name("ORACLE_WEEKLY_DIGEST.md")
    rc = main([
        "oracle-weekly-digest-evidence",
        "--lane-path", str(previous_lane),
        "--allow-legacy-lane-read",
        "--repo-root", str(repo_root),
        "--window-size", "7",
        "--signing-private-key", str(private_key),
        "--public-key", str(public_key),
        "--report-output", str(prev_digest),
        "--markdown-output", str(prev_md),
        "--output", str(prev_manifest),
        "--dsse-output", str(prev_dsse),
        "--verification-output", str(prev_verify),
    ])
    assert rc == 0

    curr_manifest = current_lane.with_name("ORACLE_WEEKLY_DIGEST_EVIDENCE.json")
    curr_dsse = current_lane.with_name("ORACLE_WEEKLY_DIGEST_EVIDENCE.dsse.json")
    curr_verify = current_lane.with_name("ORACLE_WEEKLY_DIGEST_EVIDENCE.verification.json")
    curr_digest = current_lane.with_name("ORACLE_WEEKLY_DIGEST.json")
    curr_md = current_lane.with_name("ORACLE_WEEKLY_DIGEST.md")
    rc = main([
        "oracle-weekly-digest-evidence",
        "--lane-path", str(current_lane),
        "--allow-legacy-lane-read",
        "--repo-root", str(repo_root),
        "--window-size", "7",
        "--signing-private-key", str(private_key),
        "--public-key", str(public_key),
        "--report-output", str(curr_digest),
        "--markdown-output", str(curr_md),
        "--output", str(curr_manifest),
        "--dsse-output", str(curr_dsse),
        "--verification-output", str(curr_verify),
    ])
    assert rc == 0

    drift_output = repo_root / "ORACLE_DOCTRINE_DRIFT_REPORT.json"
    drift_md = repo_root / "ORACLE_DOCTRINE_DRIFT_REPORT.md"
    rc = main([
        "oracle-doctrine-drift",
        str(prev_manifest),
        str(curr_manifest),
        "--repo-root", str(repo_root),
        "--previous-dsse", str(prev_dsse),
        "--current-dsse", str(curr_dsse),
        "--previous-public-key", str(public_key),
        "--current-public-key", str(public_key),
        "--output", str(drift_output),
        "--markdown-output", str(drift_md),
    ])
    assert rc == 0
    report = json.loads(drift_output.read_text(encoding="utf-8"))
    assert report["drift_classification"] == "DOCTRINE_ESCALATION"
    assert report["current_doctrine_posture"] == "REPAIR_FIRST"
    assert "ORACLE DOCTRINE DRIFT REPORT" in drift_md.read_text(encoding="utf-8")


@pytest.mark.constitutional
def test_oracle_doctrine_drift_reports_evidence_gap_when_current_digest_chain_is_incomplete(tmp_path: Path) -> None:
    repo_root = tmp_path
    private_key = repo_root / "oracle_private.pem"
    public_key = repo_root / "oracle_public.pem"
    generate_snapshot_signing_keypair(private_key_path=private_key, public_key_path=public_key)

    lane = repo_root / "review" / "ORACLE_REVIEW_LANE.jsonl"
    _write_review_lane(lane, [
        {
            "schema_version": "oracle_review_lane_entry/v1",
            "appended_at_utc": "2026-04-13T08:00:00Z",
            "lane_id": "ORACLE_REVIEW_LANE",
            "sequence_number": 0,
            "entry_id": "entry-0",
            "review_id": "review-0",
            "previous_entry_hash": None,
            "entry_hash": "hash-0",
            "manifest_path": "review/ORACLE_MEMORY_REVIEW_EVIDENCE.json",
            "manifest_sha256": "e" * 64,
            "review_classification": "HEIGHTENED_RESEARCH_POSTURE",
            "window_end_sequence_number": 0,
            "latest_global_action": "CANARY_REVIEW",
            "latest_epistemic_status": "ELEVATED",
            "evidence_status": "VERIFIED",
            "summary_line": "heightened lane"
        }
    ])

    prev_manifest = repo_root / "prev" / "ORACLE_WEEKLY_DIGEST_EVIDENCE.json"
    prev_manifest.parent.mkdir(parents=True)
    prev_dsse = prev_manifest.with_suffix(".dsse.json")
    prev_verify = prev_manifest.with_name("ORACLE_WEEKLY_DIGEST_EVIDENCE.verification.json")
    prev_digest = prev_manifest.with_name("ORACLE_WEEKLY_DIGEST.json")
    prev_md = prev_manifest.with_name("ORACLE_WEEKLY_DIGEST.md")
    rc = main([
        "oracle-weekly-digest-evidence",
        "--lane-path", str(lane),
        "--allow-legacy-lane-read",
        "--repo-root", str(repo_root),
        "--window-size", "7",
        "--signing-private-key", str(private_key),
        "--public-key", str(public_key),
        "--report-output", str(prev_digest),
        "--markdown-output", str(prev_md),
        "--output", str(prev_manifest),
        "--dsse-output", str(prev_dsse),
        "--verification-output", str(prev_verify),
    ])
    assert rc == 0

    curr_manifest = repo_root / "curr" / "ORACLE_WEEKLY_DIGEST_EVIDENCE.json"
    curr_manifest.parent.mkdir(parents=True)
    curr_dsse = curr_manifest.with_suffix(".dsse.json")
    curr_verify = curr_manifest.with_name("ORACLE_WEEKLY_DIGEST_EVIDENCE.verification.json")
    curr_digest = curr_manifest.with_name("ORACLE_WEEKLY_DIGEST.json")
    curr_md = curr_manifest.with_name("ORACLE_WEEKLY_DIGEST.md")
    rc = main([
        "oracle-weekly-digest-evidence",
        "--lane-path", str(lane),
        "--allow-legacy-lane-read",
        "--repo-root", str(repo_root),
        "--window-size", "7",
        "--signing-private-key", str(private_key),
        "--public-key", str(public_key),
        "--report-output", str(curr_digest),
        "--markdown-output", str(curr_md),
        "--output", str(curr_manifest),
        "--dsse-output", str(curr_dsse),
        "--verification-output", str(curr_verify),
    ])
    assert rc == 0
    curr_digest.unlink()

    drift_output = repo_root / "ORACLE_DOCTRINE_DRIFT_REPORT.json"
    rc = main([
        "oracle-doctrine-drift",
        str(prev_manifest),
        str(curr_manifest),
        "--repo-root", str(repo_root),
        "--previous-dsse", str(prev_dsse),
        "--current-dsse", str(curr_dsse),
        "--previous-public-key", str(public_key),
        "--current-public-key", str(public_key),
        "--output", str(drift_output),
    ])
    assert rc == 2
    report = json.loads(drift_output.read_text(encoding="utf-8"))
    assert report["drift_classification"] == "DOCTRINE_EVIDENCE_GAP"
    assert report["comparison_status"] == "INCOMPLETE"
