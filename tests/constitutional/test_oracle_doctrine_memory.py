from __future__ import annotations

import json
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.validator.rollout_ops import generate_snapshot_signing_keypair


def _write_review_lane(path: Path, entries: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(entry) + "\n")


@pytest.mark.constitutional
def test_oracle_doctrine_drift_evidence_lane_and_monthly_digest_round_trip(tmp_path: Path) -> None:
    repo_root = tmp_path
    private_key = repo_root / "oracle_private.pem"
    public_key = repo_root / "oracle_public.pem"
    generate_snapshot_signing_keypair(private_key_path=private_key, public_key_path=public_key)

    week1_lane = repo_root / "week1" / "ORACLE_REVIEW_LANE.jsonl"
    week2_lane = repo_root / "week2" / "ORACLE_REVIEW_LANE.jsonl"
    week3_lane = repo_root / "week3" / "ORACLE_REVIEW_LANE.jsonl"

    _write_review_lane(week1_lane, [
        {
            "schema_version": "oracle_review_lane_entry/v1",
            "appended_at_utc": "2026-04-13T08:00:00Z",
            "lane_id": "ORACLE_REVIEW_LANE",
            "sequence_number": 0,
            "entry_id": "entry-w1-0",
            "review_id": "review-w1-0",
            "previous_entry_hash": None,
            "entry_hash": "hash-w1-0",
            "manifest_path": "week1/ORACLE_MEMORY_REVIEW_EVIDENCE.json",
            "manifest_sha256": "a" * 64,
            "review_classification": "STABLE_RESEARCH_POSTURE",
            "window_end_sequence_number": 0,
            "latest_global_action": "OBSERVE",
            "latest_epistemic_status": "NOMINAL",
            "evidence_status": "VERIFIED",
            "summary_line": "stable review lane",
        },
        {
            "schema_version": "oracle_review_lane_entry/v1",
            "appended_at_utc": "2026-04-14T08:00:00Z",
            "lane_id": "ORACLE_REVIEW_LANE",
            "sequence_number": 1,
            "entry_id": "entry-w1-1",
            "review_id": "review-w1-1",
            "previous_entry_hash": "hash-w1-0",
            "entry_hash": "hash-w1-1",
            "manifest_path": "week1/ORACLE_MEMORY_REVIEW_EVIDENCE_1.json",
            "manifest_sha256": "b" * 64,
            "review_classification": "HEIGHTENED_RESEARCH_POSTURE",
            "window_end_sequence_number": 1,
            "latest_global_action": "CANARY_REVIEW",
            "latest_epistemic_status": "ELEVATED",
            "evidence_status": "VERIFIED",
            "summary_line": "heightened review lane",
        },
    ])
    _write_review_lane(week2_lane, [
        {
            "schema_version": "oracle_review_lane_entry/v1",
            "appended_at_utc": "2026-04-20T08:00:00Z",
            "lane_id": "ORACLE_REVIEW_LANE",
            "sequence_number": 0,
            "entry_id": "entry-w2-0",
            "review_id": "review-w2-0",
            "previous_entry_hash": None,
            "entry_hash": "hash-w2-0",
            "manifest_path": "week2/ORACLE_MEMORY_REVIEW_EVIDENCE.json",
            "manifest_sha256": "c" * 64,
            "review_classification": "HEIGHTENED_RESEARCH_POSTURE",
            "window_end_sequence_number": 0,
            "latest_global_action": "CANARY_REVIEW",
            "latest_epistemic_status": "ELEVATED",
            "evidence_status": "VERIFIED",
            "summary_line": "heightened review lane sustained",
        },
        {
            "schema_version": "oracle_review_lane_entry/v1",
            "appended_at_utc": "2026-04-21T08:00:00Z",
            "lane_id": "ORACLE_REVIEW_LANE",
            "sequence_number": 1,
            "entry_id": "entry-w2-1",
            "review_id": "review-w2-1",
            "previous_entry_hash": "hash-w2-0",
            "entry_hash": "hash-w2-1",
            "manifest_path": "week2/ORACLE_MEMORY_REVIEW_EVIDENCE_1.json",
            "manifest_sha256": "d" * 64,
            "review_classification": "HEIGHTENED_RESEARCH_POSTURE",
            "window_end_sequence_number": 1,
            "latest_global_action": "CANARY_REVIEW",
            "latest_epistemic_status": "ELEVATED",
            "evidence_status": "VERIFIED",
            "summary_line": "heightened review lane sustained again",
        },
    ])
    _write_review_lane(week3_lane, [
        {
            "schema_version": "oracle_review_lane_entry/v1",
            "appended_at_utc": "2026-04-27T08:00:00Z",
            "lane_id": "ORACLE_REVIEW_LANE",
            "sequence_number": 0,
            "entry_id": "entry-w3-0",
            "review_id": "review-w3-0",
            "previous_entry_hash": None,
            "entry_hash": "hash-w3-0",
            "manifest_path": "week3/ORACLE_MEMORY_REVIEW_EVIDENCE.json",
            "manifest_sha256": "e" * 64,
            "review_classification": "REPAIR_FIRST",
            "window_end_sequence_number": 0,
            "latest_global_action": "DEFENSIVE_POSTURE",
            "latest_epistemic_status": "UNKNOWN_UNKNOWNS",
            "evidence_status": "VERIFIED",
            "summary_line": "repair review lane",
        },
        {
            "schema_version": "oracle_review_lane_entry/v1",
            "appended_at_utc": "2026-04-28T08:00:00Z",
            "lane_id": "ORACLE_REVIEW_LANE",
            "sequence_number": 1,
            "entry_id": "entry-w3-1",
            "review_id": "review-w3-1",
            "previous_entry_hash": "hash-w3-0",
            "entry_hash": "hash-w3-1",
            "manifest_path": "week3/ORACLE_MEMORY_REVIEW_EVIDENCE_1.json",
            "manifest_sha256": "f" * 64,
            "review_classification": "REPAIR_FIRST",
            "window_end_sequence_number": 1,
            "latest_global_action": "DEFENSIVE_POSTURE",
            "latest_epistemic_status": "UNKNOWN_UNKNOWNS",
            "evidence_status": "VERIFIED",
            "summary_line": "repair review lane sustained",
        },
    ])

    def build_weekly(lane: Path) -> tuple[Path, Path]:
        manifest = lane.with_name("ORACLE_WEEKLY_DIGEST_EVIDENCE.json")
        dsse = lane.with_name("ORACLE_WEEKLY_DIGEST_EVIDENCE.dsse.json")
        verify = lane.with_name("ORACLE_WEEKLY_DIGEST_EVIDENCE.verification.json")
        digest = lane.with_name("ORACLE_WEEKLY_DIGEST.json")
        md = lane.with_name("ORACLE_WEEKLY_DIGEST.md")
        rc = main([
            "oracle-weekly-digest-evidence",
            "--lane-path", str(lane),
        "--allow-legacy-lane-read",
            "--repo-root", str(repo_root),
            "--window-size", "7",
            "--signing-private-key", str(private_key),
            "--public-key", str(public_key),
            "--report-output", str(digest),
            "--markdown-output", str(md),
            "--output", str(manifest),
            "--dsse-output", str(dsse),
            "--verification-output", str(verify),
        ])
        assert rc == 0
        return manifest, dsse

    week1_manifest, week1_dsse = build_weekly(week1_lane)
    week2_manifest, week2_dsse = build_weekly(week2_lane)
    week3_manifest, week3_dsse = build_weekly(week3_lane)

    doctrine_lane = repo_root / "docs" / "artifacts" / "oracle" / "ORACLE_DOCTRINE_LANE.jsonl"
    for idx, (prev_manifest, prev_dsse, curr_manifest, curr_dsse) in enumerate([
        (week1_manifest, week1_dsse, week2_manifest, week2_dsse),
        (week2_manifest, week2_dsse, week3_manifest, week3_dsse),
    ], start=1):
        drift_manifest = repo_root / f"doctrine{idx}" / "ORACLE_DOCTRINE_DRIFT_EVIDENCE.json"
        drift_manifest.parent.mkdir(parents=True, exist_ok=True)
        drift_dsse = drift_manifest.with_name("ORACLE_DOCTRINE_DRIFT_EVIDENCE.dsse.json")
        drift_verify = drift_manifest.with_name("ORACLE_DOCTRINE_DRIFT_EVIDENCE.verification.json")
        drift_report = drift_manifest.with_name("ORACLE_DOCTRINE_DRIFT_REPORT.json")
        drift_md = drift_manifest.with_name("ORACLE_DOCTRINE_DRIFT_REPORT.md")
        rc = main([
            "oracle-doctrine-drift-evidence",
            str(prev_manifest),
            str(curr_manifest),
            "--repo-root", str(repo_root),
            "--previous-dsse", str(prev_dsse),
            "--current-dsse", str(curr_dsse),
            "--previous-public-key", str(public_key),
            "--current-public-key", str(public_key),
            "--signing-private-key", str(private_key),
            "--public-key", str(public_key),
            "--report-output", str(drift_report),
            "--markdown-output", str(drift_md),
            "--output", str(drift_manifest),
            "--dsse-output", str(drift_dsse),
            "--verification-output", str(drift_verify),
        ])
        assert rc == 0
        rc = main([
            "oracle-doctrine-lane-append",
            str(drift_manifest),
            "--repo-root", str(repo_root),
            "--dsse", str(drift_dsse),
            "--public-key", str(public_key),
            "--lane-path", str(doctrine_lane),
        ])
        assert rc == 0

    monthly_output = doctrine_lane.with_name("ORACLE_MONTHLY_DIGEST.json")
    monthly_md = doctrine_lane.with_name("ORACLE_MONTHLY_DIGEST.md")
    rc = main([
        "oracle-monthly-digest",
        "--lane-path", str(doctrine_lane),
        "--allow-legacy-lane-read",
        "--window-size", "4",
        "--output", str(monthly_output),
        "--markdown-output", str(monthly_md),
    ])
    assert rc == 0
    digest = json.loads(monthly_output.read_text(encoding="utf-8"))
    assert digest["doctrine_memory_classification"] == "DOCTRINE_REPAIR_PERSISTENT"
    assert digest["drift_classification_counts"]["DOCTRINE_ESCALATION"] >= 1
    assert "ORACLE MONTHLY DIGEST" in monthly_md.read_text(encoding="utf-8")


