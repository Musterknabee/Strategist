"""Final closure packets for paper execution evidence bundles.

A closure packet is a read-only operator review artifact. It aggregates the
sealed bundle, bundle verification, drift check, keyless attestation, and
attestation verification posture into one final status. It never submits orders,
never grants execution authority, and never mutates the adjudication ledger.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.paper_execution_evidence_bundle import _paper_broker_root, _safe_timestamp, read_paper_execution_evidence_bundle_views
from strategy_validator.application.paper_execution_evidence_bundle_attestation import read_paper_execution_evidence_bundle_attestation_views
from strategy_validator.application.paper_execution_evidence_bundle_attestation_verification import read_paper_execution_evidence_bundle_attestation_verification_views
from strategy_validator.application.paper_execution_evidence_bundle_drift import read_paper_execution_evidence_bundle_drift_views
from strategy_validator.application.paper_execution_evidence_bundle_verification import read_paper_execution_evidence_bundle_verification_views
from strategy_validator.contracts.paper_execution import (
    PaperExecutionEvidenceBundleAttestationVerificationView,
    PaperExecutionEvidenceBundleAttestationView,
    PaperExecutionEvidenceBundleClosureArtifact,
    PaperExecutionEvidenceBundleClosureView,
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


def _latest_verification_for_bundle_sha(
    rows: list[PaperExecutionEvidenceBundleVerificationView],
    bundle_sha: str | None,
) -> PaperExecutionEvidenceBundleVerificationView | None:
    if not rows:
        return None
    if bundle_sha:
        for row in rows:
            if row.source_bundle_declared_sha256 == bundle_sha or row.source_bundle_computed_sha256 == bundle_sha:
                return row
    return rows[0]


def _latest_drift_for_bundle_sha(
    rows: list[PaperExecutionEvidenceBundleDriftView],
    bundle_sha: str | None,
) -> PaperExecutionEvidenceBundleDriftView | None:
    if not rows:
        return None
    if bundle_sha:
        for row in rows:
            if row.source_bundle_sha256 == bundle_sha:
                return row
    return rows[0]


def _latest_attestation_for_bundle_sha(
    rows: list[PaperExecutionEvidenceBundleAttestationView],
    bundle_sha: str | None,
) -> PaperExecutionEvidenceBundleAttestationView | None:
    if not rows:
        return None
    if bundle_sha:
        for row in rows:
            if row.source_bundle_sha256 == bundle_sha:
                return row
    return rows[0]


def _latest_attestation_verification_for_attestation_sha(
    rows: list[PaperExecutionEvidenceBundleAttestationVerificationView],
    attestation_sha: str | None,
) -> PaperExecutionEvidenceBundleAttestationVerificationView | None:
    if not rows:
        return None
    if attestation_sha:
        for row in rows:
            if row.source_attestation_declared_sha256 == attestation_sha or row.source_attestation_computed_sha256 == attestation_sha:
                return row
    return rows[0]


def _finish(artifact: PaperExecutionEvidenceBundleClosureArtifact) -> PaperExecutionEvidenceBundleClosureArtifact:
    plain = artifact.model_copy(
        update={
            "blockers": sorted(set(artifact.blockers)),
            "warnings": sorted(set(artifact.warnings)),
            "closure_reason_codes": sorted(set(artifact.closure_reason_codes)),
            "artifact_sha256": "",
        }
    )
    digest = canonical_json_sha256(plain.model_dump(mode="json", exclude={"artifact_sha256"}))
    return plain.model_copy(update={"artifact_sha256": digest})


def _closure_posture(
    *,
    bundle: PaperExecutionEvidenceBundleView | None,
    verification: PaperExecutionEvidenceBundleVerificationView | None,
    drift: PaperExecutionEvidenceBundleDriftView | None,
    attestation: PaperExecutionEvidenceBundleAttestationView | None,
    attestation_verification: PaperExecutionEvidenceBundleAttestationVerificationView | None,
) -> tuple[str, str, list[str], list[str], list[str], list[str]]:
    blockers: list[str] = []
    warnings: list[str] = []
    reasons: list[str] = []
    sequence: list[str] = []

    if bundle is None:
        blockers.append("PAPER_EXECUTION_EVIDENCE_BUNDLE_MISSING")
        reasons.append("NO_BUNDLE")
        sequence.append("Run strategy-validator-paper-broker seal-evidence-bundle.")
    else:
        if bundle.bundle_status == "SEALED_BLOCKED":
            blockers.append("PAPER_EXECUTION_EVIDENCE_BUNDLE_SEALED_BLOCKED")
            reasons.append("BUNDLE_BLOCKED")
        elif bundle.bundle_status == "SEALED_RESTRICTED":
            warnings.append("PAPER_EXECUTION_EVIDENCE_BUNDLE_SEALED_RESTRICTED")
            reasons.append("BUNDLE_RESTRICTED")
        if bundle.trust_banner == "UNTRUSTED":
            blockers.append("PAPER_EXECUTION_EVIDENCE_BUNDLE_UNTRUSTED")
            reasons.append("BUNDLE_UNTRUSTED")
        elif bundle.trust_banner == "TRUST_RESTRICTED":
            warnings.append("PAPER_EXECUTION_EVIDENCE_BUNDLE_TRUST_RESTRICTED")
            reasons.append("BUNDLE_TRUST_RESTRICTED")
        blockers.extend(bundle.blockers)
        warnings.extend(bundle.warnings)

    if verification is None:
        blockers.append("PAPER_EXECUTION_EVIDENCE_BUNDLE_VERIFICATION_MISSING")
        reasons.append("NO_BUNDLE_VERIFICATION")
        sequence.append("Run strategy-validator-paper-broker verify-evidence-bundle.")
    elif verification.verification_status != "PASS":
        blockers.append("PAPER_EXECUTION_EVIDENCE_BUNDLE_VERIFICATION_NOT_PASS")
        reasons.append("BUNDLE_VERIFICATION_FAILED")
        blockers.extend(verification.blockers)
    else:
        if verification.trust_banner == "TRUST_RESTRICTED":
            warnings.append("PAPER_EXECUTION_EVIDENCE_BUNDLE_VERIFICATION_RESTRICTED")
            reasons.append("BUNDLE_VERIFICATION_RESTRICTED")
        warnings.extend(verification.warnings)

    if drift is None:
        blockers.append("PAPER_EXECUTION_EVIDENCE_BUNDLE_DRIFT_CHECK_MISSING")
        reasons.append("NO_DRIFT_CHECK")
        sequence.append("Run strategy-validator-paper-broker check-evidence-bundle-drift.")
    elif drift.drift_status != "IN_SYNC":
        blockers.append(f"PAPER_EXECUTION_EVIDENCE_BUNDLE_DRIFT_{drift.drift_status}")
        reasons.append(f"BUNDLE_DRIFT_{drift.drift_status}")
        blockers.extend(drift.blockers)
        sequence.append("Run strategy-validator-paper-broker recommend-evidence-bundle-rotation, then run-evidence-bundle-rotation if recommended.")
    else:
        if drift.trust_banner == "TRUST_RESTRICTED":
            warnings.append("PAPER_EXECUTION_EVIDENCE_BUNDLE_DRIFT_RESTRICTED")
            reasons.append("BUNDLE_DRIFT_RESTRICTED")
        warnings.extend(drift.warnings)

    if attestation is None:
        blockers.append("PAPER_EXECUTION_EVIDENCE_BUNDLE_ATTESTATION_MISSING")
        reasons.append("NO_ATTESTATION")
        sequence.append("Run strategy-validator-paper-broker attest-evidence-bundle.")
    elif attestation.attestation_status == "BLOCKED":
        blockers.append("PAPER_EXECUTION_EVIDENCE_BUNDLE_ATTESTATION_BLOCKED")
        reasons.append("ATTESTATION_BLOCKED")
        blockers.extend(attestation.blockers)
    elif attestation.attestation_status == "ATTESTED_RESTRICTED":
        warnings.append("PAPER_EXECUTION_EVIDENCE_BUNDLE_ATTESTATION_RESTRICTED")
        reasons.append("ATTESTATION_RESTRICTED")
        warnings.extend(attestation.warnings)
    elif attestation.attestation_status != "ATTESTED":
        blockers.append("PAPER_EXECUTION_EVIDENCE_BUNDLE_ATTESTATION_NOT_ATTESTED")
        reasons.append("ATTESTATION_NOT_ATTESTED")
    else:
        if attestation.trust_banner == "TRUST_RESTRICTED":
            warnings.append("PAPER_EXECUTION_EVIDENCE_BUNDLE_ATTESTATION_TRUST_RESTRICTED")
            reasons.append("ATTESTATION_TRUST_RESTRICTED")
        warnings.extend(attestation.warnings)

    required_attestation_checks: list[tuple[str, bool]] = []
    if attestation_verification is None:
        blockers.append("PAPER_EXECUTION_EVIDENCE_BUNDLE_ATTESTATION_VERIFICATION_MISSING")
        reasons.append("NO_ATTESTATION_VERIFICATION")
        sequence.append("Run strategy-validator-paper-broker verify-evidence-bundle-attestation.")
    else:
        required_attestation_checks = [
            ("ATTESTATION_ARTIFACT_HASH_INVALID", attestation_verification.artifact_hash_valid),
            ("ATTESTATION_STATEMENT_HASH_INVALID", attestation_verification.statement_payload_hash_valid),
            ("ATTESTATION_ENVELOPE_HASH_INVALID", attestation_verification.envelope_payload_hash_valid),
            ("ATTESTATION_KEYLESS_STUB_INVALID", attestation_verification.keyless_stub_signature_valid),
            ("ATTESTATION_SOURCE_BUNDLE_HASH_INVALID", attestation_verification.source_bundle_hash_valid),
            ("ATTESTATION_SOURCE_VERIFICATION_HASH_INVALID", attestation_verification.source_verification_hash_valid),
            ("ATTESTATION_SOURCE_DRIFT_HASH_INVALID", attestation_verification.source_drift_hash_valid),
        ]
        if attestation_verification.verification_status != "PASS":
            blockers.append("PAPER_EXECUTION_EVIDENCE_BUNDLE_ATTESTATION_VERIFICATION_NOT_PASS")
            reasons.append("ATTESTATION_VERIFICATION_FAILED")
            blockers.extend(attestation_verification.blockers)
        for code, ok in required_attestation_checks:
            if not ok:
                blockers.append(f"PAPER_EXECUTION_EVIDENCE_BUNDLE_{code}")
                reasons.append(code)
        if attestation_verification.trust_banner == "TRUST_RESTRICTED":
            warnings.append("PAPER_EXECUTION_EVIDENCE_BUNDLE_ATTESTATION_VERIFICATION_RESTRICTED")
            reasons.append("ATTESTATION_VERIFICATION_RESTRICTED")
        warnings.extend(attestation_verification.warnings)

    blockers = sorted(set(blockers))
    warnings = sorted(set(warnings))
    if blockers:
        status = "BLOCKED"
        trust = "UNTRUSTED"
    elif warnings:
        status = "READY_RESTRICTED"
        trust = "TRUST_RESTRICTED"
        reasons.append("READY_WITH_RESTRICTIONS")
    else:
        status = "READY_FOR_OPERATOR_REVIEW"
        trust = "TRUSTED"
        reasons.append("READY_FOR_OPERATOR_REVIEW")
    if status in {"READY_FOR_OPERATOR_REVIEW", "READY_RESTRICTED"}:
        sequence.append("Review the closure packet, archive the evidence chain, and keep execution authority CLI-only/paper-only.")
    return status, trust, blockers, warnings, sorted(set(reasons)), list(dict.fromkeys(sequence))


def build_paper_execution_evidence_bundle_closure_artifact(
    *,
    latest_evidence_bundle: PaperExecutionEvidenceBundleView | None,
    latest_evidence_bundle_verification: PaperExecutionEvidenceBundleVerificationView | None,
    latest_evidence_bundle_drift: PaperExecutionEvidenceBundleDriftView | None,
    latest_evidence_bundle_attestation: PaperExecutionEvidenceBundleAttestationView | None,
    latest_evidence_bundle_attestation_verification: PaperExecutionEvidenceBundleAttestationVerificationView | None,
    generated_at_utc: datetime | None = None,
) -> PaperExecutionEvidenceBundleClosureArtifact:
    """Build a final paper evidence-bundle closure artifact."""

    now = generated_at_utc or datetime.now(timezone.utc)
    status, trust, blockers, warnings, reasons, sequence = _closure_posture(
        bundle=latest_evidence_bundle,
        verification=latest_evidence_bundle_verification,
        drift=latest_evidence_bundle_drift,
        attestation=latest_evidence_bundle_attestation,
        attestation_verification=latest_evidence_bundle_attestation_verification,
    )
    tracking_id = (
        getattr(latest_evidence_bundle, "tracking_id", None)
        or getattr(latest_evidence_bundle_attestation, "tracking_id", None)
        or getattr(latest_evidence_bundle_attestation_verification, "tracking_id", None)
    )
    artifact = PaperExecutionEvidenceBundleClosureArtifact(
        generated_at_utc=now,
        tracking_id=tracking_id,
        closure_status=status,  # type: ignore[arg-type]
        trust_banner=trust,  # type: ignore[arg-type]
        source_bundle_artifact_path=getattr(latest_evidence_bundle, "artifact_path", None),
        source_bundle_sha256=getattr(latest_evidence_bundle, "bundle_sha256", None),
        source_bundle_status=getattr(latest_evidence_bundle, "bundle_status", None),
        source_bundle_trust_banner=getattr(latest_evidence_bundle, "trust_banner", None),
        source_verification_artifact_path=getattr(latest_evidence_bundle_verification, "artifact_path", None),
        source_verification_artifact_sha256=getattr(latest_evidence_bundle_verification, "artifact_sha256", None),
        source_verification_status=getattr(latest_evidence_bundle_verification, "verification_status", None),
        source_verification_trust_banner=getattr(latest_evidence_bundle_verification, "trust_banner", None),
        source_drift_artifact_path=getattr(latest_evidence_bundle_drift, "artifact_path", None),
        source_drift_artifact_sha256=getattr(latest_evidence_bundle_drift, "artifact_sha256", None),
        source_drift_status=getattr(latest_evidence_bundle_drift, "drift_status", None),
        source_drift_trust_banner=getattr(latest_evidence_bundle_drift, "trust_banner", None),
        source_attestation_artifact_path=getattr(latest_evidence_bundle_attestation, "artifact_path", None),
        source_attestation_artifact_sha256=getattr(latest_evidence_bundle_attestation, "artifact_sha256", None),
        source_attestation_status=getattr(latest_evidence_bundle_attestation, "attestation_status", None),
        source_attestation_trust_banner=getattr(latest_evidence_bundle_attestation, "trust_banner", None),
        source_attestation_verification_artifact_path=getattr(latest_evidence_bundle_attestation_verification, "artifact_path", None),
        source_attestation_verification_artifact_sha256=getattr(latest_evidence_bundle_attestation_verification, "artifact_sha256", None),
        source_attestation_verification_status=getattr(latest_evidence_bundle_attestation_verification, "verification_status", None),
        source_attestation_verification_trust_banner=getattr(latest_evidence_bundle_attestation_verification, "trust_banner", None),
        source_attestation_artifact_hash_valid=bool(getattr(latest_evidence_bundle_attestation_verification, "artifact_hash_valid", False)),
        source_attestation_statement_hash_valid=bool(getattr(latest_evidence_bundle_attestation_verification, "statement_payload_hash_valid", False)),
        source_attestation_envelope_hash_valid=bool(getattr(latest_evidence_bundle_attestation_verification, "envelope_payload_hash_valid", False)),
        source_attestation_keyless_stub_valid=bool(getattr(latest_evidence_bundle_attestation_verification, "keyless_stub_signature_valid", False)),
        source_attestation_bundle_hash_valid=bool(getattr(latest_evidence_bundle_attestation_verification, "source_bundle_hash_valid", False)),
        source_attestation_bundle_verification_hash_valid=bool(getattr(latest_evidence_bundle_attestation_verification, "source_verification_hash_valid", False)),
        source_attestation_drift_hash_valid=bool(getattr(latest_evidence_bundle_attestation_verification, "source_drift_hash_valid", False)),
        closure_reason_codes=reasons,
        recommended_operator_sequence=sequence,
        one_command_sequence_hint="strategy-validator-paper-broker close-evidence-bundle",
        blockers=blockers,
        warnings=warnings,
    )
    return _finish(artifact)


def _view_from_artifact(artifact: PaperExecutionEvidenceBundleClosureArtifact, *, artifact_path: str) -> PaperExecutionEvidenceBundleClosureView:
    return PaperExecutionEvidenceBundleClosureView(
        tracking_id=artifact.tracking_id,
        artifact_path=artifact_path,
        artifact_sha256=artifact.artifact_sha256,
        generated_at_utc=artifact.generated_at_utc.isoformat(),
        closure_status=artifact.closure_status,
        trust_banner=artifact.trust_banner,
        source_bundle_sha256=artifact.source_bundle_sha256,
        source_bundle_status=artifact.source_bundle_status,
        source_verification_status=artifact.source_verification_status,
        source_drift_status=artifact.source_drift_status,
        source_attestation_status=artifact.source_attestation_status,
        source_attestation_verification_status=artifact.source_attestation_verification_status,
        source_attestation_artifact_hash_valid=artifact.source_attestation_artifact_hash_valid,
        source_attestation_statement_hash_valid=artifact.source_attestation_statement_hash_valid,
        source_attestation_envelope_hash_valid=artifact.source_attestation_envelope_hash_valid,
        source_attestation_keyless_stub_valid=artifact.source_attestation_keyless_stub_valid,
        source_attestation_bundle_hash_valid=artifact.source_attestation_bundle_hash_valid,
        source_attestation_bundle_verification_hash_valid=artifact.source_attestation_bundle_verification_hash_valid,
        source_attestation_drift_hash_valid=artifact.source_attestation_drift_hash_valid,
        closure_reason_codes=artifact.closure_reason_codes,
        recommended_operator_sequence=artifact.recommended_operator_sequence,
        one_command_sequence_hint=artifact.one_command_sequence_hint,
        blocker_count=len(artifact.blockers),
        warning_count=len(artifact.warnings),
        blockers=artifact.blockers,
        warnings=artifact.warnings,
    )


def _view_from_raw(path: Path, raw: dict[str, Any]) -> PaperExecutionEvidenceBundleClosureView:
    return PaperExecutionEvidenceBundleClosureView(
        tracking_id=str(raw.get("tracking_id") or "") or None,
        artifact_path=str(path),
        artifact_sha256=str(raw.get("artifact_sha256") or canonical_json_sha256(raw)) or None,
        generated_at_utc=str(raw.get("generated_at_utc") or "") or None,
        closure_status=str(raw.get("closure_status") or "UNKNOWN"),  # type: ignore[arg-type]
        trust_banner=str(raw.get("trust_banner") or "TRUST_RESTRICTED"),  # type: ignore[arg-type]
        source_bundle_sha256=str(raw.get("source_bundle_sha256") or "") or None,
        source_bundle_status=str(raw.get("source_bundle_status") or "") or None,
        source_verification_status=str(raw.get("source_verification_status") or "") or None,
        source_drift_status=str(raw.get("source_drift_status") or "") or None,
        source_attestation_status=str(raw.get("source_attestation_status") or "") or None,
        source_attestation_verification_status=str(raw.get("source_attestation_verification_status") or "") or None,
        source_attestation_artifact_hash_valid=bool(raw.get("source_attestation_artifact_hash_valid")),
        source_attestation_statement_hash_valid=bool(raw.get("source_attestation_statement_hash_valid")),
        source_attestation_envelope_hash_valid=bool(raw.get("source_attestation_envelope_hash_valid")),
        source_attestation_keyless_stub_valid=bool(raw.get("source_attestation_keyless_stub_valid")),
        source_attestation_bundle_hash_valid=bool(raw.get("source_attestation_bundle_hash_valid")),
        source_attestation_bundle_verification_hash_valid=bool(raw.get("source_attestation_bundle_verification_hash_valid")),
        source_attestation_drift_hash_valid=bool(raw.get("source_attestation_drift_hash_valid")),
        closure_reason_codes=[str(x) for x in raw.get("closure_reason_codes", []) if x not in (None, "")] if isinstance(raw.get("closure_reason_codes"), list) else [],
        recommended_operator_sequence=[str(x) for x in raw.get("recommended_operator_sequence", []) if x not in (None, "")] if isinstance(raw.get("recommended_operator_sequence"), list) else [],
        one_command_sequence_hint=str(raw.get("one_command_sequence_hint") or "") or None,
        blocker_count=len(raw.get("blockers", [])) if isinstance(raw.get("blockers"), list) else 0,
        warning_count=len(raw.get("warnings", [])) if isinstance(raw.get("warnings"), list) else 0,
        blockers=[str(x) for x in raw.get("blockers", []) if x not in (None, "")] if isinstance(raw.get("blockers"), list) else [],
        warnings=[str(x) for x in raw.get("warnings", []) if x not in (None, "")] if isinstance(raw.get("warnings"), list) else [],
    )


def write_paper_execution_evidence_bundle_closure_artifact(
    *,
    output_root: Path | None = None,
    generated_at_utc: datetime | None = None,
) -> tuple[Path, Path, PaperExecutionEvidenceBundleClosureArtifact]:
    """Write the latest paper evidence-bundle closure packet to latest + history."""

    bundles = read_paper_execution_evidence_bundle_views(output_root=output_root)
    latest_bundle = bundles[0] if bundles else None
    bundle_sha = latest_bundle.bundle_sha256 if latest_bundle else None
    latest_verification = _latest_verification_for_bundle_sha(read_paper_execution_evidence_bundle_verification_views(output_root=output_root), bundle_sha)
    latest_drift = _latest_drift_for_bundle_sha(read_paper_execution_evidence_bundle_drift_views(output_root=output_root), bundle_sha)
    latest_attestation = _latest_attestation_for_bundle_sha(read_paper_execution_evidence_bundle_attestation_views(output_root=output_root), bundle_sha)
    latest_attestation_verification = _latest_attestation_verification_for_attestation_sha(
        read_paper_execution_evidence_bundle_attestation_verification_views(output_root=output_root),
        latest_attestation.artifact_sha256 if latest_attestation else None,
    )
    artifact = build_paper_execution_evidence_bundle_closure_artifact(
        latest_evidence_bundle=latest_bundle,
        latest_evidence_bundle_verification=latest_verification,
        latest_evidence_bundle_drift=latest_drift,
        latest_evidence_bundle_attestation=latest_attestation,
        latest_evidence_bundle_attestation_verification=latest_attestation_verification,
        generated_at_utc=generated_at_utc,
    )
    tracking_id = artifact.tracking_id or (latest_bundle.tracking_id if latest_bundle else None) or "untracked"
    root = _paper_broker_root(output_root=output_root) / tracking_id
    history_dir = root / "evidence_bundle_closures"
    history_dir.mkdir(parents=True, exist_ok=True)
    latest_path = root / "paper_execution_evidence_bundle_closure.json"
    history_path = history_dir / f"{_safe_timestamp(artifact.generated_at_utc)}_{artifact.artifact_sha256[:12]}.json"
    body = json.dumps(artifact.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
    history_path.write_text(body, encoding="utf-8")
    latest_path.write_text(body, encoding="utf-8")
    return latest_path, history_path, artifact


def read_paper_execution_evidence_bundle_closure_views(
    *,
    repo_root: Path | None = None,
    output_root: Path | None = None,
    limit: int = 100,
) -> list[PaperExecutionEvidenceBundleClosureView]:
    root = _paper_broker_root(repo_root=repo_root, output_root=output_root)
    if not root.is_dir():
        return []
    candidates = list(root.glob("*/evidence_bundle_closures/*.json"))
    history_tracking_ids = {path.parent.parent.name for path in candidates if path.parent.parent.name}
    for latest_path in root.glob("*/paper_execution_evidence_bundle_closure.json"):
        if latest_path.parent.name not in history_tracking_ids:
            candidates.append(latest_path)
    rows: list[PaperExecutionEvidenceBundleClosureView] = []
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
    "build_paper_execution_evidence_bundle_closure_artifact",
    "read_paper_execution_evidence_bundle_closure_views",
    "write_paper_execution_evidence_bundle_closure_artifact",
    "_view_from_artifact",
]
