from __future__ import annotations

from pathlib import Path

from tests.constitutional.cli_release_candidate_sources import read_release_candidate_sources


def test_release_candidate_records_frontend_absence_when_skipped() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    source = read_release_candidate_sources(repo_root)
    assert "frontend_status" in source
    assert "backend assessment cannot imply frontend readiness" in source
    assert '"skipped": True' in source
    assert "ui/strategist-web is missing" in source
