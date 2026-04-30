from __future__ import annotations

from strategy_validator.contracts.semantic_core import NonEmptyString, SemanticBaseModel
from strategy_validator.contracts.semantic_feature_materialization import (
    FeatureFactoryArtifact,
    SemanticFeatureRow,
    SemanticResearchFeatureMaterialization,
    SemanticMaterializationEvidenceIssue,
    SemanticMaterializationEvidenceVerificationReport,
    SemanticResearchPreflightReport,
)
from strategy_validator.contracts.semantic_gate_artifact import (
    SemanticResearchIntegrityIssue,
    SemanticResearchIntegrityReport,
    SemanticResearchAdjudicationGateSummary,
    SemanticResearchGateArtifact,
    SemanticResearchGateArtifactIssue,
    SemanticResearchGateArtifactVerificationReport,
    SemanticAdjudicationReadinessIssue,
    SemanticAdjudicationReadinessReport,
)
from strategy_validator.contracts.semantic_adjudication_bundle import (
    SemanticAdjudicationHandoffArtifact,
    SemanticAdjudicationHandoffArtifactIssue,
    SemanticAdjudicationHandoffArtifactVerificationReport,
    SemanticAdjudicationBundle,
    SemanticAdjudicationBundleIssue,
    SemanticAdjudicationBundleVerificationReport,
    SemanticAdjudicationBundleSummary,
)
from strategy_validator.contracts.semantic_bundle_release_index import (
    SemanticAdjudicationBundleManifest,
    SemanticAdjudicationBundleManifestIssue,
    SemanticAdjudicationBundleManifestVerificationReport,
    SemanticAdjudicationBundleReleasePreflightReport,
    SemanticAdjudicationBundleReleaseIndex,
    SemanticAdjudicationBundleReleaseIndexIssue,
    SemanticAdjudicationBundleReleaseIndexVerificationReport,
)
from strategy_validator.contracts.semantic_release_capsule import (
    SemanticAdjudicationReleaseCapsule,
    SemanticAdjudicationReleaseCapsuleIssue,
    SemanticAdjudicationReleaseCapsuleVerificationReport,
    SemanticAdjudicationReleaseCapsuleSummary,
    SemanticAdjudicationReleaseDecisionRecord,
    SemanticAdjudicationReleaseDecisionRecordIssue,
    SemanticAdjudicationReleaseDecisionRecordVerificationReport,
    SemanticAdjudicationReleaseDecisionRecordSummary,
)
from strategy_validator.contracts.semantic_release_handoff import (
    SemanticAdjudicationReleaseDecisionLedgerEntry,
    SemanticAdjudicationReleaseDecisionLedger,
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
)
from strategy_validator.contracts.semantic_validator_handoff import (
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
)
from strategy_validator.contracts.semantic_validator_submission import (
    SemanticValidatorIngressAcceptanceRecord,
    SemanticValidatorIngressAcceptanceRecordIssue,
    SemanticValidatorIngressAcceptanceRecordVerificationReport,
    SemanticValidatorIngressAcceptanceRecordSummary,
    SemanticValidatorIngressAcceptanceLedgerEntry,
    SemanticValidatorIngressAcceptanceLedger,
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
)

# Compatibility declaration ledger for constitutional/read-surface tests.
# These contracts are defined in the imported modules above and re-exported here.
# class SemanticAdjudicationBundleReleaseIndex
# class SemanticAdjudicationBundleReleaseIndexVerificationReport
# class SemanticAdjudicationReleaseCapsule
# class SemanticAdjudicationReleaseCapsuleVerificationReport
# class SemanticAdjudicationReleaseCapsuleSummary
# class SemanticAdjudicationReleaseDecisionRecord
# class SemanticAdjudicationReleaseDecisionRecordVerificationReport
# class SemanticAdjudicationReleaseDecisionRecordSummary
# class SemanticAdjudicationReleaseDecisionLedgerEntry
# class SemanticAdjudicationReleaseDecisionLedger
# class SemanticAdjudicationReleaseDecisionLedgerVerificationReport
# class SemanticReleaseHandoffCertificateEvidenceIssue
# class SemanticReleaseHandoffCertificateEvidenceVerificationReport
# class SemanticValidatorHandoffPacket
# class SemanticValidatorHandoffPacketVerificationReport
# class SemanticValidatorHandoffPacketSummary
# semantic_adjudication_release_capsule_summary/v1
# semantic_adjudication_release_decision_record/v1
