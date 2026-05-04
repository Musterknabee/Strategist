"""Read-only verifier for paper evidence-chain retention handoff capsules."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.paper_execution_evidence_bundle import _paper_broker_root, _safe_timestamp
from strategy_validator.contracts.paper_execution import (
    PaperExecutionEvidenceBundleRetentionHandoffVerificationArtifact,
    PaperExecutionEvidenceBundleRetentionHandoffVerificationView,
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


def _int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _strings(raw: Any) -> list[str]:
    if isinstance(raw, list):
        return [str(x) for x in raw if x not in (None, "")]
    if raw in (None, ""):
        return []
    return [str(raw)]


def _embedded_digest(raw: dict[str, Any], *, digest_key: str = "artifact_sha256") -> str | None:
    if not raw:
        return None
    plain = dict(raw)
    plain.pop(digest_key, None)
    return canonical_json_sha256(plain)


def _declared_matches_computed(declared: str | None, computed: str | None) -> bool:
    declared = (declared or "").strip()
    computed = (computed or "").strip()
    if not declared or not computed:
        return False
    return declared == computed or computed.startswith(declared)


def find_latest_paper_execution_evidence_bundle_retention_handoff_artifact(
    *,
    retention_handoff_artifact_path: Path | None = None,
    output_root: Path | None = None,
) -> tuple[Path | None, dict[str, Any] | None]:
    if retention_handoff_artifact_path is not None:
        path = retention_handoff_artifact_path.expanduser().resolve()
        return path, _safe_read_json(path)
    root = _paper_broker_root(output_root=output_root)
    candidates = list(root.glob("*/evidence_bundle_retention_handoffs/*.json"))
    history_tracking_ids = {path.parent.parent.name for path in candidates if path.parent.parent.name}
    for latest_path in root.glob("*/paper_execution_evidence_bundle_retention_handoff.json"):
        if latest_path.parent.name not in history_tracking_ids:
            candidates.append(latest_path)
    if not candidates:
        return None, None
    path = sorted(candidates, key=_mtime, reverse=True)[0]
    return path, _safe_read_json(path)


def _handoff_statement_digest(handoff_raw: dict[str, Any]) -> str | None:
    if not handoff_raw:
        return None
    statement = {
        "schema_version": "paper_execution_evidence_bundle_retention_handoff_statement/v1",
        "custodian_id": str(handoff_raw.get("custodian_id") or "operator").strip() or "operator",
        "handoff_note": str(handoff_raw.get("handoff_note") or "").strip() or None,
        "source_retention_signoff_verification_artifact_sha256": str(handoff_raw.get("source_retention_signoff_verification_declared_sha256") or "").strip() or None,
        "source_retention_signoff_verification_computed_sha256": str(handoff_raw.get("source_retention_signoff_verification_computed_sha256") or "").strip() or None,
        "source_retention_signoff_verification_status": str(handoff_raw.get("source_retention_signoff_verification_status") or "UNKNOWN"),
        "source_retention_signoff_verification_trust_banner": str(handoff_raw.get("source_retention_signoff_verification_trust_banner") or "TRUST_RESTRICTED"),
        "source_retention_signoff_artifact_path": str(handoff_raw.get("source_retention_signoff_artifact_path") or "").strip() or None,
        "source_retention_verification_artifact_path": str(handoff_raw.get("source_retention_verification_artifact_path") or "").strip() or None,
        "source_retention_receipt_artifact_path": str(handoff_raw.get("source_retention_receipt_artifact_path") or "").strip() or None,
        "source_retention_index_sha256": str(handoff_raw.get("source_retention_index_sha256") or "").strip() or None,
        "recomputed_retention_entry_count": _int(handoff_raw.get("recomputed_retention_entry_count")),
        "recomputed_retention_ready_entry_count": _int(handoff_raw.get("recomputed_retention_ready_entry_count")),
        "checklist": _strings(handoff_raw.get("checklist")),
    }
    return canonical_json_sha256(statement)


def build_paper_execution_evidence_bundle_retention_handoff_verification_artifact(
    *,
    retention_handoff_artifact_path: Path,
    retention_handoff_raw: dict[str, Any],
    generated_at_utc: datetime | None = None,
) -> PaperExecutionEvidenceBundleRetentionHandoffVerificationArtifact:
    now = generated_at_utc or datetime.now(timezone.utc)
    blockers: list[str] = []
    warnings: list[str] = []

    declared_handoff_sha = str(retention_handoff_raw.get("artifact_sha256") or "").strip() or None
    computed_handoff_sha = _embedded_digest(retention_handoff_raw)
    handoff_hash_valid = _declared_matches_computed(declared_handoff_sha, computed_handoff_sha)
    if not retention_handoff_raw:
        blockers.append("RETENTION_HANDOFF_ARTIFACT_MISSING_OR_UNREADABLE")
    elif not handoff_hash_valid:
        blockers.append("RETENTION_HANDOFF_ARTIFACT_SHA256_MISMATCH")

    handoff_status = str(retention_handoff_raw.get("handoff_status") or "UNKNOWN")
    handoff_trust = str(retention_handoff_raw.get("trust_banner") or "TRUST_RESTRICTED")
    if handoff_status == "BLOCKED":
        blockers.append("RETENTION_HANDOFF_STATUS_BLOCKED")
    elif handoff_status != "READY_FOR_HANDOFF":
        warnings.append("RETENTION_HANDOFF_STATUS_NOT_READY_FOR_HANDOFF")
    if handoff_trust != "TRUSTED":
        warnings.append("RETENTION_HANDOFF_TRUST_NOT_TRUSTED")

    declared_statement_sha = str(retention_handoff_raw.get("handoff_statement_sha256") or "").strip() or None
    computed_statement_sha = _handoff_statement_digest(retention_handoff_raw)
    statement_hash_valid = _declared_matches_computed(declared_statement_sha, computed_statement_sha)
    if not statement_hash_valid:
        blockers.append("RETENTION_HANDOFF_STATEMENT_SHA256_MISMATCH")

    source_path_raw = str(retention_handoff_raw.get("source_retention_signoff_verification_artifact_path") or "").strip()
    source_path = Path(source_path_raw).expanduser() if source_path_raw else None
    source_raw = _safe_read_json(source_path) if source_path is not None else None
    if source_path is None or source_raw is None:
        blockers.append("SOURCE_RETENTION_SIGNOFF_VERIFICATION_ARTIFACT_MISSING_OR_UNREADABLE")

    source_declared = str((source_raw or {}).get("artifact_sha256") or "").strip() or None
    source_recomputed = _embedded_digest(source_raw or {})
    handoff_declared_source = str(retention_handoff_raw.get("source_retention_signoff_verification_declared_sha256") or "").strip() or None
    handoff_computed_source = str(retention_handoff_raw.get("source_retention_signoff_verification_computed_sha256") or "").strip() or None
    source_hash_valid = False
    if source_raw:
        source_hash_valid = (
            _declared_matches_computed(source_declared, source_recomputed)
            and _declared_matches_computed(handoff_declared_source, source_recomputed)
            and _declared_matches_computed(handoff_computed_source, source_recomputed)
        )
    if not source_hash_valid:
        blockers.append("SOURCE_RETENTION_SIGNOFF_VERIFICATION_ARTIFACT_SHA256_MISMATCH")

    source_status = str((source_raw or {}).get("verification_status") or retention_handoff_raw.get("source_retention_signoff_verification_status") or "UNKNOWN")
    source_trust = str((source_raw or {}).get("trust_banner") or retention_handoff_raw.get("source_retention_signoff_verification_trust_banner") or "TRUST_RESTRICTED")
    if source_status != "PASS":
        blockers.append("SOURCE_RETENTION_SIGNOFF_VERIFICATION_NOT_PASS")
    if source_trust != "TRUSTED":
        warnings.append("SOURCE_RETENTION_SIGNOFF_VERIFICATION_TRUST_NOT_TRUSTED")

    for field, code in [
        ("retention_signoff_verification_artifact_hash_valid", "RETENTION_HANDOFF_DECLARED_SIGNOFF_VERIFICATION_HASH_INVALID"),
        ("retention_signoff_artifact_hash_valid", "RETENTION_HANDOFF_DECLARED_SIGNOFF_HASH_INVALID"),
        ("signoff_statement_hash_valid", "RETENTION_HANDOFF_DECLARED_SIGNOFF_STATEMENT_HASH_INVALID"),
        ("retention_verification_artifact_hash_valid", "RETENTION_HANDOFF_DECLARED_RETENTION_VERIFICATION_HASH_INVALID"),
    ]:
        if not bool(retention_handoff_raw.get(field)):
            blockers.append(code)

    entry_count = _int(retention_handoff_raw.get("recomputed_retention_entry_count"))
    ready_count = _int(retention_handoff_raw.get("recomputed_retention_ready_entry_count"))
    missing_count = _int(retention_handoff_raw.get("missing_entry_count"))
    mismatch_count = _int(retention_handoff_raw.get("digest_mismatch_entry_count"))
    if source_raw:
        if entry_count != _int(source_raw.get("recomputed_retention_entry_count")):
            blockers.append("RETENTION_HANDOFF_ENTRY_COUNT_SOURCE_MISMATCH")
        if ready_count != _int(source_raw.get("recomputed_retention_ready_entry_count")):
            blockers.append("RETENTION_HANDOFF_READY_ENTRY_COUNT_SOURCE_MISMATCH")
        if missing_count != _int(source_raw.get("missing_entry_count")):
            blockers.append("RETENTION_HANDOFF_MISSING_ENTRY_COUNT_SOURCE_MISMATCH")
        if mismatch_count != _int(source_raw.get("digest_mismatch_entry_count")):
            blockers.append("RETENTION_HANDOFF_DIGEST_MISMATCH_COUNT_SOURCE_MISMATCH")
    if entry_count <= 0:
        blockers.append("RETENTION_HANDOFF_HAS_NO_ENTRIES")
    if entry_count != ready_count:
        blockers.append("RETENTION_HANDOFF_NOT_ALL_ENTRIES_READY")
    if missing_count:
        blockers.append("RETENTION_HANDOFF_HAS_MISSING_ENTRIES")
    if mismatch_count:
        blockers.append("RETENTION_HANDOFF_HAS_DIGEST_MISMATCHES")

    for item in _strings(retention_handoff_raw.get("blockers")):
        blockers.append(f"SOURCE_RETENTION_HANDOFF_BLOCKER:{item}")
    for item in _strings(retention_handoff_raw.get("warnings")):
        warnings.append(f"SOURCE_RETENTION_HANDOFF_WARNING:{item}")

    blockers = sorted(set(blockers))
    warnings = sorted(set(warnings))
    status = "FAIL" if blockers else "PASS"
    trust = "TRUSTED" if status == "PASS" and not warnings else ("TRUST_RESTRICTED" if status == "PASS" else "UNTRUSTED")

    artifact = PaperExecutionEvidenceBundleRetentionHandoffVerificationArtifact(
        generated_at_utc=now,
        tracking_id=str(retention_handoff_raw.get("tracking_id") or "").strip() or None,
        verification_status=status,  # type: ignore[arg-type]
        trust_banner=trust,  # type: ignore[arg-type]
        source_retention_handoff_artifact_path=str(retention_handoff_artifact_path),
        source_retention_handoff_declared_sha256=declared_handoff_sha,
        source_retention_handoff_computed_sha256=computed_handoff_sha,
        source_retention_handoff_status=handoff_status,
        source_retention_handoff_trust_banner=handoff_trust,
        retention_handoff_artifact_hash_valid=handoff_hash_valid,
        custodian_id=str(retention_handoff_raw.get("custodian_id") or "").strip() or None,
        handoff_note=str(retention_handoff_raw.get("handoff_note") or "").strip() or None,
        handoff_statement_declared_sha256=declared_statement_sha,
        handoff_statement_computed_sha256=computed_statement_sha,
        handoff_statement_hash_valid=statement_hash_valid,
        source_retention_signoff_verification_artifact_path=source_path_raw or None,
        source_retention_signoff_verification_declared_sha256=handoff_declared_source,
        source_retention_signoff_verification_computed_sha256=handoff_computed_source,
        source_retention_signoff_verification_recomputed_sha256=source_recomputed,
        source_retention_signoff_verification_status=source_status,
        source_retention_signoff_verification_trust_banner=source_trust,
        retention_signoff_verification_artifact_hash_valid=source_hash_valid,
        retention_signoff_artifact_hash_valid=bool(retention_handoff_raw.get("retention_signoff_artifact_hash_valid")),
        signoff_statement_hash_valid=bool(retention_handoff_raw.get("signoff_statement_hash_valid")),
        retention_verification_artifact_hash_valid=bool(retention_handoff_raw.get("retention_verification_artifact_hash_valid")),
        source_retention_receipt_artifact_path=str(retention_handoff_raw.get("source_retention_receipt_artifact_path") or "").strip() or None,
        source_retention_receipt_status=str(retention_handoff_raw.get("source_retention_receipt_status") or "").strip() or None,
        source_retention_index_sha256=str(retention_handoff_raw.get("source_retention_index_sha256") or "").strip() or None,
        recomputed_retention_entry_count=entry_count,
        recomputed_retention_ready_entry_count=ready_count,
        missing_entry_count=missing_count,
        digest_mismatch_entry_count=mismatch_count,
        blockers=blockers,
        warnings=warnings,
    )
    return artifact.model_copy(update={"artifact_sha256": canonical_json_sha256(artifact.model_dump(mode="json", exclude={"artifact_sha256"}))})


def write_paper_execution_evidence_bundle_retention_handoff_verification_artifact(
    *,
    retention_handoff_artifact_path: Path | None = None,
    output_root: Path | None = None,
    generated_at_utc: datetime | None = None,
) -> tuple[Path, Path, PaperExecutionEvidenceBundleRetentionHandoffVerificationArtifact]:
    source_path, raw = find_latest_paper_execution_evidence_bundle_retention_handoff_artifact(
        retention_handoff_artifact_path=retention_handoff_artifact_path,
        output_root=output_root,
    )
    if source_path is None or raw is None:
        source_path = (retention_handoff_artifact_path or (_paper_broker_root(output_root=output_root) / "untracked" / "paper_execution_evidence_bundle_retention_handoff.json")).expanduser().resolve()
        raw = {}
    artifact = build_paper_execution_evidence_bundle_retention_handoff_verification_artifact(
        retention_handoff_artifact_path=source_path,
        retention_handoff_raw=raw,
        generated_at_utc=generated_at_utc,
    )
    tracking_id = artifact.tracking_id or "untracked"
    root = _paper_broker_root(output_root=output_root) / tracking_id
    history_dir = root / "evidence_bundle_retention_handoff_verifications"
    history_dir.mkdir(parents=True, exist_ok=True)
    latest_path = root / "paper_execution_evidence_bundle_retention_handoff_verification.json"
    history_path = history_dir / f"{_safe_timestamp(artifact.generated_at_utc)}_{artifact.artifact_sha256[:12]}.json"
    body = json.dumps(artifact.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
    history_path.write_text(body, encoding="utf-8")
    latest_path.write_text(body, encoding="utf-8")
    return latest_path, history_path, artifact


def _view_from_raw(path: Path, raw: dict[str, Any]) -> PaperExecutionEvidenceBundleRetentionHandoffVerificationView:
    blockers = _strings(raw.get("blockers"))
    warnings = _strings(raw.get("warnings"))
    return PaperExecutionEvidenceBundleRetentionHandoffVerificationView(
        tracking_id=str(raw.get("tracking_id") or "").strip() or None,
        artifact_path=str(path),
        artifact_sha256=str(raw.get("artifact_sha256") or canonical_json_sha256(raw)) or None,
        generated_at_utc=str(raw.get("generated_at_utc") or "").strip() or None,
        verification_status=str(raw.get("verification_status") or "UNKNOWN"),  # type: ignore[arg-type]
        trust_banner=str(raw.get("trust_banner") or "TRUST_RESTRICTED"),  # type: ignore[arg-type]
        source_retention_handoff_artifact_path=str(raw.get("source_retention_handoff_artifact_path") or "").strip() or None,
        source_retention_handoff_declared_sha256=str(raw.get("source_retention_handoff_declared_sha256") or "").strip() or None,
        source_retention_handoff_computed_sha256=str(raw.get("source_retention_handoff_computed_sha256") or "").strip() or None,
        source_retention_handoff_status=str(raw.get("source_retention_handoff_status") or "").strip() or None,
        source_retention_handoff_trust_banner=str(raw.get("source_retention_handoff_trust_banner") or "").strip() or None,
        retention_handoff_artifact_hash_valid=bool(raw.get("retention_handoff_artifact_hash_valid")),
        custodian_id=str(raw.get("custodian_id") or "").strip() or None,
        handoff_note=str(raw.get("handoff_note") or "").strip() or None,
        handoff_statement_declared_sha256=str(raw.get("handoff_statement_declared_sha256") or "").strip() or None,
        handoff_statement_computed_sha256=str(raw.get("handoff_statement_computed_sha256") or "").strip() or None,
        handoff_statement_hash_valid=bool(raw.get("handoff_statement_hash_valid")),
        source_retention_signoff_verification_artifact_path=str(raw.get("source_retention_signoff_verification_artifact_path") or "").strip() or None,
        source_retention_signoff_verification_declared_sha256=str(raw.get("source_retention_signoff_verification_declared_sha256") or "").strip() or None,
        source_retention_signoff_verification_status=str(raw.get("source_retention_signoff_verification_status") or "").strip() or None,
        source_retention_signoff_verification_trust_banner=str(raw.get("source_retention_signoff_verification_trust_banner") or "").strip() or None,
        retention_signoff_verification_artifact_hash_valid=bool(raw.get("retention_signoff_verification_artifact_hash_valid")),
        retention_signoff_artifact_hash_valid=bool(raw.get("retention_signoff_artifact_hash_valid")),
        signoff_statement_hash_valid=bool(raw.get("signoff_statement_hash_valid")),
        retention_verification_artifact_hash_valid=bool(raw.get("retention_verification_artifact_hash_valid")),
        source_retention_receipt_artifact_path=str(raw.get("source_retention_receipt_artifact_path") or "").strip() or None,
        source_retention_receipt_status=str(raw.get("source_retention_receipt_status") or "").strip() or None,
        source_retention_index_sha256=str(raw.get("source_retention_index_sha256") or "").strip() or None,
        recomputed_retention_entry_count=_int(raw.get("recomputed_retention_entry_count")),
        recomputed_retention_ready_entry_count=_int(raw.get("recomputed_retention_ready_entry_count")),
        missing_entry_count=_int(raw.get("missing_entry_count")),
        digest_mismatch_entry_count=_int(raw.get("digest_mismatch_entry_count")),
        blocker_count=len(blockers),
        warning_count=len(warnings),
        blockers=blockers,
        warnings=warnings,
    )


def read_paper_execution_evidence_bundle_retention_handoff_verification_views(
    *,
    repo_root: Path | None = None,
    output_root: Path | None = None,
    limit: int = 100,
) -> list[PaperExecutionEvidenceBundleRetentionHandoffVerificationView]:
    root = _paper_broker_root(repo_root=repo_root, output_root=output_root)
    if not root.is_dir():
        return []
    candidates = list(root.glob("*/evidence_bundle_retention_handoff_verifications/*.json"))
    history_tracking_ids = {path.parent.parent.name for path in candidates if path.parent.parent.name}
    for latest_path in root.glob("*/paper_execution_evidence_bundle_retention_handoff_verification.json"):
        if latest_path.parent.name not in history_tracking_ids:
            candidates.append(latest_path)
    rows: list[PaperExecutionEvidenceBundleRetentionHandoffVerificationView] = []
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
    "build_paper_execution_evidence_bundle_retention_handoff_verification_artifact",
    "find_latest_paper_execution_evidence_bundle_retention_handoff_artifact",
    "read_paper_execution_evidence_bundle_retention_handoff_verification_views",
    "write_paper_execution_evidence_bundle_retention_handoff_verification_artifact",
]
