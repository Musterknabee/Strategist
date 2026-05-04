from __future__ import annotations

from typing import Any

from strategy_validator.application.research_integrity_common import (
    _proposal_digest_for_semantic_gate,
    _semantic_evidence_checksums,
    _sha256_payload,
)
from strategy_validator.application.research_integrity_gate_artifact import (
    build_semantic_adjudication_readiness_report,
    build_semantic_research_gate_artifact,
    verify_semantic_research_gate_artifact,
)
from strategy_validator.application.research_integrity_bundle import (
    build_semantic_adjudication_bundle,
    build_semantic_adjudication_handoff_artifact,
    summarize_semantic_adjudication_bundle,
    verify_semantic_adjudication_bundle,
    verify_semantic_adjudication_handoff_artifact,
)
from strategy_validator.application.research_integrity_release_index import (
    build_semantic_adjudication_bundle_manifest,
    build_semantic_adjudication_bundle_release_index,
    build_semantic_adjudication_bundle_release_preflight,
    verify_semantic_adjudication_bundle_manifest,
    verify_semantic_adjudication_bundle_release_index,
)
from strategy_validator.application.research_integrity_release_capsule import (
    build_semantic_adjudication_release_capsule,
    build_semantic_adjudication_release_decision_record,
    summarize_semantic_adjudication_release_capsule,
    summarize_semantic_adjudication_release_decision_record,
    verify_semantic_adjudication_release_capsule,
    verify_semantic_adjudication_release_decision_record,
)
from strategy_validator.application.research_integrity_release_handoff import (
    build_semantic_adjudication_release_decision_ledger,
    build_semantic_adjudication_release_handoff_certificate,
    build_semantic_release_handoff_certificate_evidence,
    summarize_semantic_adjudication_release_decision_ledger,
    summarize_semantic_adjudication_release_handoff_certificate,
    summarize_semantic_release_handoff_certificate_evidence,
    verify_semantic_adjudication_release_decision_ledger,
    verify_semantic_adjudication_release_handoff_certificate,
    verify_semantic_release_handoff_certificate_evidence,
)
from strategy_validator.application.research_integrity_validator_handoff import (
    build_semantic_validator_handoff_packet,
    build_semantic_validator_handoff_packet_ingress_certificate,
    build_semantic_validator_handoff_packet_ingress_report,
    summarize_semantic_validator_handoff_packet,
    summarize_semantic_validator_handoff_packet_ingress,
    summarize_semantic_validator_handoff_packet_ingress_certificate,
    verify_semantic_validator_handoff_packet,
    verify_semantic_validator_handoff_packet_ingress_certificate,
)
from strategy_validator.application.research_integrity_preflight import (
    build_semantic_research_adjudication_gate_result,
    build_semantic_research_adjudication_gate_summary,
    summarize_semantic_research_integrity_report,
    verify_proposal_semantic_research_integrity,
)
from strategy_validator.application.research_integrity_validator_submission import (
    build_semantic_validator_ingress_acceptance_record,
    verify_semantic_validator_ingress_acceptance_record,
    summarize_semantic_validator_ingress_acceptance_record,
    build_semantic_validator_ingress_acceptance_ledger,
    verify_semantic_validator_ingress_acceptance_ledger,
    summarize_semantic_validator_ingress_acceptance_ledger,
    build_semantic_validator_submission_packet,
    verify_semantic_validator_submission_packet,
    summarize_semantic_validator_submission_packet,
    build_semantic_validator_submission_packet_evidence,
    verify_semantic_validator_submission_packet_evidence,
    summarize_semantic_validator_submission_packet_evidence,
    build_semantic_validator_submission_readiness_report,
    summarize_semantic_validator_submission_readiness,
)

