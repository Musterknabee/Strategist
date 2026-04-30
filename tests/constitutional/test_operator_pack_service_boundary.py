"""Shared fixtures for operator pack service boundary constitutional tests."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.contracts.oracle_operator_reports import OracleStatusPackReport


def _status_report(tmp_path: Path) -> OracleStatusPackReport:
    root = str(tmp_path.resolve())
    return OracleStatusPackReport(
        generated_at_utc=datetime(2026, 4, 14, 8, 0, tzinfo=timezone.utc),
        repo_root=root,
        search_root=root,
        trust_status="TRUST_RESTRICTED",
        summary_line="status pack test",
    )
