from __future__ import annotations

from typing import Optional
from strategy_validator.contracts.oracle_types import (
    OracleSupportVerificationStatus,
    OracleMemoryReviewClassification,
    OracleDoctrineDriftClassification,
    OracleDoctrineMemoryClassification,
    OracleQuarterlyReviewClassification,
    OracleSemiannualAuditClassification,
    OracleAnnualReviewClassification,
    OracleConstitutionalDigestClassification,
    OracleDoctrineLineageSealStatus,
    OracleConstitutionalTrustStatus,
    OracleExplanationCategory,
    OracleOperatorReadiness,
    OracleArtifactIntegrityStatus,
    OracleArtifactCoverageStatus,
    OracleSupportChainRemediationStatus,
    OracleReliancePosture,
    OracleEscalationLane,
    OraclePropagationPosture,
    OracleAutomationPosture,
    OracleGovernancePlaneStatus,
    OracleGovernanceDimension,
    OracleGovernancePrimarySeverity,
    OracleGovernancePriorityBand,
    OracleGovernanceReviewTarget,
    OracleGovernanceDispatchPosture,
    OracleGovernanceDispatchTimeliness,
    OracleGovernanceDispatchClaimUrgency,
    OracleGovernanceClaimCode,
    OracleGovernanceClaimWorkerLane,
    OracleGovernanceClaimDisposition,
    OracleGovernanceClaimActionSeverity,
    OracleGovernanceClaimLeaseMode,
    OracleGovernanceClaimLeaseRenewalPosture,
    OracleGovernanceClaimLeaseAction,
    OracleGovernanceClaimLeaseCoverage,
    OracleGovernanceClaimLeaseHealth,
    OracleGovernanceClaimProcessPosture,
    OracleGovernanceClaimOperability,
)


from strategy_validator.contracts.oracle_core import (
    OracleGovernanceClaimActionItem,
    OracleGovernanceQueueKey,
    OracleGovernanceCode,
    SemanticSensorSnapshot,
    MicrostructureSensorSnapshot,
    MacroRegimeSensorSnapshot,
    StrategyHealthSnapshot,
    OracleSensorMatrix,
    OraclePolicyArtifact,
    OracleAdvisoryInput,
    RegimeProbability,
    StrategyAdvisory,
    EpistemicUncertaintyAssessment,
    OracleArtifactFreshnessItem,
    OracleArtifactLineageItem,
    OracleGovernanceActionItem,
    OracleGovernanceFingerprint,
    OracleMorningAttestation,
)


from strategy_validator.contracts.oracle_evidence_events import (
    OracleDerivedViewCheckpointMetadata,
    OracleDerivedViewReport,
    OracleEventCheckpointManifest,
    OracleEventCheckpointVerification,
    OracleEventLogEntry,
    OracleEventLogQuerySpec,
    OracleEvidenceManifest,
    OracleEvidenceVerification,
    OracleRegimeTransition,
    OracleStateTransitionReport,
    OracleTransitionEvidenceManifest,
    OracleTransitionEvidenceVerification,
)

from strategy_validator.contracts.oracle_cadence_reviews import (
    OracleAnnualLaneEntry,
    OracleAnnualReviewEvidenceManifest,
    OracleAnnualReviewEvidenceVerification,
    OracleAnnualReviewReport,
    OracleConstitutionalDigestEvidenceManifest,
    OracleConstitutionalDigestEvidenceVerification,
    OracleConstitutionalDigestReport,
    OracleConstitutionalGateReport,
    OracleConstitutionalLaneEntry,
    OracleDoctrineDriftEvidenceManifest,
    OracleDoctrineDriftEvidenceVerification,
    OracleDoctrineDriftReport,
    OracleDoctrineLaneEntry,
    OracleDoctrineLineageIndex,
    OracleDoctrineLineageVerification,
    OracleMemoryLaneEntry,
    OracleMemoryLaneSummary,
    OracleMemoryReviewEvidenceManifest,
    OracleMemoryReviewEvidenceVerification,
    OracleMemoryReviewReport,
    OracleMonthlyDigestEvidenceManifest,
    OracleMonthlyDigestEvidenceVerification,
    OracleMonthlyDigestReport,
    OracleMonthlyLaneEntry,
    OracleQuarterlyLaneEntry,
    OracleQuarterlyReviewEvidenceManifest,
    OracleQuarterlyReviewEvidenceVerification,
    OracleQuarterlyReviewReport,
    OracleReviewLaneEntry,
    OracleSemiannualAuditEvidenceManifest,
    OracleSemiannualAuditEvidenceVerification,
    OracleSemiannualAuditReport,
    OracleSemiannualLaneEntry,
    OracleWeeklyDigestEvidenceManifest,
    OracleWeeklyDigestEvidenceVerification,
    OracleWeeklyDigestReport,
)