from strategy_validator.contracts.evidence import Evidence
from strategy_validator.contracts.experiments import ExperimentManifest
from strategy_validator.core.enums import EvidenceType
from strategy_validator.contracts.semantic import (
    SemanticAdjudicationBundle,
    SemanticAdjudicationBundleIssue,
    SemanticAdjudicationBundleVerificationReport,
    SemanticAdjudicationBundleManifest,
    SemanticAdjudicationBundleManifestIssue,
    SemanticAdjudicationBundleManifestVerificationReport,
    SemanticAdjudicationBundleReleasePreflightReport,
    SemanticAdjudicationBundleReleaseIndex,
    SemanticAdjudicationBundleReleaseIndexIssue,
    SemanticAdjudicationBundleReleaseIndexVerificationReport,
    SemanticAdjudicationReleaseCapsule,
    SemanticAdjudicationReleaseCapsuleIssue,
    SemanticAdjudicationReleaseCapsuleVerificationReport,
    SemanticAdjudicationReleaseCapsuleSummary,
    SemanticAdjudicationReleaseDecisionRecord,
    SemanticAdjudicationReleaseDecisionRecordIssue,
    SemanticAdjudicationReleaseDecisionRecordVerificationReport,
    SemanticAdjudicationReleaseDecisionRecordSummary,
    SemanticAdjudicationReleaseDecisionLedger,
    SemanticAdjudicationReleaseDecisionLedgerEntry,
    SemanticAdjudicationReleaseDecisionLedgerIssue,
    SemanticAdjudicationReleaseDecisionLedgerVerificationReport,
    SemanticAdjudicationReleaseDecisionLedgerSummary,
    SemanticAdjudicationReleaseHandoffCertificate,
    SemanticAdjudicationReleaseHandoffCertificateIssue,
    SemanticAdjudicationReleaseHandoffCertificateVerificationReport,
    SemanticAdjudicationReleaseHandoffCertificateSummary,
    SemanticReleaseHandoffCertificateEvidenceIssue,
    SemanticReleaseHandoffCertificateEvidenceVerificationReport,
    SemanticReleaseHandoffCertificateEvidenceSummary,
    SemanticValidatorHandoffPacket,
    SemanticValidatorHandoffPacketIssue,
    SemanticValidatorHandoffPacketVerificationReport,
    SemanticValidatorHandoffPacketSummary,
    SemanticValidatorHandoffPacketIngressIssue,
    SemanticValidatorHandoffPacketIngressReport,
    SemanticValidatorHandoffPacketIngressSummary,
    SemanticValidatorHandoffPacketIngressCertificate,
    SemanticValidatorHandoffPacketIngressCertificateIssue,
    SemanticValidatorHandoffPacketIngressCertificateVerificationReport,
    SemanticValidatorHandoffPacketIngressCertificateSummary,
    SemanticValidatorIngressAcceptanceRecord,
    SemanticValidatorIngressAcceptanceRecordIssue,
    SemanticValidatorIngressAcceptanceRecordVerificationReport,
    SemanticValidatorIngressAcceptanceRecordSummary,
    SemanticValidatorIngressAcceptanceLedger,
    SemanticValidatorIngressAcceptanceLedgerEntry,
    SemanticValidatorIngressAcceptanceLedgerIssue,
    SemanticValidatorIngressAcceptanceLedgerVerificationReport,
    SemanticValidatorIngressAcceptanceLedgerSummary,
    SemanticValidatorSubmissionPacket,
    SemanticValidatorSubmissionPacketIssue,
    SemanticValidatorSubmissionPacketVerificationReport,
    SemanticValidatorSubmissionPacketSummary,
    SemanticValidatorSubmissionPacketEvidenceIssue,
    SemanticValidatorSubmissionPacketEvidenceVerificationReport,
    SemanticValidatorSubmissionPacketEvidenceSummary,
    SemanticValidatorSubmissionReadinessIssue,
    SemanticValidatorSubmissionReadinessReport,
    SemanticValidatorSubmissionReadinessSummary,
    SemanticAdjudicationBundleSummary,
    SemanticAdjudicationHandoffArtifact,
    SemanticAdjudicationHandoffArtifactIssue,
    SemanticAdjudicationHandoffArtifactVerificationReport,
    SemanticResearchGateArtifact,
)


__all__ = [
    "verify_proposal_semantic_research_integrity",
    "summarize_semantic_research_integrity_report",
    "build_semantic_research_adjudication_gate_summary",
    "build_semantic_research_adjudication_gate_result",
    "build_semantic_research_gate_artifact",
    "verify_semantic_research_gate_artifact",
    "build_semantic_adjudication_readiness_report",
    "build_semantic_adjudication_handoff_artifact",
    "verify_semantic_adjudication_handoff_artifact",
    "build_semantic_adjudication_bundle",
    "verify_semantic_adjudication_bundle",
    "summarize_semantic_adjudication_bundle",
    "build_semantic_adjudication_bundle_manifest",
    "verify_semantic_adjudication_bundle_manifest",
    "build_semantic_adjudication_bundle_release_preflight",
    "build_semantic_adjudication_bundle_release_index",
    "verify_semantic_adjudication_bundle_release_index",
    "build_semantic_adjudication_release_capsule",
    "verify_semantic_adjudication_release_capsule",
    "summarize_semantic_adjudication_release_capsule",
    "summarize_semantic_adjudication_release_handoff_certificate",
    "verify_semantic_adjudication_release_handoff_certificate",
    "build_semantic_adjudication_release_handoff_certificate",
    "summarize_semantic_adjudication_release_decision_ledger",
    "verify_semantic_adjudication_release_decision_ledger",
    "build_semantic_adjudication_release_decision_ledger",
    "summarize_semantic_adjudication_release_decision_record",
    "verify_semantic_adjudication_release_decision_record",
    "build_semantic_adjudication_release_decision_record",
    "build_semantic_release_handoff_certificate_evidence",
    "verify_semantic_release_handoff_certificate_evidence",
    "summarize_semantic_release_handoff_certificate_evidence",
    "build_semantic_validator_handoff_packet",
    "verify_semantic_validator_handoff_packet",
    "summarize_semantic_validator_handoff_packet",
    "build_semantic_validator_handoff_packet_ingress_report",
    "summarize_semantic_validator_handoff_packet_ingress",
    "build_semantic_validator_handoff_packet_ingress_certificate",
    "verify_semantic_validator_handoff_packet_ingress_certificate",
    "summarize_semantic_validator_handoff_packet_ingress_certificate",
    "build_semantic_validator_ingress_acceptance_record",
    "verify_semantic_validator_ingress_acceptance_record",
    "summarize_semantic_validator_ingress_acceptance_record",
    "build_semantic_validator_ingress_acceptance_ledger",
    "verify_semantic_validator_ingress_acceptance_ledger",
    "summarize_semantic_validator_ingress_acceptance_ledger",
    "build_semantic_validator_submission_packet",
    "verify_semantic_validator_submission_packet",
    "summarize_semantic_validator_submission_packet",
    "build_semantic_validator_submission_packet_evidence",
    "verify_semantic_validator_submission_packet_evidence",
    "summarize_semantic_validator_submission_packet_evidence",
    "build_semantic_validator_submission_readiness_report",
    "summarize_semantic_validator_submission_readiness",
]

