from __future__ import annotations

import hashlib
from datetime import date, datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator

from strategy_validator.contracts.oracle_strategic_fusion import OracleSensorRawSemanticInput

TemporalVerificationStatus = Literal["VERIFIED", "REJECTED"]
TemporalFindingSeverity = Literal["ERROR", "WARNING", "INFO"]
TemporalProviderKind = Literal["NVIDIA_NIM", "OPENAI_COMPATIBLE", "OPENBB", "OTHER"]


class TemporalSourceRecord(BaseModel):
    source_id: str = Field(min_length=1)
    source_timestamp_utc: datetime
    source_kind: str = Field(default="UNKNOWN", min_length=1)
    text: str = Field(min_length=1)

    model_config = {"extra": "forbid"}


class TemporalSemanticExtractionDayRequest(BaseModel):
    point_in_time_date: date
    trading_session_id: str = Field(min_length=1)
    allowed_prefix_digest_sha256: str = Field(min_length=1)
    source_records: list[TemporalSourceRecord] = Field(default_factory=list)
    advisory_notes: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class TemporalSemanticExtractionBatchRequest(BaseModel):
    schema_version: Literal["oracle_temporal_semantic_extraction_batch_request/v1"] = "oracle_temporal_semantic_extraction_batch_request/v1"
    generated_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provider_kind: TemporalProviderKind = "OTHER"
    provider_id: str = Field(min_length=1)
    model_name: str = Field(min_length=1)
    batch_start_date: date
    batch_end_date: date
    days: list[TemporalSemanticExtractionDayRequest] = Field(default_factory=list)

    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def _validate_window(self) -> "TemporalSemanticExtractionBatchRequest":
        if self.batch_start_date > self.batch_end_date:
            raise ValueError("batch_start_date must be <= batch_end_date")
        return self


class TemporalEvidenceRef(BaseModel):
    source_id: str = Field(min_length=1)
    source_timestamp_utc: datetime
    source_kind: str = Field(default="UNKNOWN", min_length=1)
    exact_quote: str = ""
    excerpt_sha256: str = ""

    model_config = {"extra": "forbid"}

    def model_post_init(self, __context) -> None:
        if not self.excerpt_sha256 and self.exact_quote:
            self.excerpt_sha256 = hashlib.sha256(self.exact_quote.encode("utf-8")).hexdigest()


class TemporalSemanticDay(BaseModel):
    point_in_time_date: date
    trading_session_id: str = Field(min_length=1)
    semantic_raw: OracleSensorRawSemanticInput
    allowed_prefix_digest_sha256: str = Field(min_length=1)
    provider_response_sha256: str = Field(default="", min_length=0)
    citations: list[TemporalEvidenceRef] = Field(default_factory=list)
    advisory_notes: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class TemporalSemanticBatchManifest(BaseModel):
    schema_version: Literal["oracle_temporal_semantic_batch_manifest/v1"] = "oracle_temporal_semantic_batch_manifest/v1"
    generated_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provider_kind: TemporalProviderKind = "OTHER"
    provider_id: str = Field(min_length=1)
    model_name: str = Field(min_length=1)
    batch_start_date: date
    batch_end_date: date
    days: list[TemporalSemanticDay] = Field(default_factory=list)

    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def _validate_window(self) -> "TemporalSemanticBatchManifest":
        if self.batch_start_date > self.batch_end_date:
            raise ValueError("batch_start_date must be <= batch_end_date")
        return self


class TemporalSemanticVerificationFinding(BaseModel):
    point_in_time_date: Optional[date] = None
    code: str = Field(min_length=1)
    severity: TemporalFindingSeverity = "ERROR"
    message: str = Field(min_length=1)

    model_config = {"extra": "forbid"}


class TemporalSemanticBatchVerification(BaseModel):
    schema_version: Literal["oracle_temporal_semantic_batch_verification/v1"] = "oracle_temporal_semantic_batch_verification/v1"
    generated_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provider_id: str = Field(min_length=1)
    model_name: str = Field(min_length=1)
    batch_start_date: date
    batch_end_date: date
    status: TemporalVerificationStatus = "REJECTED"
    accepted_dates: list[date] = Field(default_factory=list)
    rejected_dates: list[date] = Field(default_factory=list)
    findings: list[TemporalSemanticVerificationFinding] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class TemporalProviderArtifactManifest(BaseModel):
    schema_version: Literal["oracle_temporal_provider_artifact_manifest/v1"] = "oracle_temporal_provider_artifact_manifest/v1"
    generated_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provider_kind: TemporalProviderKind = "OTHER"
    provider_id: str = Field(min_length=1)
    model_name: str = Field(min_length=1)
    request_sha256: str = Field(min_length=1)
    response_sha256: str = Field(min_length=1)
    request_window_start: date
    request_window_end: date
    vendor_request_id: str | None = None
    retry_count: int = Field(default=0, ge=0)
    timeout_seconds: float = Field(default=0.0, ge=0.0)

    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def _validate_window(self) -> "TemporalProviderArtifactManifest":
        if self.request_window_start > self.request_window_end:
            raise ValueError("request_window_start must be <= request_window_end")
        return self


class OpenBBTemporalSensorIngressDayResult(BaseModel):
    point_in_time_date: date
    macro_available: bool = False
    microstructure_available: bool = False
    notes: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OpenBBTemporalSensorIngressBatchResult(BaseModel):
    schema_version: Literal["oracle_openbb_temporal_sensor_ingress_batch_result/v1"] = "oracle_openbb_temporal_sensor_ingress_batch_result/v1"
    generated_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provider_id: str = Field(min_length=1)
    universe_label: str = Field(min_length=1)
    requested_dates: list[date] = Field(default_factory=list)
    hydrated_dates: list[date] = Field(default_factory=list)
    missing_macro_dates: list[date] = Field(default_factory=list)
    missing_microstructure_dates: list[date] = Field(default_factory=list)
    results: list[OpenBBTemporalSensorIngressDayResult] = Field(default_factory=list)
    summary_line: str = ""

    model_config = {"extra": "forbid"}