from strategy_validator.contracts.oracle_operator_reports import (
    OracleExplanationNode,
    OracleTrustExplanationReport,
    OracleOperatorDiagnosticReport,
    OracleStatusPackSection,
    OracleOperatorWorkboardItemReport,
    OracleOperatorWorkboardReport,
    OracleStatusPackReport,
    OracleIncidentPackArtifact,
    OracleIncidentPackReport,
    OracleCompactedStateRebuildReport,
    OracleBriefingSection,
    OracleBriefingPackReport,
    OracleCompactedStateInspectionReport,
    OracleReplayAuditSource,
    OracleReplayAuditReport,
)

from strategy_validator.contracts.oracle_strategic import (
    OracleStrategicPosture,
    OracleStrategicTransitionClassification,
    OracleStrategicQueueKind,
    OracleThesisCurrentState,
    OracleThesisEvolutionState,
    OracleScenarioKind,
    OracleStrategyCohortBucket,
    OracleResearchPriorityKind,
    StrategyRegimeFit,
    OracleSensorRawMacroInput,
    OracleSensorRawSemanticInput,
    OracleSensorRawMicrostructureInput,
    OracleSensorIngestionInput,
    OracleSensorIngestionReport,
    OracleStrategicFusionReport,
    StrategyPosteriorState,
    StrategyHealthPosteriorReport,
    OracleRegimeTransitionSignalReport,
    OracleOpportunityQueueItem,
    OracleOpportunityQueueReport,
    OracleThesisMemoryItem,
    OracleThesisMemoryReport,
    OracleDoctrineAdaptationItem,
    OracleDoctrineAdaptationReport,
    OracleResearchPriorityItem,
    OracleResearchPriorityReport,
    OracleInvestigationOutcomeInputItem,
    OracleInvestigationOutcomeInput,
    OracleResearchExecutionMemoryItem,
    OracleResearchExecutionMemoryReport,
    OracleThesisGraphNode,
    OracleThesisGraphEdge,
    OracleThesisGraphReport,
    OracleStrategicTensionItem,
    OracleStrategicTensionReport,
    OracleStrategicNarrativeItem,
    OracleStrategicNarrativeReport,
    OracleStrategicMemoryPoint,
    OracleStrategicDriverDriftItem,
    OracleStrategicMemoryHorizonReport,
    OracleContradictionResolutionItem,
    OracleContradictionResolutionReport,
    OracleStrategicInterventionItem,
    OracleStrategicInterventionReport,
    OracleStrategicCampaignStep,
    OracleStrategicCampaignItem,
    OracleStrategicCampaignReport,
    OracleStrategicCampaignExecutionUpdateItem,
    OracleStrategicCampaignExecutionInput,
    OracleStrategicCampaignExecutionItem,
    OracleStrategicCampaignExecutionReport,
    OracleStrategicBriefingSection,
    OracleStrategicBriefingReport,
    OracleStrategicStackEvidenceManifest,
    OracleStrategicArtifactEvidenceManifest,
    OracleStrategicArtifactEvidenceVerification,
    OracleStrategicStackEvidenceVerification,
    OracleScenarioShock,
    OracleScenarioPlanInput,
    OracleScenarioOutcome,
    OracleScenarioLabReport,
    OracleStrategyCohortItem,
    OracleStrategyCohortReport,
)


class OracleStatusPackCompatibility:
    """Compatibility surface marker for status pack migration."""


class OracleIncidentPackCompatibility:
    """Compatibility surface marker for incident pack migration."""


class OracleBriefingPackCompatibility:
    """Compatibility surface marker for briefing pack migration."""


class OracleOpportunityQueueCompatibility:
    """Compatibility surface marker for research queue migration."""


class OracleResearchCompatibility:
    """Compatibility surface marker for research migration."""


class OracleStrategicCompatibility:
    """Compatibility surface marker for strategic migration."""


class OracleStrategyCohortCompatibility:
    """Compatibility surface marker for cohort migration."""


class OracleThesisMemoryCompatibility:
    """Compatibility surface marker for thesis memory migration."""


class OracleThesisGraphCompatibility:
    """Compatibility surface marker for thesis graph migration."""


class OracleRegimeTransitionCompatibility:
    """Compatibility surface marker for transition migration."""


class OracleStrategicInterventionCompatibility:
    """Compatibility surface marker for strategic intervention migration."""


class OracleContradictionResolutionCompatibility:
    """Compatibility surface marker for contradiction-resolution migration."""


class OracleStrategicTensionCompatibility:
    """Compatibility surface marker for analytics migration."""


class StrategyHealthPosteriorCompatibility:
    """Compatibility surface marker for posterior analytics migration."""

