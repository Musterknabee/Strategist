from __future__ import annotations

from typing import Iterable

from strategy_validator.contracts.oracle_types import OracleArtifactIntegrityStatus
from strategy_validator.contracts.oracle_core import OracleArtifactLineageItem


def summarize_artifact_integrity(items: Iterable[OracleArtifactLineageItem]) -> tuple[OracleArtifactIntegrityStatus, int, str]:
    materialized = list(items)
    if not materialized:
        return "UNKNOWN", 0, "No artifact integrity evidence was available."
    verified = sum(1 for item in materialized if item.integrity_status == "VERIFIED")
    unverified = sum(1 for item in materialized if item.integrity_status in {"INCOMPLETE", "UNVERIFIED"})
    not_applicable = sum(1 for item in materialized if item.integrity_status == "NOT_APPLICABLE")
    if unverified == 0 and verified > 0:
        status: OracleArtifactIntegrityStatus = "VERIFIED"
    elif verified > 0 or not_applicable > 0:
        status = "MIXED"
    else:
        status = "UNVERIFIED"
    summary = (
        f"Artifact integrity status={status}; verified={verified}; "
        f"unverified_or_incomplete={unverified}; not_applicable={not_applicable}."
    )
    return status, unverified, summary
