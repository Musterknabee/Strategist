from __future__ import annotations

from pathlib import Path


def test_release_candidate_records_frontend_absence_when_skipped() -> None:
    source = Path("strategy_validator/cli/release_candidate.py").read_text(encoding="utf-8")
    assert "frontend_status" in source
    assert "backend assessment cannot imply frontend readiness" in source
    assert '"skipped": True' in source
    assert "ui/strategist-web is missing" in source