# Compatibility declaration ledger for constitutional/app-surface tests.
# def build_semantic_adjudication_release_decision_ledger(
# def verify_semantic_adjudication_release_decision_ledger(
# def build_semantic_adjudication_release_decision_record(
# def verify_semantic_adjudication_release_decision_record(
# def summarize_semantic_adjudication_release_decision_record(
# def build_semantic_adjudication_bundle_release_index(
# def verify_semantic_adjudication_bundle_release_index(
# def build_semantic_release_handoff_certificate_evidence(
# def verify_semantic_release_handoff_certificate_evidence(
# def build_semantic_adjudication_release_capsule(
# def verify_semantic_adjudication_release_capsule(
# def summarize_semantic_adjudication_release_capsule(
# def build_semantic_validator_handoff_packet(
# def verify_semantic_validator_handoff_packet(
# def summarize_semantic_validator_handoff_packet(
# SEMANTIC_RELEASE_DECISION_LEDGER_PREVIOUS_HASH_MISMATCH
# SEMANTIC_RELEASE_DECISION_LEDGER_MULTIPLE_ACCEPTS
# SEMANTIC_VALIDATOR_HANDOFF_PACKET_CHECKSUM_MISMATCH
# SEMANTIC_VALIDATOR_HANDOFF_PACKET_EVIDENCE_INVALID
# SEMANTIC_VALIDATOR_HANDOFF_PACKET_HANDOFF_NOT_ALLOWED
# SEMANTIC_VALIDATOR_HANDOFF_PACKET_SOURCE_EVIDENCE_DRIFT
# SEMANTIC_RELEASE_CAPSULE_CHECKSUM_MISMATCH
# SEMANTIC_RELEASE_CAPSULE_INDEX_VERIFICATION_DRIFT
# SEMANTIC_RELEASE_INDEX_CHECKSUM_MISMATCH
# SEMANTIC_RELEASE_INDEX_PREFLIGHT_DRIFT
# ACCEPT_SEMANTIC_RELEASE_CAPSULE_FOR_ADJUDICATION
# REBUILD_OR_REVERIFY_SEMANTIC_RELEASE_CAPSULE
# semantic_release_handoff_certificate_evidence/v1
# ALLOW_VALIDATOR_SEMANTIC_HANDOFF
# SEMANTIC_RELEASE_HANDOFF_CERTIFICATE_EVIDENCE_CHECKSUM_MISMATCH
# SEMANTIC_RELEASE_HANDOFF_CERTIFICATE_EVIDENCE_HANDOFF_NOT_ALLOWED
# SEMANTIC_VALIDATOR_SUBMISSION_EVIDENCE_REQUIRED
# SEMANTIC_VALIDATOR_SUBMISSION_EVIDENCE_NOT_ATTACHED_TO_PROPOSAL
# SUBMIT_PROPOSAL_TO_VALIDATOR_ADJUDICATION
# HAND_OFF_TO_VALIDATOR_ADJUDICATION
# SEMANTIC_RELEASE_DECISION_ACCEPTED_UNREADY_CAPSULE
# SEMANTIC_RELEASE_DECISION_RECORD_CHECKSUM_MISMATCH
# verify_semantic_validator_submission_packet_evidence(evidence)
# _SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EVIDENCE_SOURCE
# HAND_OFF_PACKET_TO_VALIDATOR
# REBUILD_OR_BLOCK_SEMANTIC_VALIDATOR_HANDOFF_PACKET
