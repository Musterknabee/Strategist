from __future__ import annotations

from datetime import date, datetime, time, timezone

from strategy_validator.contracts.oracle_temporal import (
    TemporalSemanticBatchManifest,
    TemporalSemanticBatchVerification,
    TemporalSemanticVerificationFinding,
)


def _utc_day_cutoff(day: date) -> datetime:
    return datetime.combine(day, time.max, tzinfo=timezone.utc)


def verify_temporal_semantic_batch_manifest(
    manifest: TemporalSemanticBatchManifest,
    *,
    expected_dates: list[date] | tuple[date, ...] | None = None,
    allowed_prefix_digests_by_date: dict[date, str] | None = None,
    max_citation_timestamp_by_date: dict[date, datetime] | None = None,
) -> TemporalSemanticBatchVerification:
    findings: list[TemporalSemanticVerificationFinding] = []
    accepted_dates: list[date] = []
    rejected_dates: list[date] = []
    seen_dates: set[date] = set()
    prior_date: date | None = None

    for day in manifest.days:
        day_errors = 0
        pt_date = day.point_in_time_date
        if pt_date < manifest.batch_start_date or pt_date > manifest.batch_end_date:
            findings.append(TemporalSemanticVerificationFinding(
                point_in_time_date=pt_date,
                code="DATE_OUTSIDE_BATCH_WINDOW",
                severity="ERROR",
                message=(
                    f"{pt_date.isoformat()} is outside the declared batch window "
                    f"{manifest.batch_start_date.isoformat()} → {manifest.batch_end_date.isoformat()}."
                ),
            ))
            day_errors += 1
        if pt_date in seen_dates:
            findings.append(TemporalSemanticVerificationFinding(
                point_in_time_date=pt_date,
                code="DATE_DUPLICATED",
                severity="ERROR",
                message=f"{pt_date.isoformat()} appears more than once in the temporal batch.",
            ))
            day_errors += 1
        else:
            seen_dates.add(pt_date)
        if prior_date is not None and pt_date < prior_date:
            findings.append(TemporalSemanticVerificationFinding(
                point_in_time_date=pt_date,
                code="DATE_ORDER_VIOLATION",
                severity="ERROR",
                message=(
                    f"{pt_date.isoformat()} appears after {prior_date.isoformat()} even though the batch must be chronological."
                ),
            ))
            day_errors += 1
        prior_date = pt_date

        if allowed_prefix_digests_by_date is not None:
            expected_digest = allowed_prefix_digests_by_date.get(pt_date)
            if expected_digest is not None and day.allowed_prefix_digest_sha256 != expected_digest:
                findings.append(TemporalSemanticVerificationFinding(
                    point_in_time_date=pt_date,
                    code="PREFIX_DIGEST_MISMATCH",
                    severity="ERROR",
                    message=(
                        f"{pt_date.isoformat()} carries prefix digest {day.allowed_prefix_digest_sha256} "
                        f"but expected {expected_digest}."
                    ),
                ))
                day_errors += 1

        cutoff = max_citation_timestamp_by_date.get(pt_date) if max_citation_timestamp_by_date else _utc_day_cutoff(pt_date)
        for citation in day.citations:
            if citation.source_timestamp_utc > cutoff:
                findings.append(TemporalSemanticVerificationFinding(
                    point_in_time_date=pt_date,
                    code="CITATION_AFTER_CUTOFF",
                    severity="ERROR",
                    message=(
                        f"Citation {citation.source_id} has timestamp {citation.source_timestamp_utc.isoformat()} "
                        f"which exceeds the lawful cutoff for {pt_date.isoformat()}."
                    ),
                ))
                day_errors += 1

        if day_errors:
            rejected_dates.append(pt_date)
        else:
            accepted_dates.append(pt_date)

    if expected_dates is not None:
        expected_set = set(expected_dates)
        missing = sorted(expected_set - seen_dates)
        unexpected = sorted(seen_dates - expected_set)
        for missing_date in missing:
            findings.append(TemporalSemanticVerificationFinding(
                point_in_time_date=missing_date,
                code="EXPECTED_DATE_MISSING",
                severity="ERROR",
                message=f"Expected {missing_date.isoformat()} in the batch but no day artifact was present.",
            ))
            rejected_dates.append(missing_date)
        for extra_date in unexpected:
            findings.append(TemporalSemanticVerificationFinding(
                point_in_time_date=extra_date,
                code="UNEXPECTED_DATE_PRESENT",
                severity="ERROR",
                message=f"{extra_date.isoformat()} is present in the batch but not in the expected trading-date set.",
            ))
            if extra_date not in rejected_dates:
                rejected_dates.append(extra_date)

    status = "VERIFIED" if not [f for f in findings if f.severity == "ERROR"] else "REJECTED"
    return TemporalSemanticBatchVerification(
        provider_id=manifest.provider_id,
        model_name=manifest.model_name,
        batch_start_date=manifest.batch_start_date,
        batch_end_date=manifest.batch_end_date,
        status=status,
        accepted_dates=sorted(set(accepted_dates)),
        rejected_dates=sorted(set(rejected_dates)),
        findings=findings,
    )
