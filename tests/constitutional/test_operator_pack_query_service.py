"""Shared fixtures for operator pack query / approval disposition constitutional tests."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.contracts.oracle_operator_reports import OracleBriefingPackReport


def _build_briefing_report(
    tmp_path: Path,
    *,
    summary_line: str,
    trust_status: str,
) -> OracleBriefingPackReport:
    root = str(tmp_path.resolve())
    return OracleBriefingPackReport(
        generated_at_utc=datetime.now(timezone.utc),
        repo_root=root,
        search_root=root,
        trust_status=trust_status,
        summary_line=summary_line,
        status_pack_digest_sha256="a" * 64,
        provenance_digest_sha256="b" * 64,
    )
