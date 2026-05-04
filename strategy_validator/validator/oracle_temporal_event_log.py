from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.contracts.oracle_evidence_events import OracleEventLogEntry, OracleEvidenceVerification
from strategy_validator.contracts.oracle_temporal_results import (
    TemporalCanonicalizationBatchResult,
    TemporalEventLogAppendBatchResult,
    TemporalEventLogAppendDayResult,
)
from strategy_validator.validator.oracle_event_log import append_oracle_event_log


def _resolve(repo_root: Path, value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    if path.is_absolute():
        return path
    return (repo_root / path).resolve()


def _load_verification(path: Path) -> OracleEvidenceVerification:
    return OracleEvidenceVerification.model_validate(json.loads(path.read_text(encoding="utf-8")))


def append_temporal_canonicalization_to_event_log(
    canonicalization: TemporalCanonicalizationBatchResult,
    *,
    lane_path: Path,
    repo_root: Path | None = None,
    require_complete_success: bool = False,
) -> TemporalEventLogAppendBatchResult:
    repo_root = (repo_root or Path.cwd()).resolve()
    lane_path = lane_path.resolve()

    if require_complete_success and canonicalization.skipped_dates:
        raise ValueError("temporal event-log append requires complete canonicalization success when require_complete_success=true")

    results: list[TemporalEventLogAppendDayResult] = []
    appended_dates = []
    skipped_dates = []
    entry_paths = []

    for day in canonicalization.results:
        if day.status != "CANONICALIZED":
            skipped_dates.append(day.point_in_time_date)
            results.append(
                TemporalEventLogAppendDayResult(
                    point_in_time_date=day.point_in_time_date,
                    status="SKIPPED_REJECTED",
                    notes=["Canonicalization result was not eligible for event-log append."],
                )
            )
            continue
        if day.evidence_verification_status != "VERIFIED":
            skipped_dates.append(day.point_in_time_date)
            results.append(
                TemporalEventLogAppendDayResult(
                    point_in_time_date=day.point_in_time_date,
                    status="SKIPPED_UNVERIFIED",
                    notes=["Canonicalized evidence verification status was not VERIFIED."],
                )
            )
            continue

        manifest_path = _resolve(repo_root, day.evidence_manifest_path)
        verification_path = _resolve(repo_root, day.evidence_verification_path)
        if manifest_path is None or verification_path is None:
            skipped_dates.append(day.point_in_time_date)
            results.append(
                TemporalEventLogAppendDayResult(
                    point_in_time_date=day.point_in_time_date,
                    status="SKIPPED_UNVERIFIED",
                    notes=["Canonicalization result is missing evidence manifest or verification path."],
                )
            )
            continue
        verification = _load_verification(verification_path)
        entry: OracleEventLogEntry = append_oracle_event_log(
            manifest_path=manifest_path,
            verification=verification,
            lane_path=lane_path,
            repo_root=repo_root,
        )
        entry_output = manifest_path.with_name("ORACLE_EVENT_LOG_ENTRY.json")
        entry_output.write_text(json.dumps(entry.model_dump(mode="json"), indent=2, default=str), encoding="utf-8")
        entry_paths.append(str(entry_output.resolve()))
        appended_dates.append(day.point_in_time_date)
        results.append(
            TemporalEventLogAppendDayResult(
                point_in_time_date=day.point_in_time_date,
                status="APPENDED",
                event_log_entry_path=str(entry_output.resolve()),
                event_log_entry_id=entry.entry_id,
                event_log_sequence_number=entry.sequence_number,
                notes=[entry.summary_line],
            )
        )

    summary_line = (
        f"Temporal canonicalization append completed; appended={len(appended_dates)} skipped={len(skipped_dates)} "
        f"verification_status={canonicalization.verification_status}."
    )
    return TemporalEventLogAppendBatchResult(
        provider_id=canonicalization.provider_id,
        model_name=canonicalization.model_name,
        universe_label=canonicalization.universe_label,
        lane_path=str(lane_path),
        canonicalization_output_root=canonicalization.output_root,
        canonicalization_verification_status=canonicalization.verification_status,
        appended_dates=sorted(set(appended_dates)),
        skipped_dates=sorted(set(skipped_dates)),
        results=results,
        event_log_entry_paths=entry_paths,
        summary_line=summary_line,
    )
