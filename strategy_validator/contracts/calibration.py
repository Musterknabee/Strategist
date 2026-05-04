"""
Typed empirical calibration contracts (seam-first).

Lawful use:
  - `CalibrationMetadata` seals what calibration artifact was consumed.
  - `CalibrationArtifactV1` is the minimal on-disk schema operators can version.
  - No silent promotion to calibrated impact without a valid artifact + policy.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator


CalibrationSchemaVersion = Literal["1.0.0"]

ImpactModelKind = Literal["SQRT_MULTIPLIER", "EMPIRICAL_CURVE"]


class ParticipationImpactPoint(BaseModel):
    """One empirical observation: participation rate vs realized impact (bps)."""
    participation_rate: float = Field(ge=0.0, le=1.0)
    impact_bps: float = Field(ge=0.0)

    model_config = {"extra": "forbid"}


class CalibrationMetadata(BaseModel):
    """Versioned metadata sealed into adjudication when calibration is applied."""
    calibration_schema_version: CalibrationSchemaVersion = "1.0.0"
    dataset_fingerprint: str = Field(min_length=8)
    model_version: str = Field(default="empirical_sqrt_v1", min_length=1)
    nonlinear_sqrt_multiplier: float = Field(gt=0.0)
    fitted_at_utc: datetime
    impact_model_kind: ImpactModelKind = "SQRT_MULTIPLIER"
    empirical_curve_point_count: Optional[int] = None

    model_config = {"extra": "forbid"}


class CalibrationArtifactV1(BaseModel):
    """
    Calibration artifact (disk contract).

    Either:
      - `nonlinear_sqrt_multiplier` only (sqrt-shaped impact), or
      - `empirical_participation_curve` with ≥3 strictly increasing points (real curve data).

    When the curve is present it is authoritative for impact; multiplier is still carried for audit.

    Optional governance fields (operators / CI should populate for production acceptance):
      - ``validation_quality_score`` — in [0, 1], higher is better (held-out fit, etc.).
      - ``training_run_id`` — stable id linking artifact to an offline training publish.
    """
    calibration_schema_version: CalibrationSchemaVersion = "1.0.0"
    dataset_fingerprint: str = Field(min_length=8)
    model_version: str = Field(default="empirical_sqrt_v1", min_length=1)
    nonlinear_sqrt_multiplier: float = Field(gt=0.0)
    fitted_at_utc: datetime
    empirical_participation_curve: Optional[list[ParticipationImpactPoint]] = None
    validation_quality_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    training_run_id: Optional[str] = Field(default=None, min_length=1)

    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def _validate_curve(self) -> "CalibrationArtifactV1":
        curve = self.empirical_participation_curve
        if curve is None:
            return self
        if len(curve) < 3:
            raise ValueError("empirical_participation_curve requires at least 3 points")
        prev = -1.0
        for p in curve:
            if p.participation_rate <= prev:
                raise ValueError("empirical_participation_curve must be strictly increasing in participation_rate")
            prev = p.participation_rate
        return self

    def to_metadata(self) -> CalibrationMetadata:
        curve = self.empirical_participation_curve
        kind: ImpactModelKind = "EMPIRICAL_CURVE" if curve else "SQRT_MULTIPLIER"
        return CalibrationMetadata(
            calibration_schema_version=self.calibration_schema_version,
            dataset_fingerprint=self.dataset_fingerprint,
            model_version=self.model_version,
            nonlinear_sqrt_multiplier=self.nonlinear_sqrt_multiplier,
            fitted_at_utc=self.fitted_at_utc,
            impact_model_kind=kind,
            empirical_curve_point_count=len(curve) if curve else None,
        )


def empirical_curve_spread_bps(curve: list[ParticipationImpactPoint]) -> float:
    """Max minus min impact_bps over the curve (audit helper for flat-curve rejection)."""
    if not curve:
        return 0.0
    vals = [p.impact_bps for p in curve]
    return float(max(vals) - min(vals))
