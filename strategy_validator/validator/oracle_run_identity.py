from __future__ import annotations

from typing import Any

from strategy_validator.contracts.oracle import OracleAdvisoryInput
from strategy_validator.validator.oracle_advisory import _json_canonical_bytes, _sha256_bytes


def derive_oracle_run_id(payload: OracleAdvisoryInput) -> str:
    return _sha256_bytes(
        _json_canonical_bytes(
            {
                "generated_for_utc": payload.generated_for_utc.isoformat(),
                "universe_label": payload.universe_label,
            }
        )
    )


def strategic_epoch_from_payload(payload: OracleAdvisoryInput) -> tuple[str, object]:
    return derive_oracle_run_id(payload), payload.generated_for_utc


def strategic_epoch_from_report(report: Any) -> tuple[str, object]:
    oracle_run_id = getattr(report, "oracle_run_id", None)
    input_timestamp_utc = getattr(report, "input_timestamp_utc", None)
    if not isinstance(oracle_run_id, str) or not oracle_run_id.strip() or input_timestamp_utc is None:
        raise ValueError("strategic report missing oracle run identity")
    return oracle_run_id, input_timestamp_utc


def assert_matching_strategic_epoch(*reports: Any) -> tuple[str, object, str]:
    seen: tuple[str, object, str] | None = None
    for report in reports:
        if report is None:
            continue
        current = (
            getattr(report, "oracle_run_id", None),
            getattr(report, "input_timestamp_utc", None),
            getattr(report, "universe_label", None),
        )
        if not isinstance(current[0], str) or not current[0].strip() or current[1] is None or not isinstance(current[2], str):
            raise ValueError("strategic report missing oracle run identity")
        if seen is None:
            seen = current
            continue
        if current != seen:
            raise ValueError("strategic reports must share matching oracle_run_id, input_timestamp_utc, and universe_label values")
    if seen is None:
        raise ValueError("at least one strategic report is required to establish strategic epoch consistency")
    return seen
