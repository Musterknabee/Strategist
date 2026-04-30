from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.contracts.oracle_strategic_memory import OracleStrategicNarrativeReport
from strategy_validator.contracts.oracle_strategic_programs import (
    OracleStrategicStackEvidenceManifest,
    OracleStrategicStackEvidenceVerification,
)


def _load_json(path: Path) -> dict:
    return dict(json.loads(path.read_text(encoding="utf-8")))


def load_verified_strategic_stack_history_bundle(
    *,
    narrative_report_path: Path,
    manifest_path: Path,
    verification_path: Path,
) -> tuple[OracleStrategicNarrativeReport, OracleStrategicStackEvidenceManifest, OracleStrategicStackEvidenceVerification]:
    narrative = OracleStrategicNarrativeReport.model_validate(_load_json(narrative_report_path))
    manifest = OracleStrategicStackEvidenceManifest.model_validate(_load_json(manifest_path))
    verification = OracleStrategicStackEvidenceVerification.model_validate(_load_json(verification_path))

    if verification.status != "VERIFIED":
        raise ValueError(
            f"verified strategic history requires VERIFIED stack evidence verification; got {verification.status!r}"
        )
    if manifest.integrity_status != "VERIFIED":
        raise ValueError(
            f"verified strategic history requires VERIFIED stack evidence manifest integrity; got {manifest.integrity_status!r}"
        )
    if narrative.universe_label != manifest.universe_label:
        raise ValueError("verified strategic history requires matching universe_label values")
    if narrative.oracle_run_id != manifest.oracle_run_id:
        raise ValueError("verified strategic history requires matching oracle_run_id values")
    if narrative.input_timestamp_utc != manifest.input_timestamp_utc:
        raise ValueError("verified strategic history requires matching input_timestamp_utc values")
    if Path(verification.manifest_path).name != manifest_path.name:
        raise ValueError("verified strategic history requires verification.manifest_path to reference the supplied manifest")

    return narrative, manifest, verification
