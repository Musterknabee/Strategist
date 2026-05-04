"""Research OS operator run orchestration.

This module sequences already-safe evidence operations into one daily/operator run
manifest. It is offline/read-plane oriented and never sends broker orders, performs
browser mutation, mutates the ledger, grants deployment approval, or certifies profitability.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from strategy_validator.application.research_os_attestation_ops import (
    build_operator_attestation,
    write_operator_attestation,
    write_research_os_closure_verification,
    verify_research_os_closure_manifest,
)
from strategy_validator.application.research_os_briefing_ops import (
    build_research_os_briefing_pack,
    write_research_os_briefing_pack,
)
from strategy_validator.application.research_os_closure_ops import (
    build_research_os_closure_manifest,
    write_research_os_closure_manifest,
)
from strategy_validator.application.research_os_export_ops import (
    build_research_os_export_manifest,
    verify_research_os_export,
)
from strategy_validator.application.research_os_paths import artifact_root_directory
from strategy_validator.contracts.research_os_attestation import ResearchOsOperatorDecision
from strategy_validator.contracts.research_os_closure import ResearchOsTrustBanner
from strategy_validator.contracts.research_os_export import ResearchOsExportStatus
from strategy_validator.contracts.research_os_operator_run import (
    ResearchOsOperatorRunManifest,
    ResearchOsOperatorRunStatus,
    ResearchOsOperatorRunStep,
    ResearchOsOperatorRunStepStatus,
)
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256

_SCHEMA = "ui_research_os_operator_run/v1"


def _artifact_root(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    if artifact_root is not None:
        return artifact_root.expanduser().resolve()
    return artifact_root_directory(repo_root)


def research_os_operator_run_root(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    return (_artifact_root(repo_root, artifact_root) / "research_os_operator_runs").resolve()


def research_os_operator_run_latest_path(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    return (research_os_operator_run_root(repo_root, artifact_root) / "latest" / "research_os_operator_run_manifest.json").resolve()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _as_list(raw: Any) -> list[str]:
    if isinstance(raw, list):
        return [str(x) for x in raw if x is not None]
    if raw in (None, ""):
        return []
    return [str(raw)]


def _step(
    *,
    step_id: str,
    title: str,
    status: ResearchOsOperatorRunStepStatus,
    started: datetime,
    artifact_path: Path | None = None,
    artifact_sha256: str | None = None,
    warnings: list[str] | None = None,
    blockers: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> ResearchOsOperatorRunStep:
    if artifact_sha256 is None and artifact_path is not None and artifact_path.is_file():
        artifact_sha256 = _sha256_file(artifact_path)
    return ResearchOsOperatorRunStep(
        step_id=step_id,
        title=title,
        status=status,
        started_at_utc=started,
        completed_at_utc=datetime.now(timezone.utc),
        artifact_path=str(artifact_path.resolve()) if artifact_path is not None else None,
        artifact_sha256=artifact_sha256,
        warnings=sorted(set(warnings or [])),
        blockers=sorted(set(blockers or [])),
        metadata={k: v for k, v in (metadata or {}).items() if v is not None},
    )


def _step_status(*, blockers: list[str], warnings: list[str], hard_status: str | None = None) -> ResearchOsOperatorRunStepStatus:
    if blockers:
        return ResearchOsOperatorRunStepStatus.BLOCKED
    if hard_status in {"BLOCKED", "FAILED", "TAMPERED", "MISSING"}:
        return ResearchOsOperatorRunStepStatus.BLOCKED
    if hard_status in {"RESTRICTED", "DEGRADED", "STALE", "EMPTY"} or warnings:
        return ResearchOsOperatorRunStepStatus.WARNING
    return ResearchOsOperatorRunStepStatus.SUCCESS


def _manifest_status(steps: list[ResearchOsOperatorRunStep]) -> tuple[ResearchOsOperatorRunStatus, ResearchOsTrustBanner, list[str], list[str]]:
    warnings: list[str] = []
    blockers: list[str] = []
    if not steps:
        return ResearchOsOperatorRunStatus.EMPTY, ResearchOsTrustBanner.UNTRUSTED, ["NO_OPERATOR_RUN_STEPS"], []
    for s in steps:
        warnings.extend(f"{s.step_id}:{x}" for x in s.warnings)
        blockers.extend(f"{s.step_id}:{x}" for x in s.blockers)
        if s.status in {ResearchOsOperatorRunStepStatus.BLOCKED, ResearchOsOperatorRunStepStatus.FAILED}:
            blockers.append(f"{s.step_id}:STEP_{s.status.value}")
        elif s.status == ResearchOsOperatorRunStepStatus.WARNING:
            warnings.append(f"{s.step_id}:STEP_WARNING")
    if blockers:
        return ResearchOsOperatorRunStatus.BLOCKED, ResearchOsTrustBanner.UNTRUSTED, sorted(set(warnings)), sorted(set(blockers))
    if warnings:
        return ResearchOsOperatorRunStatus.RESTRICTED, ResearchOsTrustBanner.TRUST_RESTRICTED, sorted(set(warnings)), []
    return ResearchOsOperatorRunStatus.COMPLETE, ResearchOsTrustBanner.TRUSTED, [], []


def _with_digest(manifest: ResearchOsOperatorRunManifest) -> ResearchOsOperatorRunManifest:
    payload = manifest.model_dump(mode="json", exclude={"manifest_sha256"})
    payload["manifest_sha256"] = canonical_json_sha256(payload)
    return ResearchOsOperatorRunManifest.model_validate(payload)


def build_research_os_operator_run(
    *,
    run_id: str,
    operator_id: str = "local-operator",
    decision: ResearchOsOperatorDecision | str = ResearchOsOperatorDecision.ACCEPTED_WITH_RESTRICTIONS,
    rationale: str = "Paper-only Research OS operator run evidence acknowledged; not deployment approval.",
    constraints: list[str] | None = None,
    repo_root: Path | None = None,
    artifact_root: Path | None = None,
    overwrite: bool = False,
    include_export_archive: bool = True,
) -> ResearchOsOperatorRunManifest:
    """Run closure -> verification -> attestation -> briefing -> export as one safe operator sequence."""
    root = _artifact_root(repo_root, artifact_root)
    steps: list[ResearchOsOperatorRunStep] = []
    constraints = list(constraints or ["No live trading", "No broker orders", "No browser order controls"])

    started = datetime.now(timezone.utc)
    closure = build_research_os_closure_manifest(closure_id=f"{run_id}-closure", repo_root=repo_root, artifact_root=root)
    closure_path = write_research_os_closure_manifest(closure, repo_root=repo_root, artifact_root=root, overwrite=overwrite)
    steps.append(
        _step(
            step_id="closure",
            title="Build Research OS closure manifest",
            status=_step_status(blockers=list(closure.blockers), warnings=list(closure.warnings), hard_status=closure.status.value),
            started=started,
            artifact_path=closure_path,
            warnings=list(closure.warnings),
            blockers=list(closure.blockers),
            metadata={"closure_id": closure.closure_id, "closure_status": closure.status.value, "trust_banner": closure.trust_banner.value},
        )
    )

    started = datetime.now(timezone.utc)
    verification = verify_research_os_closure_manifest(
        verification_id=f"{run_id}-verification",
        manifest_path=closure_path,
        repo_root=repo_root,
        artifact_root=root,
    )
    verification_path = write_research_os_closure_verification(verification, repo_root=repo_root, artifact_root=root, overwrite=overwrite)
    steps.append(
        _step(
            step_id="closure_verification",
            title="Verify closure artifact digests",
            status=_step_status(blockers=list(verification.blockers), warnings=list(verification.warnings), hard_status=verification.status.value),
            started=started,
            artifact_path=verification_path,
            warnings=list(verification.warnings),
            blockers=list(verification.blockers),
            metadata={"verification_id": verification.verification_id, "verification_status": verification.status.value, "closure_id": verification.closure_id},
        )
    )

    started = datetime.now(timezone.utc)
    attestation = build_operator_attestation(
        attestation_id=f"{run_id}-attestation",
        operator_id=operator_id,
        decision=decision,
        rationale=rationale,
        constraints=constraints,
        verification=verification,
        repo_root=repo_root,
        artifact_root=root,
    )
    attestation_path = write_operator_attestation(attestation, repo_root=repo_root, artifact_root=root, overwrite=overwrite)
    steps.append(
        _step(
            step_id="operator_attestation",
            title="Write operator attestation",
            status=_step_status(blockers=list(attestation.blockers), warnings=list(attestation.warnings), hard_status=attestation.decision.value),
            started=started,
            artifact_path=attestation_path,
            warnings=list(attestation.warnings),
            blockers=list(attestation.blockers),
            metadata={"attestation_id": attestation.attestation_id, "decision": attestation.decision.value, "operator_id": attestation.operator_id},
        )
    )

    started = datetime.now(timezone.utc)
    briefing = build_research_os_briefing_pack(briefing_id=f"{run_id}-briefing", repo_root=repo_root, artifact_root=root)
    briefing_path = write_research_os_briefing_pack(briefing, repo_root=repo_root, artifact_root=root, overwrite=overwrite)
    steps.append(
        _step(
            step_id="briefing",
            title="Build Research OS briefing pack",
            status=_step_status(blockers=list(briefing.blockers), warnings=list(briefing.warnings), hard_status=briefing.status.value),
            started=started,
            artifact_path=briefing_path,
            artifact_sha256=briefing.briefing_sha256 or None,
            warnings=list(briefing.warnings),
            blockers=list(briefing.blockers),
            metadata={"briefing_id": briefing.briefing_id, "briefing_status": briefing.status.value, "action_item_count": len(briefing.action_items)},
        )
    )

    started = datetime.now(timezone.utc)
    export = build_research_os_export_manifest(
        export_id=f"{run_id}-export",
        repo_root=repo_root,
        artifact_root=root,
        overwrite=overwrite,
        include_archive=include_export_archive,
    )
    export_verification = verify_research_os_export(repo_root=repo_root, artifact_root=root, write_latest=True)
    export_path = Path(export.bundle_directory).parent / "research_os_export_manifest.json"
    export_warnings = list(export.warnings) + list(export_verification.warnings)
    export_blockers = list(export.blockers) + list(export_verification.blockers)
    hard = export_verification.status.value if export_verification.status != ResearchOsExportStatus.READY else export.status.value
    steps.append(
        _step(
            step_id="export",
            title="Build and verify portable evidence export",
            status=_step_status(blockers=export_blockers, warnings=export_warnings, hard_status=hard),
            started=started,
            artifact_path=export_path,
            artifact_sha256=export.manifest_sha256 or None,
            warnings=export_warnings,
            blockers=export_blockers,
            metadata={
                "export_id": export.export_id,
                "export_status": export.status.value,
                "export_verification_status": export_verification.status.value,
                "archive_path": export.archive_path,
                "archive_sha256": export.archive_sha256,
            },
        )
    )

    status, banner, warnings, blockers = _manifest_status(steps)
    digests = {s.step_id: s.artifact_sha256 for s in steps if s.artifact_sha256}
    digests["operator_run_spine_sha256"] = canonical_json_sha256({"steps": [s.model_dump(mode="json") for s in steps], "digests": digests})
    manifest = ResearchOsOperatorRunManifest(
        run_id=run_id,
        artifact_root=str(root),
        status=status,
        trust_banner=banner,
        steps=steps,
        warnings=warnings,
        blockers=blockers,
        digests=digests,
    )
    return _with_digest(manifest)


def write_research_os_operator_run_manifest(
    manifest: ResearchOsOperatorRunManifest,
    *,
    repo_root: Path | None = None,
    artifact_root: Path | None = None,
    overwrite: bool = False,
) -> Path:
    root = research_os_operator_run_root(repo_root, artifact_root)
    rdir = root / "runs" / manifest.run_id
    if rdir.exists():
        if not overwrite:
            raise FileExistsError(f"RESEARCH_OS_OPERATOR_RUN_EXISTS:{manifest.run_id}")
        shutil.rmtree(rdir)
    payload = manifest.model_dump(mode="json")
    path = rdir / "research_os_operator_run_manifest.json"
    _write_json(path, payload)
    latest = root / "latest"
    if latest.exists():
        shutil.rmtree(latest)
    latest.mkdir(parents=True, exist_ok=True)
    _write_json(latest / "research_os_operator_run_manifest.json", payload)
    _write_json(latest / "latest_ref.json", {"run_id": manifest.run_id, "manifest_path": str(path.resolve())})
    return path.resolve()


def build_and_write_research_os_operator_run(
    *,
    run_id: str,
    operator_id: str = "local-operator",
    decision: ResearchOsOperatorDecision | str = ResearchOsOperatorDecision.ACCEPTED_WITH_RESTRICTIONS,
    rationale: str = "Paper-only Research OS operator run evidence acknowledged; not deployment approval.",
    constraints: list[str] | None = None,
    repo_root: Path | None = None,
    artifact_root: Path | None = None,
    overwrite: bool = False,
    include_export_archive: bool = True,
) -> tuple[ResearchOsOperatorRunManifest, Path]:
    manifest = build_research_os_operator_run(
        run_id=run_id,
        operator_id=operator_id,
        decision=decision,
        rationale=rationale,
        constraints=constraints,
        repo_root=repo_root,
        artifact_root=artifact_root,
        overwrite=overwrite,
        include_export_archive=include_export_archive,
    )
    path = write_research_os_operator_run_manifest(manifest, repo_root=repo_root, artifact_root=artifact_root, overwrite=overwrite)
    return manifest, path


def load_latest_research_os_operator_run(*, repo_root: Path | None = None, artifact_root: Path | None = None) -> ResearchOsOperatorRunManifest | None:
    raw = _read_json(research_os_operator_run_latest_path(repo_root, artifact_root))
    if raw is None:
        return None
    return ResearchOsOperatorRunManifest.model_validate(raw)


def build_ui_research_os_operator_run_latest_payload(*, repo_root: Path | None = None, artifact_root: Path | None = None) -> dict[str, Any]:
    path = research_os_operator_run_latest_path(repo_root, artifact_root)
    manifest = load_latest_research_os_operator_run(repo_root=repo_root, artifact_root=artifact_root)
    if manifest is None:
        return {
            "schema_version": _SCHEMA,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "read_plane_only": True,
            "no_live_trading": True,
            "no_broker_orders": True,
            "no_order_controls": True,
            "status": "NOT_PRESENT",
            "manifest_path": str(path),
            "latest": None,
            "degraded": ["NO_RESEARCH_OS_OPERATOR_RUN_MANIFEST"],
        }
    return {
        "schema_version": _SCHEMA,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "read_plane_only": True,
        "no_live_trading": True,
        "no_broker_orders": True,
        "no_order_controls": True,
        "status": "PRESENT",
        "manifest_path": str(path),
        "latest": manifest.model_dump(mode="json"),
        "degraded": [] if manifest.status == ResearchOsOperatorRunStatus.COMPLETE else [f"OPERATOR_RUN_{manifest.status.value}"],
    }


__all__ = [
    "build_and_write_research_os_operator_run",
    "build_research_os_operator_run",
    "build_ui_research_os_operator_run_latest_payload",
    "load_latest_research_os_operator_run",
    "research_os_operator_run_latest_path",
    "research_os_operator_run_root",
    "write_research_os_operator_run_manifest",
]
