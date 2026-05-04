"""Strategy memory / candidate graveyard artifact operations.

All operations are read-plane / artifact-plane only. This module deliberately does
not import ledger writer, broker order, or live trading modules.
"""
from __future__ import annotations

import hashlib
import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.research_os_paths import artifact_root_directory, paper_tracking_root_directory
from strategy_validator.contracts.paper_tracking import PaperTrackingManifest
from strategy_validator.contracts.strategy_batch import StrategyBatchRunSummary, StrategyRunResult, StrategyRunStatus
from strategy_validator.contracts.strategy_memory import (
    CandidateGraveyardEntry,
    StrategyFailureReason,
    StrategyFamily,
    StrategyMemoryIndex,
    StrategyMemoryRecord,
    StrategyMemoryStatus,
    StrategySimilarityWarning,
    StrategyVariantLineage,
)


def strategy_memory_root_directory(repo_root: Path | None = None) -> Path:
    raw = os.environ.get("STRATEGY_VALIDATOR_STRATEGY_MEMORY_ROOT", "").strip()
    if raw:
        p = Path(raw)
        return p if p.is_absolute() else (Path.cwd() / p).resolve()
    return (artifact_root_directory(repo_root) / "strategy_memory").resolve()


def _json_default(o: Any) -> str:
    if isinstance(o, datetime):
        return o.isoformat()
    raise TypeError(type(o))


def _canonical_sha256(obj: Any) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":"), default=_json_default).encode("utf-8")
    ).hexdigest()


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, default=_json_default) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _family_id(strategy_type: str, universe: str, tags: list[str] | None = None) -> str:
    clean_tags = [t for t in (tags or []) if t.startswith("family:")]
    if clean_tags:
        return clean_tags[0].split(":", 1)[1].strip() or f"{strategy_type}:{universe}"
    return f"{strategy_type}:{universe}".replace(" ", "_").lower()


def _variant_fingerprint(strategy_type: str, universe: str, params: dict[str, Any]) -> str:
    return _canonical_sha256({"strategy_type": strategy_type, "universe": universe, "params": params})


def _failure_reasons_from_result(result: StrategyRunResult) -> list[StrategyFailureReason]:
    reasons: set[StrategyFailureReason] = set()
    text = " ".join([*result.blockers, *result.warnings]).upper()
    gate = result.gate_summary
    if "PIT" in text or gate.pit_gate == "BLOCKED":
        reasons.add(StrategyFailureReason.PIT)
    if "DATA" in text or gate.data_gate == "BLOCKED" or gate.data_quality_gate == "BLOCKED":
        reasons.add(StrategyFailureReason.DATA_QUALITY)
    if "EXECUTION" in text or gate.execution_realism_gate == "BLOCKED":
        reasons.add(StrategyFailureReason.EXECUTION_REALISM)
    if "ROBUST" in text or gate.robustness_gate == "BLOCKED" or gate.cpcv_robustness_gate == "BLOCKED":
        reasons.add(StrategyFailureReason.ROBUSTNESS)
    if "PARAMETER" in text or gate.parameter_sensitivity_gate == "BLOCKED":
        reasons.add(StrategyFailureReason.PARAMETER_FRAGILITY)
    if "REGIME" in text or gate.regime_analysis_gate == "BLOCKED":
        reasons.add(StrategyFailureReason.REGIME_FAILURE)
    if "DUPLICATIVE" in text:
        reasons.add(StrategyFailureReason.PORTFOLIO_DUPLICATIVE)
    if not reasons and result.status in {StrategyRunStatus.BLOCKED, StrategyRunStatus.FAILED, StrategyRunStatus.PAPER_ONLY}:
        reasons.add(StrategyFailureReason.INSUFFICIENT_EVIDENCE)
    return sorted(reasons, key=lambda r: r.value)


def _status_from_result(result: StrategyRunResult) -> StrategyMemoryStatus:
    if result.status == StrategyRunStatus.PASSED and result.gate_summary.promotion_eligible:
        return StrategyMemoryStatus.PROMOTION_REVIEW_READY
    if result.status == StrategyRunStatus.PASSED:
        return StrategyMemoryStatus.ACTIVE_RESEARCH
    if result.status in {StrategyRunStatus.BLOCKED, StrategyRunStatus.FAILED}:
        return StrategyMemoryStatus.REJECTED
    if result.status == StrategyRunStatus.PAPER_ONLY:
        return StrategyMemoryStatus.PAPER_TRACKING
    return StrategyMemoryStatus.ACTIVE_RESEARCH


