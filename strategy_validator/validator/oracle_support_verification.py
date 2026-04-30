"""Summarize oracle support-chain verification manifests (advisory/read-only)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from strategy_validator.contracts.oracle_types import OracleSupportVerificationStatus


def summarize_support_verification(
    support_manifest_paths: Iterable[Path | str],
) -> tuple[OracleSupportVerificationStatus, list[str], str]:
    """Return (status, paths-as-strings, summary_line) for supplied verification JSON paths."""

    paths = [Path(p) for p in support_manifest_paths if p]
    if not paths:
        return (
            "ABSENT",
            [],
            "No oracle support-chain verification manifests were supplied.",
        )

    normalized_paths: list[str] = []
    statuses: list[str] = []
    for path in paths:
        normalized_paths.append(str(path))
        if not path.exists():
            statuses.append("MISSING")
            continue
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            statuses.append("INVALID")
            continue
        if not isinstance(raw, dict):
            statuses.append("INVALID")
            continue
        st = str(raw.get("status") or "").strip().upper() or "UNVERIFIED"
        statuses.append(st)

    if all(s == "VERIFIED" for s in statuses):
        return "VERIFIED", normalized_paths, f"Verified {len(paths)} support manifest(s)."
    if any(s == "VERIFIED" for s in statuses):
        return (
            "INCOMPLETE",
            normalized_paths,
            "Partial verification: not all manifests are VERIFIED.",
        )
    if any(s in {"MISSING", "INVALID"} for s in statuses):
        return (
            "INCOMPLETE",
            normalized_paths,
            "One or more verification manifests are missing or unreadable.",
        )
    return "UNVERIFIED", normalized_paths, "Support-chain verification is not sealed as VERIFIED."
