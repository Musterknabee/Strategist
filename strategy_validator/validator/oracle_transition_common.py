from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from strategy_validator.contracts.operational import DsseEnvelope
from strategy_validator.contracts.oracle import (
    OracleDoctrineDriftEvidenceManifest,
    OracleDoctrineDriftEvidenceVerification,
    OracleDoctrineDriftReport,
    OracleDoctrineLaneEntry,
    OracleDoctrineMemoryClassification,
    OracleSemiannualAuditClassification,
    OracleSemiannualAuditEvidenceManifest,
    OracleSemiannualAuditEvidenceVerification,
    OracleSemiannualLaneEntry,
    OracleAnnualReviewClassification,
    OracleAnnualReviewEvidenceManifest,
    OracleAnnualReviewEvidenceVerification,
    OracleAnnualLaneEntry,
    OracleAnnualReviewReport,
    OracleConstitutionalDigestClassification,
    OracleConstitutionalDigestEvidenceManifest,
    OracleConstitutionalDigestEvidenceVerification,
    OracleConstitutionalDigestReport,
    OracleConstitutionalGateReport,
    OracleConstitutionalLaneEntry,
    OracleDoctrineLineageIndex,
    OracleDoctrineLineageVerification,
    OracleDriftLevel,
    OracleEvidenceManifest,
    OracleEvidenceVerification,
    OracleMemoryLaneEntry,
    OracleMemoryLaneSummary,
    OracleMemoryReviewEvidenceManifest,
    OracleMemoryReviewEvidenceVerification,
    OracleMemoryReviewReport,
    OracleMonthlyDigestEvidenceManifest,
    OracleMonthlyDigestEvidenceVerification,
    OracleMonthlyDigestReport,
    OracleMonthlyLaneEntry,
    OracleMorningAttestation,
    OracleQuarterlyLaneEntry,
    OracleQuarterlyReviewEvidenceManifest,
    OracleQuarterlyReviewEvidenceVerification,
    OracleQuarterlyReviewReport,
    OracleSemiannualAuditReport,
    OracleRegimeTransition,
    OracleReviewLaneEntry,
    OracleStateTransitionReport,
    OracleTransitionEvidenceManifest,
    OracleTransitionEvidenceVerification,
    OracleWeeklyDigestEvidenceManifest,
    OracleWeeklyDigestEvidenceVerification,
    OracleWeeklyDigestReport,
    StrategyAdvisory,
    StrategyAdvisoryTransition,
)
from strategy_validator.validator.oracle_advisory import (
    _artifact_descriptor,
    _json_canonical_bytes,
    _resolve_existing_path as advisory_resolve_existing_path,
    _sha256_bytes,
    _sha256_file,
    _sign_dsse_payload,
    _utc_now as advisory_utc_now,
    _verify_dsse_envelope,
    verify_oracle_evidence_bundle,
)
from strategy_validator.validator.oracle_evidence_common import (
    assemble_evidence_subjects,
    build_evidence_verification,
    build_signed_evidence_manifest,
    collect_evidence_subjects,
    sign_manifest_envelope,
    verify_evidence_bundle,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _advisory_rank(action: str) -> int:
    return {
        "MAINTAIN": 0,
        "CANARY": 1,
        "HIBERNATE": 2,
    }[action]


def _global_action_rank(action: str) -> int:
    return {
        "OBSERVE": 0,
        "CANARY_REVIEW": 1,
        "DEFENSIVE_POSTURE": 2,
    }[action]


def _epistemic_rank(status: str) -> int:
    return {
        "NOMINAL": 0,
        "ELEVATED": 1,
        "UNKNOWN_UNKNOWNS": 2,
    }[status]



def _doctrine_rank(posture: str) -> int:
    return {
        "STABLE_RESEARCH_POSTURE": 0,
        "HEIGHTENED_RESEARCH_POSTURE": 1,
        "STRATEGY_RETRAIN_REVIEW": 2,
        "DEFENSIVE_RESEARCH_POSTURE": 3,
        "REPAIR_FIRST": 4,
    }[posture]


def _drift_level_from_score(score: float) -> OracleDriftLevel:
    if score >= 0.85:
        return "SEVERE"
    if score >= 0.55:
        return "MATERIAL"
    if score >= 0.20:
        return "MODERATE"
    return "STABLE"


def _normalize_path(path: Path | str) -> str:
    return str(path).replace("\\", "/")


def _resolve_existing_path(path_str: str, *, repo_root: Path, preferred_parent: Path) -> Path | None:
    candidate = Path(path_str)
    attempts: list[Path] = []
    if candidate.is_absolute():
        attempts.append(candidate)
    else:
        attempts.extend([
            preferred_parent / candidate,
            repo_root / candidate,
            Path.cwd() / candidate,
        ])
    for item in attempts:
        resolved = item.resolve()
        if resolved.exists():
            return resolved
    return None


def _load_manifest(path: Path) -> OracleEvidenceManifest:
    return OracleEvidenceManifest.model_validate(json.loads(path.read_text(encoding="utf-8")))


def _find_attestation_path(*, manifest: OracleEvidenceManifest, manifest_path: Path, repo_root: Path) -> Path:
    for subject in manifest.subjects:
        if subject.name == "ORACLE_MORNING_ATTESTATION.json":
            resolved = _resolve_existing_path(subject.path, repo_root=repo_root, preferred_parent=manifest_path.parent)
            if resolved is None:
                raise FileNotFoundError(f"oracle attestation subject missing from evidence chain: {subject.path}")
            return resolved
    raise FileNotFoundError("oracle evidence manifest does not include ORACLE_MORNING_ATTESTATION.json")


def _load_attestation(*, manifest: OracleEvidenceManifest, manifest_path: Path, repo_root: Path) -> OracleMorningAttestation:
    attestation_path = _find_attestation_path(manifest=manifest, manifest_path=manifest_path, repo_root=repo_root)
    return OracleMorningAttestation.model_validate(json.loads(attestation_path.read_text(encoding="utf-8")))


def _find_transition_report_path(*, manifest: OracleTransitionEvidenceManifest, manifest_path: Path, repo_root: Path) -> Path:
    for subject in manifest.subjects:
        if subject.name == "ORACLE_STATE_TRANSITION_REPORT.json":
            resolved = advisory_resolve_existing_path(subject.path, repo_root=repo_root, preferred_parent=manifest_path.parent)
            if resolved is None:
                fallback = manifest_path.parent / Path(subject.path).name
                if fallback.exists():
                    return fallback.resolve()
                raise FileNotFoundError(f"oracle transition report subject missing from evidence chain: {subject.path}")
            return resolved
    raise FileNotFoundError("oracle transition evidence manifest does not include ORACLE_STATE_TRANSITION_REPORT.json")


def _load_transition_report(*, manifest: OracleTransitionEvidenceManifest, manifest_path: Path, repo_root: Path) -> OracleStateTransitionReport:
    report_path = _find_transition_report_path(manifest=manifest, manifest_path=manifest_path, repo_root=repo_root)
    return OracleStateTransitionReport.model_validate(json.loads(report_path.read_text(encoding="utf-8")))


def _dominant_probability(attestation: OracleMorningAttestation) -> float:
    for item in attestation.regime_probabilities:
        if item.regime == attestation.dominant_regime:
            return item.probability
    return 0.0


def _build_regime_transition(previous: OracleMorningAttestation, current: OracleMorningAttestation) -> OracleRegimeTransition:
    previous_probability = _dominant_probability(previous)
    current_probability = _dominant_probability(current)
    dominant_changed = previous.dominant_regime != current.dominant_regime
    drivers: list[str] = []
    if dominant_changed:
        drivers.append(f"dominant_regime rotated from {previous.dominant_regime} to {current.dominant_regime}")
    probability_gap = abs(current_probability - previous_probability)
    if probability_gap >= 0.10:
        drivers.append(f"dominant regime confidence shifted by {probability_gap:.1%}")
    if current.epistemic_uncertainty.status != previous.epistemic_uncertainty.status:
        drivers.append(
            f"epistemic status moved from {previous.epistemic_uncertainty.status} to {current.epistemic_uncertainty.status}"
        )

    severity_score = 0.0
    if dominant_changed:
        severity_score += 0.55
    severity_score += min(probability_gap * 1.5, 0.30)
    if _global_action_rank(current.recommended_global_action) > _global_action_rank(previous.recommended_global_action):
        severity_score += 0.15
    if _epistemic_rank(current.epistemic_uncertainty.status) > _epistemic_rank(previous.epistemic_uncertainty.status):
        severity_score += 0.20
    severity_score = min(severity_score, 1.0)

    return OracleRegimeTransition(
        previous_dominant_regime=previous.dominant_regime,
        current_dominant_regime=current.dominant_regime,
        previous_dominant_probability=round(previous_probability, 6),
        current_dominant_probability=round(current_probability, 6),
        dominant_changed=dominant_changed,
        drift_level=_drift_level_from_score(severity_score),
        drivers=drivers,
    )


def _build_strategy_transition(previous: StrategyAdvisory, current: StrategyAdvisory) -> StrategyAdvisoryTransition:
    delta = round(current.posterior_edge_confidence - previous.posterior_edge_confidence, 6)
    action_changed = previous.action != current.action
    reasons: list[str] = []
    if action_changed:
        reasons.append(f"strategy action changed from {previous.action} to {current.action}")
    if abs(delta) >= 0.05:
        reasons.append(f"posterior edge confidence moved by {delta:+.1%}")
    reasons.extend(current.reasons[:2])

    severity_score = min(abs(delta) * 2.4, 0.5)
    if action_changed:
        severity_score += 0.25 + 0.20 * max(_advisory_rank(current.action) - _advisory_rank(previous.action), 0)
    if current.action == "HIBERNATE":
        severity_score += 0.15
    severity_score = min(severity_score, 1.0)

    return StrategyAdvisoryTransition(
        strategy_id=current.strategy_id,
        strategy_type=current.strategy_type,
        previous_action=previous.action,
        current_action=current.action,
        previous_posterior_edge_confidence=previous.posterior_edge_confidence,
        current_posterior_edge_confidence=current.posterior_edge_confidence,
        posterior_delta=delta,
        action_changed=action_changed,
        drift_level=_drift_level_from_score(severity_score),
        reasons=reasons,
    )