def finalize_memory_record(record: StrategyMemoryRecord) -> StrategyMemoryRecord:
    body = record.model_dump(mode="json", exclude={"record_sha256"})
    return record.model_copy(update={"record_sha256": _canonical_sha256(body)})


def finalize_graveyard_entry(entry: CandidateGraveyardEntry) -> CandidateGraveyardEntry:
    body = entry.model_dump(mode="json", exclude={"entry_sha256"})
    return entry.model_copy(update={"entry_sha256": _canonical_sha256(body)})


def build_memory_record_from_batch_result(
    result: StrategyRunResult,
    *,
    batch_id: str,
    run_id: str,
    strategy_type: str = "unknown",
    universe: str = "unknown",
    timeframe: str = "unknown",
    params: dict[str, Any] | None = None,
    tags: list[str] | None = None,
) -> StrategyMemoryRecord:
    params = params or {}
    family_id = _family_id(strategy_type, universe, tags)
    lineage = StrategyVariantLineage(
        strategy_id=result.strategy_id,
        family_id=family_id,
        lineage_tags=tags or [],
        variant_fingerprint=_variant_fingerprint(strategy_type, universe, params),
    )
    refs: list[dict[str, Any]] = []
    if result.evidence_manifest_path:
        refs.append({"ref_kind": "strategy_evidence_manifest", "artifact_path": result.evidence_manifest_path, "sha256": result.evidence_manifest_sha256})
    if result.strategy_scorecard_path:
        refs.append({"ref_kind": "strategy_scorecard", "artifact_path": result.strategy_scorecard_path})
    record = StrategyMemoryRecord(
        strategy_id=result.strategy_id,
        family_id=family_id,
        status=_status_from_result(result),
        strategy_type=strategy_type,
        universe=universe,
        timeframe=timeframe,
        params=params,
        data_plane=result.data_plane,
        provider_snapshot_manifest_sha256=result.provider_snapshot_manifest_sha256,
        batch_id=batch_id,
        run_id=run_id,
        failure_reasons=_failure_reasons_from_result(result),
        blockers=list(result.blockers),
        warnings=list(result.warnings),
        evidence_refs=refs,
        lineage=lineage,
    )
    return finalize_memory_record(record)


def build_memory_record_from_paper_tracking(
    manifest: PaperTrackingManifest,
    *,
    lifecycle: dict[str, Any] | None = None,
    scorecard: dict[str, Any] | None = None,
) -> StrategyMemoryRecord:
    cand = manifest.candidate
    family_id = _family_id(cand.strategy_type, cand.gauntlet_gate_snapshot.get("universe", "unknown"), None)
    reasons: list[StrategyFailureReason] = []
    status = StrategyMemoryStatus.PAPER_TRACKING
    lifecycle_state = str((lifecycle or {}).get("current_state") or (lifecycle or {}).get("state") or "") or None
    kill_state = str((scorecard or {}).get("kill_state") or "")
    if kill_state == "KILLED" or lifecycle_state in {"KILLED_BY_RULE", "KILL_CANDIDATE"}:
        status = StrategyMemoryStatus.KILLED
        reasons.append(StrategyFailureReason.KILL_RULE)
    elif lifecycle_state == "REJECTED":
        status = StrategyMemoryStatus.REJECTED
        reasons.append(StrategyFailureReason.OPERATOR_REJECTED)
    elif bool((lifecycle or {}).get("promotion_review_ready")):
        status = StrategyMemoryStatus.PROMOTION_REVIEW_READY
    lineage = StrategyVariantLineage(
        strategy_id=cand.strategy_id,
        family_id=family_id,
        variant_fingerprint=_variant_fingerprint(cand.strategy_type, family_id, cand.gauntlet_gate_snapshot),
    )
    refs = [{"ref_kind": "paper_tracking_manifest", "tracking_id": manifest.tracking_id, "sha256": manifest.manifest_sha256}]
    record = StrategyMemoryRecord(
        strategy_id=cand.strategy_id,
        family_id=family_id,
        status=status,
        strategy_type=cand.strategy_type,
        universe=str(cand.gauntlet_gate_snapshot.get("universe", "unknown")),
        timeframe=str(cand.gauntlet_gate_snapshot.get("timeframe", "unknown")),
        params={},
        data_plane=cand.data_plane_at_enrollment,
        batch_id=cand.batch_id,
        run_id=cand.run_id,
        tracking_id=manifest.tracking_id,
        lifecycle_state=lifecycle_state,
        failure_reasons=reasons,
        blockers=list((lifecycle or {}).get("blockers") or []),
        warnings=list((scorecard or {}).get("warnings") or []),
        evidence_refs=refs,
        lineage=lineage,
    )
    return finalize_memory_record(record)


