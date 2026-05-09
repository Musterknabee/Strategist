"""Evidence-bundle lifecycle projection for the paper execution cockpit read model."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from strategy_validator.application.paper_execution_cockpit_execution_state import _safe_read_json
from strategy_validator.application.paper_execution_cockpit_runtime import *  # noqa: F403,F401
from strategy_validator.application.paper_execution_cockpit_evidence_lifecycle_payloads import (
    build_evidence_lifecycle_action_kwargs,
    build_evidence_lifecycle_payload_kwargs,
    build_evidence_lifecycle_summary_kwargs,
)


@dataclass(frozen=True)
class PaperExecutionEvidenceLifecycleProjection:
    """Collected evidence lifecycle state and model kwargs for cockpit synthesis."""

    values: dict[str, Any]
    summary_kwargs: dict[str, Any]
    action_kwargs: dict[str, Any]
    payload_kwargs: dict[str, Any]

    def __getattr__(self, name: str) -> Any:
        try:
            return self.values[name]
        except KeyError as exc:  # pragma: no cover - defensive introspection path
            raise AttributeError(name) from exc


def _attestation_view_from_artifact(artifact) -> PaperExecutionEvidenceBundleAttestationView:
    return PaperExecutionEvidenceBundleAttestationView(
        tracking_id=artifact.tracking_id,
        artifact_path="CURRENT_PROJECTION_NOT_PERSISTED",
        artifact_sha256=artifact.artifact_sha256,
        generated_at_utc=artifact.generated_at_utc.isoformat(),
        attestation_status=artifact.attestation_status,
        trust_banner=artifact.trust_banner,
        attestation_mode=artifact.attestation_mode,
        signature_status=artifact.signature_status,
        signer_identity=artifact.signer_identity,
        source_bundle_sha256=artifact.source_bundle_sha256,
        source_bundle_status=artifact.source_bundle_status,
        source_verification_status=artifact.source_verification_status,
        source_drift_status=artifact.source_drift_status,
        statement_payload_sha256=artifact.statement_payload_sha256,
        blocker_count=len(artifact.blockers),
        warning_count=len(artifact.warnings),
        blockers=artifact.blockers,
        warnings=artifact.warnings,
    )


def build_paper_execution_evidence_lifecycle_projection(
    *,
    repo_root: Path | None,
    now: datetime,
    execution_timeline: list[Any],
    execution_timeline_summary: Any,
) -> PaperExecutionEvidenceLifecycleProjection:
    evidence_bundles = read_paper_execution_evidence_bundle_views(repo_root=repo_root)
    latest_evidence_bundle = evidence_bundles[0] if evidence_bundles else None
    evidence_bundle_verifications = read_paper_execution_evidence_bundle_verification_views(repo_root=repo_root)
    latest_evidence_bundle_verification = evidence_bundle_verifications[0] if evidence_bundle_verifications else None
    evidence_bundle_drifts = read_paper_execution_evidence_bundle_drift_views(repo_root=repo_root)
    latest_evidence_bundle_drift = evidence_bundle_drifts[0] if evidence_bundle_drifts else None
    if latest_evidence_bundle is not None:
        current_drift = build_paper_execution_evidence_bundle_drift_artifact(
            current_timeline=execution_timeline,
            current_timeline_summary=execution_timeline_summary,
            bundle_artifact_path=Path(latest_evidence_bundle.artifact_path),
            bundle_raw=_safe_read_json(Path(latest_evidence_bundle.artifact_path)),
            generated_at_utc=now,
        )
        latest_evidence_bundle_drift = PaperExecutionEvidenceBundleDriftView(
            tracking_id=current_drift.tracking_id,
            artifact_path="CURRENT_PROJECTION_NOT_PERSISTED",
            artifact_sha256=current_drift.artifact_sha256,
            generated_at_utc=current_drift.generated_at_utc.isoformat(),
            drift_status=current_drift.drift_status,
            trust_banner=current_drift.trust_banner,
            source_bundle_artifact_path=current_drift.source_bundle_artifact_path,
            source_bundle_sha256=current_drift.source_bundle_sha256,
            source_bundle_generated_at_utc=current_drift.source_bundle_generated_at_utc,
            current_timeline_sequence_status=current_drift.current_timeline_sequence_status,
            current_timeline_event_count=current_drift.current_timeline_event_count,
            bundled_timeline_event_count=current_drift.bundled_timeline_event_count,
            current_source_artifact_count=current_drift.current_source_artifact_count,
            bundled_source_artifact_count=current_drift.bundled_source_artifact_count,
            current_timeline_fingerprint=current_drift.current_timeline_fingerprint,
            bundled_timeline_fingerprint=current_drift.bundled_timeline_fingerprint,
            new_source_artifact_count=len(current_drift.new_source_artifacts),
            removed_source_artifact_count=len(current_drift.removed_source_artifacts),
            changed_stage_count=current_drift.changed_stage_count,
            blockers=current_drift.blockers,
            warnings=current_drift.warnings,
        )
        evidence_bundle_drifts = [latest_evidence_bundle_drift, *evidence_bundle_drifts]
    evidence_bundle_rotations = read_paper_execution_evidence_bundle_rotation_views(repo_root=repo_root)
    current_rotation = build_paper_execution_evidence_bundle_rotation_artifact(
        timeline_summary=execution_timeline_summary,
        latest_evidence_bundle=latest_evidence_bundle,
        latest_evidence_bundle_verification=latest_evidence_bundle_verification,
        latest_evidence_bundle_drift=latest_evidence_bundle_drift,
        generated_at_utc=now,
    )
    latest_evidence_bundle_rotation = PaperExecutionEvidenceBundleRotationView(
        tracking_id=current_rotation.tracking_id,
        artifact_path="CURRENT_PROJECTION_NOT_PERSISTED",
        artifact_sha256=current_rotation.artifact_sha256,
        generated_at_utc=current_rotation.generated_at_utc.isoformat(),
        rotation_status=current_rotation.rotation_status,
        trust_banner=current_rotation.trust_banner,
        source_bundle_sha256=current_rotation.source_bundle_sha256,
        source_bundle_status=current_rotation.source_bundle_status,
        source_verification_status=current_rotation.source_verification_status,
        source_drift_status=current_rotation.source_drift_status,
        timeline_sequence_status=current_rotation.timeline_sequence_status,
        timeline_event_count=current_rotation.timeline_event_count,
        rotation_reason_codes=current_rotation.rotation_reason_codes,
        recommended_operator_sequence=current_rotation.recommended_operator_sequence,
        one_command_sequence_hint=current_rotation.one_command_sequence_hint,
        blockers=current_rotation.blockers,
        warnings=current_rotation.warnings,
    )
    evidence_bundle_rotations = [latest_evidence_bundle_rotation, *evidence_bundle_rotations]
    evidence_bundle_rotation_executions = read_paper_execution_evidence_bundle_rotation_execution_views(repo_root=repo_root)
    latest_evidence_bundle_rotation_execution = evidence_bundle_rotation_executions[0] if evidence_bundle_rotation_executions else None
    persisted_evidence_bundle_attestations = read_paper_execution_evidence_bundle_attestation_views(repo_root=repo_root)
    current_attestation = build_paper_execution_evidence_bundle_attestation_artifact(
        latest_evidence_bundle=latest_evidence_bundle,
        latest_evidence_bundle_verification=latest_evidence_bundle_verification,
        latest_evidence_bundle_drift=latest_evidence_bundle_drift,
        generated_at_utc=now,
    )
    current_evidence_bundle_attestation = _attestation_view_from_artifact(current_attestation)
    latest_evidence_bundle_attestation = persisted_evidence_bundle_attestations[0] if persisted_evidence_bundle_attestations else current_evidence_bundle_attestation
    evidence_bundle_attestations = [latest_evidence_bundle_attestation, current_evidence_bundle_attestation, *persisted_evidence_bundle_attestations[1:]]
    evidence_bundle_attestation_verifications = read_paper_execution_evidence_bundle_attestation_verification_views(repo_root=repo_root)
    latest_evidence_bundle_attestation_verification = evidence_bundle_attestation_verifications[0] if evidence_bundle_attestation_verifications else None
    persisted_evidence_bundle_closures = read_paper_execution_evidence_bundle_closure_views(repo_root=repo_root)
    current_closure = build_paper_execution_evidence_bundle_closure_artifact(
        latest_evidence_bundle=latest_evidence_bundle,
        latest_evidence_bundle_verification=latest_evidence_bundle_verification,
        latest_evidence_bundle_drift=latest_evidence_bundle_drift,
        latest_evidence_bundle_attestation=latest_evidence_bundle_attestation,
        latest_evidence_bundle_attestation_verification=latest_evidence_bundle_attestation_verification,
        generated_at_utc=now,
    )
    current_evidence_bundle_closure = _closure_view_from_artifact(current_closure, artifact_path="CURRENT_PROJECTION_NOT_PERSISTED")
    latest_evidence_bundle_closure = persisted_evidence_bundle_closures[0] if persisted_evidence_bundle_closures else current_evidence_bundle_closure
    evidence_bundle_closures = [latest_evidence_bundle_closure, current_evidence_bundle_closure, *persisted_evidence_bundle_closures[1:]]
    evidence_bundle_closure_verifications = read_paper_execution_evidence_bundle_closure_verification_views(repo_root=repo_root)
    latest_evidence_bundle_closure_verification = evidence_bundle_closure_verifications[0] if evidence_bundle_closure_verifications else None
    evidence_bundle_export_manifests = read_paper_execution_evidence_bundle_export_manifest_views(repo_root=repo_root)
    latest_evidence_bundle_export_manifest = evidence_bundle_export_manifests[0] if evidence_bundle_export_manifests else None
    evidence_bundle_export_verifications = read_paper_execution_evidence_bundle_export_verification_views(repo_root=repo_root)
    latest_evidence_bundle_export_verification = evidence_bundle_export_verifications[0] if evidence_bundle_export_verifications else None
    evidence_bundle_retention_receipts = read_paper_execution_evidence_bundle_retention_receipt_views(repo_root=repo_root)
    latest_evidence_bundle_retention_receipt = evidence_bundle_retention_receipts[0] if evidence_bundle_retention_receipts else None
    evidence_bundle_retention_verifications = read_paper_execution_evidence_bundle_retention_verification_views(repo_root=repo_root)
    latest_evidence_bundle_retention_verification = evidence_bundle_retention_verifications[0] if evidence_bundle_retention_verifications else None
    evidence_bundle_retention_signoffs = read_paper_execution_evidence_bundle_retention_signoff_views(repo_root=repo_root)
    latest_evidence_bundle_retention_signoff = evidence_bundle_retention_signoffs[0] if evidence_bundle_retention_signoffs else None
    evidence_bundle_retention_signoff_verifications = read_paper_execution_evidence_bundle_retention_signoff_verification_views(repo_root=repo_root)
    latest_evidence_bundle_retention_signoff_verification = evidence_bundle_retention_signoff_verifications[0] if evidence_bundle_retention_signoff_verifications else None
    evidence_bundle_retention_handoffs = read_paper_execution_evidence_bundle_retention_handoff_views(repo_root=repo_root)
    latest_evidence_bundle_retention_handoff = evidence_bundle_retention_handoffs[0] if evidence_bundle_retention_handoffs else None
    evidence_bundle_retention_handoff_verifications = read_paper_execution_evidence_bundle_retention_handoff_verification_views(repo_root=repo_root)
    latest_evidence_bundle_retention_handoff_verification = evidence_bundle_retention_handoff_verifications[0] if evidence_bundle_retention_handoff_verifications else None
    evidence_bundle_retention_handoff_acceptances = read_paper_execution_evidence_bundle_retention_handoff_acceptance_views(repo_root=repo_root)
    latest_evidence_bundle_retention_handoff_acceptance = evidence_bundle_retention_handoff_acceptances[0] if evidence_bundle_retention_handoff_acceptances else None
    evidence_bundle_retention_handoff_acceptance_verifications = read_paper_execution_evidence_bundle_retention_handoff_acceptance_verification_views(repo_root=repo_root)
    latest_evidence_bundle_retention_handoff_acceptance_verification = evidence_bundle_retention_handoff_acceptance_verifications[0] if evidence_bundle_retention_handoff_acceptance_verifications else None
    evidence_bundle_retention_custody_registers = read_paper_execution_evidence_bundle_retention_custody_register_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_register = evidence_bundle_retention_custody_registers[0] if evidence_bundle_retention_custody_registers else None
    evidence_bundle_retention_custody_register_verifications = read_paper_execution_evidence_bundle_retention_custody_register_verification_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_register_verification = evidence_bundle_retention_custody_register_verifications[0] if evidence_bundle_retention_custody_register_verifications else None
    evidence_bundle_retention_custody_seals = read_paper_execution_evidence_bundle_retention_custody_seal_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_seal = evidence_bundle_retention_custody_seals[0] if evidence_bundle_retention_custody_seals else None
    evidence_bundle_retention_custody_seal_verifications = read_paper_execution_evidence_bundle_retention_custody_seal_verification_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_seal_verification = evidence_bundle_retention_custody_seal_verifications[0] if evidence_bundle_retention_custody_seal_verifications else None
    evidence_bundle_retention_custody_audits = read_paper_execution_evidence_bundle_retention_custody_audit_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_audit = evidence_bundle_retention_custody_audits[0] if evidence_bundle_retention_custody_audits else None
    evidence_bundle_retention_custody_audit_verifications = read_paper_execution_evidence_bundle_retention_custody_audit_verification_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_audit_verification = evidence_bundle_retention_custody_audit_verifications[0] if evidence_bundle_retention_custody_audit_verifications else None
    evidence_bundle_retention_custody_continuities = read_paper_execution_evidence_bundle_retention_custody_continuity_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_continuity = evidence_bundle_retention_custody_continuities[0] if evidence_bundle_retention_custody_continuities else None
    evidence_bundle_retention_custody_continuity_verifications = read_paper_execution_evidence_bundle_retention_custody_continuity_verification_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_continuity_verification = evidence_bundle_retention_custody_continuity_verifications[0] if evidence_bundle_retention_custody_continuity_verifications else None
    evidence_bundle_retention_custody_reviews = read_paper_execution_evidence_bundle_retention_custody_review_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_review = evidence_bundle_retention_custody_reviews[0] if evidence_bundle_retention_custody_reviews else None
    evidence_bundle_retention_custody_review_verifications = read_paper_execution_evidence_bundle_retention_custody_review_verification_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_review_verification = evidence_bundle_retention_custody_review_verifications[0] if evidence_bundle_retention_custody_review_verifications else None
    evidence_bundle_retention_custody_renewals = read_paper_execution_evidence_bundle_retention_custody_renewal_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_renewal = evidence_bundle_retention_custody_renewals[0] if evidence_bundle_retention_custody_renewals else None
    evidence_bundle_retention_custody_renewal_verifications = read_paper_execution_evidence_bundle_retention_custody_renewal_verification_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_renewal_verification = evidence_bundle_retention_custody_renewal_verifications[0] if evidence_bundle_retention_custody_renewal_verifications else None
    evidence_bundle_retention_custody_schedules = read_paper_execution_evidence_bundle_retention_custody_schedule_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_schedule = evidence_bundle_retention_custody_schedules[0] if evidence_bundle_retention_custody_schedules else None
    evidence_bundle_retention_custody_schedule_verifications = read_paper_execution_evidence_bundle_retention_custody_schedule_verification_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_schedule_verification = evidence_bundle_retention_custody_schedule_verifications[0] if evidence_bundle_retention_custody_schedule_verifications else None
    evidence_bundle_retention_custody_notices = read_paper_execution_evidence_bundle_retention_custody_notice_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_notice = evidence_bundle_retention_custody_notices[0] if evidence_bundle_retention_custody_notices else None
    evidence_bundle_retention_custody_notice_verifications = read_paper_execution_evidence_bundle_retention_custody_notice_verification_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_notice_verification = evidence_bundle_retention_custody_notice_verifications[0] if evidence_bundle_retention_custody_notice_verifications else None
    evidence_bundle_retention_custody_acknowledgments = read_paper_execution_evidence_bundle_retention_custody_acknowledgment_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_acknowledgment = evidence_bundle_retention_custody_acknowledgments[0] if evidence_bundle_retention_custody_acknowledgments else None
    evidence_bundle_retention_custody_acknowledgment_verifications = read_paper_execution_evidence_bundle_retention_custody_acknowledgment_verification_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_acknowledgment_verification = evidence_bundle_retention_custody_acknowledgment_verifications[0] if evidence_bundle_retention_custody_acknowledgment_verifications else None
    evidence_bundle_retention_custody_completions = read_paper_execution_evidence_bundle_retention_custody_completion_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_completion = evidence_bundle_retention_custody_completions[0] if evidence_bundle_retention_custody_completions else None
    evidence_bundle_retention_custody_completion_verifications = read_paper_execution_evidence_bundle_retention_custody_completion_verification_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_completion_verification = evidence_bundle_retention_custody_completion_verifications[0] if evidence_bundle_retention_custody_completion_verifications else None
    evidence_bundle_retention_custody_closeouts = read_paper_execution_evidence_bundle_retention_custody_closeout_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_closeout = evidence_bundle_retention_custody_closeouts[0] if evidence_bundle_retention_custody_closeouts else None
    evidence_bundle_retention_custody_closeout_verifications = read_paper_execution_evidence_bundle_retention_custody_closeout_verification_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_closeout_verification = evidence_bundle_retention_custody_closeout_verifications[0] if evidence_bundle_retention_custody_closeout_verifications else None
    evidence_bundle_retention_custody_archives = read_paper_execution_evidence_bundle_retention_custody_archive_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_archive = evidence_bundle_retention_custody_archives[0] if evidence_bundle_retention_custody_archives else None
    evidence_bundle_retention_custody_archive_verifications = read_paper_execution_evidence_bundle_retention_custody_archive_verification_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_archive_verification = evidence_bundle_retention_custody_archive_verifications[0] if evidence_bundle_retention_custody_archive_verifications else None
    evidence_bundle_retention_custody_retrievals = read_paper_execution_evidence_bundle_retention_custody_retrieval_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_retrieval = evidence_bundle_retention_custody_retrievals[0] if evidence_bundle_retention_custody_retrievals else None
    evidence_bundle_retention_custody_retrieval_verifications = read_paper_execution_evidence_bundle_retention_custody_retrieval_verification_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_retrieval_verification = evidence_bundle_retention_custody_retrieval_verifications[0] if evidence_bundle_retention_custody_retrieval_verifications else None
    evidence_bundle_retention_custody_returns = read_paper_execution_evidence_bundle_retention_custody_return_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_return = evidence_bundle_retention_custody_returns[0] if evidence_bundle_retention_custody_returns else None
    evidence_bundle_retention_custody_return_verifications = read_paper_execution_evidence_bundle_retention_custody_return_verification_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_return_verification = evidence_bundle_retention_custody_return_verifications[0] if evidence_bundle_retention_custody_return_verifications else None
    evidence_bundle_retention_custody_redeposits = read_paper_execution_evidence_bundle_retention_custody_redeposit_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_redeposit = evidence_bundle_retention_custody_redeposits[0] if evidence_bundle_retention_custody_redeposits else None
    evidence_bundle_retention_custody_redeposit_verifications = read_paper_execution_evidence_bundle_retention_custody_redeposit_verification_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_redeposit_verification = evidence_bundle_retention_custody_redeposit_verifications[0] if evidence_bundle_retention_custody_redeposit_verifications else None
    evidence_bundle_retention_custody_inventories = read_paper_execution_evidence_bundle_retention_custody_inventory_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_inventory = evidence_bundle_retention_custody_inventories[0] if evidence_bundle_retention_custody_inventories else None
    evidence_bundle_retention_custody_inventory_verifications = read_paper_execution_evidence_bundle_retention_custody_inventory_verification_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_inventory_verification = evidence_bundle_retention_custody_inventory_verifications[0] if evidence_bundle_retention_custody_inventory_verifications else None
    evidence_bundle_retention_custody_reconciliations = read_paper_execution_evidence_bundle_retention_custody_reconciliation_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_reconciliation = evidence_bundle_retention_custody_reconciliations[0] if evidence_bundle_retention_custody_reconciliations else None
    evidence_bundle_retention_custody_reconciliation_verifications = read_paper_execution_evidence_bundle_retention_custody_reconciliation_verification_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_reconciliation_verification = evidence_bundle_retention_custody_reconciliation_verifications[0] if evidence_bundle_retention_custody_reconciliation_verifications else None
    evidence_bundle_retention_custody_certifications = read_paper_execution_evidence_bundle_retention_custody_certification_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_certification = evidence_bundle_retention_custody_certifications[0] if evidence_bundle_retention_custody_certifications else None
    evidence_bundle_retention_custody_certification_verifications = read_paper_execution_evidence_bundle_retention_custody_certification_verification_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_certification_verification = evidence_bundle_retention_custody_certification_verifications[0] if evidence_bundle_retention_custody_certification_verifications else None
    evidence_bundle_retention_custody_attestations = read_paper_execution_evidence_bundle_retention_custody_attestation_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_attestation = evidence_bundle_retention_custody_attestations[0] if evidence_bundle_retention_custody_attestations else None
    evidence_bundle_retention_custody_attestation_verifications = read_paper_execution_evidence_bundle_retention_custody_attestation_verification_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_attestation_verification = evidence_bundle_retention_custody_attestation_verifications[0] if evidence_bundle_retention_custody_attestation_verifications else None
    values = {
        'evidence_bundles': evidence_bundles,
        'latest_evidence_bundle': latest_evidence_bundle,
        'evidence_bundle_verifications': evidence_bundle_verifications,
        'latest_evidence_bundle_verification': latest_evidence_bundle_verification,
        'evidence_bundle_drifts': evidence_bundle_drifts,
        'latest_evidence_bundle_drift': latest_evidence_bundle_drift,
        'evidence_bundle_rotations': evidence_bundle_rotations,
        'latest_evidence_bundle_rotation': latest_evidence_bundle_rotation,
        'evidence_bundle_rotation_executions': evidence_bundle_rotation_executions,
        'latest_evidence_bundle_rotation_execution': latest_evidence_bundle_rotation_execution,
        'evidence_bundle_attestations': evidence_bundle_attestations,
        'latest_evidence_bundle_attestation': latest_evidence_bundle_attestation,
        'evidence_bundle_attestation_verifications': evidence_bundle_attestation_verifications,
        'latest_evidence_bundle_attestation_verification': latest_evidence_bundle_attestation_verification,
        'evidence_bundle_closures': evidence_bundle_closures,
        'latest_evidence_bundle_closure': latest_evidence_bundle_closure,
        'evidence_bundle_closure_verifications': evidence_bundle_closure_verifications,
        'latest_evidence_bundle_closure_verification': latest_evidence_bundle_closure_verification,
        'evidence_bundle_export_manifests': evidence_bundle_export_manifests,
        'latest_evidence_bundle_export_manifest': latest_evidence_bundle_export_manifest,
        'evidence_bundle_export_verifications': evidence_bundle_export_verifications,
        'latest_evidence_bundle_export_verification': latest_evidence_bundle_export_verification,
        'evidence_bundle_retention_receipts': evidence_bundle_retention_receipts,
        'latest_evidence_bundle_retention_receipt': latest_evidence_bundle_retention_receipt,
        'evidence_bundle_retention_verifications': evidence_bundle_retention_verifications,
        'latest_evidence_bundle_retention_verification': latest_evidence_bundle_retention_verification,
        'evidence_bundle_retention_signoffs': evidence_bundle_retention_signoffs,
        'latest_evidence_bundle_retention_signoff': latest_evidence_bundle_retention_signoff,
        'evidence_bundle_retention_signoff_verifications': evidence_bundle_retention_signoff_verifications,
        'latest_evidence_bundle_retention_signoff_verification': latest_evidence_bundle_retention_signoff_verification,
        'evidence_bundle_retention_handoffs': evidence_bundle_retention_handoffs,
        'latest_evidence_bundle_retention_handoff': latest_evidence_bundle_retention_handoff,
        'evidence_bundle_retention_handoff_verifications': evidence_bundle_retention_handoff_verifications,
        'latest_evidence_bundle_retention_handoff_verification': latest_evidence_bundle_retention_handoff_verification,
        'evidence_bundle_retention_handoff_acceptances': evidence_bundle_retention_handoff_acceptances,
        'latest_evidence_bundle_retention_handoff_acceptance': latest_evidence_bundle_retention_handoff_acceptance,
        'evidence_bundle_retention_handoff_acceptance_verifications': evidence_bundle_retention_handoff_acceptance_verifications,
        'latest_evidence_bundle_retention_handoff_acceptance_verification': latest_evidence_bundle_retention_handoff_acceptance_verification,
        'evidence_bundle_retention_custody_registers': evidence_bundle_retention_custody_registers,
        'latest_evidence_bundle_retention_custody_register': latest_evidence_bundle_retention_custody_register,
        'evidence_bundle_retention_custody_register_verifications': evidence_bundle_retention_custody_register_verifications,
        'latest_evidence_bundle_retention_custody_register_verification': latest_evidence_bundle_retention_custody_register_verification,
        'evidence_bundle_retention_custody_seals': evidence_bundle_retention_custody_seals,
        'latest_evidence_bundle_retention_custody_seal': latest_evidence_bundle_retention_custody_seal,
        'evidence_bundle_retention_custody_seal_verifications': evidence_bundle_retention_custody_seal_verifications,
        'latest_evidence_bundle_retention_custody_seal_verification': latest_evidence_bundle_retention_custody_seal_verification,
        'evidence_bundle_retention_custody_audits': evidence_bundle_retention_custody_audits,
        'latest_evidence_bundle_retention_custody_audit': latest_evidence_bundle_retention_custody_audit,
        'evidence_bundle_retention_custody_audit_verifications': evidence_bundle_retention_custody_audit_verifications,
        'latest_evidence_bundle_retention_custody_audit_verification': latest_evidence_bundle_retention_custody_audit_verification,
        'evidence_bundle_retention_custody_continuities': evidence_bundle_retention_custody_continuities,
        'latest_evidence_bundle_retention_custody_continuity': latest_evidence_bundle_retention_custody_continuity,
        'evidence_bundle_retention_custody_continuity_verifications': evidence_bundle_retention_custody_continuity_verifications,
        'latest_evidence_bundle_retention_custody_continuity_verification': latest_evidence_bundle_retention_custody_continuity_verification,
        'evidence_bundle_retention_custody_reviews': evidence_bundle_retention_custody_reviews,
        'latest_evidence_bundle_retention_custody_review': latest_evidence_bundle_retention_custody_review,
        'evidence_bundle_retention_custody_review_verifications': evidence_bundle_retention_custody_review_verifications,
        'latest_evidence_bundle_retention_custody_review_verification': latest_evidence_bundle_retention_custody_review_verification,
        'evidence_bundle_retention_custody_renewals': evidence_bundle_retention_custody_renewals,
        'latest_evidence_bundle_retention_custody_renewal': latest_evidence_bundle_retention_custody_renewal,
        'evidence_bundle_retention_custody_renewal_verifications': evidence_bundle_retention_custody_renewal_verifications,
        'latest_evidence_bundle_retention_custody_renewal_verification': latest_evidence_bundle_retention_custody_renewal_verification,
        'evidence_bundle_retention_custody_schedules': evidence_bundle_retention_custody_schedules,
        'latest_evidence_bundle_retention_custody_schedule': latest_evidence_bundle_retention_custody_schedule,
        'evidence_bundle_retention_custody_schedule_verifications': evidence_bundle_retention_custody_schedule_verifications,
        'latest_evidence_bundle_retention_custody_schedule_verification': latest_evidence_bundle_retention_custody_schedule_verification,
        'evidence_bundle_retention_custody_notices': evidence_bundle_retention_custody_notices,
        'latest_evidence_bundle_retention_custody_notice': latest_evidence_bundle_retention_custody_notice,
        'evidence_bundle_retention_custody_notice_verifications': evidence_bundle_retention_custody_notice_verifications,
        'latest_evidence_bundle_retention_custody_notice_verification': latest_evidence_bundle_retention_custody_notice_verification,
        'evidence_bundle_retention_custody_acknowledgments': evidence_bundle_retention_custody_acknowledgments,
        'latest_evidence_bundle_retention_custody_acknowledgment': latest_evidence_bundle_retention_custody_acknowledgment,
        'evidence_bundle_retention_custody_acknowledgment_verifications': evidence_bundle_retention_custody_acknowledgment_verifications,
        'latest_evidence_bundle_retention_custody_acknowledgment_verification': latest_evidence_bundle_retention_custody_acknowledgment_verification,
        'evidence_bundle_retention_custody_completions': evidence_bundle_retention_custody_completions,
        'latest_evidence_bundle_retention_custody_completion': latest_evidence_bundle_retention_custody_completion,
        'evidence_bundle_retention_custody_completion_verifications': evidence_bundle_retention_custody_completion_verifications,
        'latest_evidence_bundle_retention_custody_completion_verification': latest_evidence_bundle_retention_custody_completion_verification,
        'evidence_bundle_retention_custody_closeouts': evidence_bundle_retention_custody_closeouts,
        'latest_evidence_bundle_retention_custody_closeout': latest_evidence_bundle_retention_custody_closeout,
        'evidence_bundle_retention_custody_closeout_verifications': evidence_bundle_retention_custody_closeout_verifications,
        'latest_evidence_bundle_retention_custody_closeout_verification': latest_evidence_bundle_retention_custody_closeout_verification,
        'evidence_bundle_retention_custody_archives': evidence_bundle_retention_custody_archives,
        'latest_evidence_bundle_retention_custody_archive': latest_evidence_bundle_retention_custody_archive,
        'evidence_bundle_retention_custody_archive_verifications': evidence_bundle_retention_custody_archive_verifications,
        'latest_evidence_bundle_retention_custody_archive_verification': latest_evidence_bundle_retention_custody_archive_verification,
        'evidence_bundle_retention_custody_retrievals': evidence_bundle_retention_custody_retrievals,
        'latest_evidence_bundle_retention_custody_retrieval': latest_evidence_bundle_retention_custody_retrieval,
        'evidence_bundle_retention_custody_retrieval_verifications': evidence_bundle_retention_custody_retrieval_verifications,
        'latest_evidence_bundle_retention_custody_retrieval_verification': latest_evidence_bundle_retention_custody_retrieval_verification,
        'evidence_bundle_retention_custody_returns': evidence_bundle_retention_custody_returns,
        'latest_evidence_bundle_retention_custody_return': latest_evidence_bundle_retention_custody_return,
        'evidence_bundle_retention_custody_return_verifications': evidence_bundle_retention_custody_return_verifications,
        'latest_evidence_bundle_retention_custody_return_verification': latest_evidence_bundle_retention_custody_return_verification,
        'evidence_bundle_retention_custody_redeposits': evidence_bundle_retention_custody_redeposits,
        'latest_evidence_bundle_retention_custody_redeposit': latest_evidence_bundle_retention_custody_redeposit,
        'evidence_bundle_retention_custody_redeposit_verifications': evidence_bundle_retention_custody_redeposit_verifications,
        'latest_evidence_bundle_retention_custody_redeposit_verification': latest_evidence_bundle_retention_custody_redeposit_verification,
        'evidence_bundle_retention_custody_inventories': evidence_bundle_retention_custody_inventories,
        'latest_evidence_bundle_retention_custody_inventory': latest_evidence_bundle_retention_custody_inventory,
        'evidence_bundle_retention_custody_inventory_verifications': evidence_bundle_retention_custody_inventory_verifications,
        'latest_evidence_bundle_retention_custody_inventory_verification': latest_evidence_bundle_retention_custody_inventory_verification,
        'evidence_bundle_retention_custody_reconciliations': evidence_bundle_retention_custody_reconciliations,
        'latest_evidence_bundle_retention_custody_reconciliation': latest_evidence_bundle_retention_custody_reconciliation,
        'evidence_bundle_retention_custody_reconciliation_verifications': evidence_bundle_retention_custody_reconciliation_verifications,
        'latest_evidence_bundle_retention_custody_reconciliation_verification': latest_evidence_bundle_retention_custody_reconciliation_verification,
        'evidence_bundle_retention_custody_certifications': evidence_bundle_retention_custody_certifications,
        'latest_evidence_bundle_retention_custody_certification': latest_evidence_bundle_retention_custody_certification,
        'evidence_bundle_retention_custody_certification_verifications': evidence_bundle_retention_custody_certification_verifications,
        'latest_evidence_bundle_retention_custody_certification_verification': latest_evidence_bundle_retention_custody_certification_verification,
        'evidence_bundle_retention_custody_attestations': evidence_bundle_retention_custody_attestations,
        'latest_evidence_bundle_retention_custody_attestation': latest_evidence_bundle_retention_custody_attestation,
        'evidence_bundle_retention_custody_attestation_verifications': evidence_bundle_retention_custody_attestation_verifications,
        'latest_evidence_bundle_retention_custody_attestation_verification': latest_evidence_bundle_retention_custody_attestation_verification,
    }
    summary_kwargs = build_evidence_lifecycle_summary_kwargs(values)
    action_kwargs = build_evidence_lifecycle_action_kwargs(values)
    payload_kwargs = build_evidence_lifecycle_payload_kwargs(values)
    return PaperExecutionEvidenceLifecycleProjection(
        values=values,
        summary_kwargs=summary_kwargs,
        action_kwargs=action_kwargs,
        payload_kwargs=payload_kwargs,
    )


__all__ = [
    "PaperExecutionEvidenceLifecycleProjection",
    "build_paper_execution_evidence_lifecycle_projection",
]
