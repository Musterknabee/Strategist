from __future__ import annotations

from typing import Iterable, Sequence

from strategy_validator.contracts.oracle import OracleArtifactCoverageStatus, OracleArtifactLineageItem


def summarize_artifact_coverage(
    *,
    expected_labels: Sequence[str],
    items: Iterable[OracleArtifactLineageItem],
) -> tuple[OracleArtifactCoverageStatus, int, str, list[str]]:
    materialized = list(items)
    normalized_expected = [str(label).strip() for label in expected_labels if str(label).strip()]
    if not normalized_expected:
        return "UNKNOWN", 0, "No artifact coverage expectations were declared.", []
    present = {item.artifact_label for item in materialized if str(item.artifact_label).strip()}
    missing = [label for label in normalized_expected if label not in present]
    present_count = len(normalized_expected) - len(missing)
    if not missing:
        status: OracleArtifactCoverageStatus = "COMPLETE"
    elif present_count > 0:
        status = "PARTIAL"
    else:
        status = "MISSING"
    summary = (
        f"Artifact coverage status={status}; present={present_count}; missing={len(missing)}; "
        f"expected={len(normalized_expected)}."
    )
    return status, len(missing), summary, missing
