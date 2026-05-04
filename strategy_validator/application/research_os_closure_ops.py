"""Research OS closure manifest builder (artifact digest spine; no mutation authority)."""
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.research_os_paths import artifact_root_directory
from strategy_validator.application.ui_strategy_batch import discover_latest_batch_summary
from strategy_validator.contracts.research_os_closure import (
    ResearchOsClosureManifest,
    ResearchOsClosureStatus,
    ResearchOsEvidenceArtifactRef,
    ResearchOsTrustBanner,
)
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256

_SCHEMA = "ui_research_os_closure/v1"

SECRET_MARKERS = (
    "STRATEGY_VALIDATOR_API_TOKEN",
    "ALPACA_API_SECRET",
    "ALPACA_SECRET_KEY",
    "POLYGON_API_KEY",
    "TIINGO_API_KEY",
    "TWELVE_DATA_API_KEY",
    "SECRET_KEY",
    "PRIVATE_KEY",
    "BEARER ",
)


def _artifact_root(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    if artifact_root is not None:
        return artifact_root.expanduser().resolve()
    return artifact_root_directory(repo_root)


def research_os_closure_root(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    return (_artifact_root(repo_root, artifact_root) / "research_os_closure").resolve()


def research_os_closure_latest_path(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    return (research_os_closure_root(repo_root, artifact_root) / "latest" / "research_os_closure_manifest.json").resolve()


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


def _status_hint(kind: str, data: dict[str, Any] | None) -> tuple[str | None, bool | None, list[str], list[str], dict[str, Any]]:
    if data is None:
        return None, None, [], [], {}
    schema = data.get("schema_version")
    status = data.get("status") or data.get("provider_status") or data.get("policy_status")
    ok = data.get("ok") if isinstance(data.get("ok"), bool) else None
    warnings = _as_list(data.get("warnings"))
    blockers = _as_list(data.get("blockers"))
    meta: dict[str, Any] = {}
    for key in (
        "run_id",
        "batch_id",
        "book_id",
        "tracking_id",
        "provider_id",
        "provider_status",
        "policy_status",
        "pit_status",
        "trust_level",
        "license_scope",
        "manifest_sha256",
        "evidence_sha256",
    ):
        val = data.get(key)
        if val not in (None, ""):
            meta[key] = val
    if kind == "provider_paper_loop_manifest":
        meta["paper_broker_status"] = data.get("paper_broker", {}).get("policy_status") if isinstance(data.get("paper_broker"), dict) else None
    if schema and isinstance(schema, str):
        meta.setdefault("source_schema_version", schema)
    return str(status) if status is not None else None, ok, warnings, blockers, meta


def _artifact_ref(kind: str, path: Path, *, required: bool) -> ResearchOsEvidenceArtifactRef:
    exists = path.is_file()
    raw = _read_json(path) if exists else None
    readable = raw is not None
    warnings: list[str] = []
    blockers: list[str] = []
    meta: dict[str, Any] = {}
    status_hint: str | None = None
    ok_hint: bool | None = None
    schema_observed: str | None = None
    digest: str | None = None

    if exists:
        try:
            digest = _sha256_file(path)
        except OSError:
            readable = False
    if exists and not readable:
        blockers.append("UNREADABLE_JSON_ARTIFACT")
    if raw is not None:
        schema_observed = str(raw.get("schema_version")) if raw.get("schema_version") is not None else None
        status_hint, ok_hint, warnings, blockers, meta = _status_hint(kind, raw)
        body = json.dumps(raw, sort_keys=True)
        for marker in SECRET_MARKERS:
            if marker in body:
                blockers.append(f"SECRET_MARKER_PRESENT:{marker}")
    if required and not exists:
        blockers.append("MISSING_REQUIRED_ARTIFACT")
    return ResearchOsEvidenceArtifactRef(
        artifact_kind=kind,
        artifact_path=str(path),
        required=required,
        exists=exists,
        readable=readable,
        file_sha256=digest,
        schema_version_observed=schema_observed,
        status_hint=status_hint,
        ok_hint=ok_hint,
        warnings=warnings,
        blockers=blockers,
        metadata={k: v for k, v in meta.items() if v is not None},
    )


def _candidate_artifacts(repo_root: Path | None = None, artifact_root: Path | None = None) -> list[tuple[str, Path, bool]]:
    root = _artifact_root(repo_root, artifact_root)
    batch_path, _summary = discover_latest_batch_summary(repo_root=repo_root)
    candidates: list[tuple[str, Path, bool]] = [
        ("provider_paper_loop_manifest", root / "provider_paper_loop" / "latest" / "provider_paper_loop_manifest.json", False),
        ("provider_historical_snapshot_run", root / "provider_historical_snapshots" / "latest" / "provider_historical_snapshot_run.json", False),
        ("paper_broker_status", root / "paper_broker" / "latest" / "paper_broker_status.json", False),
        ("shadow_book_manifest", root / "shadow_books" / "latest" / "shadow_book_manifest.json", False),
        ("shadow_book_risk_summary", root / "shadow_books" / "latest" / "latest_risk_summary.json", False),
        ("strategy_memory_index", root / "strategy_memory" / "latest" / "memory_index.json", False),
        ("strategy_thesis_evaluation", root / "strategy_theses" / "latest" / "thesis_evaluation.json", False),
        ("research_os_runtime_manifest", root / "research_os_runtime" / "latest" / "runtime_demo_manifest.json", False),
    ]
    if batch_path is not None:
        candidates.append(("strategy_batch_summary", batch_path, False))
        mdi_paths = sorted(batch_path.parent.rglob("market_data_integrity_result.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if mdi_paths:
            candidates.append(("market_data_integrity_result", mdi_paths[0], False))
    else:
        candidates.append(("strategy_batch_summary", root / "strategy_runs" / "latest" / "batch_summary.json", False))
    return candidates


def _classify(refs: list[ResearchOsEvidenceArtifactRef]) -> tuple[ResearchOsClosureStatus, ResearchOsTrustBanner, list[str], list[str]]:
    present = [r for r in refs if r.exists and r.readable]
    warnings: list[str] = []
    blockers: list[str] = []
    missing_required = [r.artifact_kind for r in refs if r.required and not r.exists]
    unreadable = [r.artifact_kind for r in refs if r.exists and not r.readable]
    if missing_required:
        blockers.extend(f"MISSING_REQUIRED:{x}" for x in missing_required)
    if unreadable:
        blockers.extend(f"UNREADABLE:{x}" for x in unreadable)
    for r in refs:
        warnings.extend(f"{r.artifact_kind}:{x}" for x in r.warnings)
        blockers.extend(f"{r.artifact_kind}:{x}" for x in r.blockers if x != "MISSING_REQUIRED_ARTIFACT")
        if r.status_hint in {"PENDING_KEY", "PROVIDER_UNAVAILABLE", "UNAVAILABLE", "NOT_PRESENT", "DEGRADED"}:
            warnings.append(f"{r.artifact_kind}:STATUS_{r.status_hint}")
        if r.status_hint in {"BLOCKED", "BLOCKED_BY_POLICY", "FAILED_VALIDATION"}:
            blockers.append(f"{r.artifact_kind}:STATUS_{r.status_hint}")
    if not present:
        return ResearchOsClosureStatus.EMPTY, ResearchOsTrustBanner.UNTRUSTED, sorted(set(warnings + ["NO_EVIDENCE_ARTIFACTS_PRESENT"])), sorted(set(blockers))
    if blockers:
        return ResearchOsClosureStatus.BLOCKED, ResearchOsTrustBanner.UNTRUSTED, sorted(set(warnings)), sorted(set(blockers))
    missing_core = [r.artifact_kind for r in refs if not r.exists and r.artifact_kind in {"provider_paper_loop_manifest", "strategy_batch_summary"}]
    if missing_core:
        warnings.extend(f"MISSING_CORE_ARTIFACT:{x}" for x in missing_core)
        return ResearchOsClosureStatus.DEGRADED, ResearchOsTrustBanner.TRUST_RESTRICTED, sorted(set(warnings)), []
    if warnings:
        return ResearchOsClosureStatus.DEGRADED, ResearchOsTrustBanner.TRUST_RESTRICTED, sorted(set(warnings)), []
    return ResearchOsClosureStatus.COMPLETE, ResearchOsTrustBanner.TRUSTED, [], []


def build_research_os_closure_manifest(
    *,
    closure_id: str,
    repo_root: Path | None = None,
    artifact_root: Path | None = None,
) -> ResearchOsClosureManifest:
    root = _artifact_root(repo_root, artifact_root)
    refs = [_artifact_ref(kind, path.resolve(), required=req) for kind, path, req in _candidate_artifacts(repo_root, artifact_root)]
    status, banner, warnings, blockers = _classify(refs)
    missing_required = [r.artifact_kind for r in refs if r.required and not r.exists]
    unreadable = [r.artifact_kind for r in refs if r.exists and not r.readable]
    digests = {r.artifact_kind: r.file_sha256 for r in refs if r.file_sha256}
    digest_spine = canonical_json_sha256({"artifacts": [r.model_dump(mode="json") for r in refs], "digests": digests})
    manifest = ResearchOsClosureManifest(
        closure_id=closure_id,
        artifact_root=str(root),
        status=status,
        trust_banner=banner,
        artifacts=refs,
        artifact_count=len(refs),
        present_artifact_count=len([r for r in refs if r.exists and r.readable]),
        missing_required=missing_required,
        unreadable_artifacts=unreadable,
        warnings=warnings,
        blockers=blockers,
        digests={**digests, "evidence_spine_sha256": digest_spine},
    )
    body = manifest.model_dump(mode="json", exclude={"manifest_sha256"})
    return manifest.model_copy(update={"manifest_sha256": canonical_json_sha256(body)})


def write_research_os_closure_manifest(
    manifest: ResearchOsClosureManifest,
    *,
    repo_root: Path | None = None,
    artifact_root: Path | None = None,
    overwrite: bool = False,
) -> Path:
    root = research_os_closure_root(repo_root, artifact_root)
    cdir = root / manifest.closure_id
    if cdir.exists():
        if not overwrite:
            raise FileExistsError(f"RESEARCH_OS_CLOSURE_EXISTS:{manifest.closure_id}")
        shutil.rmtree(cdir)
    path = cdir / "research_os_closure_manifest.json"
    _write_json(path, manifest.model_dump(mode="json"))
    latest = root / "latest"
    latest.mkdir(parents=True, exist_ok=True)
    _write_json(latest / "research_os_closure_manifest.json", manifest.model_dump(mode="json"))
    _write_json(latest / "latest_ref.json", {"closure_id": manifest.closure_id, "manifest_path": str(path.resolve())})
    return path.resolve()


def load_latest_research_os_closure(*, repo_root: Path | None = None, artifact_root: Path | None = None) -> ResearchOsClosureManifest | None:
    path = research_os_closure_latest_path(repo_root, artifact_root)
    raw = _read_json(path)
    if raw is None:
        return None
    return ResearchOsClosureManifest.model_validate(raw)


def build_ui_research_os_closure_latest_payload(*, repo_root: Path | None = None) -> dict[str, Any]:
    path = research_os_closure_latest_path(repo_root)
    manifest = load_latest_research_os_closure(repo_root=repo_root)
    if manifest is None:
        return {
            "schema_version": _SCHEMA,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "read_plane_only": True,
            "no_live_trading": True,
            "no_broker_orders": True,
            "no_order_controls": True,
            "status": "NOT_PRESENT",
            "artifact_path": str(path),
            "latest": None,
            "degraded": ["NO_RESEARCH_OS_CLOSURE_MANIFEST"],
        }
    return {
        "schema_version": _SCHEMA,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "read_plane_only": True,
        "no_live_trading": True,
        "no_broker_orders": True,
        "no_order_controls": True,
        "status": "PRESENT",
        "artifact_path": str(path),
        "latest": manifest.model_dump(mode="json"),
        "degraded": [] if manifest.status == ResearchOsClosureStatus.COMPLETE else [f"CLOSURE_{manifest.status.value}"],
    }


__all__ = [
    "build_research_os_closure_manifest",
    "build_ui_research_os_closure_latest_payload",
    "load_latest_research_os_closure",
    "research_os_closure_latest_path",
    "research_os_closure_root",
    "write_research_os_closure_manifest",
]