def build_memory_record_from_incubation(payload: dict[str, Any]) -> StrategyMemoryRecord:
    strategy_id = str(payload.get("strategy_id") or payload.get("id") or "unknown")
    strategy_type = str(payload.get("strategy_type") or "unknown")
    universe = str(payload.get("universe") or "unknown")
    family_id = _family_id(strategy_type, universe, payload.get("tags") if isinstance(payload.get("tags"), list) else None)
    status_raw = str(payload.get("status") or "INCUBATING")
    status = StrategyMemoryStatus.INCUBATING if status_raw not in StrategyMemoryStatus.__members__ else StrategyMemoryStatus[status_raw]
    record = StrategyMemoryRecord(
        strategy_id=strategy_id,
        family_id=family_id,
        status=status,
        strategy_type=strategy_type,
        universe=universe,
        timeframe=str(payload.get("timeframe") or "unknown"),
        params=payload.get("params") if isinstance(payload.get("params"), dict) else {},
        data_plane=str(payload.get("data_plane") or "UNKNOWN"),
        failure_reasons=[],
        blockers=list(payload.get("blockers") or []),
        warnings=list(payload.get("warnings") or []),
        evidence_refs=list(payload.get("evidence_refs") or []),
        lineage=StrategyVariantLineage(
            strategy_id=strategy_id,
            family_id=family_id,
            variant_fingerprint=_variant_fingerprint(strategy_type, universe, payload.get("params") if isinstance(payload.get("params"), dict) else {}),
        ),
    )
    return finalize_memory_record(record)


def _record_paths(root: Path) -> list[Path]:
    variants = root / "variants"
    if not variants.is_dir():
        return []
    return sorted(variants.glob("*.json"))


def _graveyard_paths(root: Path) -> list[Path]:
    gy = root / "graveyard"
    if not gy.is_dir():
        return []
    return sorted(gy.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)


def write_memory_record(record: StrategyMemoryRecord, *, repo_root: Path | None = None) -> Path:
    root = strategy_memory_root_directory(repo_root)
    rec = finalize_memory_record(record)
    variant_path = root / "variants" / f"{rec.strategy_id}.json"
    _write_json(variant_path, rec.model_dump(mode="json"))
    family = StrategyFamily(
        family_id=rec.family_id,
        strategy_type=rec.strategy_type,
        universe=rec.universe,
        family_tags=rec.lineage.lineage_tags,
        latest_strategy_id=rec.strategy_id,
        variant_count=1,
    )
    fam_path = root / "families" / f"{rec.family_id.replace('/', '_')}.json"
    if fam_path.is_file():
        try:
            old = StrategyFamily.model_validate(_read_json(fam_path))
            family = old.model_copy(update={"latest_strategy_id": rec.strategy_id, "variant_count": max(old.variant_count, 0) + 1})
        except Exception:
            pass
    _write_json(fam_path, family.model_dump(mode="json"))
    if rec.status in {StrategyMemoryStatus.KILLED, StrategyMemoryStatus.REJECTED, StrategyMemoryStatus.DUPLICATE_VARIANT}:
        append_graveyard_entry(rec, kill_reason="; ".join(rec.blockers or [rec.status.value]), repo_root=repo_root)
    return variant_path


def append_graveyard_entry(
    record: StrategyMemoryRecord,
    *,
    kill_reason: str = "",
    repo_root: Path | None = None,
) -> CandidateGraveyardEntry:
    entry = finalize_graveyard_entry(
        CandidateGraveyardEntry(
            strategy_id=record.strategy_id,
            family_id=record.family_id,
            status=record.status if record.status in {StrategyMemoryStatus.KILLED, StrategyMemoryStatus.REJECTED, StrategyMemoryStatus.DUPLICATE_VARIANT} else StrategyMemoryStatus.KILLED,
            failure_reasons=record.failure_reasons,
            kill_reason=kill_reason or "; ".join(record.blockers or record.warnings or [record.status.value]),
            source_record_sha256=record.record_sha256,
            evidence_refs=record.evidence_refs,
        )
    )
    root = strategy_memory_root_directory(repo_root)
    _write_json(root / "graveyard" / f"{entry.strategy_id}.json", entry.model_dump(mode="json"))
    return entry


