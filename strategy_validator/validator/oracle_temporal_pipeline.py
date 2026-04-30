from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from strategy_validator.contracts.oracle_evidence_events import OracleEvidenceVerification
from strategy_validator.contracts.oracle_strategic_fusion import (
    OracleSensorRawMacroInput,
    OracleSensorRawMicrostructureInput,
)
from strategy_validator.contracts.oracle_core import StrategyHealthSnapshot
from strategy_validator.contracts.oracle_temporal_results import (
    TemporalCanonicalizationBatchResult,
    TemporalCanonicalizationDayResult,
)
from strategy_validator.contracts.oracle_temporal_semantics import (
    TemporalSemanticBatchManifest,
    TemporalSemanticBatchVerification,
)
from strategy_validator.validator.oracle_advisory import (
    build_oracle_evidence_bundle,
    build_oracle_morning_attestation,
    render_oracle_morning_attestation_markdown,
    verify_oracle_evidence_bundle,
)
from strategy_validator.validator.oracle_sensors import normalize_sensor_input
from strategy_validator.validator.oracle_temporal_materialization import materialize_temporal_semantic_sensor_inputs
from strategy_validator.validator.oracle_temporal_verification import verify_temporal_semantic_batch_manifest


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def _rel(path: Path, repo_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path.resolve()).replace("\\", "/")


def canonicalize_temporal_semantic_batch(
    manifest: TemporalSemanticBatchManifest,
    *,
    universe_label: str,
    output_root: Path,
    repo_root: Optional[Path] = None,
    macro_by_date: dict[date | datetime | str, OracleSensorRawMacroInput],
    microstructure_by_date: dict[date | datetime | str, OracleSensorRawMicrostructureInput],
    generated_for_by_date: dict[date | datetime | str, datetime] | None = None,
    strategies_by_date: dict[date | datetime | str, list[StrategyHealthSnapshot]] | None = None,
    verification: TemporalSemanticBatchVerification | None = None,
    expected_dates: list[date] | tuple[date, ...] | None = None,
    allowed_prefix_digests_by_date: dict[date, str] | None = None,
    max_citation_timestamp_by_date: dict[date, datetime] | None = None,
    signing_private_key_path: Path | None = None,
    public_key_path: Path | None = None,
) -> TemporalCanonicalizationBatchResult:
    repo_root = (repo_root or Path.cwd()).resolve()
    output_root = output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    verification = verification or verify_temporal_semantic_batch_manifest(
        manifest,
        expected_dates=expected_dates,
        allowed_prefix_digests_by_date=allowed_prefix_digests_by_date,
        max_citation_timestamp_by_date=max_citation_timestamp_by_date,
    )
    accepted = set(verification.accepted_dates)

    materialized_inputs = materialize_temporal_semantic_sensor_inputs(
        manifest,
        universe_label=universe_label,
        macro_by_date=macro_by_date,
        microstructure_by_date=microstructure_by_date,
        generated_for_by_date=generated_for_by_date,
        strategies_by_date=strategies_by_date,
    )
    materialized_by_date = {payload.generated_for_utc.date(): payload for payload in materialized_inputs}

    results: list[TemporalCanonicalizationDayResult] = []
    canonicalized_dates: list[date] = []
    skipped_dates: list[date] = []

    for day in manifest.days:
        pt_date = day.point_in_time_date
        day_dir = output_root / pt_date.isoformat()
        if pt_date not in accepted:
            results.append(
                TemporalCanonicalizationDayResult(
                    point_in_time_date=pt_date,
                    status="SKIPPED_REJECTED",
                    notes=["Temporal batch verification rejected this date; canonical artifacts were not emitted."],
                )
            )
            skipped_dates.append(pt_date)
            continue

        sensor_input = materialized_by_date[pt_date]
        sensor_report = normalize_sensor_input(sensor_input)
        advisory_input = sensor_report.advisory_input
        attestation = build_oracle_morning_attestation(payload=advisory_input, repo_root=repo_root)
        markdown = render_oracle_morning_attestation_markdown(attestation)

        sensor_input_path = day_dir / "ORACLE_SENSOR_INGESTION_INPUT.json"
        sensor_report_path = day_dir / "ORACLE_SENSOR_INGESTION_REPORT.json"
        advisory_input_path = day_dir / "ORACLE_ADVISORY_INPUT.json"
        attestation_path = day_dir / "ORACLE_MORNING_ATTESTATION.json"
        markdown_path = day_dir / "ORACLE_MORNING_ATTESTATION.md"
        evidence_manifest_path = day_dir / "ORACLE_EVIDENCE.json"
        dsse_path = day_dir / "ORACLE_EVIDENCE.dsse.json"
        evidence_verification_path = day_dir / "ORACLE_EVIDENCE.verification.json"

        _write_json(sensor_input_path, sensor_input.model_dump(mode="json"))
        _write_json(sensor_report_path, sensor_report.model_dump(mode="json"))
        _write_json(advisory_input_path, advisory_input.model_dump(mode="json"))
        _write_json(attestation_path, attestation.model_dump(mode="json"))
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(markdown, encoding="utf-8")

        evidence_manifest, envelope = build_oracle_evidence_bundle(
            input_path=advisory_input_path,
            attestation_path=attestation_path,
            markdown_path=markdown_path,
            repo_root=repo_root,
            signing_private_key_path=signing_private_key_path,
        )
        _write_json(evidence_manifest_path, evidence_manifest.model_dump(mode="json"))
        if envelope is not None:
            _write_json(dsse_path, envelope.model_dump(mode="json"))
        verification_report: OracleEvidenceVerification = verify_oracle_evidence_bundle(
            manifest_path=evidence_manifest_path,
            repo_root=repo_root,
            dsse_path=dsse_path if envelope is not None else None,
            public_key_path=public_key_path if envelope is not None else None,
        )
        _write_json(evidence_verification_path, verification_report.model_dump(mode="json"))

        results.append(
            TemporalCanonicalizationDayResult(
                point_in_time_date=pt_date,
                status="CANONICALIZED",
                sensor_input_path=_rel(sensor_input_path, repo_root),
                sensor_report_path=_rel(sensor_report_path, repo_root),
                advisory_input_path=_rel(advisory_input_path, repo_root),
                attestation_path=_rel(attestation_path, repo_root),
                markdown_path=_rel(markdown_path, repo_root),
                evidence_manifest_path=_rel(evidence_manifest_path, repo_root),
                dsse_path=_rel(dsse_path, repo_root) if envelope is not None else None,
                evidence_verification_path=_rel(evidence_verification_path, repo_root),
                evidence_verification_status=verification_report.status,
                summary_line=attestation.summary_line,
                notes=list(verification_report.notes),
            )
        )
        canonicalized_dates.append(pt_date)

    return TemporalCanonicalizationBatchResult(
        provider_id=manifest.provider_id,
        model_name=manifest.model_name,
        universe_label=universe_label,
        output_root=_rel(output_root, repo_root),
        verification_status=verification.status,
        canonicalized_dates=sorted(set(canonicalized_dates)),
        skipped_dates=sorted(set(skipped_dates)),
        results=results,
    )
