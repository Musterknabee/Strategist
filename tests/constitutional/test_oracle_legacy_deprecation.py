from __future__ import annotations

import json
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main


def _write_review_lane(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "schema_version": "oracle_review_lane_entry/v1",
        "appended_at_utc": "2026-04-13T08:00:00Z",
        "lane_id": path.stem,
        "sequence_number": 0,
        "entry_id": "entry-0",
        "review_id": "review-0",
        "previous_entry_hash": None,
        "entry_hash": "hash-0",
        "manifest_path": "docs/artifacts/oracle/ORACLE_MEMORY_REVIEW_EVIDENCE.json",
        "manifest_sha256": "a" * 64,
        "review_classification": "HEIGHTENED_RESEARCH_POSTURE",
        "window_end_sequence_number": 0,
        "latest_global_action": "CANARY_REVIEW",
        "latest_epistemic_status": "ELEVATED",
        "evidence_status": "VERIFIED",
        "summary_line": "heightened review",
    }
    path.write_text(json.dumps(entry) + "\n", encoding="utf-8")


@pytest.mark.constitutional
def test_legacy_weekly_digest_requires_explicit_opt_in(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    lane_path = tmp_path / "docs" / "artifacts" / "oracle" / "ORACLE_REVIEW_LANE.jsonl"
    _write_review_lane(lane_path)
    output = lane_path.with_name("ORACLE_WEEKLY_DIGEST.json")

    rc = main([
        "oracle-weekly-digest",
        "--lane-path", str(lane_path),
        "--window-size", "1",
        "--output", str(output),
    ])

    assert rc == 2
    captured = capsys.readouterr()
    assert "--allow-legacy-lane-read" in captured.err
    assert not output.exists()


@pytest.mark.constitutional
def test_legacy_weekly_digest_warns_when_opted_in(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    lane_path = tmp_path / "docs" / "artifacts" / "oracle" / "ORACLE_REVIEW_LANE.jsonl"
    _write_review_lane(lane_path)
    output = lane_path.with_name("ORACLE_WEEKLY_DIGEST.json")
    markdown_output = lane_path.with_name("ORACLE_WEEKLY_DIGEST.md")

    rc = main([
        "oracle-weekly-digest",
        "--lane-path", str(lane_path),
        "--allow-legacy-lane-read",
        "--window-size", "1",
        "--output", str(output),
        "--markdown-output", str(markdown_output),
    ])

    assert rc == 0
    captured = capsys.readouterr()
    assert "[deprecated] oracle-weekly-digest" in captured.err
    rendered = markdown_output.read_text(encoding="utf-8")
    assert "Direct legacy lane reads require explicit operator opt-in" in rendered