def detect_duplicate_variant(record: StrategyMemoryRecord, existing: list[StrategyMemoryRecord]) -> list[StrategySimilarityWarning]:
    warnings: list[StrategySimilarityWarning] = []
    for other in existing:
        if other.strategy_id == record.strategy_id:
            continue
        basis: list[str] = []
        if other.strategy_type == record.strategy_type and other.universe == record.universe:
            basis.append("same strategy_type + universe")
        if other.lineage.variant_fingerprint and other.lineage.variant_fingerprint == record.lineage.variant_fingerprint:
            basis.append("same normalized variant fingerprint")
        if other.provider_snapshot_manifest_sha256 and other.provider_snapshot_manifest_sha256 == record.provider_snapshot_manifest_sha256:
            basis.append("same provider snapshot digest")
        if set(other.lineage.lineage_tags) & set(record.lineage.lineage_tags):
            basis.append("overlapping lineage/family tags")
        if len(basis) >= 2 or "same normalized variant fingerprint" in basis:
            warnings.append(
                StrategySimilarityWarning(
                    strategy_id=record.strategy_id,
                    similar_strategy_id=other.strategy_id,
                    family_id=record.family_id,
                    similarity_basis=basis,
                )
            )
    return warnings


def ingest_batch_run(batch_run: Path, *, repo_root: Path | None = None) -> list[StrategyMemoryRecord]:
    summary_path = batch_run / "batch_summary.json"
    if not summary_path.is_file():
        raise FileNotFoundError(f"batch summary missing: {summary_path}")
    summary = StrategyBatchRunSummary.model_validate(_read_json(summary_path))
    spec_strategies: dict[str, dict[str, Any]] = {}
    spec_path = batch_run / "batch_spec.json"
    if spec_path.is_file():
        try:
            spec = _read_json(spec_path)
            for s in spec.get("strategies", []):
                if isinstance(s, dict) and s.get("strategy_id"):
                    spec_strategies[str(s["strategy_id"])] = s
        except Exception:
            pass
    records: list[StrategyMemoryRecord] = []
    existing = load_memory_records(repo_root=repo_root)
    for result in summary.strategies:
        spec = spec_strategies.get(result.strategy_id, {})
        record = build_memory_record_from_batch_result(
            result,
            batch_id=summary.batch_id,
            run_id=summary.run_id,
            strategy_type=str(spec.get("strategy_type") or "unknown"),
            universe=str(spec.get("universe") or "unknown"),
            timeframe=str(spec.get("timeframe") or "unknown"),
            params=spec.get("params") if isinstance(spec.get("params"), dict) else {},
            tags=spec.get("tags") if isinstance(spec.get("tags"), list) else [],
        )
        dupes = detect_duplicate_variant(record, existing + records)
        if dupes and record.status == StrategyMemoryStatus.ACTIVE_RESEARCH:
            record = finalize_memory_record(record.model_copy(update={"status": StrategyMemoryStatus.DUPLICATE_VARIANT, "warnings": [*record.warnings, "DUPLICATE_VARIANT_WARNING"]}))
        write_memory_record(record, repo_root=repo_root)
        records.append(record)
    build_strategy_memory_index(repo_root=repo_root)
    return records


def ingest_paper_tracking(tracking_id: str, *, repo_root: Path | None = None) -> StrategyMemoryRecord:
    troot = paper_tracking_root_directory(repo_root) / tracking_id
    manifest_path = troot / "paper_tracking_manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"paper tracking manifest missing: {manifest_path}")
    manifest = PaperTrackingManifest.model_validate(_read_json(manifest_path))
    lifecycle = _read_json(troot / "lifecycle_assessment.json") if (troot / "lifecycle_assessment.json").is_file() else None
    scorecard = _read_json(troot / "paper_tracking_scorecard.json") if (troot / "paper_tracking_scorecard.json").is_file() else None
    record = build_memory_record_from_paper_tracking(manifest, lifecycle=lifecycle, scorecard=scorecard)
    write_memory_record(record, repo_root=repo_root)
    build_strategy_memory_index(repo_root=repo_root)
    return record


def load_memory_records(*, repo_root: Path | None = None) -> list[StrategyMemoryRecord]:
    root = strategy_memory_root_directory(repo_root)
    rows: list[StrategyMemoryRecord] = []
    for path in _record_paths(root):
        try:
            rows.append(StrategyMemoryRecord.model_validate(_read_json(path)))
        except Exception:
            continue
    return rows


