from __future__ import annotations

from strategy_validator.contracts.oracle_temporal import (
    TemporalCanonicalizationBatchResult,
    TemporalEventLogAppendBatchResult,
    TemporalLaneStatus,
    TemporalSemanticBatchManifest,
    TemporalSemanticBatchVerification,
)


def summarize_temporal_lane(
    manifest: TemporalSemanticBatchManifest,
    *,
    universe_label: str,
    verification: TemporalSemanticBatchVerification | None = None,
    canonicalization: TemporalCanonicalizationBatchResult | None = None,
    append_report: TemporalEventLogAppendBatchResult | None = None,
) -> TemporalLaneStatus:
    verification = verification or TemporalSemanticBatchVerification(
        provider_id=manifest.provider_id,
        model_name=manifest.model_name,
        batch_start_date=manifest.batch_start_date,
        batch_end_date=manifest.batch_end_date,
        status="REJECTED",
    )
    canonicalization_verification_status = (
        canonicalization.verification_status if canonicalization is not None else verification.status
    )
    extraction_days = len(manifest.days)
    verified_days = len(verification.accepted_dates)
    rejected_days = len(verification.rejected_dates)
    canonicalized_days = len(canonicalization.canonicalized_dates) if canonicalization is not None else 0
    canonicalization_skipped_days = len(canonicalization.skipped_dates) if canonicalization is not None else 0
    appended_days = len(append_report.appended_dates) if append_report is not None else 0
    append_skipped_days = len(append_report.skipped_dates) if append_report is not None else 0
    append_lane_path = append_report.lane_path if append_report is not None else None

    summary_line = (
        f"Temporal lane status for {universe_label}: extracted={extraction_days} verified={verified_days} "
        f"rejected={rejected_days} canonicalized={canonicalized_days} appended={appended_days}."
    )
    operator_lines = [
        summary_line,
        f"Verification status: {verification.status}; accepted_dates={verified_days}; rejected_dates={rejected_days}.",
        (
            f"Canonicalization status: verification={canonicalization_verification_status}; "
            f"canonicalized_dates={canonicalized_days}; skipped_dates={canonicalization_skipped_days}."
        ),
        (
            f"Event-log append status: appended_dates={appended_days}; append_skipped_dates={append_skipped_days}; "
            f"lane_path={append_lane_path or 'N/A'}."
        ),
    ]
    if rejected_days:
        operator_lines.append(
            "Rejected dates remain outside the canonical truth spine until PIT/citation defects are resolved."
        )
    if canonicalization_skipped_days and canonicalized_days == 0:
        operator_lines.append(
            "No daily oracle evidence artifacts were canonicalized; operators should inspect temporal verification findings first."
        )
    if append_skipped_days:
        operator_lines.append(
            "Some canonicalized days did not reach the Oracle Event Log; inspect evidence verification status and append notes."
        )

    return TemporalLaneStatus(
        provider_id=manifest.provider_id,
        model_name=manifest.model_name,
        universe_label=universe_label,
        batch_start_date=manifest.batch_start_date,
        batch_end_date=manifest.batch_end_date,
        extraction_days=extraction_days,
        verified_days=verified_days,
        rejected_days=rejected_days,
        canonicalized_days=canonicalized_days,
        canonicalization_skipped_days=canonicalization_skipped_days,
        appended_days=appended_days,
        append_skipped_days=append_skipped_days,
        verification_status=verification.status,
        canonicalization_verification_status=canonicalization_verification_status,
        append_lane_path=append_lane_path,
        summary_line=summary_line,
        operator_lines=operator_lines,
    )
