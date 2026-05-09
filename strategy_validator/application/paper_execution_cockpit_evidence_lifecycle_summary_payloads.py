"""Paper execution evidence lifecycle summary kwarg synthesis."""
from __future__ import annotations

from typing import Any, Mapping

from strategy_validator.application.paper_execution_cockpit_evidence_lifecycle_keys import _require_complete_values

def build_evidence_lifecycle_summary_kwargs(values: Mapping[str, Any]) -> dict[str, Any]:
    """Build PaperExecutionSummary kwargs for evidence lifecycle fields."""
    _require_complete_values(values)
    evidence_bundles = values["evidence_bundles"]
    latest_evidence_bundle = values["latest_evidence_bundle"]
    evidence_bundle_verifications = values["evidence_bundle_verifications"]
    latest_evidence_bundle_verification = values["latest_evidence_bundle_verification"]
    evidence_bundle_drifts = values["evidence_bundle_drifts"]
    latest_evidence_bundle_drift = values["latest_evidence_bundle_drift"]
    evidence_bundle_rotations = values["evidence_bundle_rotations"]
    latest_evidence_bundle_rotation = values["latest_evidence_bundle_rotation"]
    evidence_bundle_rotation_executions = values["evidence_bundle_rotation_executions"]
    latest_evidence_bundle_rotation_execution = values["latest_evidence_bundle_rotation_execution"]
    evidence_bundle_attestations = values["evidence_bundle_attestations"]
    latest_evidence_bundle_attestation = values["latest_evidence_bundle_attestation"]
    evidence_bundle_attestation_verifications = values["evidence_bundle_attestation_verifications"]
    latest_evidence_bundle_attestation_verification = values["latest_evidence_bundle_attestation_verification"]
    evidence_bundle_closures = values["evidence_bundle_closures"]
    latest_evidence_bundle_closure = values["latest_evidence_bundle_closure"]
    evidence_bundle_closure_verifications = values["evidence_bundle_closure_verifications"]
    latest_evidence_bundle_closure_verification = values["latest_evidence_bundle_closure_verification"]
    evidence_bundle_export_manifests = values["evidence_bundle_export_manifests"]
    latest_evidence_bundle_export_manifest = values["latest_evidence_bundle_export_manifest"]
    evidence_bundle_export_verifications = values["evidence_bundle_export_verifications"]
    latest_evidence_bundle_export_verification = values["latest_evidence_bundle_export_verification"]
    evidence_bundle_retention_receipts = values["evidence_bundle_retention_receipts"]
    latest_evidence_bundle_retention_receipt = values["latest_evidence_bundle_retention_receipt"]
    evidence_bundle_retention_verifications = values["evidence_bundle_retention_verifications"]
    latest_evidence_bundle_retention_verification = values["latest_evidence_bundle_retention_verification"]
    evidence_bundle_retention_signoffs = values["evidence_bundle_retention_signoffs"]
    latest_evidence_bundle_retention_signoff = values["latest_evidence_bundle_retention_signoff"]
    evidence_bundle_retention_signoff_verifications = values["evidence_bundle_retention_signoff_verifications"]
    latest_evidence_bundle_retention_signoff_verification = values["latest_evidence_bundle_retention_signoff_verification"]
    evidence_bundle_retention_handoffs = values["evidence_bundle_retention_handoffs"]
    latest_evidence_bundle_retention_handoff = values["latest_evidence_bundle_retention_handoff"]
    evidence_bundle_retention_handoff_verifications = values["evidence_bundle_retention_handoff_verifications"]
    latest_evidence_bundle_retention_handoff_verification = values["latest_evidence_bundle_retention_handoff_verification"]
    evidence_bundle_retention_handoff_acceptances = values["evidence_bundle_retention_handoff_acceptances"]
    latest_evidence_bundle_retention_handoff_acceptance = values["latest_evidence_bundle_retention_handoff_acceptance"]
    evidence_bundle_retention_handoff_acceptance_verifications = values["evidence_bundle_retention_handoff_acceptance_verifications"]
    latest_evidence_bundle_retention_handoff_acceptance_verification = values["latest_evidence_bundle_retention_handoff_acceptance_verification"]
    evidence_bundle_retention_custody_registers = values["evidence_bundle_retention_custody_registers"]
    latest_evidence_bundle_retention_custody_register = values["latest_evidence_bundle_retention_custody_register"]
    evidence_bundle_retention_custody_register_verifications = values["evidence_bundle_retention_custody_register_verifications"]
    latest_evidence_bundle_retention_custody_register_verification = values["latest_evidence_bundle_retention_custody_register_verification"]
    evidence_bundle_retention_custody_seals = values["evidence_bundle_retention_custody_seals"]
    latest_evidence_bundle_retention_custody_seal = values["latest_evidence_bundle_retention_custody_seal"]
    evidence_bundle_retention_custody_seal_verifications = values["evidence_bundle_retention_custody_seal_verifications"]
    latest_evidence_bundle_retention_custody_seal_verification = values["latest_evidence_bundle_retention_custody_seal_verification"]
    evidence_bundle_retention_custody_audits = values["evidence_bundle_retention_custody_audits"]
    latest_evidence_bundle_retention_custody_audit = values["latest_evidence_bundle_retention_custody_audit"]
    evidence_bundle_retention_custody_audit_verifications = values["evidence_bundle_retention_custody_audit_verifications"]
    latest_evidence_bundle_retention_custody_audit_verification = values["latest_evidence_bundle_retention_custody_audit_verification"]
    evidence_bundle_retention_custody_continuities = values["evidence_bundle_retention_custody_continuities"]
    latest_evidence_bundle_retention_custody_continuity = values["latest_evidence_bundle_retention_custody_continuity"]
    evidence_bundle_retention_custody_continuity_verifications = values["evidence_bundle_retention_custody_continuity_verifications"]
    latest_evidence_bundle_retention_custody_continuity_verification = values["latest_evidence_bundle_retention_custody_continuity_verification"]
    evidence_bundle_retention_custody_reviews = values["evidence_bundle_retention_custody_reviews"]
    latest_evidence_bundle_retention_custody_review = values["latest_evidence_bundle_retention_custody_review"]
    evidence_bundle_retention_custody_review_verifications = values["evidence_bundle_retention_custody_review_verifications"]
    latest_evidence_bundle_retention_custody_review_verification = values["latest_evidence_bundle_retention_custody_review_verification"]
    evidence_bundle_retention_custody_renewals = values["evidence_bundle_retention_custody_renewals"]
    latest_evidence_bundle_retention_custody_renewal = values["latest_evidence_bundle_retention_custody_renewal"]
    evidence_bundle_retention_custody_renewal_verifications = values["evidence_bundle_retention_custody_renewal_verifications"]
    latest_evidence_bundle_retention_custody_renewal_verification = values["latest_evidence_bundle_retention_custody_renewal_verification"]
    evidence_bundle_retention_custody_schedules = values["evidence_bundle_retention_custody_schedules"]
    latest_evidence_bundle_retention_custody_schedule = values["latest_evidence_bundle_retention_custody_schedule"]
    evidence_bundle_retention_custody_schedule_verifications = values["evidence_bundle_retention_custody_schedule_verifications"]
    latest_evidence_bundle_retention_custody_schedule_verification = values["latest_evidence_bundle_retention_custody_schedule_verification"]
    evidence_bundle_retention_custody_notices = values["evidence_bundle_retention_custody_notices"]
    latest_evidence_bundle_retention_custody_notice = values["latest_evidence_bundle_retention_custody_notice"]
    evidence_bundle_retention_custody_notice_verifications = values["evidence_bundle_retention_custody_notice_verifications"]
    latest_evidence_bundle_retention_custody_notice_verification = values["latest_evidence_bundle_retention_custody_notice_verification"]
    evidence_bundle_retention_custody_acknowledgments = values["evidence_bundle_retention_custody_acknowledgments"]
    latest_evidence_bundle_retention_custody_acknowledgment = values["latest_evidence_bundle_retention_custody_acknowledgment"]
    evidence_bundle_retention_custody_acknowledgment_verifications = values["evidence_bundle_retention_custody_acknowledgment_verifications"]
    latest_evidence_bundle_retention_custody_acknowledgment_verification = values["latest_evidence_bundle_retention_custody_acknowledgment_verification"]
    evidence_bundle_retention_custody_completions = values["evidence_bundle_retention_custody_completions"]
    latest_evidence_bundle_retention_custody_completion = values["latest_evidence_bundle_retention_custody_completion"]
    evidence_bundle_retention_custody_completion_verifications = values["evidence_bundle_retention_custody_completion_verifications"]
    latest_evidence_bundle_retention_custody_completion_verification = values["latest_evidence_bundle_retention_custody_completion_verification"]
    evidence_bundle_retention_custody_closeouts = values["evidence_bundle_retention_custody_closeouts"]
    latest_evidence_bundle_retention_custody_closeout = values["latest_evidence_bundle_retention_custody_closeout"]
    evidence_bundle_retention_custody_closeout_verifications = values["evidence_bundle_retention_custody_closeout_verifications"]
    latest_evidence_bundle_retention_custody_closeout_verification = values["latest_evidence_bundle_retention_custody_closeout_verification"]
    evidence_bundle_retention_custody_archives = values["evidence_bundle_retention_custody_archives"]
    latest_evidence_bundle_retention_custody_archive = values["latest_evidence_bundle_retention_custody_archive"]
    evidence_bundle_retention_custody_archive_verifications = values["evidence_bundle_retention_custody_archive_verifications"]
    latest_evidence_bundle_retention_custody_archive_verification = values["latest_evidence_bundle_retention_custody_archive_verification"]
    evidence_bundle_retention_custody_retrievals = values["evidence_bundle_retention_custody_retrievals"]
    latest_evidence_bundle_retention_custody_retrieval = values["latest_evidence_bundle_retention_custody_retrieval"]
    evidence_bundle_retention_custody_retrieval_verifications = values["evidence_bundle_retention_custody_retrieval_verifications"]
    latest_evidence_bundle_retention_custody_retrieval_verification = values["latest_evidence_bundle_retention_custody_retrieval_verification"]
    evidence_bundle_retention_custody_returns = values["evidence_bundle_retention_custody_returns"]
    latest_evidence_bundle_retention_custody_return = values["latest_evidence_bundle_retention_custody_return"]
    evidence_bundle_retention_custody_return_verifications = values["evidence_bundle_retention_custody_return_verifications"]
    latest_evidence_bundle_retention_custody_return_verification = values["latest_evidence_bundle_retention_custody_return_verification"]
    evidence_bundle_retention_custody_redeposits = values["evidence_bundle_retention_custody_redeposits"]
    latest_evidence_bundle_retention_custody_redeposit = values["latest_evidence_bundle_retention_custody_redeposit"]
    evidence_bundle_retention_custody_redeposit_verifications = values["evidence_bundle_retention_custody_redeposit_verifications"]
    latest_evidence_bundle_retention_custody_redeposit_verification = values["latest_evidence_bundle_retention_custody_redeposit_verification"]
    evidence_bundle_retention_custody_inventories = values["evidence_bundle_retention_custody_inventories"]
    latest_evidence_bundle_retention_custody_inventory = values["latest_evidence_bundle_retention_custody_inventory"]
    evidence_bundle_retention_custody_inventory_verifications = values["evidence_bundle_retention_custody_inventory_verifications"]
    latest_evidence_bundle_retention_custody_inventory_verification = values["latest_evidence_bundle_retention_custody_inventory_verification"]
    evidence_bundle_retention_custody_reconciliations = values["evidence_bundle_retention_custody_reconciliations"]
    latest_evidence_bundle_retention_custody_reconciliation = values["latest_evidence_bundle_retention_custody_reconciliation"]
    evidence_bundle_retention_custody_reconciliation_verifications = values["evidence_bundle_retention_custody_reconciliation_verifications"]
    latest_evidence_bundle_retention_custody_reconciliation_verification = values["latest_evidence_bundle_retention_custody_reconciliation_verification"]
    evidence_bundle_retention_custody_certifications = values["evidence_bundle_retention_custody_certifications"]
    latest_evidence_bundle_retention_custody_certification = values["latest_evidence_bundle_retention_custody_certification"]
    evidence_bundle_retention_custody_certification_verifications = values["evidence_bundle_retention_custody_certification_verifications"]
    latest_evidence_bundle_retention_custody_certification_verification = values["latest_evidence_bundle_retention_custody_certification_verification"]
    evidence_bundle_retention_custody_attestations = values["evidence_bundle_retention_custody_attestations"]
    latest_evidence_bundle_retention_custody_attestation = values["latest_evidence_bundle_retention_custody_attestation"]
    evidence_bundle_retention_custody_attestation_verifications = values["evidence_bundle_retention_custody_attestation_verifications"]
    latest_evidence_bundle_retention_custody_attestation_verification = values["latest_evidence_bundle_retention_custody_attestation_verification"]
    return {
            'evidence_bundle_count': len(evidence_bundles),
            'latest_evidence_bundle_at_utc': latest_evidence_bundle.generated_at_utc if latest_evidence_bundle else None,
            'latest_evidence_bundle_trust_banner': latest_evidence_bundle.trust_banner if latest_evidence_bundle else None,
            'latest_evidence_bundle_status': latest_evidence_bundle.bundle_status if latest_evidence_bundle else None,
            'latest_evidence_bundle_sha256': latest_evidence_bundle.bundle_sha256 if latest_evidence_bundle else None,
            'evidence_bundle_blocker_count': sum((len(row.blockers) for row in evidence_bundles)),
            'evidence_bundle_verification_count': len(evidence_bundle_verifications),
            'latest_evidence_bundle_verification_at_utc': latest_evidence_bundle_verification.generated_at_utc if latest_evidence_bundle_verification else None,
            'latest_evidence_bundle_verification_status': latest_evidence_bundle_verification.verification_status if latest_evidence_bundle_verification else None,
            'latest_evidence_bundle_verification_trust_banner': latest_evidence_bundle_verification.trust_banner if latest_evidence_bundle_verification else None,
            'latest_evidence_bundle_verification_sha256': latest_evidence_bundle_verification.artifact_sha256 if latest_evidence_bundle_verification else None,
            'evidence_bundle_verification_blocker_count': sum((len(row.blockers) for row in evidence_bundle_verifications)),
            'evidence_bundle_drift_count': len(evidence_bundle_drifts),
            'latest_evidence_bundle_drift_at_utc': latest_evidence_bundle_drift.generated_at_utc if latest_evidence_bundle_drift else None,
            'latest_evidence_bundle_drift_status': latest_evidence_bundle_drift.drift_status if latest_evidence_bundle_drift else None,
            'latest_evidence_bundle_drift_trust_banner': latest_evidence_bundle_drift.trust_banner if latest_evidence_bundle_drift else None,
            'latest_evidence_bundle_drift_sha256': latest_evidence_bundle_drift.artifact_sha256 if latest_evidence_bundle_drift else None,
            'evidence_bundle_drift_blocker_count': sum((len(row.blockers) for row in evidence_bundle_drifts)),
            'evidence_bundle_drift_new_source_count': sum((row.new_source_artifact_count for row in evidence_bundle_drifts)),
            'evidence_bundle_drift_removed_source_count': sum((row.removed_source_artifact_count for row in evidence_bundle_drifts)),
            'evidence_bundle_rotation_count': len(evidence_bundle_rotations),
            'latest_evidence_bundle_rotation_at_utc': latest_evidence_bundle_rotation.generated_at_utc if latest_evidence_bundle_rotation else None,
            'latest_evidence_bundle_rotation_status': latest_evidence_bundle_rotation.rotation_status if latest_evidence_bundle_rotation else None,
            'latest_evidence_bundle_rotation_trust_banner': latest_evidence_bundle_rotation.trust_banner if latest_evidence_bundle_rotation else None,
            'latest_evidence_bundle_rotation_sha256': latest_evidence_bundle_rotation.artifact_sha256 if latest_evidence_bundle_rotation else None,
            'evidence_bundle_rotation_blocker_count': sum((len(row.blockers) for row in evidence_bundle_rotations)),
            'evidence_bundle_rotation_execution_count': len(evidence_bundle_rotation_executions),
            'latest_evidence_bundle_rotation_execution_at_utc': latest_evidence_bundle_rotation_execution.generated_at_utc if latest_evidence_bundle_rotation_execution else None,
            'latest_evidence_bundle_rotation_execution_status': latest_evidence_bundle_rotation_execution.rotation_execution_status if latest_evidence_bundle_rotation_execution else None,
            'latest_evidence_bundle_rotation_execution_trust_banner': latest_evidence_bundle_rotation_execution.trust_banner if latest_evidence_bundle_rotation_execution else None,
            'latest_evidence_bundle_rotation_execution_sha256': latest_evidence_bundle_rotation_execution.artifact_sha256 if latest_evidence_bundle_rotation_execution else None,
            'evidence_bundle_rotation_execution_blocker_count': sum((len(row.blockers) for row in evidence_bundle_rotation_executions)),
            'evidence_bundle_attestation_count': len(evidence_bundle_attestations),
            'latest_evidence_bundle_attestation_at_utc': latest_evidence_bundle_attestation.generated_at_utc if latest_evidence_bundle_attestation else None,
            'latest_evidence_bundle_attestation_status': latest_evidence_bundle_attestation.attestation_status if latest_evidence_bundle_attestation else None,
            'latest_evidence_bundle_attestation_trust_banner': latest_evidence_bundle_attestation.trust_banner if latest_evidence_bundle_attestation else None,
            'latest_evidence_bundle_attestation_sha256': latest_evidence_bundle_attestation.artifact_sha256 if latest_evidence_bundle_attestation else None,
            'evidence_bundle_attestation_blocker_count': sum((row.blocker_count for row in evidence_bundle_attestations)),
            'evidence_bundle_attestation_verification_count': len(evidence_bundle_attestation_verifications),
            'latest_evidence_bundle_attestation_verification_at_utc': latest_evidence_bundle_attestation_verification.generated_at_utc if latest_evidence_bundle_attestation_verification else None,
            'latest_evidence_bundle_attestation_verification_status': latest_evidence_bundle_attestation_verification.verification_status if latest_evidence_bundle_attestation_verification else None,
            'latest_evidence_bundle_attestation_verification_trust_banner': latest_evidence_bundle_attestation_verification.trust_banner if latest_evidence_bundle_attestation_verification else None,
            'latest_evidence_bundle_attestation_verification_sha256': latest_evidence_bundle_attestation_verification.artifact_sha256 if latest_evidence_bundle_attestation_verification else None,
            'evidence_bundle_attestation_verification_blocker_count': sum((row.blocker_count for row in evidence_bundle_attestation_verifications)),
            'evidence_bundle_closure_count': len(evidence_bundle_closures),
            'latest_evidence_bundle_closure_at_utc': latest_evidence_bundle_closure.generated_at_utc if latest_evidence_bundle_closure else None,
            'latest_evidence_bundle_closure_status': latest_evidence_bundle_closure.closure_status if latest_evidence_bundle_closure else None,
            'latest_evidence_bundle_closure_trust_banner': latest_evidence_bundle_closure.trust_banner if latest_evidence_bundle_closure else None,
            'latest_evidence_bundle_closure_sha256': latest_evidence_bundle_closure.artifact_sha256 if latest_evidence_bundle_closure else None,
            'evidence_bundle_closure_blocker_count': sum((row.blocker_count for row in evidence_bundle_closures)),
            'evidence_bundle_closure_verification_count': len(evidence_bundle_closure_verifications),
            'latest_evidence_bundle_closure_verification_at_utc': latest_evidence_bundle_closure_verification.generated_at_utc if latest_evidence_bundle_closure_verification else None,
            'latest_evidence_bundle_closure_verification_status': latest_evidence_bundle_closure_verification.verification_status if latest_evidence_bundle_closure_verification else None,
            'latest_evidence_bundle_closure_verification_trust_banner': latest_evidence_bundle_closure_verification.trust_banner if latest_evidence_bundle_closure_verification else None,
            'latest_evidence_bundle_closure_verification_sha256': latest_evidence_bundle_closure_verification.artifact_sha256 if latest_evidence_bundle_closure_verification else None,
            'evidence_bundle_closure_verification_blocker_count': sum((row.blocker_count for row in evidence_bundle_closure_verifications)),
            'evidence_bundle_export_manifest_count': len(evidence_bundle_export_manifests),
            'latest_evidence_bundle_export_manifest_at_utc': latest_evidence_bundle_export_manifest.generated_at_utc if latest_evidence_bundle_export_manifest else None,
            'latest_evidence_bundle_export_manifest_status': latest_evidence_bundle_export_manifest.export_status if latest_evidence_bundle_export_manifest else None,
            'latest_evidence_bundle_export_manifest_trust_banner': latest_evidence_bundle_export_manifest.trust_banner if latest_evidence_bundle_export_manifest else None,
            'latest_evidence_bundle_export_manifest_sha256': latest_evidence_bundle_export_manifest.artifact_sha256 if latest_evidence_bundle_export_manifest else None,
            'evidence_bundle_export_manifest_blocker_count': sum((row.blocker_count for row in evidence_bundle_export_manifests)),
            'evidence_bundle_export_verification_count': len(evidence_bundle_export_verifications),
            'latest_evidence_bundle_export_verification_at_utc': latest_evidence_bundle_export_verification.generated_at_utc if latest_evidence_bundle_export_verification else None,
            'latest_evidence_bundle_export_verification_status': latest_evidence_bundle_export_verification.verification_status if latest_evidence_bundle_export_verification else None,
            'latest_evidence_bundle_export_verification_trust_banner': latest_evidence_bundle_export_verification.trust_banner if latest_evidence_bundle_export_verification else None,
            'latest_evidence_bundle_export_verification_sha256': latest_evidence_bundle_export_verification.artifact_sha256 if latest_evidence_bundle_export_verification else None,
            'evidence_bundle_export_verification_blocker_count': sum((row.blocker_count for row in evidence_bundle_export_verifications)),
            'evidence_bundle_retention_receipt_count': len(evidence_bundle_retention_receipts),
            'latest_evidence_bundle_retention_receipt_at_utc': latest_evidence_bundle_retention_receipt.generated_at_utc if latest_evidence_bundle_retention_receipt else None,
            'latest_evidence_bundle_retention_receipt_status': latest_evidence_bundle_retention_receipt.retention_status if latest_evidence_bundle_retention_receipt else None,
            'latest_evidence_bundle_retention_receipt_trust_banner': latest_evidence_bundle_retention_receipt.trust_banner if latest_evidence_bundle_retention_receipt else None,
            'latest_evidence_bundle_retention_receipt_sha256': latest_evidence_bundle_retention_receipt.artifact_sha256 if latest_evidence_bundle_retention_receipt else None,
            'evidence_bundle_retention_receipt_blocker_count': sum((row.blocker_count for row in evidence_bundle_retention_receipts)),
            'evidence_bundle_retention_verification_count': len(evidence_bundle_retention_verifications),
            'latest_evidence_bundle_retention_verification_at_utc': latest_evidence_bundle_retention_verification.generated_at_utc if latest_evidence_bundle_retention_verification else None,
            'latest_evidence_bundle_retention_verification_status': latest_evidence_bundle_retention_verification.verification_status if latest_evidence_bundle_retention_verification else None,
            'latest_evidence_bundle_retention_verification_trust_banner': latest_evidence_bundle_retention_verification.trust_banner if latest_evidence_bundle_retention_verification else None,
            'latest_evidence_bundle_retention_verification_sha256': latest_evidence_bundle_retention_verification.artifact_sha256 if latest_evidence_bundle_retention_verification else None,
            'evidence_bundle_retention_verification_blocker_count': sum((row.blocker_count for row in evidence_bundle_retention_verifications)),
            'evidence_bundle_retention_signoff_count': len(evidence_bundle_retention_signoffs),
            'latest_evidence_bundle_retention_signoff_at_utc': latest_evidence_bundle_retention_signoff.generated_at_utc if latest_evidence_bundle_retention_signoff else None,
            'latest_evidence_bundle_retention_signoff_status': latest_evidence_bundle_retention_signoff.signoff_status if latest_evidence_bundle_retention_signoff else None,
            'latest_evidence_bundle_retention_signoff_trust_banner': latest_evidence_bundle_retention_signoff.trust_banner if latest_evidence_bundle_retention_signoff else None,
            'latest_evidence_bundle_retention_signoff_sha256': latest_evidence_bundle_retention_signoff.artifact_sha256 if latest_evidence_bundle_retention_signoff else None,
            'evidence_bundle_retention_signoff_blocker_count': sum((row.blocker_count for row in evidence_bundle_retention_signoffs)),
            'evidence_bundle_retention_signoff_verification_count': len(evidence_bundle_retention_signoff_verifications),
            'latest_evidence_bundle_retention_signoff_verification_at_utc': latest_evidence_bundle_retention_signoff_verification.generated_at_utc if latest_evidence_bundle_retention_signoff_verification else None,
            'latest_evidence_bundle_retention_signoff_verification_status': latest_evidence_bundle_retention_signoff_verification.verification_status if latest_evidence_bundle_retention_signoff_verification else None,
            'latest_evidence_bundle_retention_signoff_verification_trust_banner': latest_evidence_bundle_retention_signoff_verification.trust_banner if latest_evidence_bundle_retention_signoff_verification else None,
            'latest_evidence_bundle_retention_signoff_verification_sha256': latest_evidence_bundle_retention_signoff_verification.artifact_sha256 if latest_evidence_bundle_retention_signoff_verification else None,
            'evidence_bundle_retention_signoff_verification_blocker_count': sum((row.blocker_count for row in evidence_bundle_retention_signoff_verifications)),
            'evidence_bundle_retention_handoff_count': len(evidence_bundle_retention_handoffs),
            'latest_evidence_bundle_retention_handoff_at_utc': latest_evidence_bundle_retention_handoff.generated_at_utc if latest_evidence_bundle_retention_handoff else None,
            'latest_evidence_bundle_retention_handoff_status': latest_evidence_bundle_retention_handoff.handoff_status if latest_evidence_bundle_retention_handoff else None,
            'latest_evidence_bundle_retention_handoff_trust_banner': latest_evidence_bundle_retention_handoff.trust_banner if latest_evidence_bundle_retention_handoff else None,
            'latest_evidence_bundle_retention_handoff_sha256': latest_evidence_bundle_retention_handoff.artifact_sha256 if latest_evidence_bundle_retention_handoff else None,
            'evidence_bundle_retention_handoff_blocker_count': sum((row.blocker_count for row in evidence_bundle_retention_handoffs)),
            'evidence_bundle_retention_handoff_verification_count': len(evidence_bundle_retention_handoff_verifications),
            'latest_evidence_bundle_retention_handoff_verification_at_utc': latest_evidence_bundle_retention_handoff_verification.generated_at_utc if latest_evidence_bundle_retention_handoff_verification else None,
            'latest_evidence_bundle_retention_handoff_verification_status': latest_evidence_bundle_retention_handoff_verification.verification_status if latest_evidence_bundle_retention_handoff_verification else None,
            'latest_evidence_bundle_retention_handoff_verification_trust_banner': latest_evidence_bundle_retention_handoff_verification.trust_banner if latest_evidence_bundle_retention_handoff_verification else None,
            'latest_evidence_bundle_retention_handoff_verification_sha256': latest_evidence_bundle_retention_handoff_verification.artifact_sha256 if latest_evidence_bundle_retention_handoff_verification else None,
            'evidence_bundle_retention_handoff_verification_blocker_count': sum((row.blocker_count for row in evidence_bundle_retention_handoff_verifications)),
            'evidence_bundle_retention_handoff_acceptance_count': len(evidence_bundle_retention_handoff_acceptances),
            'latest_evidence_bundle_retention_handoff_acceptance_at_utc': latest_evidence_bundle_retention_handoff_acceptance.generated_at_utc if latest_evidence_bundle_retention_handoff_acceptance else None,
            'latest_evidence_bundle_retention_handoff_acceptance_status': latest_evidence_bundle_retention_handoff_acceptance.acceptance_status if latest_evidence_bundle_retention_handoff_acceptance else None,
            'latest_evidence_bundle_retention_handoff_acceptance_trust_banner': latest_evidence_bundle_retention_handoff_acceptance.trust_banner if latest_evidence_bundle_retention_handoff_acceptance else None,
            'latest_evidence_bundle_retention_handoff_acceptance_sha256': latest_evidence_bundle_retention_handoff_acceptance.artifact_sha256 if latest_evidence_bundle_retention_handoff_acceptance else None,
            'evidence_bundle_retention_handoff_acceptance_blocker_count': sum((row.blocker_count for row in evidence_bundle_retention_handoff_acceptances)),
            'evidence_bundle_retention_handoff_acceptance_verification_count': len(evidence_bundle_retention_handoff_acceptance_verifications),
            'latest_evidence_bundle_retention_handoff_acceptance_verification_at_utc': latest_evidence_bundle_retention_handoff_acceptance_verification.generated_at_utc if latest_evidence_bundle_retention_handoff_acceptance_verification else None,
            'latest_evidence_bundle_retention_handoff_acceptance_verification_status': latest_evidence_bundle_retention_handoff_acceptance_verification.verification_status if latest_evidence_bundle_retention_handoff_acceptance_verification else None,
            'latest_evidence_bundle_retention_handoff_acceptance_verification_trust_banner': latest_evidence_bundle_retention_handoff_acceptance_verification.trust_banner if latest_evidence_bundle_retention_handoff_acceptance_verification else None,
            'latest_evidence_bundle_retention_handoff_acceptance_verification_sha256': latest_evidence_bundle_retention_handoff_acceptance_verification.artifact_sha256 if latest_evidence_bundle_retention_handoff_acceptance_verification else None,
            'evidence_bundle_retention_handoff_acceptance_verification_blocker_count': sum((row.blocker_count for row in evidence_bundle_retention_handoff_acceptance_verifications)),
            'evidence_bundle_retention_custody_register_count': len(evidence_bundle_retention_custody_registers),
            'latest_evidence_bundle_retention_custody_register_at_utc': latest_evidence_bundle_retention_custody_register.generated_at_utc if latest_evidence_bundle_retention_custody_register else None,
            'latest_evidence_bundle_retention_custody_register_status': latest_evidence_bundle_retention_custody_register.register_status if latest_evidence_bundle_retention_custody_register else None,
            'latest_evidence_bundle_retention_custody_register_trust_banner': latest_evidence_bundle_retention_custody_register.trust_banner if latest_evidence_bundle_retention_custody_register else None,
            'latest_evidence_bundle_retention_custody_register_sha256': latest_evidence_bundle_retention_custody_register.artifact_sha256 if latest_evidence_bundle_retention_custody_register else None,
            'evidence_bundle_retention_custody_register_blocker_count': sum((row.blocker_count for row in evidence_bundle_retention_custody_registers)),
            'evidence_bundle_retention_custody_register_verification_count': len(evidence_bundle_retention_custody_register_verifications),
            'latest_evidence_bundle_retention_custody_register_verification_at_utc': latest_evidence_bundle_retention_custody_register_verification.generated_at_utc if latest_evidence_bundle_retention_custody_register_verification else None,
            'latest_evidence_bundle_retention_custody_register_verification_status': latest_evidence_bundle_retention_custody_register_verification.verification_status if latest_evidence_bundle_retention_custody_register_verification else None,
            'latest_evidence_bundle_retention_custody_register_verification_trust_banner': latest_evidence_bundle_retention_custody_register_verification.trust_banner if latest_evidence_bundle_retention_custody_register_verification else None,
            'latest_evidence_bundle_retention_custody_register_verification_sha256': latest_evidence_bundle_retention_custody_register_verification.artifact_sha256 if latest_evidence_bundle_retention_custody_register_verification else None,
            'evidence_bundle_retention_custody_register_verification_blocker_count': sum((row.blocker_count for row in evidence_bundle_retention_custody_register_verifications)),
            'evidence_bundle_retention_custody_seal_count': len(evidence_bundle_retention_custody_seals),
            'latest_evidence_bundle_retention_custody_seal_at_utc': latest_evidence_bundle_retention_custody_seal.generated_at_utc if latest_evidence_bundle_retention_custody_seal else None,
            'latest_evidence_bundle_retention_custody_seal_status': latest_evidence_bundle_retention_custody_seal.seal_status if latest_evidence_bundle_retention_custody_seal else None,
            'latest_evidence_bundle_retention_custody_seal_trust_banner': latest_evidence_bundle_retention_custody_seal.trust_banner if latest_evidence_bundle_retention_custody_seal else None,
            'latest_evidence_bundle_retention_custody_seal_sha256': latest_evidence_bundle_retention_custody_seal.artifact_sha256 if latest_evidence_bundle_retention_custody_seal else None,
            'evidence_bundle_retention_custody_seal_blocker_count': sum((row.blocker_count for row in evidence_bundle_retention_custody_seals)),
            'evidence_bundle_retention_custody_seal_verification_count': len(evidence_bundle_retention_custody_seal_verifications),
            'latest_evidence_bundle_retention_custody_seal_verification_at_utc': latest_evidence_bundle_retention_custody_seal_verification.generated_at_utc if latest_evidence_bundle_retention_custody_seal_verification else None,
            'latest_evidence_bundle_retention_custody_seal_verification_status': latest_evidence_bundle_retention_custody_seal_verification.verification_status if latest_evidence_bundle_retention_custody_seal_verification else None,
            'latest_evidence_bundle_retention_custody_seal_verification_trust_banner': latest_evidence_bundle_retention_custody_seal_verification.trust_banner if latest_evidence_bundle_retention_custody_seal_verification else None,
            'latest_evidence_bundle_retention_custody_seal_verification_sha256': latest_evidence_bundle_retention_custody_seal_verification.artifact_sha256 if latest_evidence_bundle_retention_custody_seal_verification else None,
            'evidence_bundle_retention_custody_seal_verification_blocker_count': sum((row.blocker_count for row in evidence_bundle_retention_custody_seal_verifications)),
            'evidence_bundle_retention_custody_audit_count': len(evidence_bundle_retention_custody_audits),
            'latest_evidence_bundle_retention_custody_audit_at_utc': latest_evidence_bundle_retention_custody_audit.generated_at_utc if latest_evidence_bundle_retention_custody_audit else None,
            'latest_evidence_bundle_retention_custody_audit_status': latest_evidence_bundle_retention_custody_audit.audit_status if latest_evidence_bundle_retention_custody_audit else None,
            'latest_evidence_bundle_retention_custody_audit_trust_banner': latest_evidence_bundle_retention_custody_audit.trust_banner if latest_evidence_bundle_retention_custody_audit else None,
            'latest_evidence_bundle_retention_custody_audit_sha256': latest_evidence_bundle_retention_custody_audit.artifact_sha256 if latest_evidence_bundle_retention_custody_audit else None,
            'evidence_bundle_retention_custody_audit_blocker_count': sum((row.blocker_count for row in evidence_bundle_retention_custody_audits)),
            'evidence_bundle_retention_custody_audit_verification_count': len(evidence_bundle_retention_custody_audit_verifications),
            'latest_evidence_bundle_retention_custody_audit_verification_at_utc': latest_evidence_bundle_retention_custody_audit_verification.generated_at_utc if latest_evidence_bundle_retention_custody_audit_verification else None,
            'latest_evidence_bundle_retention_custody_audit_verification_status': latest_evidence_bundle_retention_custody_audit_verification.verification_status if latest_evidence_bundle_retention_custody_audit_verification else None,
            'latest_evidence_bundle_retention_custody_audit_verification_trust_banner': latest_evidence_bundle_retention_custody_audit_verification.trust_banner if latest_evidence_bundle_retention_custody_audit_verification else None,
            'latest_evidence_bundle_retention_custody_audit_verification_sha256': latest_evidence_bundle_retention_custody_audit_verification.artifact_sha256 if latest_evidence_bundle_retention_custody_audit_verification else None,
            'evidence_bundle_retention_custody_audit_verification_blocker_count': sum((row.blocker_count for row in evidence_bundle_retention_custody_audit_verifications)),
            'evidence_bundle_retention_custody_continuity_count': len(evidence_bundle_retention_custody_continuities),
            'latest_evidence_bundle_retention_custody_continuity_at_utc': latest_evidence_bundle_retention_custody_continuity.generated_at_utc if latest_evidence_bundle_retention_custody_continuity else None,
            'latest_evidence_bundle_retention_custody_continuity_status': latest_evidence_bundle_retention_custody_continuity.continuity_status if latest_evidence_bundle_retention_custody_continuity else None,
            'latest_evidence_bundle_retention_custody_continuity_trust_banner': latest_evidence_bundle_retention_custody_continuity.trust_banner if latest_evidence_bundle_retention_custody_continuity else None,
            'latest_evidence_bundle_retention_custody_continuity_sha256': latest_evidence_bundle_retention_custody_continuity.artifact_sha256 if latest_evidence_bundle_retention_custody_continuity else None,
            'evidence_bundle_retention_custody_continuity_blocker_count': sum((row.blocker_count for row in evidence_bundle_retention_custody_continuities)),
            'evidence_bundle_retention_custody_continuity_verification_count': len(evidence_bundle_retention_custody_continuity_verifications),
            'latest_evidence_bundle_retention_custody_continuity_verification_at_utc': latest_evidence_bundle_retention_custody_continuity_verification.generated_at_utc if latest_evidence_bundle_retention_custody_continuity_verification else None,
            'latest_evidence_bundle_retention_custody_continuity_verification_status': latest_evidence_bundle_retention_custody_continuity_verification.verification_status if latest_evidence_bundle_retention_custody_continuity_verification else None,
            'latest_evidence_bundle_retention_custody_continuity_verification_trust_banner': latest_evidence_bundle_retention_custody_continuity_verification.trust_banner if latest_evidence_bundle_retention_custody_continuity_verification else None,
            'latest_evidence_bundle_retention_custody_continuity_verification_sha256': latest_evidence_bundle_retention_custody_continuity_verification.artifact_sha256 if latest_evidence_bundle_retention_custody_continuity_verification else None,
            'evidence_bundle_retention_custody_continuity_verification_blocker_count': sum((row.blocker_count for row in evidence_bundle_retention_custody_continuity_verifications)),
            'evidence_bundle_retention_custody_review_count': len(evidence_bundle_retention_custody_reviews),
            'latest_evidence_bundle_retention_custody_review_at_utc': latest_evidence_bundle_retention_custody_review.generated_at_utc if latest_evidence_bundle_retention_custody_review else None,
            'latest_evidence_bundle_retention_custody_review_status': latest_evidence_bundle_retention_custody_review.review_status if latest_evidence_bundle_retention_custody_review else None,
            'latest_evidence_bundle_retention_custody_review_trust_banner': latest_evidence_bundle_retention_custody_review.trust_banner if latest_evidence_bundle_retention_custody_review else None,
            'latest_evidence_bundle_retention_custody_review_sha256': latest_evidence_bundle_retention_custody_review.artifact_sha256 if latest_evidence_bundle_retention_custody_review else None,
            'evidence_bundle_retention_custody_review_blocker_count': sum((row.blocker_count for row in evidence_bundle_retention_custody_reviews)),
            'evidence_bundle_retention_custody_review_verification_count': len(evidence_bundle_retention_custody_review_verifications),
            'latest_evidence_bundle_retention_custody_review_verification_at_utc': latest_evidence_bundle_retention_custody_review_verification.generated_at_utc if latest_evidence_bundle_retention_custody_review_verification else None,
            'latest_evidence_bundle_retention_custody_review_verification_status': latest_evidence_bundle_retention_custody_review_verification.verification_status if latest_evidence_bundle_retention_custody_review_verification else None,
            'latest_evidence_bundle_retention_custody_review_verification_trust_banner': latest_evidence_bundle_retention_custody_review_verification.trust_banner if latest_evidence_bundle_retention_custody_review_verification else None,
            'latest_evidence_bundle_retention_custody_review_verification_sha256': latest_evidence_bundle_retention_custody_review_verification.artifact_sha256 if latest_evidence_bundle_retention_custody_review_verification else None,
            'evidence_bundle_retention_custody_review_verification_blocker_count': sum((row.blocker_count for row in evidence_bundle_retention_custody_review_verifications)),
            'evidence_bundle_retention_custody_renewal_count': len(evidence_bundle_retention_custody_renewals),
            'latest_evidence_bundle_retention_custody_renewal_at_utc': latest_evidence_bundle_retention_custody_renewal.generated_at_utc if latest_evidence_bundle_retention_custody_renewal else None,
            'latest_evidence_bundle_retention_custody_renewal_status': latest_evidence_bundle_retention_custody_renewal.renewal_status if latest_evidence_bundle_retention_custody_renewal else None,
            'latest_evidence_bundle_retention_custody_renewal_trust_banner': latest_evidence_bundle_retention_custody_renewal.trust_banner if latest_evidence_bundle_retention_custody_renewal else None,
            'latest_evidence_bundle_retention_custody_renewal_sha256': latest_evidence_bundle_retention_custody_renewal.artifact_sha256 if latest_evidence_bundle_retention_custody_renewal else None,
            'evidence_bundle_retention_custody_renewal_blocker_count': sum((row.blocker_count for row in evidence_bundle_retention_custody_renewals)),
            'evidence_bundle_retention_custody_renewal_verification_count': len(evidence_bundle_retention_custody_renewal_verifications),
            'latest_evidence_bundle_retention_custody_renewal_verification_at_utc': latest_evidence_bundle_retention_custody_renewal_verification.generated_at_utc if latest_evidence_bundle_retention_custody_renewal_verification else None,
            'latest_evidence_bundle_retention_custody_renewal_verification_status': latest_evidence_bundle_retention_custody_renewal_verification.verification_status if latest_evidence_bundle_retention_custody_renewal_verification else None,
            'latest_evidence_bundle_retention_custody_renewal_verification_trust_banner': latest_evidence_bundle_retention_custody_renewal_verification.trust_banner if latest_evidence_bundle_retention_custody_renewal_verification else None,
            'latest_evidence_bundle_retention_custody_renewal_verification_sha256': latest_evidence_bundle_retention_custody_renewal_verification.artifact_sha256 if latest_evidence_bundle_retention_custody_renewal_verification else None,
            'evidence_bundle_retention_custody_renewal_verification_blocker_count': sum((row.blocker_count for row in evidence_bundle_retention_custody_renewal_verifications)),
            'evidence_bundle_retention_custody_schedule_count': len(evidence_bundle_retention_custody_schedules),
            'latest_evidence_bundle_retention_custody_schedule_at_utc': latest_evidence_bundle_retention_custody_schedule.generated_at_utc if latest_evidence_bundle_retention_custody_schedule else None,
            'latest_evidence_bundle_retention_custody_schedule_status': latest_evidence_bundle_retention_custody_schedule.schedule_status if latest_evidence_bundle_retention_custody_schedule else None,
            'latest_evidence_bundle_retention_custody_schedule_trust_banner': latest_evidence_bundle_retention_custody_schedule.trust_banner if latest_evidence_bundle_retention_custody_schedule else None,
            'latest_evidence_bundle_retention_custody_schedule_sha256': latest_evidence_bundle_retention_custody_schedule.artifact_sha256 if latest_evidence_bundle_retention_custody_schedule else None,
            'latest_evidence_bundle_retention_custody_schedule_due_at_utc': latest_evidence_bundle_retention_custody_schedule.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_schedule else None,
            'evidence_bundle_retention_custody_schedule_blocker_count': sum((row.blocker_count for row in evidence_bundle_retention_custody_schedules)),
            'evidence_bundle_retention_custody_schedule_verification_count': len(evidence_bundle_retention_custody_schedule_verifications),
            'latest_evidence_bundle_retention_custody_schedule_verification_at_utc': latest_evidence_bundle_retention_custody_schedule_verification.generated_at_utc if latest_evidence_bundle_retention_custody_schedule_verification else None,
            'latest_evidence_bundle_retention_custody_schedule_verification_status': latest_evidence_bundle_retention_custody_schedule_verification.verification_status if latest_evidence_bundle_retention_custody_schedule_verification else None,
            'latest_evidence_bundle_retention_custody_schedule_verification_trust_banner': latest_evidence_bundle_retention_custody_schedule_verification.trust_banner if latest_evidence_bundle_retention_custody_schedule_verification else None,
            'latest_evidence_bundle_retention_custody_schedule_verification_sha256': latest_evidence_bundle_retention_custody_schedule_verification.artifact_sha256 if latest_evidence_bundle_retention_custody_schedule_verification else None,
            'latest_evidence_bundle_retention_custody_schedule_verification_due_at_utc': latest_evidence_bundle_retention_custody_schedule_verification.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_schedule_verification else None,
            'evidence_bundle_retention_custody_schedule_verification_blocker_count': sum((row.blocker_count for row in evidence_bundle_retention_custody_schedule_verifications)),
            'evidence_bundle_retention_custody_notice_count': len(evidence_bundle_retention_custody_notices),
            'latest_evidence_bundle_retention_custody_notice_at_utc': latest_evidence_bundle_retention_custody_notice.generated_at_utc if latest_evidence_bundle_retention_custody_notice else None,
            'latest_evidence_bundle_retention_custody_notice_status': latest_evidence_bundle_retention_custody_notice.notice_status if latest_evidence_bundle_retention_custody_notice else None,
            'latest_evidence_bundle_retention_custody_notice_trust_banner': latest_evidence_bundle_retention_custody_notice.trust_banner if latest_evidence_bundle_retention_custody_notice else None,
            'latest_evidence_bundle_retention_custody_notice_sha256': latest_evidence_bundle_retention_custody_notice.artifact_sha256 if latest_evidence_bundle_retention_custody_notice else None,
            'latest_evidence_bundle_retention_custody_notice_due_at_utc': latest_evidence_bundle_retention_custody_notice.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_notice else None,
            'evidence_bundle_retention_custody_notice_blocker_count': sum((row.blocker_count for row in evidence_bundle_retention_custody_notices)),
            'evidence_bundle_retention_custody_notice_verification_count': len(evidence_bundle_retention_custody_notice_verifications),
            'latest_evidence_bundle_retention_custody_notice_verification_at_utc': latest_evidence_bundle_retention_custody_notice_verification.generated_at_utc if latest_evidence_bundle_retention_custody_notice_verification else None,
            'latest_evidence_bundle_retention_custody_notice_verification_status': latest_evidence_bundle_retention_custody_notice_verification.verification_status if latest_evidence_bundle_retention_custody_notice_verification else None,
            'latest_evidence_bundle_retention_custody_notice_verification_trust_banner': latest_evidence_bundle_retention_custody_notice_verification.trust_banner if latest_evidence_bundle_retention_custody_notice_verification else None,
            'latest_evidence_bundle_retention_custody_notice_verification_sha256': latest_evidence_bundle_retention_custody_notice_verification.artifact_sha256 if latest_evidence_bundle_retention_custody_notice_verification else None,
            'latest_evidence_bundle_retention_custody_notice_verification_due_at_utc': latest_evidence_bundle_retention_custody_notice_verification.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_notice_verification else None,
            'evidence_bundle_retention_custody_notice_verification_blocker_count': sum((row.blocker_count for row in evidence_bundle_retention_custody_notice_verifications)),
            'evidence_bundle_retention_custody_acknowledgment_count': len(evidence_bundle_retention_custody_acknowledgments),
            'latest_evidence_bundle_retention_custody_acknowledgment_at_utc': latest_evidence_bundle_retention_custody_acknowledgment.generated_at_utc if latest_evidence_bundle_retention_custody_acknowledgment else None,
            'latest_evidence_bundle_retention_custody_acknowledgment_status': latest_evidence_bundle_retention_custody_acknowledgment.acknowledgment_status if latest_evidence_bundle_retention_custody_acknowledgment else None,
            'latest_evidence_bundle_retention_custody_acknowledgment_trust_banner': latest_evidence_bundle_retention_custody_acknowledgment.trust_banner if latest_evidence_bundle_retention_custody_acknowledgment else None,
            'latest_evidence_bundle_retention_custody_acknowledgment_sha256': latest_evidence_bundle_retention_custody_acknowledgment.artifact_sha256 if latest_evidence_bundle_retention_custody_acknowledgment else None,
            'latest_evidence_bundle_retention_custody_acknowledgment_due_at_utc': latest_evidence_bundle_retention_custody_acknowledgment.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_acknowledgment else None,
            'evidence_bundle_retention_custody_acknowledgment_blocker_count': sum((row.blocker_count for row in evidence_bundle_retention_custody_acknowledgments)),
            'evidence_bundle_retention_custody_acknowledgment_verification_count': len(evidence_bundle_retention_custody_acknowledgment_verifications),
            'latest_evidence_bundle_retention_custody_acknowledgment_verification_at_utc': latest_evidence_bundle_retention_custody_acknowledgment_verification.generated_at_utc if latest_evidence_bundle_retention_custody_acknowledgment_verification else None,
            'latest_evidence_bundle_retention_custody_acknowledgment_verification_status': latest_evidence_bundle_retention_custody_acknowledgment_verification.verification_status if latest_evidence_bundle_retention_custody_acknowledgment_verification else None,
            'latest_evidence_bundle_retention_custody_acknowledgment_verification_trust_banner': latest_evidence_bundle_retention_custody_acknowledgment_verification.trust_banner if latest_evidence_bundle_retention_custody_acknowledgment_verification else None,
            'latest_evidence_bundle_retention_custody_acknowledgment_verification_sha256': latest_evidence_bundle_retention_custody_acknowledgment_verification.artifact_sha256 if latest_evidence_bundle_retention_custody_acknowledgment_verification else None,
            'latest_evidence_bundle_retention_custody_acknowledgment_verification_due_at_utc': latest_evidence_bundle_retention_custody_acknowledgment_verification.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_acknowledgment_verification else None,
            'evidence_bundle_retention_custody_acknowledgment_verification_blocker_count': sum((row.blocker_count for row in evidence_bundle_retention_custody_acknowledgment_verifications)),
            'evidence_bundle_retention_custody_completion_count': len(evidence_bundle_retention_custody_completions),
            'latest_evidence_bundle_retention_custody_completion_at_utc': latest_evidence_bundle_retention_custody_completion.generated_at_utc if latest_evidence_bundle_retention_custody_completion else None,
            'latest_evidence_bundle_retention_custody_completion_status': latest_evidence_bundle_retention_custody_completion.completion_status if latest_evidence_bundle_retention_custody_completion else None,
            'latest_evidence_bundle_retention_custody_completion_trust_banner': latest_evidence_bundle_retention_custody_completion.trust_banner if latest_evidence_bundle_retention_custody_completion else None,
            'latest_evidence_bundle_retention_custody_completion_sha256': latest_evidence_bundle_retention_custody_completion.artifact_sha256 if latest_evidence_bundle_retention_custody_completion else None,
            'latest_evidence_bundle_retention_custody_completion_due_at_utc': latest_evidence_bundle_retention_custody_completion.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_completion else None,
            'evidence_bundle_retention_custody_completion_blocker_count': sum((row.blocker_count for row in evidence_bundle_retention_custody_completions)),
            'evidence_bundle_retention_custody_completion_verification_count': len(evidence_bundle_retention_custody_completion_verifications),
            'latest_evidence_bundle_retention_custody_completion_verification_at_utc': latest_evidence_bundle_retention_custody_completion_verification.generated_at_utc if latest_evidence_bundle_retention_custody_completion_verification else None,
            'latest_evidence_bundle_retention_custody_completion_verification_status': latest_evidence_bundle_retention_custody_completion_verification.verification_status if latest_evidence_bundle_retention_custody_completion_verification else None,
            'latest_evidence_bundle_retention_custody_completion_verification_trust_banner': latest_evidence_bundle_retention_custody_completion_verification.trust_banner if latest_evidence_bundle_retention_custody_completion_verification else None,
            'latest_evidence_bundle_retention_custody_completion_verification_sha256': latest_evidence_bundle_retention_custody_completion_verification.artifact_sha256 if latest_evidence_bundle_retention_custody_completion_verification else None,
            'latest_evidence_bundle_retention_custody_completion_verification_due_at_utc': latest_evidence_bundle_retention_custody_completion_verification.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_completion_verification else None,
            'evidence_bundle_retention_custody_completion_verification_blocker_count': sum((row.blocker_count for row in evidence_bundle_retention_custody_completion_verifications)),
            'evidence_bundle_retention_custody_closeout_count': len(evidence_bundle_retention_custody_closeouts),
            'latest_evidence_bundle_retention_custody_closeout_at_utc': latest_evidence_bundle_retention_custody_closeout.generated_at_utc if latest_evidence_bundle_retention_custody_closeout else None,
            'latest_evidence_bundle_retention_custody_closeout_status': latest_evidence_bundle_retention_custody_closeout.closeout_status if latest_evidence_bundle_retention_custody_closeout else None,
            'latest_evidence_bundle_retention_custody_closeout_trust_banner': latest_evidence_bundle_retention_custody_closeout.trust_banner if latest_evidence_bundle_retention_custody_closeout else None,
            'latest_evidence_bundle_retention_custody_closeout_sha256': latest_evidence_bundle_retention_custody_closeout.artifact_sha256 if latest_evidence_bundle_retention_custody_closeout else None,
            'latest_evidence_bundle_retention_custody_closeout_due_at_utc': latest_evidence_bundle_retention_custody_closeout.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_closeout else None,
            'evidence_bundle_retention_custody_closeout_blocker_count': sum((row.blocker_count for row in evidence_bundle_retention_custody_closeouts)),
            'evidence_bundle_retention_custody_closeout_verification_count': len(evidence_bundle_retention_custody_closeout_verifications),
            'latest_evidence_bundle_retention_custody_closeout_verification_at_utc': latest_evidence_bundle_retention_custody_closeout_verification.generated_at_utc if latest_evidence_bundle_retention_custody_closeout_verification else None,
            'latest_evidence_bundle_retention_custody_closeout_verification_status': latest_evidence_bundle_retention_custody_closeout_verification.verification_status if latest_evidence_bundle_retention_custody_closeout_verification else None,
            'latest_evidence_bundle_retention_custody_closeout_verification_trust_banner': latest_evidence_bundle_retention_custody_closeout_verification.trust_banner if latest_evidence_bundle_retention_custody_closeout_verification else None,
            'latest_evidence_bundle_retention_custody_closeout_verification_sha256': latest_evidence_bundle_retention_custody_closeout_verification.artifact_sha256 if latest_evidence_bundle_retention_custody_closeout_verification else None,
            'latest_evidence_bundle_retention_custody_closeout_verification_due_at_utc': latest_evidence_bundle_retention_custody_closeout_verification.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_closeout_verification else None,
            'evidence_bundle_retention_custody_closeout_verification_blocker_count': sum((row.blocker_count for row in evidence_bundle_retention_custody_closeout_verifications)),
            'evidence_bundle_retention_custody_archive_count': len(evidence_bundle_retention_custody_archives),
            'latest_evidence_bundle_retention_custody_archive_at_utc': latest_evidence_bundle_retention_custody_archive.generated_at_utc if latest_evidence_bundle_retention_custody_archive else None,
            'latest_evidence_bundle_retention_custody_archive_status': latest_evidence_bundle_retention_custody_archive.archive_status if latest_evidence_bundle_retention_custody_archive else None,
            'latest_evidence_bundle_retention_custody_archive_trust_banner': latest_evidence_bundle_retention_custody_archive.trust_banner if latest_evidence_bundle_retention_custody_archive else None,
            'latest_evidence_bundle_retention_custody_archive_sha256': latest_evidence_bundle_retention_custody_archive.artifact_sha256 if latest_evidence_bundle_retention_custody_archive else None,
            'latest_evidence_bundle_retention_custody_archive_due_at_utc': latest_evidence_bundle_retention_custody_archive.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_archive else None,
            'evidence_bundle_retention_custody_archive_blocker_count': sum((row.blocker_count for row in evidence_bundle_retention_custody_archives)),
            'evidence_bundle_retention_custody_archive_verification_count': len(evidence_bundle_retention_custody_archive_verifications),
            'latest_evidence_bundle_retention_custody_archive_verification_at_utc': latest_evidence_bundle_retention_custody_archive_verification.generated_at_utc if latest_evidence_bundle_retention_custody_archive_verification else None,
            'latest_evidence_bundle_retention_custody_archive_verification_status': latest_evidence_bundle_retention_custody_archive_verification.verification_status if latest_evidence_bundle_retention_custody_archive_verification else None,
            'latest_evidence_bundle_retention_custody_archive_verification_trust_banner': latest_evidence_bundle_retention_custody_archive_verification.trust_banner if latest_evidence_bundle_retention_custody_archive_verification else None,
            'latest_evidence_bundle_retention_custody_archive_verification_sha256': latest_evidence_bundle_retention_custody_archive_verification.artifact_sha256 if latest_evidence_bundle_retention_custody_archive_verification else None,
            'latest_evidence_bundle_retention_custody_archive_verification_due_at_utc': latest_evidence_bundle_retention_custody_archive_verification.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_archive_verification else None,
            'evidence_bundle_retention_custody_archive_verification_blocker_count': sum((row.blocker_count for row in evidence_bundle_retention_custody_archive_verifications)),
            'evidence_bundle_retention_custody_retrieval_count': len(evidence_bundle_retention_custody_retrievals),
            'latest_evidence_bundle_retention_custody_retrieval_at_utc': latest_evidence_bundle_retention_custody_retrieval.generated_at_utc if latest_evidence_bundle_retention_custody_retrieval else None,
            'latest_evidence_bundle_retention_custody_retrieval_status': latest_evidence_bundle_retention_custody_retrieval.retrieval_status if latest_evidence_bundle_retention_custody_retrieval else None,
            'latest_evidence_bundle_retention_custody_retrieval_trust_banner': latest_evidence_bundle_retention_custody_retrieval.trust_banner if latest_evidence_bundle_retention_custody_retrieval else None,
            'latest_evidence_bundle_retention_custody_retrieval_sha256': latest_evidence_bundle_retention_custody_retrieval.artifact_sha256 if latest_evidence_bundle_retention_custody_retrieval else None,
            'latest_evidence_bundle_retention_custody_retrieval_due_at_utc': latest_evidence_bundle_retention_custody_retrieval.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_retrieval else None,
            'evidence_bundle_retention_custody_retrieval_blocker_count': sum((row.blocker_count for row in evidence_bundle_retention_custody_retrievals)),
            'evidence_bundle_retention_custody_retrieval_verification_count': len(evidence_bundle_retention_custody_retrieval_verifications),
            'latest_evidence_bundle_retention_custody_retrieval_verification_at_utc': latest_evidence_bundle_retention_custody_retrieval_verification.generated_at_utc if latest_evidence_bundle_retention_custody_retrieval_verification else None,
            'latest_evidence_bundle_retention_custody_retrieval_verification_status': latest_evidence_bundle_retention_custody_retrieval_verification.verification_status if latest_evidence_bundle_retention_custody_retrieval_verification else None,
            'latest_evidence_bundle_retention_custody_retrieval_verification_trust_banner': latest_evidence_bundle_retention_custody_retrieval_verification.trust_banner if latest_evidence_bundle_retention_custody_retrieval_verification else None,
            'latest_evidence_bundle_retention_custody_retrieval_verification_sha256': latest_evidence_bundle_retention_custody_retrieval_verification.artifact_sha256 if latest_evidence_bundle_retention_custody_retrieval_verification else None,
            'latest_evidence_bundle_retention_custody_retrieval_verification_due_at_utc': latest_evidence_bundle_retention_custody_retrieval_verification.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_retrieval_verification else None,
            'evidence_bundle_retention_custody_retrieval_verification_blocker_count': sum((row.blocker_count for row in evidence_bundle_retention_custody_retrieval_verifications)),
            'evidence_bundle_retention_custody_return_count': len(evidence_bundle_retention_custody_returns),
            'latest_evidence_bundle_retention_custody_return_at_utc': latest_evidence_bundle_retention_custody_return.generated_at_utc if latest_evidence_bundle_retention_custody_return else None,
            'latest_evidence_bundle_retention_custody_return_status': latest_evidence_bundle_retention_custody_return.return_status if latest_evidence_bundle_retention_custody_return else None,
            'latest_evidence_bundle_retention_custody_return_trust_banner': latest_evidence_bundle_retention_custody_return.trust_banner if latest_evidence_bundle_retention_custody_return else None,
            'latest_evidence_bundle_retention_custody_return_sha256': latest_evidence_bundle_retention_custody_return.artifact_sha256 if latest_evidence_bundle_retention_custody_return else None,
            'latest_evidence_bundle_retention_custody_return_due_at_utc': latest_evidence_bundle_retention_custody_return.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_return else None,
            'evidence_bundle_retention_custody_return_blocker_count': sum((row.blocker_count for row in evidence_bundle_retention_custody_returns)),
            'evidence_bundle_retention_custody_return_verification_count': len(evidence_bundle_retention_custody_return_verifications),
            'latest_evidence_bundle_retention_custody_return_verification_at_utc': latest_evidence_bundle_retention_custody_return_verification.generated_at_utc if latest_evidence_bundle_retention_custody_return_verification else None,
            'latest_evidence_bundle_retention_custody_return_verification_status': latest_evidence_bundle_retention_custody_return_verification.verification_status if latest_evidence_bundle_retention_custody_return_verification else None,
            'latest_evidence_bundle_retention_custody_return_verification_trust_banner': latest_evidence_bundle_retention_custody_return_verification.trust_banner if latest_evidence_bundle_retention_custody_return_verification else None,
            'latest_evidence_bundle_retention_custody_return_verification_sha256': latest_evidence_bundle_retention_custody_return_verification.artifact_sha256 if latest_evidence_bundle_retention_custody_return_verification else None,
            'latest_evidence_bundle_retention_custody_return_verification_due_at_utc': latest_evidence_bundle_retention_custody_return_verification.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_return_verification else None,
            'evidence_bundle_retention_custody_return_verification_blocker_count': sum((row.blocker_count for row in evidence_bundle_retention_custody_return_verifications)),
            'evidence_bundle_retention_custody_redeposit_count': len(evidence_bundle_retention_custody_redeposits),
            'latest_evidence_bundle_retention_custody_redeposit_at_utc': latest_evidence_bundle_retention_custody_redeposit.generated_at_utc if latest_evidence_bundle_retention_custody_redeposit else None,
            'latest_evidence_bundle_retention_custody_redeposit_status': latest_evidence_bundle_retention_custody_redeposit.redeposit_status if latest_evidence_bundle_retention_custody_redeposit else None,
            'latest_evidence_bundle_retention_custody_redeposit_trust_banner': latest_evidence_bundle_retention_custody_redeposit.trust_banner if latest_evidence_bundle_retention_custody_redeposit else None,
            'latest_evidence_bundle_retention_custody_redeposit_sha256': latest_evidence_bundle_retention_custody_redeposit.artifact_sha256 if latest_evidence_bundle_retention_custody_redeposit else None,
            'latest_evidence_bundle_retention_custody_redeposit_due_at_utc': latest_evidence_bundle_retention_custody_redeposit.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_redeposit else None,
            'evidence_bundle_retention_custody_redeposit_blocker_count': sum((row.blocker_count for row in evidence_bundle_retention_custody_redeposits)),
            'evidence_bundle_retention_custody_redeposit_verification_count': len(evidence_bundle_retention_custody_redeposit_verifications),
            'latest_evidence_bundle_retention_custody_redeposit_verification_at_utc': latest_evidence_bundle_retention_custody_redeposit_verification.generated_at_utc if latest_evidence_bundle_retention_custody_redeposit_verification else None,
            'latest_evidence_bundle_retention_custody_redeposit_verification_status': latest_evidence_bundle_retention_custody_redeposit_verification.verification_status if latest_evidence_bundle_retention_custody_redeposit_verification else None,
            'latest_evidence_bundle_retention_custody_redeposit_verification_trust_banner': latest_evidence_bundle_retention_custody_redeposit_verification.trust_banner if latest_evidence_bundle_retention_custody_redeposit_verification else None,
            'latest_evidence_bundle_retention_custody_redeposit_verification_sha256': latest_evidence_bundle_retention_custody_redeposit_verification.artifact_sha256 if latest_evidence_bundle_retention_custody_redeposit_verification else None,
            'latest_evidence_bundle_retention_custody_redeposit_verification_due_at_utc': latest_evidence_bundle_retention_custody_redeposit_verification.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_redeposit_verification else None,
            'evidence_bundle_retention_custody_redeposit_verification_blocker_count': sum((row.blocker_count for row in evidence_bundle_retention_custody_redeposit_verifications)),
            'evidence_bundle_retention_custody_inventory_count': len(evidence_bundle_retention_custody_inventories),
            'latest_evidence_bundle_retention_custody_inventory_at_utc': latest_evidence_bundle_retention_custody_inventory.generated_at_utc if latest_evidence_bundle_retention_custody_inventory else None,
            'latest_evidence_bundle_retention_custody_inventory_status': latest_evidence_bundle_retention_custody_inventory.inventory_status if latest_evidence_bundle_retention_custody_inventory else None,
            'latest_evidence_bundle_retention_custody_inventory_trust_banner': latest_evidence_bundle_retention_custody_inventory.trust_banner if latest_evidence_bundle_retention_custody_inventory else None,
            'latest_evidence_bundle_retention_custody_inventory_sha256': latest_evidence_bundle_retention_custody_inventory.artifact_sha256 if latest_evidence_bundle_retention_custody_inventory else None,
            'latest_evidence_bundle_retention_custody_inventory_due_at_utc': latest_evidence_bundle_retention_custody_inventory.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_inventory else None,
            'evidence_bundle_retention_custody_inventory_blocker_count': sum((row.blocker_count for row in evidence_bundle_retention_custody_inventories)),
            'evidence_bundle_retention_custody_inventory_verification_count': len(evidence_bundle_retention_custody_inventory_verifications),
            'latest_evidence_bundle_retention_custody_inventory_verification_at_utc': latest_evidence_bundle_retention_custody_inventory_verification.generated_at_utc if latest_evidence_bundle_retention_custody_inventory_verification else None,
            'latest_evidence_bundle_retention_custody_inventory_verification_status': latest_evidence_bundle_retention_custody_inventory_verification.verification_status if latest_evidence_bundle_retention_custody_inventory_verification else None,
            'latest_evidence_bundle_retention_custody_inventory_verification_trust_banner': latest_evidence_bundle_retention_custody_inventory_verification.trust_banner if latest_evidence_bundle_retention_custody_inventory_verification else None,
            'latest_evidence_bundle_retention_custody_inventory_verification_sha256': latest_evidence_bundle_retention_custody_inventory_verification.artifact_sha256 if latest_evidence_bundle_retention_custody_inventory_verification else None,
            'latest_evidence_bundle_retention_custody_inventory_verification_due_at_utc': latest_evidence_bundle_retention_custody_inventory_verification.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_inventory_verification else None,
            'evidence_bundle_retention_custody_inventory_verification_blocker_count': sum((row.blocker_count for row in evidence_bundle_retention_custody_inventory_verifications)),
            'evidence_bundle_retention_custody_reconciliation_count': len(evidence_bundle_retention_custody_reconciliations),
            'latest_evidence_bundle_retention_custody_reconciliation_at_utc': latest_evidence_bundle_retention_custody_reconciliation.generated_at_utc if latest_evidence_bundle_retention_custody_reconciliation else None,
            'latest_evidence_bundle_retention_custody_reconciliation_status': latest_evidence_bundle_retention_custody_reconciliation.reconciliation_status if latest_evidence_bundle_retention_custody_reconciliation else None,
            'latest_evidence_bundle_retention_custody_reconciliation_trust_banner': latest_evidence_bundle_retention_custody_reconciliation.trust_banner if latest_evidence_bundle_retention_custody_reconciliation else None,
            'latest_evidence_bundle_retention_custody_reconciliation_sha256': latest_evidence_bundle_retention_custody_reconciliation.artifact_sha256 if latest_evidence_bundle_retention_custody_reconciliation else None,
            'latest_evidence_bundle_retention_custody_reconciliation_due_at_utc': latest_evidence_bundle_retention_custody_reconciliation.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_reconciliation else None,
            'evidence_bundle_retention_custody_reconciliation_blocker_count': sum((row.blocker_count for row in evidence_bundle_retention_custody_reconciliations)),
            'evidence_bundle_retention_custody_reconciliation_verification_count': len(evidence_bundle_retention_custody_reconciliation_verifications),
            'latest_evidence_bundle_retention_custody_reconciliation_verification_at_utc': latest_evidence_bundle_retention_custody_reconciliation_verification.generated_at_utc if latest_evidence_bundle_retention_custody_reconciliation_verification else None,
            'latest_evidence_bundle_retention_custody_reconciliation_verification_status': latest_evidence_bundle_retention_custody_reconciliation_verification.verification_status if latest_evidence_bundle_retention_custody_reconciliation_verification else None,
            'latest_evidence_bundle_retention_custody_reconciliation_verification_trust_banner': latest_evidence_bundle_retention_custody_reconciliation_verification.trust_banner if latest_evidence_bundle_retention_custody_reconciliation_verification else None,
            'latest_evidence_bundle_retention_custody_reconciliation_verification_sha256': latest_evidence_bundle_retention_custody_reconciliation_verification.artifact_sha256 if latest_evidence_bundle_retention_custody_reconciliation_verification else None,
            'latest_evidence_bundle_retention_custody_reconciliation_verification_due_at_utc': latest_evidence_bundle_retention_custody_reconciliation_verification.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_reconciliation_verification else None,
            'evidence_bundle_retention_custody_reconciliation_verification_blocker_count': sum((row.blocker_count for row in evidence_bundle_retention_custody_reconciliation_verifications)),
            'evidence_bundle_retention_custody_certification_count': len(evidence_bundle_retention_custody_certifications),
            'latest_evidence_bundle_retention_custody_certification_at_utc': latest_evidence_bundle_retention_custody_certification.generated_at_utc if latest_evidence_bundle_retention_custody_certification else None,
            'latest_evidence_bundle_retention_custody_certification_status': latest_evidence_bundle_retention_custody_certification.certification_status if latest_evidence_bundle_retention_custody_certification else None,
            'latest_evidence_bundle_retention_custody_certification_trust_banner': latest_evidence_bundle_retention_custody_certification.trust_banner if latest_evidence_bundle_retention_custody_certification else None,
            'latest_evidence_bundle_retention_custody_certification_sha256': latest_evidence_bundle_retention_custody_certification.artifact_sha256 if latest_evidence_bundle_retention_custody_certification else None,
            'latest_evidence_bundle_retention_custody_certification_due_at_utc': latest_evidence_bundle_retention_custody_certification.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_certification else None,
            'evidence_bundle_retention_custody_certification_blocker_count': sum((row.blocker_count for row in evidence_bundle_retention_custody_certifications)),
            'evidence_bundle_retention_custody_certification_verification_count': len(evidence_bundle_retention_custody_certification_verifications),
            'latest_evidence_bundle_retention_custody_certification_verification_at_utc': latest_evidence_bundle_retention_custody_certification_verification.generated_at_utc if latest_evidence_bundle_retention_custody_certification_verification else None,
            'latest_evidence_bundle_retention_custody_certification_verification_status': latest_evidence_bundle_retention_custody_certification_verification.verification_status if latest_evidence_bundle_retention_custody_certification_verification else None,
            'latest_evidence_bundle_retention_custody_certification_verification_trust_banner': latest_evidence_bundle_retention_custody_certification_verification.trust_banner if latest_evidence_bundle_retention_custody_certification_verification else None,
            'latest_evidence_bundle_retention_custody_certification_verification_sha256': latest_evidence_bundle_retention_custody_certification_verification.artifact_sha256 if latest_evidence_bundle_retention_custody_certification_verification else None,
            'latest_evidence_bundle_retention_custody_certification_verification_due_at_utc': latest_evidence_bundle_retention_custody_certification_verification.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_certification_verification else None,
            'evidence_bundle_retention_custody_certification_verification_blocker_count': sum((row.blocker_count for row in evidence_bundle_retention_custody_certification_verifications)),
            'evidence_bundle_retention_custody_attestation_count': len(evidence_bundle_retention_custody_attestations),
            'latest_evidence_bundle_retention_custody_attestation_at_utc': latest_evidence_bundle_retention_custody_attestation.generated_at_utc if latest_evidence_bundle_retention_custody_attestation else None,
            'latest_evidence_bundle_retention_custody_attestation_status': latest_evidence_bundle_retention_custody_attestation.attestation_status if latest_evidence_bundle_retention_custody_attestation else None,
            'latest_evidence_bundle_retention_custody_attestation_trust_banner': latest_evidence_bundle_retention_custody_attestation.trust_banner if latest_evidence_bundle_retention_custody_attestation else None,
            'latest_evidence_bundle_retention_custody_attestation_sha256': latest_evidence_bundle_retention_custody_attestation.artifact_sha256 if latest_evidence_bundle_retention_custody_attestation else None,
            'latest_evidence_bundle_retention_custody_attestation_due_at_utc': latest_evidence_bundle_retention_custody_attestation.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_attestation else None,
            'evidence_bundle_retention_custody_attestation_blocker_count': sum((row.blocker_count for row in evidence_bundle_retention_custody_attestations)),
            'evidence_bundle_retention_custody_attestation_verification_count': len(evidence_bundle_retention_custody_attestation_verifications),
            'latest_evidence_bundle_retention_custody_attestation_verification_at_utc': latest_evidence_bundle_retention_custody_attestation_verification.generated_at_utc if latest_evidence_bundle_retention_custody_attestation_verification else None,
            'latest_evidence_bundle_retention_custody_attestation_verification_status': latest_evidence_bundle_retention_custody_attestation_verification.verification_status if latest_evidence_bundle_retention_custody_attestation_verification else None,
            'latest_evidence_bundle_retention_custody_attestation_verification_trust_banner': latest_evidence_bundle_retention_custody_attestation_verification.trust_banner if latest_evidence_bundle_retention_custody_attestation_verification else None,
            'latest_evidence_bundle_retention_custody_attestation_verification_sha256': latest_evidence_bundle_retention_custody_attestation_verification.artifact_sha256 if latest_evidence_bundle_retention_custody_attestation_verification else None,
            'latest_evidence_bundle_retention_custody_attestation_verification_due_at_utc': latest_evidence_bundle_retention_custody_attestation_verification.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_attestation_verification else None,
            'evidence_bundle_retention_custody_attestation_verification_blocker_count': sum((row.blocker_count for row in evidence_bundle_retention_custody_attestation_verifications)),
        }

__all__ = ["build_evidence_lifecycle_summary_kwargs"]
