"""Keyless local attestation envelopes for paper execution evidence bundles.

This module deliberately implements a DSSE-style stub envelope: it binds a
verified, in-sync paper execution evidence bundle to a structured attestation
artifact without using private keys or external signing infrastructure. It is a
paper-only, CLI evidence step; it never submits orders, calls broker mutation
endpoints, promotes strategies, or mutates the adjudication ledger.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.paper_execution_evidence_bundle import _paper_broker_root, _safe_timestamp, read_paper_execution_evidence_bundle_views
from strategy_validator.application.paper_execution_evidence_bundle_drift import read_paper_execution_evidence_bundle_drift_views
from strategy_validator.application.paper_execution_evidence_bundle_verification import read_paper_execution_evidence_bundle_verification_views
from strategy_validator.contracts.paper_execution import (
    PaperExecutionEvidenceBundleAttestationArtifact,
    PaperExecutionEvidenceBundleAttestationView,
    PaperExecutionEvidenceBundleDriftView,
    PaperExecutionEvidenceBundleVerificationView,
    PaperExecutionEvidenceBundleView,
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


def _latest_verification_for_bundle_sha(rows: list[PaperExecutionEvidenceBundleVerificationView], bundle_sha: str | None) -> PaperExecutionEvidenceBundleVerificationView | None:
    if not rows:
        return None
    if bundle_sha:
        for row in rows:
            if row.source_bundle_declared_sha256 == bundle_sha or row.source_bundle_computed_sha256 == bundle_sha:
                return row
    return rows[0]


def _latest_drift_for_bundle_sha(rows: list[PaperExecutionEvidenceBundleDriftView], bundle_sha: str | None) -> PaperExecutionEvidenceBundleDriftView | None:
    if not rows:
        return None
    if bundle_sha:
        for row in rows:
            if row.source_bundle_sha256 == bundle_sha:
                return row
    return rows[0]


def _attestation_posture(*, bundle: PaperExecutionEvidenceBundleView | None, verification: PaperExecutionEvidenceBundleVerificationView | None, drift: PaperExecutionEvidenceBundleDriftView | None) -> tuple[str, str, list[str], list[str]]:
    blockers: list[str] = []
    warnings: list[str] = []
    if bundle is None:
        blockers.append("PAPER_EXECUTION_EVIDENCE_BUNDLE_MISSING")
    else:
        if bundle.bundle_status == "SEALED_BLOCKED":
            blockers.append("PAPER_EXECUTION_EVIDENCE_BUNDLE_SEALED_BLOCKED")
        if bundle.bundle_status == "SEALED_RESTRICTED":
            warnings.append("PAPER_EXECUTION_EVIDENCE_BUNDLE_SEALED_RESTRICTED")
        if bundle.trust_banner == "TRUST_RESTRICTED":
            warnings.append("PAPER_EXECUTION_EVIDENCE_BUNDLE_TRUST_RESTRICTED")
        if bundle.trust_banner == "UNTRUSTED":
            blockers.append("PAPER_EXECUTION_EVIDENCE_BUNDLE_UNTRUSTED")
        blockers.extend(bundle.blockers)
        warnings.extend(bundle.warnings)
    if verification is None:
        blockers.append("PAPER_EXECUTION_EVIDENCE_BUNDLE_VERIFICATION_MISSING")
    elif verification.verification_status != "PASS":
        blockers.append("PAPER_EXECUTION_EVIDENCE_BUNDLE_VERIFICATION_NOT_PASS")
        blockers.extend(verification.blockers)
    else:
        warnings.extend(verification.warnings)
    if drift is None:
        blockers.append("PAPER_EXECUTION_EVIDENCE_BUNDLE_DRIFT_CHECK_MISSING")
    elif drift.drift_status != "IN_SYNC":
        blockers.append(f"PAPER_EXECUTION_EVIDENCE_BUNDLE_DRIFT_{drift.drift_status}")
        blockers.extend(drift.blockers)
    else:
        warnings.extend(drift.warnings)
    blockers = sorted(set(blockers))
    warnings = sorted(set(warnings))
    if blockers:
        return "BLOCKED", "UNTRUSTED", blockers, warnings
    if warnings:
        return "ATTESTED_RESTRICTED", "TRUST_RESTRICTED", [], warnings
    return "ATTESTED", "TRUSTED", [], []


def build_paper_execution_evidence_bundle_attestation_artifact(
    *,
    latest_evidence_bundle: PaperExecutionEvidenceBundleView | None,
    latest_evidence_bundle_verification: PaperExecutionEvidenceBundleVerificationView | None,
    latest_evidence_bundle_drift: PaperExecutionEvidenceBundleDriftView | None,
    signer_identity: str = "local-operator-keyless-stub",
    generated_at_utc: datetime | None = None,
) -> PaperExecutionEvidenceBundleAttestationArtifact:
    now = generated_at_utc or datetime.now(timezone.utc)
    status, trust, blockers, warnings = _attestation_posture(
        bundle=latest_evidence_bundle,
        verification=latest_evidence_bundle_verification,
        drift=latest_evidence_bundle_drift,
    )
    bundle_sha = latest_evidence_bundle.bundle_sha256 if latest_evidence_bundle else None
    verification_sha = latest_evidence_bundle_verification.artifact_sha256 if latest_evidence_bundle_verification else None
    drift_sha = latest_evidence_bundle_drift.artifact_sha256 if latest_evidence_bundle_drift else None
    statement = {
        "_type": "https://strategy-validator.local/Statement/v1",
        "predicateType": "https://strategy-validator.local/paper-execution-evidence-bundle/v1",
        "subject": [
            {
                "name": latest_evidence_bundle.artifact_path if latest_evidence_bundle else "NO_BUNDLE",
                "digest": {"sha256": bundle_sha or ""},
            }
        ],
        "predicate": {
            "paper_trading_only": True,
            "live_trading_blocked": True,
            "browser_orders_blocked": True,
            "attestation_mode": "KEYLESS_LOCAL_STUB",
            "attestation_status": status,
            "trust_banner": trust,
            "bundle_status": latest_evidence_bundle.bundle_status if latest_evidence_bundle else None,
            "verification_status": latest_evidence_bundle_verification.verification_status if latest_evidence_bundle_verification else None,
            "drift_status": latest_evidence_bundle_drift.drift_status if latest_evidence_bundle_drift else None,
            "verification_artifact_sha256": verification_sha,
            "drift_artifact_sha256": drift_sha,
        },
    }
    envelope = {
        "payload_type": "application/vnd.in-toto+json",
        "payload_sha256": canonical_json_sha256(statement),
        "signatures": [
            {
                "keyid": signer_identity,
                "sig": "KEYLESS_STUB_NO_PRIVATE_KEY",
                "signature_status": "UNSIGNED_KEYLESS_STUB",
            }
        ],
        "statement": statement,
    }
    artifact = PaperExecutionEvidenceBundleAttestationArtifact(
        generated_at_utc=now,
        tracking_id=latest_evidence_bundle.tracking_id if latest_evidence_bundle else None,
        attestation_status=status,  # type: ignore[arg-type]
        trust_banner=trust,  # type: ignore[arg-type]
        signer_identity=signer_identity,
        source_bundle_artifact_path=latest_evidence_bundle.artifact_path if latest_evidence_bundle else None,
        source_bundle_sha256=bundle_sha,
        source_bundle_status=latest_evidence_bundle.bundle_status if latest_evidence_bundle else None,
        source_verification_artifact_path=latest_evidence_bundle_verification.artifact_path if latest_evidence_bundle_verification else None,
        source_verification_artifact_sha256=verification_sha,
        source_verification_status=latest_evidence_bundle_verification.verification_status if latest_evidence_bundle_verification else None,
        source_drift_artifact_path=latest_evidence_bundle_drift.artifact_path if latest_evidence_bundle_drift else None,
        source_drift_artifact_sha256=drift_sha,
        source_drift_status=latest_evidence_bundle_drift.drift_status if latest_evidence_bundle_drift else None,
        statement_payload_sha256=envelope["payload_sha256"],
        envelope=envelope,
        blockers=blockers,
        warnings=warnings,
    )
    return artifact.model_copy(update={"artifact_sha256": canonical_json_sha256(artifact.model_dump(mode="json", exclude={"artifact_sha256"}))})


def write_paper_execution_evidence_bundle_attestation_artifact(
    *,
    output_root: Path | None = None,
    signer_identity: str = "local-operator-keyless-stub",
    generated_at_utc: datetime | None = None,
) -> tuple[Path, Path, PaperExecutionEvidenceBundleAttestationArtifact]:
    bundles = read_paper_execution_evidence_bundle_views(output_root=output_root)
    latest_bundle = bundles[0] if bundles else None
    bundle_sha = latest_bundle.bundle_sha256 if latest_bundle else None
    latest_verification = _latest_verification_for_bundle_sha(read_paper_execution_evidence_bundle_verification_views(output_root=output_root), bundle_sha)
    latest_drift = _latest_drift_for_bundle_sha(read_paper_execution_evidence_bundle_drift_views(output_root=output_root), bundle_sha)
    artifact = build_paper_execution_evidence_bundle_attestation_artifact(
        latest_evidence_bundle=latest_bundle,
        latest_evidence_bundle_verification=latest_verification,
        latest_evidence_bundle_drift=latest_drift,
        signer_identity=signer_identity,
        generated_at_utc=generated_at_utc,
    )
    tracking_id = artifact.tracking_id or (latest_bundle.tracking_id if latest_bundle else None) or "untracked"
    root = _paper_broker_root(output_root=output_root) / tracking_id
    history_dir = root / "evidence_bundle_attestations"
    history_dir.mkdir(parents=True, exist_ok=True)
    latest_path = root / "paper_execution_evidence_bundle_attestation.json"
    history_path = history_dir / f"{_safe_timestamp(artifact.generated_at_utc)}_{artifact.artifact_sha256[:12]}.json"
    body = json.dumps(artifact.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
    history_path.write_text(body, encoding="utf-8")
    latest_path.write_text(body, encoding="utf-8")
    return latest_path, history_path, artifact


def _view_from_raw(path: Path, raw: dict[str, Any]) -> PaperExecutionEvidenceBundleAttestationView:
    return PaperExecutionEvidenceBundleAttestationView(
        tracking_id=str(raw.get("tracking_id") or "") or None,
        artifact_path=str(path),
        artifact_sha256=str(raw.get("artifact_sha256") or canonical_json_sha256(raw)) or None,
        generated_at_utc=str(raw.get("generated_at_utc") or "") or None,
        attestation_status=str(raw.get("attestation_status") or "UNKNOWN"),  # type: ignore[arg-type]
        trust_banner=str(raw.get("trust_banner") or "TRUST_RESTRICTED"),  # type: ignore[arg-type]
        attestation_mode=str(raw.get("attestation_mode") or "KEYLESS_LOCAL_STUB"),
        signature_status=str(raw.get("signature_status") or "UNSIGNED_KEYLESS_STUB"),
        signer_identity=str(raw.get("signer_identity") or "") or None,
        source_bundle_sha256=str(raw.get("source_bundle_sha256") or "") or None,
        source_bundle_status=str(raw.get("source_bundle_status") or "") or None,
        source_verification_status=str(raw.get("source_verification_status") or "") or None,
        source_drift_status=str(raw.get("source_drift_status") or "") or None,
        statement_payload_sha256=str(raw.get("statement_payload_sha256") or "") or None,
        blocker_count=len(raw.get("blockers", [])) if isinstance(raw.get("blockers"), list) else 0,
        warning_count=len(raw.get("warnings", [])) if isinstance(raw.get("warnings"), list) else 0,
        blockers=[str(x) for x in raw.get("blockers", []) if x not in (None, "")] if isinstance(raw.get("blockers"), list) else [],
        warnings=[str(x) for x in raw.get("warnings", []) if x not in (None, "")] if isinstance(raw.get("warnings"), list) else [],
    )


def read_paper_execution_evidence_bundle_attestation_views(*, repo_root: Path | None = None, output_root: Path | None = None, limit: int = 100) -> list[PaperExecutionEvidenceBundleAttestationView]:
    root = _paper_broker_root(repo_root=repo_root, output_root=output_root)
    if not root.is_dir():
        return []
    candidates = list(root.glob("*/evidence_bundle_attestations/*.json"))
    history_tracking_ids = {path.parent.parent.name for path in candidates if path.parent.parent.name}
    for latest_path in root.glob("*/paper_execution_evidence_bundle_attestation.json"):
        if latest_path.parent.name not in history_tracking_ids:
            candidates.append(latest_path)
    rows: list[PaperExecutionEvidenceBundleAttestationView] = []
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
    "build_paper_execution_evidence_bundle_attestation_artifact",
    "read_paper_execution_evidence_bundle_attestation_views",
    "write_paper_execution_evidence_bundle_attestation_artifact",
]