@pytest.mark.constitutional
def test_oracle_doctrine_lane_append_rejects_incomplete_drift_evidence(tmp_path: Path) -> None:
    repo_root = tmp_path
    private_key = repo_root / "oracle_private.pem"
    public_key = repo_root / "oracle_public.pem"
    generate_snapshot_signing_keypair(private_key_path=private_key, public_key_path=public_key)

    lane = repo_root / "week" / "ORACLE_REVIEW_LANE.jsonl"
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
            "manifest_path": "week/ORACLE_MEMORY_REVIEW_EVIDENCE.json",
            "manifest_sha256": "a" * 64,
            "review_classification": "HEIGHTENED_RESEARCH_POSTURE",
            "window_end_sequence_number": 0,
            "latest_global_action": "CANARY_REVIEW",
            "latest_epistemic_status": "ELEVATED",
            "evidence_status": "VERIFIED",
            "summary_line": "heightened lane",
        }
    ])

    def build_weekly(outdir: Path) -> tuple[Path, Path]:
        manifest = outdir / "ORACLE_WEEKLY_DIGEST_EVIDENCE.json"
        dsse = outdir / "ORACLE_WEEKLY_DIGEST_EVIDENCE.dsse.json"
        verify = outdir / "ORACLE_WEEKLY_DIGEST_EVIDENCE.verification.json"
        digest = outdir / "ORACLE_WEEKLY_DIGEST.json"
        md = outdir / "ORACLE_WEEKLY_DIGEST.md"
        outdir.mkdir(parents=True, exist_ok=True)
        rc = main([
            "oracle-weekly-digest-evidence",
            "--lane-path", str(lane),
        "--allow-legacy-lane-read",
            "--repo-root", str(repo_root),
            "--window-size", "7",
            "--signing-private-key", str(private_key),
            "--public-key", str(public_key),
            "--report-output", str(digest),
            "--markdown-output", str(md),
            "--output", str(manifest),
            "--dsse-output", str(dsse),
            "--verification-output", str(verify),
        ])
        assert rc == 0
        return manifest, dsse

    prev_manifest, prev_dsse = build_weekly(repo_root / "prev")
    curr_manifest, curr_dsse = build_weekly(repo_root / "curr")

    drift_manifest = repo_root / "doctrine" / "ORACLE_DOCTRINE_DRIFT_EVIDENCE.json"
    drift_manifest.parent.mkdir(parents=True, exist_ok=True)
    drift_dsse = drift_manifest.with_name("ORACLE_DOCTRINE_DRIFT_EVIDENCE.dsse.json")
    drift_report = drift_manifest.with_name("ORACLE_DOCTRINE_DRIFT_REPORT.json")
    drift_md = drift_manifest.with_name("ORACLE_DOCTRINE_DRIFT_REPORT.md")
    rc = main([
        "oracle-doctrine-drift-evidence",
        str(prev_manifest),
        str(curr_manifest),
        "--repo-root", str(repo_root),
        "--previous-dsse", str(prev_dsse),
        "--current-dsse", str(curr_dsse),
        "--previous-public-key", str(public_key),
        "--current-public-key", str(public_key),
        "--signing-private-key", str(private_key),
        "--public-key", str(public_key),
        "--report-output", str(drift_report),
        "--markdown-output", str(drift_md),
        "--output", str(drift_manifest),
        "--dsse-output", str(drift_dsse),
    ])
    assert rc == 0
    drift_report.unlink()

    doctrine_lane = repo_root / "docs" / "artifacts" / "oracle" / "ORACLE_DOCTRINE_LANE.jsonl"
    rc = main([
        "oracle-doctrine-lane-append",
        str(drift_manifest),
        "--repo-root", str(repo_root),
        "--dsse", str(drift_dsse),
        "--public-key", str(public_key),
        "--lane-path", str(doctrine_lane),
    ])
    assert rc == 2
    verification = json.loads(drift_manifest.with_name("ORACLE_DOCTRINE_DRIFT_EVIDENCE.verification.json").read_text(encoding="utf-8"))
    assert verification["status"] == "INCOMPLETE"
