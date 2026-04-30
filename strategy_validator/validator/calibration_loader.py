"""Load and validate calibration artifacts (fail-closed, typed)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from strategy_validator.contracts.calibration import CalibrationArtifactV1, CalibrationMetadata


def load_calibration_artifact_from_path(path: str | Path) -> Optional[CalibrationArtifactV1]:
    """
    Load and validate a full v1 calibration artifact (including curve laws).

    Returns None if the file is missing, unreadable, or fails validation.
    """
    p = Path(path)
    if not p.is_file():
        return None
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    try:
        return CalibrationArtifactV1.model_validate(raw)
    except Exception:
        return None


def load_calibration_metadata_from_path(path: str | Path) -> Optional[CalibrationMetadata]:
    """
    Load a v1 calibration artifact from disk and return sealed metadata only.

    Returns None if the file is missing, unreadable, or fails schema validation.
    """
    art = load_calibration_artifact_from_path(path)
    return None if art is None else art.to_metadata()