def load_graveyard_entries(*, repo_root: Path | None = None) -> list[CandidateGraveyardEntry]:
    root = strategy_memory_root_directory(repo_root)
    rows: list[CandidateGraveyardEntry] = []
    for path in _graveyard_paths(root):
        try:
            rows.append(CandidateGraveyardEntry.model_validate(_read_json(path)))
        except Exception:
            continue
    return rows


def build_strategy_memory_index(*, repo_root: Path | None = None) -> StrategyMemoryIndex:
    root = strategy_memory_root_directory(repo_root)
    records = load_memory_records(repo_root=repo_root)
    graveyard = load_graveyard_entries(repo_root=repo_root)
    families_by_id: dict[str, StrategyFamily] = {}
    fam_counts: dict[str, int] = defaultdict(int)
    latest_by_family: dict[str, str] = {}
    for r in records:
        fam_counts[r.family_id] += 1
        latest_by_family[r.family_id] = r.strategy_id
    for r in records:
        if r.family_id not in families_by_id:
            families_by_id[r.family_id] = StrategyFamily(
                family_id=r.family_id,
                strategy_type=r.strategy_type,
                universe=r.universe,
                family_tags=r.lineage.lineage_tags,
                latest_strategy_id=latest_by_family.get(r.family_id),
                variant_count=fam_counts[r.family_id],
            )
    reason_counts: Counter[str] = Counter()
    for r in records:
        for reason in r.failure_reasons:
            reason_counts[reason.value] += 1
    warnings: list[StrategySimilarityWarning] = []
    for i, record in enumerate(records):
        warnings.extend(detect_duplicate_variant(record, records[:i]))
    index = StrategyMemoryIndex(
        active_count=sum(1 for r in records if r.status in {StrategyMemoryStatus.ACTIVE_RESEARCH, StrategyMemoryStatus.PAPER_TRACKING, StrategyMemoryStatus.INCUBATING, StrategyMemoryStatus.PROMOTION_REVIEW_READY}),
        killed_count=sum(1 for r in records if r.status == StrategyMemoryStatus.KILLED),
        rejected_count=sum(1 for r in records if r.status == StrategyMemoryStatus.REJECTED),
        duplicate_variant_count=sum(1 for r in records if r.status == StrategyMemoryStatus.DUPLICATE_VARIANT),
        family_count=len(families_by_id),
        top_failure_reasons=dict(reason_counts.most_common(12)),
        families=sorted(families_by_id.values(), key=lambda f: f.family_id),
        recent_graveyard_entries=graveyard[:16],
        duplicate_variant_warnings=warnings[:32],
        memory_records=records[:128],
    )
    body = index.model_dump(mode="json", exclude={"index_sha256"})
    index = index.model_copy(update={"index_sha256": _canonical_sha256(body)})
    _write_json(root / "memory_index.json", index.model_dump(mode="json"))
    _write_json(root / "latest" / "memory_index.json", index.model_dump(mode="json"))
    return index


def build_ui_strategy_memory_latest_payload(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = strategy_memory_root_directory(repo_root)
    index_path = root / "latest" / "memory_index.json"
    degraded: list[str] = []
    if not index_path.is_file():
        degraded.append("NO_STRATEGY_MEMORY_INDEX")
        index = StrategyMemoryIndex()
    else:
        try:
            index = StrategyMemoryIndex.model_validate(_read_json(index_path))
        except Exception:
            degraded.append("STRATEGY_MEMORY_INDEX_UNREADABLE")
            index = StrategyMemoryIndex()
    return {
        "schema_version": "ui_strategy_memory/v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "read_plane_only": True,
        "no_live_trading": True,
        "scan_root": str(root),
        "index_path": str(index_path),
        "degraded": degraded,
        "latest": index.model_dump(mode="json"),
    }


__all__ = [
    "append_graveyard_entry",
    "build_memory_record_from_batch_result",
    "build_memory_record_from_incubation",
    "build_memory_record_from_paper_tracking",
    "build_strategy_memory_index",
    "build_ui_strategy_memory_latest_payload",
    "detect_duplicate_variant",
    "ingest_batch_run",
    "ingest_paper_tracking",
    "load_graveyard_entries",
    "load_memory_records",
    "strategy_memory_root_directory",
    "write_memory_record",
]
