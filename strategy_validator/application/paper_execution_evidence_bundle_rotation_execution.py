"""CLI-only paper evidence-bundle rotation execution manifests.

The rotation executor turns a recommendation into an audited local workflow:
seal the current timeline, verify the sealed bundle, then check bundle drift.
It never submits orders, calls broker mutation endpoints, promotes strategies,
or mutates the adjudication ledger.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.paper_execution_evidence_bundle import (
    _paper_broker_root,
    _safe_timestamp,
    write_paper_execution_evidence_bundle_artifact,
)
from strategy_validator.application.paper_execution_evidence_bundle_drift import (
    write_paper_execution_evidence_bundle_drift_artifact,
)
from strategy_validator.application.paper_execution_evidence_bundle_verification import (
    write_paper_execution_evidence_bundle_verification_artifact,
)
from strategy_validator.contracts.paper_execution import (
    PaperExecutionEvidenceBundleRotationExecutionArtifact,
    PaperExecutionEvidenceBundleRotationExecutionStep,
    PaperExecutionEvidenceBundleRotationExecutionView,
    PaperExecutionEvidenceBundleRotationView,
    PaperExecutionTimelineEntry,
    PaperExecutionTimelineSummary,
)
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256


def _mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def _safe_read_json(path: Path) -> dict[str, Any] | None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return raw if isinstance(raw, dict) else None


def _timeline_tracking_id(timeline: list[PaperExecutionTimelineEntry]) -> str | None:
    for row in timeline:
        raw = (row.tracking_id or "").strip()
        if raw:
            return raw
    return None


def _step(
    *,
    name: str,
    status: str,
    artifact_path: Path | None = None,
    history_path: Path | None = None,
    artifact_sha256: str | None = None,
    output_status: str | None = None,
    trust_banner: str | None = None,
    blockers: list[str] | None = None,
    warnings: list[str] | None = None,
) -> PaperExecutionEvidenceBundleRotationExecutionStep:
    return PaperExecutionEvidenceBundleRotationExecutionStep(
        step_name=name,  # type: ignore[arg-type]
        status=status,  # type: ignore[arg-type]
        artifact_path=str(artifact_path) if artifact_path else None,
        history_artifact_path=str(history_path) if history_path else None,
        artifact_sha256=artifact_sha256,
        output_status=output_status,
        trust_banner=trust_banner,
        blockers=sorted(set(blockers or [])),
        warnings=sorted(set(warnings or [])),
    )


def _finalize(
    artifact: PaperExecutionEvidenceBundleRotationExecutionArtifact,
) -> PaperExecutionEvidenceBundleRotationExecutionArtifact:
    steps = list(artifact.steps)
    plain = artifact.model_copy(
        update={
            "step_count": len(steps),
            "passed_step_count": sum(1 for step in steps if step.status == "PASS"),
            "failed_step_count": sum(1 for step in steps if step.status == "FAIL"),
            "skipped_step_count": sum(1 for step in steps if step.status == "SKIPPED"),
            "blockers": sorted(set(artifact.blockers)),
            "warnings": sorted(set(artifact.warnings)),
            "artifact_sha256": "",
        }
    )
    digest = canonical_json_sha256(plain.model_dump(mode="json", exclude={"artifact_sha256"}))
    return plain.model_copy(update={"artifact_sha256": digest})


def build_blocked_paper_execution_evidence_bundle_rotation_execution_artifact(
    *,
    timeline_summary: PaperExecutionTimelineSummary,
    latest_rotation: PaperExecutionEvidenceBundleRotationView | None = None,
    force: bool = False,
    generated_at_utc: datetime | None = None,
) -> PaperExecutionEvidenceBundleRotationExecutionArtifact:
    """Build a non-executed rotation manifest for blocked/skipped situations."""

    now = generated_at_utc or datetime.now(timezone.utc)
    timeline_status = str(timeline_summary.sequence_status or "EMPTY")
    blockers: list[str] = []
    warnings: list[str] = []
    steps: list[PaperExecutionEvidenceBundleRotationExecutionStep] = []
    source_status = str(getattr(latest_rotation, "rotation_status", "NO_RECOMMENDATION") or "NO_RECOMMENDATION")

    if timeline_status != "COMPLETE":
        status = "BLOCKED"
        trust = "UNTRUSTED"
        blockers.append("PAPER_EXECUTION_TIMELINE_NOT_COMPLETE_FOR_ROTATION_EXECUTION")
        steps.append(_step(name="BLOCK", status="BLOCKED", output_status=timeline_status, blockers=blockers))
    elif latest_rotation is not None and latest_rotation.rotation_status == "BLOCKED" and not force:
        status = "BLOCKED"
        trust = "UNTRUSTED"
        blockers.extend(latest_rotation.blockers or ["SOURCE_ROTATION_RECOMMENDATION_BLOCKED"])
        steps.append(_step(name="BLOCK", status="BLOCKED", output_status="SOURCE_ROTATION_BLOCKED", blockers=blockers))
    elif latest_rotation is not None and latest_rotation.rotation_status == "NOT_NEEDED" and not force:
        status = "SKIPPED"
        trust = "TRUSTED"
        warnings.append("SOURCE_ROTATION_RECOMMENDATION_NOT_NEEDED")
        steps.append(_step(name="SKIP", status="SKIPPED", output_status="NOT_NEEDED", warnings=warnings))
    else:
        status = "BLOCKED"
        trust = "TRUST_RESTRICTED"
        blockers.append("ROTATION_EXECUTION_NO_STEPS_REQUESTED")
        steps.append(_step(name="BLOCK", status="BLOCKED", output_status="NO_STEPS", blockers=blockers))

    return _finalize(
        PaperExecutionEvidenceBundleRotationExecutionArtifact(
            generated_at_utc=now,
            tracking_id=getattr(latest_rotation, "tracking_id", None),
            rotation_execution_status=status,  # type: ignore[arg-type]
            trust_banner=trust,  # type: ignore[arg-type]
            source_recommendation_artifact_path=getattr(latest_rotation, "artifact_path", None),
            source_recommendation_artifact_sha256=getattr(latest_rotation, "artifact_sha256", None),
            source_recommendation_status=source_status,
            source_recommendation_trust_banner=getattr(latest_rotation, "trust_banner", None),
            force=force,
            timeline_sequence_status=timeline_status,
            timeline_event_count=int(timeline_summary.event_count or 0),
            steps=steps,
            blockers=blockers,
            warnings=warnings,
        )
    )


def run_paper_execution_evidence_bundle_rotation(
    *,
    timeline: list[PaperExecutionTimelineEntry],
    timeline_summary: PaperExecutionTimelineSummary,
    latest_rotation: PaperExecutionEvidenceBundleRotationView | None = None,
    output_root: Path | None = None,
    force: bool = False,
    generated_at_utc: datetime | None = None,
) -> PaperExecutionEvidenceBundleRotationExecutionArtifact:
    """Execute the safe local rotation workflow and return the manifest."""

    now = generated_at_utc or datetime.now(timezone.utc)
    if timeline_summary.sequence_status != "COMPLETE" or (
        latest_rotation is not None and latest_rotation.rotation_status in {"BLOCKED", "NOT_NEEDED"} and not force
    ):
        artifact = build_blocked_paper_execution_evidence_bundle_rotation_execution_artifact(
            timeline_summary=timeline_summary,
            latest_rotation=latest_rotation,
            force=force,
            generated_at_utc=now,
        )
        if artifact.tracking_id is None:
            return artifact.model_copy(update={"tracking_id": _timeline_tracking_id(timeline)})
        return artifact

    blockers: list[str] = []
    warnings: list[str] = []
    steps: list[PaperExecutionEvidenceBundleRotationExecutionStep] = []
    sealed_bundle_artifact_path: str | None = None
    sealed_bundle_sha256: str | None = None
    verification_artifact_path: str | None = None
    verification_status: str | None = None
    drift_artifact_path: str | None = None
    drift_status: str | None = None

    try:
        bundle_latest, bundle_history, bundle_artifact = write_paper_execution_evidence_bundle_artifact(
            timeline=timeline,
            timeline_summary=timeline_summary,
            output_root=output_root,
            generated_at_utc=now,
        )
        sealed_bundle_artifact_path = str(bundle_latest)
        sealed_bundle_sha256 = bundle_artifact.bundle_sha256
        seal_ok = bundle_artifact.bundle_status != "SEALED_BLOCKED"
        steps.append(
            _step(
                name="SEAL",
                status="PASS" if seal_ok else "FAIL",
                artifact_path=bundle_latest,
                history_path=bundle_history,
                artifact_sha256=bundle_artifact.bundle_sha256,
                output_status=bundle_artifact.bundle_status,
                trust_banner=bundle_artifact.trust_banner,
                blockers=list(bundle_artifact.blockers),
                warnings=list(bundle_artifact.warnings),
            )
        )
        blockers.extend(bundle_artifact.blockers)
        warnings.extend(bundle_artifact.warnings)
    except Exception as exc:  # pragma: no cover - defensive CLI safety
        blockers.append(f"SEAL_STEP_FAILED:{exc.__class__.__name__}")
        steps.append(_step(name="SEAL", status="FAIL", output_status="EXCEPTION", blockers=blockers))
        bundle_latest = None

    if bundle_latest is not None:
        try:
            verify_latest, verify_history, verify_artifact = write_paper_execution_evidence_bundle_verification_artifact(
                bundle_artifact_path=bundle_latest,
                output_root=output_root,
                generated_at_utc=now,
            )
            verification_artifact_path = str(verify_latest)
            verification_status = verify_artifact.verification_status
            verify_ok = verify_artifact.verification_status == "PASS"
            steps.append(
                _step(
                    name="VERIFY",
                    status="PASS" if verify_ok else "FAIL",
                    artifact_path=verify_latest,
                    history_path=verify_history,
                    artifact_sha256=verify_artifact.artifact_sha256,
                    output_status=verify_artifact.verification_status,
                    trust_banner=verify_artifact.trust_banner,
                    blockers=list(verify_artifact.blockers),
                    warnings=list(verify_artifact.warnings),
                )
            )
            blockers.extend(verify_artifact.blockers)
            warnings.extend(verify_artifact.warnings)
        except Exception as exc:  # pragma: no cover - defensive CLI safety
            blockers.append(f"VERIFY_STEP_FAILED:{exc.__class__.__name__}")
            steps.append(_step(name="VERIFY", status="FAIL", output_status="EXCEPTION", blockers=blockers))

        try:
            drift_latest, drift_history, drift_artifact = write_paper_execution_evidence_bundle_drift_artifact(
                current_timeline=timeline,
                current_timeline_summary=timeline_summary,
                bundle_artifact_path=bundle_latest,
                output_root=output_root,
                generated_at_utc=now,
            )
            drift_artifact_path = str(drift_latest)
            drift_status = drift_artifact.drift_status
            drift_ok = drift_artifact.drift_status == "IN_SYNC"
            steps.append(
                _step(
                    name="DRIFT_CHECK",
                    status="PASS" if drift_ok else "FAIL",
                    artifact_path=drift_latest,
                    history_path=drift_history,
                    artifact_sha256=drift_artifact.artifact_sha256,
                    output_status=drift_artifact.drift_status,
                    trust_banner=drift_artifact.trust_banner,
                    blockers=list(drift_artifact.blockers),
                    warnings=list(drift_artifact.warnings),
                )
            )
            blockers.extend(drift_artifact.blockers)
            warnings.extend(drift_artifact.warnings)
        except Exception as exc:  # pragma: no cover - defensive CLI safety
            blockers.append(f"DRIFT_CHECK_STEP_FAILED:{exc.__class__.__name__}")
            steps.append(_step(name="DRIFT_CHECK", status="FAIL", output_status="EXCEPTION", blockers=blockers))

    failed = any(step.status == "FAIL" for step in steps)
    status = "FAILED" if failed or blockers else "PASS"
    trust = "TRUSTED" if status == "PASS" else "UNTRUSTED"
    return _finalize(
        PaperExecutionEvidenceBundleRotationExecutionArtifact(
            generated_at_utc=now,
            tracking_id=_timeline_tracking_id(timeline) or getattr(latest_rotation, "tracking_id", None),
            rotation_execution_status=status,  # type: ignore[arg-type]
            trust_banner=trust,  # type: ignore[arg-type]
            source_recommendation_artifact_path=getattr(latest_rotation, "artifact_path", None),
            source_recommendation_artifact_sha256=getattr(latest_rotation, "artifact_sha256", None),
            source_recommendation_status=getattr(latest_rotation, "rotation_status", None),
            source_recommendation_trust_banner=getattr(latest_rotation, "trust_banner", None),
            force=force,
            timeline_sequence_status=timeline_summary.sequence_status,
            timeline_event_count=int(timeline_summary.event_count or 0),
            sealed_bundle_artifact_path=sealed_bundle_artifact_path,
            sealed_bundle_sha256=sealed_bundle_sha256,
            verification_artifact_path=verification_artifact_path,
            verification_status=verification_status,
            drift_artifact_path=drift_artifact_path,
            drift_status=drift_status,
            steps=steps,
            blockers=blockers,
            warnings=warnings,
        )
    )


def write_paper_execution_evidence_bundle_rotation_execution_artifact(
    *,
    timeline: list[PaperExecutionTimelineEntry],
    timeline_summary: PaperExecutionTimelineSummary,
    latest_rotation: PaperExecutionEvidenceBundleRotationView | None = None,
    output_root: Path | None = None,
    force: bool = False,
    generated_at_utc: datetime | None = None,
) -> tuple[Path, Path, PaperExecutionEvidenceBundleRotationExecutionArtifact]:
    artifact = run_paper_execution_evidence_bundle_rotation(
        timeline=timeline,
        timeline_summary=timeline_summary,
        latest_rotation=latest_rotation,
        output_root=output_root,
        force=force,
        generated_at_utc=generated_at_utc,
    )
    tracking_id = artifact.tracking_id or "untracked"
    root = _paper_broker_root(output_root=output_root) / tracking_id
    history_dir = root / "evidence_bundle_rotation_executions"
    history_dir.mkdir(parents=True, exist_ok=True)
    latest_path = root / "paper_execution_evidence_bundle_rotation_execution.json"
    history_path = history_dir / f"{_safe_timestamp(artifact.generated_at_utc)}_{artifact.artifact_sha256[:12]}.json"
    body = json.dumps(artifact.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
    history_path.write_text(body, encoding="utf-8")
    latest_path.write_text(body, encoding="utf-8")
    return latest_path, history_path, artifact


def _view_from_raw(path: Path, raw: dict[str, Any]) -> PaperExecutionEvidenceBundleRotationExecutionView:
    digest = str(raw.get("artifact_sha256") or canonical_json_sha256(raw))
    return PaperExecutionEvidenceBundleRotationExecutionView(
        tracking_id=str(raw.get("tracking_id") or "") or None,
        artifact_path=str(path),
        artifact_sha256=digest,
        generated_at_utc=str(raw.get("generated_at_utc") or "") or None,
        rotation_execution_status=str(raw.get("rotation_execution_status") or "UNKNOWN"),  # type: ignore[arg-type]
        trust_banner=str(raw.get("trust_banner") or "TRUST_RESTRICTED"),  # type: ignore[arg-type]
        source_recommendation_status=str(raw.get("source_recommendation_status") or "") or None,
        timeline_sequence_status=str(raw.get("timeline_sequence_status") or "") or None,
        sealed_bundle_sha256=str(raw.get("sealed_bundle_sha256") or "") or None,
        verification_status=str(raw.get("verification_status") or "") or None,
        drift_status=str(raw.get("drift_status") or "") or None,
        step_count=int(raw.get("step_count") or 0),
        passed_step_count=int(raw.get("passed_step_count") or 0),
        failed_step_count=int(raw.get("failed_step_count") or 0),
        skipped_step_count=int(raw.get("skipped_step_count") or 0),
        blockers=[str(x) for x in raw.get("blockers", []) if x not in (None, "")]
        if isinstance(raw.get("blockers"), list)
        else [],
        warnings=[str(x) for x in raw.get("warnings", []) if x not in (None, "")]
        if isinstance(raw.get("warnings"), list)
        else [],
    )


def read_paper_execution_evidence_bundle_rotation_execution_views(
    *,
    repo_root: Path | None = None,
    output_root: Path | None = None,
    limit: int = 100,
) -> list[PaperExecutionEvidenceBundleRotationExecutionView]:
    root = _paper_broker_root(repo_root=repo_root, output_root=output_root)
    if not root.is_dir():
        return []
    candidates = list(root.glob("*/evidence_bundle_rotation_executions/*.json"))
    history_tracking_ids = {path.parent.parent.name for path in candidates if path.parent.parent.name}
    for latest_path in root.glob("*/paper_execution_evidence_bundle_rotation_execution.json"):
        if latest_path.parent.name not in history_tracking_ids:
            candidates.append(latest_path)
    rows: list[PaperExecutionEvidenceBundleRotationExecutionView] = []
    for path in sorted(set(candidates), key=_mtime, reverse=True)[:limit]:
        raw = _safe_read_json(path)
        if raw is None:
            continue
        try:
            rows.append(_view_from_raw(path, raw))
        except ValueError:
            continue
    return sorted(rows, key=lambda row: row.generated_at_utc or "", reverse=True)[:limit]


__all__ = [
    "build_blocked_paper_execution_evidence_bundle_rotation_execution_artifact",
    "read_paper_execution_evidence_bundle_rotation_execution_views",
    "run_paper_execution_evidence_bundle_rotation",
    "write_paper_execution_evidence_bundle_rotation_execution_artifact",
]
