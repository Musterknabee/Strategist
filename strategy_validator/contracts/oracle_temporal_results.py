from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

from strategy_validator.contracts.oracle_temporal_semantics import TemporalVerificationStatus

TemporalCanonicalizationDayStatus = Literal["CANONICALIZED", "SKIPPED_REJECTED"]


class TemporalCanonicalizationDayResult(BaseModel):
    point_in_time_date: date
    status: TemporalCanonicalizationDayStatus = "CANONICALIZED"
    sensor_input_path: str | None = None
    sensor_report_path: str | None = None
    advisory_input_path: str | None = None
    attestation_path: str | None = None
    markdown_path: str = ""
    evidence_manifest_path: str | None = None
    dsse_path: str | None = None
    evidence_verification_path: str | None = None
    evidence_verification_status: str | None = None
    summary_line: str = ""
    notes: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class TemporalCanonicalizationBatchResult(BaseModel):
    schema_version: Literal["oracle_temporal_canonicalization_batch_result/v1"] = "oracle_temporal_canonicalization_batch_result/v1"
    generated_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provider_id: str = Field(min_length=1)
    model_name: str = Field(min_length=1)
    universe_label: str = Field(min_length=1)
    output_root: str = Field(min_length=1)
    verification_status: TemporalVerificationStatus = "REJECTED"
    canonicalized_dates: list[date] = Field(default_factory=list)
    skipped_dates: list[date] = Field(default_factory=list)
    results: list[TemporalCanonicalizationDayResult] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


TemporalEventLogAppendDayStatus = Literal["APPENDED", "SKIPPED_REJECTED", "SKIPPED_UNVERIFIED"]


class TemporalEventLogAppendDayResult(BaseModel):
    point_in_time_date: date
    status: TemporalEventLogAppendDayStatus = "APPENDED"
    event_log_entry_path: str | None = None
    event_log_entry_id: str | None = None
    event_log_sequence_number: int | None = None
    notes: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class TemporalEventLogAppendBatchResult(BaseModel):
    schema_version: Literal["oracle_temporal_event_log_append_batch_result/v1"] = "oracle_temporal_event_log_append_batch_result/v1"
    generated_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provider_id: str = Field(min_length=1)
    model_name: str = Field(min_length=1)
    universe_label: str = Field(min_length=1)
    lane_path: str = Field(min_length=1)
    canonicalization_output_root: str = Field(min_length=1)
    canonicalization_verification_status: TemporalVerificationStatus = "REJECTED"
    appended_dates: list[date] = Field(default_factory=list)
    skipped_dates: list[date] = Field(default_factory=list)
    results: list[TemporalEventLogAppendDayResult] = Field(default_factory=list)
    event_log_entry_paths: list[str] = Field(default_factory=list)
    summary_line: str = ""

    model_config = {"extra": "forbid"}


class TemporalLaneStatus(BaseModel):
    schema_version: Literal["oracle_temporal_lane_status/v1"] = "oracle_temporal_lane_status/v1"
    generated_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provider_id: str = Field(min_length=1)
    model_name: str = Field(min_length=1)
    universe_label: str = Field(min_length=1)
    batch_start_date: date
    batch_end_date: date
    extraction_days: int = Field(default=0, ge=0)
    verified_days: int = Field(default=0, ge=0)
    rejected_days: int = Field(default=0, ge=0)
    canonicalized_days: int = Field(default=0, ge=0)
    canonicalization_skipped_days: int = Field(default=0, ge=0)
    appended_days: int = Field(default=0, ge=0)
    append_skipped_days: int = Field(default=0, ge=0)
    verification_status: TemporalVerificationStatus = "REJECTED"
    canonicalization_verification_status: TemporalVerificationStatus = "REJECTED"
    append_lane_path: str | None = None
    summary_line: str = ""
    operator_lines: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}
