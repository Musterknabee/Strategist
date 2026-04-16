from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from strategy_validator.contracts.oracle import OracleArtifactFreshnessItem


def _normalize_utc(value: datetime | str | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def classify_freshness(*, generated_at_utc: datetime | str | None, as_of_utc: datetime, fresh_hours: float, aging_hours: float) -> tuple[str, float | None]:
    generated = _normalize_utc(generated_at_utc)
    as_of = _normalize_utc(as_of_utc) or datetime.now(timezone.utc)
    if generated is None:
        return "UNKNOWN", None
    age_seconds = max((as_of - generated).total_seconds(), 0.0)
    age_hours = round(age_seconds / 3600.0, 3)
    if age_hours <= fresh_hours:
        return "FRESH", age_hours
    if age_hours <= aging_hours:
        return "AGING", age_hours
    return "STALE", age_hours


def build_freshness_item(
    *,
    artifact_label: str,
    generated_at_utc: datetime | str | None,
    as_of_utc: datetime,
    source_path: Path | str | None = None,
    fresh_hours: float,
    aging_hours: float,
) -> OracleArtifactFreshnessItem:
    status, age_hours = classify_freshness(
        generated_at_utc=generated_at_utc,
        as_of_utc=as_of_utc,
        fresh_hours=fresh_hours,
        aging_hours=aging_hours,
    )
    return OracleArtifactFreshnessItem(
        artifact_label=artifact_label,
        source_path=(str(Path(source_path).resolve()) if source_path is not None else None),
        generated_at_utc=_normalize_utc(generated_at_utc),
        age_hours=age_hours,
        freshness_status=status,
    )


def summarize_freshness(items: Iterable[OracleArtifactFreshnessItem]) -> tuple[str, int, str]:
    materialized = list(items)
    if not materialized:
        return "UNKNOWN", 0, "No artifact freshness evidence was available."
    stale_count = sum(1 for item in materialized if item.freshness_status == "STALE")
    aging_count = sum(1 for item in materialized if item.freshness_status == "AGING")
    fresh_count = sum(1 for item in materialized if item.freshness_status == "FRESH")
    known_count = sum(1 for item in materialized if item.freshness_status != "UNKNOWN")
    if stale_count > 0:
        status = "STALE"
    elif aging_count > 0:
        status = "AGING"
    elif fresh_count > 0:
        status = "FRESH"
    else:
        status = "UNKNOWN"
    summary = (
        f"Artifact freshness status={status}; stale={stale_count}; aging={aging_count}; "
        f"fresh={fresh_count}; known={known_count}; total={len(materialized)}."
    )
    return status, stale_count, summary
