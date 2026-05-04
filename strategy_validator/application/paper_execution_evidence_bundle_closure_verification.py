"""Verification for paper execution evidence-bundle closure packets.

The closure verifier is deliberately read-only. It recomputes the durable closure
packet digest and re-hashes every artifact referenced by the closure packet. It
never submits orders, calls broker mutation endpoints, promotes strategies, or
mutates the adjudication ledger.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.paper_execution_evidence_bundle import _paper_broker_root, _safe_timestamp
from strategy_validator.contracts.paper_execution import (
    PaperExecutionEvidenceBundleClosureVerificationArtifact,
    PaperExecutionEvidenceBundleClosureVerificationView,
)
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256


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


def _resolve_path(reference: str | None, *, closure_path: Path) -> Path | None:
    if not reference:
        return None
    path = Path(reference)
    if path.is_absolute():
        return path
    candidate = (Path.cwd() / path).resolve()
    if candidate.exists():
        return candidate
    return (closure_path.parent / path).resolve()


def _referenced_hash_valid(path_value: str | None, declared_sha: str | None, *, closure_path: Path, digest_key: str) -> tuple[bool, str | None]:
    path = _resolve_path(path_value, closure_path=closure_path)
    if path is None or not path.exists():
        return False, None
    raw = _safe_read_json(path)
    if raw is None:
        return False, None
    computed = _embedded_digest(raw, digest_key=digest_key) if digest_key in raw else canonical_json_sha256(raw)
    return _declared_matches_computed(declared_sha, computed), computed


def find_latest_paper_execution_evidence_bundle_closure_artifact(
    *,
    closure_artifact_path: Path | None = None,
    output_root: Path | None = None,
) -> tuple[Path | None, dict[str, Any] | None]:
    """Find and read the latest paper evidence-bundle closure artifact."""

    if closure_artifact_path is not None:
        path = closure_artifact_path.expanduser().resolve()
        return path, _safe_read_json(path)
    root = _paper_broker_root(output_root=output_root)
    candidates = list(root.glob("*/evidence_bundle_closures/*.json"))
    history_tracking_ids = {path.parent.parent.name for path in candidates if path.parent.parent.name}
    for latest_path in root.glob("*/paper_execution_evidence_bundle_closure.json"):
        if latest_path.parent.name not in history_tracking_ids:
            candidates.append(latest_path)
    if not candidates:
        return None, None
    path = sorted(candidates, key=_mtime, reverse=True)[0]
    return path, _safe_read_json(path)


def build_paper_execution_evidence_bundle_closure_verification_artifact(
    *,
    closure_artifact_path: Path,
    closure_raw: dict[str, Any],
    generated_at_utc: datetime | None = None,
) -> PaperExecutionEvidenceBundleClosureVerificationArtifact:
    """Build a read-only verification artifact for a paper closure packet."""

    now = generated_at_utc or datetime.now(timezone.utc)
    blockers: list[str] = []
    warnings: list[str] = []

    declared_closure_sha = str(closure_raw.get("artifact_sha256") or "").strip() or None
    computed_closure_sha = _embedded_digest(closure_raw, digest_key="artifact_sha256") if closure_raw else None
    closure_artifact_hash_valid = _declared_matches_computed(declared_closure_sha, computed_closure_sha)
    if not closure_raw:
        blockers.append("CLOSURE_ARTIFACT_MISSING_OR_UNREADABLE")
    elif not closure_artifact_hash_valid:
        blockers.append("CLOSURE_ARTIFACT_SHA256_MISMATCH")

    source_bundle_sha = str(closure_raw.get("source_bundle_sha256") or "").strip() or None
    source_verification_sha = str(closure_raw.get("source_verification_artifact_sha256") or "").strip() or None
    source_drift_sha = str(closure_raw.get("source_drift_artifact_sha256") or "").strip() or None
    source_attestation_sha = str(closure_raw.get("source_attestation_artifact_sha256") or "").strip() or None
    source_attestation_verification_sha = str(closure_raw.get("source_attestation_verification_artifact_sha256") or "").strip() or None

    source_bundle_hash_valid, _ = _referenced_hash_valid(
        str(closure_raw.get("source_bundle_artifact_path") or "") or None,
        source_bundle_sha,
        closure_path=closure_artifact_path,
        digest_key="bundle_sha256",
    )
    source_verification_hash_valid, _ = _referenced_hash_valid(
        str(closure_raw.get("source_verification_artifact_path") or "") or None,
        source_verification_sha,
        closure_path=closure_artifact_path,
        digest_key="artifact_sha256",
    )
    source_drift_hash_valid, _ = _referenced_hash_valid(
        str(closure_raw.get("source_drift_artifact_path") or "") or None,
        source_drift_sha,
        closure_path=closure_artifact_path,
        digest_key="artifact_sha256",
    )
    source_attestation_hash_valid, _ = _referenced_hash_valid(
        str(closure_raw.get("source_attestation_artifact_path") or "") or None,
        source_attestation_sha,
        closure_path=closure_artifact_path,
        digest_key="artifact_sha256",
    )
    source_attestation_verification_hash_valid, _ = _referenced_hash_valid(
        str(closure_raw.get("source_attestation_verification_artifact_path") or "") or None,
        source_attestation_verification_sha,
        closure_path=closure_artifact_path,
        digest_key="artifact_sha256",
    )

    if source_bundle_sha and not source_bundle_hash_valid:
        blockers.append("CLOSURE_SOURCE_BUNDLE_SHA256_MISMATCH_OR_MISSING")
    if source_verification_sha and not source_verification_hash_valid:
        blockers.append("CLOSURE_SOURCE_VERIFICATION_SHA256_MISMATCH_OR_MISSING")
    if source_drift_sha and not source_drift_hash_valid:
        blockers.append("CLOSURE_SOURCE_DRIFT_SHA256_MISMATCH_OR_MISSING")
    if source_attestation_sha and not source_attestation_hash_valid:
        blockers.append("CLOSURE_SOURCE_ATTESTATION_SHA256_MISMATCH_OR_MISSING")
    if source_attestation_verification_sha and not source_attestation_verification_hash_valid:
        blockers.append("CLOSURE_SOURCE_ATTESTATION_VERIFICATION_SHA256_MISMATCH_OR_MISSING")

    if str(closure_raw.get("closure_status") or "") != "READY_FOR_OPERATOR_REVIEW":
        warnings.append("CLOSURE_STATUS_NOT_READY_FOR_OPERATOR_REVIEW")
    if str(closure_raw.get("trust_banner") or "") != "TRUSTED":
        warnings.append("CLOSURE_TRUST_NOT_TRUSTED")
    if str(closure_raw.get("source_verification_status") or "") != "PASS":
        blockers.append("CLOSURE_SOURCE_BUNDLE_VERIFICATION_NOT_PASS")
    if str(closure_raw.get("source_drift_status") or "") != "IN_SYNC":
        blockers.append("CLOSURE_SOURCE_DRIFT_NOT_IN_SYNC")
    if str(closure_raw.get("source_attestation_status") or "") != "ATTESTED":
        blockers.append("CLOSURE_SOURCE_ATTESTATION_NOT_ATTESTED")
    if str(closure_raw.get("source_attestation_verification_status") or "") != "PASS":
        blockers.append("CLOSURE_SOURCE_ATTESTATION_VERIFICATION_NOT_PASS")

    blockers = sorted(set(blockers))
    warnings = sorted(set(warnings))
    status = "FAIL" if blockers else "PASS"
    trust = "TRUSTED" if status == "PASS" and not warnings else ("TRUST_RESTRICTED" if status == "PASS" else "UNTRUSTED")

    artifact = PaperExecutionEvidenceBundleClosureVerificationArtifact(
        generated_at_utc=now,
        tracking_id=str(closure_raw.get("tracking_id") or "") or None,
        verification_status=status,  # type: ignore[arg-type]
        trust_banner=trust,  # type: ignore[arg-type]
        source_closure_artifact_path=str(closure_artifact_path),
        source_closure_declared_sha256=declared_closure_sha,
        source_closure_computed_sha256=computed_closure_sha,
        source_closure_status=str(closure_raw.get("closure_status") or "") or None,
        source_closure_trust_banner=str(closure_raw.get("trust_banner") or "") or None,
        closure_artifact_hash_valid=closure_artifact_hash_valid,
        source_bundle_sha256=source_bundle_sha,
        source_bundle_hash_valid=source_bundle_hash_valid,
        source_verification_artifact_sha256=source_verification_sha,
        source_verification_hash_valid=source_verification_hash_valid,
        source_drift_artifact_sha256=source_drift_sha,
        source_drift_hash_valid=source_drift_hash_valid,
        source_attestation_artifact_sha256=source_attestation_sha,
        source_attestation_hash_valid=source_attestation_hash_valid,
        source_attestation_verification_artifact_sha256=source_attestation_verification_sha,
        source_attestation_verification_hash_valid=source_attestation_verification_hash_valid,
        blockers=blockers,
        warnings=warnings,
    )
    return artifact.model_copy(update={"artifact_sha256": canonical_json_sha256(artifact.model_dump(mode="json", exclude={"artifact_sha256"}))})


def write_paper_execution_evidence_bundle_closure_verification_artifact(
    *,
    closure_artifact_path: Path | None = None,
    output_root: Path | None = None,
    generated_at_utc: datetime | None = None,
) -> tuple[Path, Path, PaperExecutionEvidenceBundleClosureVerificationArtifact]:
    """Verify the latest or explicit closure packet and write latest + history artifacts."""

    source_path, raw = find_latest_paper_execution_evidence_bundle_closure_artifact(
        closure_artifact_path=closure_artifact_path,
        output_root=output_root,
    )
    if source_path is None or raw is None:
        source_path = (closure_artifact_path or (_paper_broker_root(output_root=output_root) / "untracked" / "paper_execution_evidence_bundle_closure.json")).expanduser().resolve()
        raw = {}
    artifact = build_paper_execution_evidence_bundle_closure_verification_artifact(
        closure_artifact_path=source_path,
        closure_raw=raw,
        generated_at_utc=generated_at_utc,
    )
    tracking_id = artifact.tracking_id or "untracked"
    root = _paper_broker_root(output_root=output_root) / tracking_id
    history_dir = root / "evidence_bundle_closure_verifications"
    history_dir.mkdir(parents=True, exist_ok=True)
    latest_path = root / "paper_execution_evidence_bundle_closure_verification.json"
    history_path = history_dir / f"{_safe_timestamp(artifact.generated_at_utc)}_{artifact.artifact_sha256[:12]}.json"
    body = json.dumps(artifact.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
    history_path.write_text(body, encoding="utf-8")
    latest_path.write_text(body, encoding="utf-8")
    return latest_path, history_path, artifact


def _view_from_raw(path: Path, raw: dict[str, Any]) -> PaperExecutionEvidenceBundleClosureVerificationView:
    return PaperExecutionEvidenceBundleClosureVerificationView(
        tracking_id=str(raw.get("tracking_id") or "") or None,
        artifact_path=str(path),
        artifact_sha256=str(raw.get("artifact_sha256") or canonical_json_sha256(raw)) or None,
        generated_at_utc=str(raw.get("generated_at_utc") or "") or None,
        verification_status=str(raw.get("verification_status") or "UNKNOWN"),  # type: ignore[arg-type]
        trust_banner=str(raw.get("trust_banner") or "TRUST_RESTRICTED"),  # type: ignore[arg-type]
        source_closure_artifact_path=str(raw.get("source_closure_artifact_path") or "") or None,
        source_closure_declared_sha256=str(raw.get("source_closure_declared_sha256") or "") or None,
        source_closure_computed_sha256=str(raw.get("source_closure_computed_sha256") or "") or None,
        source_closure_status=str(raw.get("source_closure_status") or "") or None,
        source_closure_trust_banner=str(raw.get("source_closure_trust_banner") or "") or None,
        closure_artifact_hash_valid=bool(raw.get("closure_artifact_hash_valid")),
        source_bundle_hash_valid=bool(raw.get("source_bundle_hash_valid")),
        source_verification_hash_valid=bool(raw.get("source_verification_hash_valid")),
        source_drift_hash_valid=bool(raw.get("source_drift_hash_valid")),
        source_attestation_hash_valid=bool(raw.get("source_attestation_hash_valid")),
        source_attestation_verification_hash_valid=bool(raw.get("source_attestation_verification_hash_valid")),
        blocker_count=len(raw.get("blockers", [])) if isinstance(raw.get("blockers"), list) else 0,
        warning_count=len(raw.get("warnings", [])) if isinstance(raw.get("warnings"), list) else 0,
        blockers=[str(x) for x in raw.get("blockers", []) if x not in (None, "")] if isinstance(raw.get("blockers"), list) else [],
        warnings=[str(x) for x in raw.get("warnings", []) if x not in (None, "")] if isinstance(raw.get("warnings"), list) else [],
    )


def read_paper_execution_evidence_bundle_closure_verification_views(
    *,
    repo_root: Path | None = None,
    output_root: Path | None = None,
    limit: int = 100,
) -> list[PaperExecutionEvidenceBundleClosureVerificationView]:
    root = _paper_broker_root(repo_root=repo_root, output_root=output_root)
    if not root.is_dir():
        return []
    candidates = list(root.glob("*/evidence_bundle_closure_verifications/*.json"))
    history_tracking_ids = {path.parent.parent.name for path in candidates if path.parent.parent.name}
    for latest_path in root.glob("*/paper_execution_evidence_bundle_closure_verification.json"):
        if latest_path.parent.name not in history_tracking_ids:
            candidates.append(latest_path)
    rows: list[PaperExecutionEvidenceBundleClosureVerificationView] = []
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
    "build_paper_execution_evidence_bundle_closure_verification_artifact",
    "find_latest_paper_execution_evidence_bundle_closure_artifact",
    "read_paper_execution_evidence_bundle_closure_verification_views",
    "write_paper_execution_evidence_bundle_closure_verification_artifact",
]
