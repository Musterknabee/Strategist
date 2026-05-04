from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from strategy_validator.contracts.oracle_core import OracleArtifactLineageItem
from strategy_validator.validator.oracle_schema_registry import load_registered_artifact


_VALID_INTEGRITY = {"VERIFIED", "INCOMPLETE", "UNVERIFIED", "NOT_APPLICABLE"}


def _normalize_integrity(value: str | None) -> str:
    normalized = str(value or "NOT_APPLICABLE").strip().upper() or "NOT_APPLICABLE"
    return normalized if normalized in _VALID_INTEGRITY else "NOT_APPLICABLE"


def build_lineage_item(
    *,
    artifact_label: str,
    artifact_role: str,
    schema_version: str | None = None,
    source_path: str | Path | None = None,
    integrity_status: str | None = None,
    oracle_run_id: str | None = None,
) -> OracleArtifactLineageItem:
    return OracleArtifactLineageItem(
        artifact_label=artifact_label,
        artifact_role=artifact_role,
        schema_version=str(schema_version).strip() if schema_version else None,
        source_path=str(source_path) if source_path is not None else None,
        integrity_status=_normalize_integrity(integrity_status),
        oracle_run_id=str(oracle_run_id).strip() if oracle_run_id else None,
    )


def build_lineage_item_from_model(
    *,
    artifact_label: str,
    artifact_role: str,
    model: Any,
    source_path: str | Path | None = None,
    integrity_status: str | None = None,
) -> OracleArtifactLineageItem:
    return build_lineage_item(
        artifact_label=artifact_label,
        artifact_role=artifact_role,
        schema_version=getattr(model, "schema_version", None),
        source_path=source_path,
        integrity_status=integrity_status or getattr(model, "integrity_status", None),
        oracle_run_id=getattr(model, "oracle_run_id", None),
    )


def build_lineage_item_from_registered_artifact(
    *,
    artifact_label: str,
    artifact_role: str,
    path: Path,
    integrity_status: str | None = None,
) -> OracleArtifactLineageItem:
    registration, _, model = load_registered_artifact(path)
    return build_lineage_item(
        artifact_label=artifact_label,
        artifact_role=artifact_role,
        schema_version=registration.schema_version,
        source_path=path,
        integrity_status=integrity_status or getattr(model, "integrity_status", None),
        oracle_run_id=getattr(model, "oracle_run_id", None),
    )


def summarize_lineage(items: Iterable[OracleArtifactLineageItem]) -> str:
    materialized = list(items)
    if not materialized:
        return "No artifact lineage was recorded."
    verified = sum(1 for item in materialized if item.integrity_status == "VERIFIED")
    with_paths = sum(1 for item in materialized if item.source_path)
    return (
        f"Artifact lineage captured for {len(materialized)} artifacts; verified={verified}; "
        f"path-backed={with_paths}."
    )
