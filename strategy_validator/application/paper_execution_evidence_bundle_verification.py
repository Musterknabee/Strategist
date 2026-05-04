"""Verification for sealed paper execution evidence bundles.

The verifier is read-only: it recomputes the sealed bundle digest and the
source-artifact digests referenced by the bundle. It never submits orders,
contacts brokers, mutates the decision ledger, or promotes strategies.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.paper_execution_evidence_bundle import _paper_broker_root
from strategy_validator.contracts.paper_execution import (
    PaperExecutionEvidenceBundleVerificationArtifact,
    PaperExecutionEvidenceBundleVerificationSource,
    PaperExecutionEvidenceBundleVerificationView,
)
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256

_DIGEST_KEYS = {"artifact_sha256", "bundle_sha256"}


def _safe_timestamp(now: datetime) -> str:
    return now.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def _safe_read_json(path: Path) -> dict[str, Any] | None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return raw if isinstance(raw, dict) else None


def _mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def _embedded_digest(raw: dict[str, Any], *, digest_key: str) -> str:
    plain = dict(raw)
    plain.pop(digest_key, None)
    return canonical_json_sha256(plain)


def _declared_matches_computed(declared: str | None, computed: str | None) -> bool:
    declared = (declared or "").strip()
    computed = (computed or "").strip()
    if not declared or not computed:
        return False
    return declared == computed or computed.startswith(declared)


def _resolve_source_path(bundle_path: Path, source_path: str | None) -> Path | None:
    if not source_path:
        return None
    path = Path(source_path)
    if path.is_absolute():
        return path
    candidate = (Path.cwd() / path).resolve()
    if candidate.exists():
        return candidate
    return (bundle_path.parent / path).resolve()


def find_latest_paper_execution_evidence_bundle_artifact(
    *,
    bundle_artifact_path: Path | None = None,
    output_root: Path | None = None,
) -> tuple[Path | None, dict[str, Any] | None]:
    """Find and read the latest sealed evidence bundle artifact."""

    if bundle_artifact_path is not None:
        path = bundle_artifact_path.expanduser().resolve()
        return path, _safe_read_json(path)
    root = _paper_broker_root(output_root=output_root)
    candidates = list(root.glob("*/evidence_bundles/*.json"))
    history_tracking_ids = {path.parent.parent.name for path in candidates if path.parent.parent.name}
    for latest_path in root.glob("*/paper_execution_evidence_bundle.json"):
        if latest_path.parent.name not in history_tracking_ids:
            candidates.append(latest_path)
    if not candidates:
        return None, None
    path = sorted(candidates, key=_mtime, reverse=True)[0]
    return path, _safe_read_json(path)


def build_paper_execution_evidence_bundle_verification_artifact(
    *,
    bundle_artifact_path: Path,
    bundle_raw: dict[str, Any],
    generated_at_utc: datetime | None = None,
) -> PaperExecutionEvidenceBundleVerificationArtifact:
    """Build a verification artifact for a sealed bundle."""

    now = generated_at_utc or datetime.now(timezone.utc)
    declared_bundle_sha = str(bundle_raw.get("bundle_sha256") or "").strip() or None
    computed_bundle_sha = _embedded_digest(bundle_raw, digest_key="bundle_sha256")
    bundle_hash_valid = _declared_matches_computed(declared_bundle_sha, computed_bundle_sha)
    blockers: list[str] = []
    warnings: list[str] = []
    if not bundle_hash_valid:
        blockers.append("BUNDLE_SHA256_MISMATCH")

    sources_raw = bundle_raw.get("source_artifacts")
    if not isinstance(sources_raw, list):
        sources_raw = []
        blockers.append("BUNDLE_SOURCE_ARTIFACTS_MISSING")
    timeline_raw = bundle_raw.get("timeline")
    timeline = timeline_raw if isinstance(timeline_raw, list) else []
    if not timeline:
        warnings.append("BUNDLE_TIMELINE_MISSING_OR_EMPTY")

    timeline_links = {
        (
            str(row.get("stage") or ""),
            str(row.get("artifact_path") or ""),
            str(row.get("artifact_sha256") or ""),
        )
        for row in timeline
        if isinstance(row, dict)
    }
    source_verifications: list[PaperExecutionEvidenceBundleVerificationSource] = []
    missing = 0
    mismatched = 0
    verified = 0
    link_failures = 0

    for source in sources_raw:
        if not isinstance(source, dict):
            continue
        stage = str(source.get("stage") or "UNKNOWN")
        tracking_id = str(source.get("tracking_id") or "") or None
        artifact_path = str(source.get("artifact_path") or "") or None
        declared_sha = str(source.get("artifact_sha256") or "").strip() or None
        path = _resolve_source_path(bundle_artifact_path, artifact_path)
        issue: str | None = None
        computed_sha: str | None = None
        ok = False
        if path is None:
            missing += 1
            issue = "SOURCE_ARTIFACT_PATH_MISSING"
        elif not path.exists():
            missing += 1
            issue = "SOURCE_ARTIFACT_NOT_FOUND"
        else:
            raw = _safe_read_json(path)
            if raw is None:
                mismatched += 1
                issue = "SOURCE_ARTIFACT_UNREADABLE"
            else:
                computed_sha = _embedded_digest(raw, digest_key="artifact_sha256") if "artifact_sha256" in raw else canonical_json_sha256(raw)
                ok = _declared_matches_computed(declared_sha, computed_sha)
                if ok:
                    verified += 1
                else:
                    mismatched += 1
                    issue = "SOURCE_ARTIFACT_SHA256_MISMATCH"

        link_ok = any(
            stage == row_stage
            and ((artifact_path and artifact_path == row_path) or (declared_sha and (row_sha == declared_sha or declared_sha.startswith(row_sha) or row_sha.startswith(declared_sha))))
            for row_stage, row_path, row_sha in timeline_links
        )
        if not link_ok:
            link_failures += 1
            issue = issue or "SOURCE_NOT_LINKED_IN_TIMELINE"
        source_verifications.append(
            PaperExecutionEvidenceBundleVerificationSource(
                stage=stage,
                tracking_id=tracking_id,
                artifact_path=artifact_path,
                declared_sha256=declared_sha,
                computed_sha256=computed_sha,
                verified=ok and link_ok,
                issue=issue,
            )
        )

    if missing:
        blockers.append("SOURCE_ARTIFACTS_MISSING")
    if mismatched:
        blockers.append("SOURCE_ARTIFACTS_SHA256_MISMATCHED")
    timeline_source_link_valid = link_failures == 0 and bool(source_verifications)
    if link_failures:
        blockers.append("BUNDLE_TIMELINE_SOURCE_LINK_MISMATCH")
    if not source_verifications:
        blockers.append("BUNDLE_HAS_NO_SOURCE_ARTIFACTS")
    if verified < len(source_verifications):
        warnings.append("NOT_ALL_SOURCE_ARTIFACTS_VERIFIED")

    status = "FAIL" if blockers else "PASS"
    trust = "TRUSTED" if status == "PASS" else "UNTRUSTED"
    artifact = PaperExecutionEvidenceBundleVerificationArtifact(
        generated_at_utc=now,
        tracking_id=str(bundle_raw.get("tracking_id") or "") or None,
        verification_status=status,  # type: ignore[arg-type]
        trust_banner=trust,  # type: ignore[arg-type]
        source_bundle_artifact_path=str(bundle_artifact_path),
        source_bundle_declared_sha256=declared_bundle_sha,
        source_bundle_computed_sha256=computed_bundle_sha,
        bundle_hash_valid=bundle_hash_valid,
        timeline_source_link_valid=timeline_source_link_valid,
        source_artifact_count=len(source_verifications),
        verified_source_artifact_count=sum(1 for row in source_verifications if row.verified),
        missing_source_artifact_count=missing,
        mismatched_source_artifact_count=mismatched,
        source_verifications=source_verifications,
        blockers=sorted(set(blockers)),
        warnings=sorted(set(warnings)),
    )
    plain = artifact.model_dump(mode="json", exclude={"artifact_sha256"})
    return artifact.model_copy(update={"artifact_sha256": canonical_json_sha256(plain)})


def write_paper_execution_evidence_bundle_verification_artifact(
    *,
    bundle_artifact_path: Path | None = None,
    output_root: Path | None = None,
    generated_at_utc: datetime | None = None,
) -> tuple[Path, Path, PaperExecutionEvidenceBundleVerificationArtifact]:
    """Verify a sealed bundle and write latest + immutable verification artifacts."""

    source_path, raw = find_latest_paper_execution_evidence_bundle_artifact(
        bundle_artifact_path=bundle_artifact_path,
        output_root=output_root,
    )
    if source_path is None or raw is None:
        source_path = (bundle_artifact_path or (_paper_broker_root(output_root=output_root) / "untracked" / "paper_execution_evidence_bundle.json")).expanduser().resolve()
        raw = {}
    artifact = build_paper_execution_evidence_bundle_verification_artifact(
        bundle_artifact_path=source_path,
        bundle_raw=raw,
        generated_at_utc=generated_at_utc,
    )
    tracking_id = artifact.tracking_id or "untracked"
    root = _paper_broker_root(output_root=output_root) / tracking_id
    history_dir = root / "evidence_bundle_verifications"
    history_dir.mkdir(parents=True, exist_ok=True)
    latest_path = root / "paper_execution_evidence_bundle_verification.json"
    history_path = history_dir / f"{_safe_timestamp(artifact.generated_at_utc)}_{artifact.artifact_sha256[:12]}.json"
    body = json.dumps(artifact.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
    history_path.write_text(body, encoding="utf-8")
    latest_path.write_text(body, encoding="utf-8")
    return latest_path, history_path, artifact


def _view_from_raw(path: Path, raw: dict[str, Any]) -> PaperExecutionEvidenceBundleVerificationView:
    digest = str(raw.get("artifact_sha256") or canonical_json_sha256(raw))
    return PaperExecutionEvidenceBundleVerificationView(
        tracking_id=str(raw.get("tracking_id") or "") or None,
        artifact_path=str(path),
        artifact_sha256=digest,
        generated_at_utc=str(raw.get("generated_at_utc") or "") or None,
        verification_status=str(raw.get("verification_status") or "UNKNOWN"),  # type: ignore[arg-type]
        trust_banner=str(raw.get("trust_banner") or "UNTRUSTED"),  # type: ignore[arg-type]
        source_bundle_artifact_path=str(raw.get("source_bundle_artifact_path") or "") or None,
        source_bundle_declared_sha256=str(raw.get("source_bundle_declared_sha256") or "") or None,
        source_bundle_computed_sha256=str(raw.get("source_bundle_computed_sha256") or "") or None,
        bundle_hash_valid=bool(raw.get("bundle_hash_valid")),
        timeline_source_link_valid=bool(raw.get("timeline_source_link_valid")),
        source_artifact_count=int(raw.get("source_artifact_count") or 0),
        verified_source_artifact_count=int(raw.get("verified_source_artifact_count") or 0),
        missing_source_artifact_count=int(raw.get("missing_source_artifact_count") or 0),
        mismatched_source_artifact_count=int(raw.get("mismatched_source_artifact_count") or 0),
        blockers=[str(x) for x in raw.get("blockers", []) if x not in (None, "")] if isinstance(raw.get("blockers"), list) else [],
        warnings=[str(x) for x in raw.get("warnings", []) if x not in (None, "")] if isinstance(raw.get("warnings"), list) else [],
    )


def read_paper_execution_evidence_bundle_verification_views(
    *,
    repo_root: Path | None = None,
    output_root: Path | None = None,
    limit: int = 100,
) -> list[PaperExecutionEvidenceBundleVerificationView]:
    root = _paper_broker_root(repo_root=repo_root, output_root=output_root)
    if not root.is_dir():
        return []
    candidates = list(root.glob("*/evidence_bundle_verifications/*.json"))
    history_tracking_ids = {path.parent.parent.name for path in candidates if path.parent.parent.name}
    for latest_path in root.glob("*/paper_execution_evidence_bundle_verification.json"):
        if latest_path.parent.name not in history_tracking_ids:
            candidates.append(latest_path)
    rows: list[PaperExecutionEvidenceBundleVerificationView] = []
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
    "build_paper_execution_evidence_bundle_verification_artifact",
    "find_latest_paper_execution_evidence_bundle_artifact",
    "read_paper_execution_evidence_bundle_verification_views",
    "write_paper_execution_evidence_bundle_verification_artifact",
]
