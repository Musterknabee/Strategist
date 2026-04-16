from strategy_validator.control_plane import (
    OracleControlPlaneAssessment,
    OracleGovernancePlaneAssessment,
    assess_control_plane,
    assess_governance_plane,
    assess_operator_escalation_lane,
)
from strategy_validator.validator.oracle_control_plane import (
    OracleControlPlaneAssessment as LegacyOracleControlPlaneAssessment,
    assess_control_plane as legacy_assess_control_plane,
)
from strategy_validator.validator.oracle_governance_plane import (
    OracleGovernancePlaneAssessment as LegacyOracleGovernancePlaneAssessment,
    assess_governance_plane as legacy_assess_governance_plane,
)
from strategy_validator.validator.oracle_operator_escalation import (
    assess_operator_escalation_lane as legacy_assess_operator_escalation_lane,
)


def test_control_plane_exports_assessment_types() -> None:
    assert OracleControlPlaneAssessment.__name__ == 'OracleControlPlaneAssessment'
    assert OracleGovernancePlaneAssessment.__name__ == 'OracleGovernancePlaneAssessment'


def test_control_plane_assessment_matches_legacy_shim() -> None:
    assessment = assess_control_plane(
        operator_readiness='READY',
        support_chain_trust_status='TRUSTED',
        support_chain_remediation_status='NO_REMEDIATION_REQUIRED',
        surface_label='test surface',
    )
    legacy = legacy_assess_control_plane(
        operator_readiness='READY',
        support_chain_trust_status='TRUSTED',
        support_chain_remediation_status='NO_REMEDIATION_REQUIRED',
        surface_label='test surface',
    )
    assert isinstance(assessment, OracleControlPlaneAssessment)
    assert isinstance(legacy, LegacyOracleControlPlaneAssessment)
    assert assessment.__dict__ == legacy.__dict__


def test_governance_plane_assessment_matches_legacy_shim() -> None:
    assessment = assess_governance_plane(
        evidence_freshness_status='FRESH',
        evidence_integrity_status='VERIFIED',
        evidence_coverage_status='SUFFICIENT',
        support_verification_status='VERIFIED',
        support_chain_trust_status='TRUSTED',
        support_chain_remediation_status='NO_REMEDIATION_REQUIRED',
        operator_readiness='READY',
        surface_label='test surface',
    )
    legacy = legacy_assess_governance_plane(
        evidence_freshness_status='FRESH',
        evidence_integrity_status='VERIFIED',
        evidence_coverage_status='SUFFICIENT',
        support_verification_status='VERIFIED',
        support_chain_trust_status='TRUSTED',
        support_chain_remediation_status='NO_REMEDIATION_REQUIRED',
        operator_readiness='READY',
        surface_label='test surface',
    )
    assert isinstance(assessment, OracleGovernancePlaneAssessment)
    assert isinstance(legacy, LegacyOracleGovernancePlaneAssessment)
    assert assessment.__dict__ == legacy.__dict__


def test_escalation_assessment_matches_legacy_shim() -> None:
    assessment = assess_operator_escalation_lane(
        operator_reliance_posture='CAUTIOUS_ADVISORY_ONLY',
        support_chain_trust_status='TRUST_RESTRICTED',
        support_chain_remediation_status='REMEDIATION_RECOMMENDED',
    )
    legacy = legacy_assess_operator_escalation_lane(
        operator_reliance_posture='CAUTIOUS_ADVISORY_ONLY',
        support_chain_trust_status='TRUST_RESTRICTED',
        support_chain_remediation_status='REMEDIATION_RECOMMENDED',
    )
    assert assessment == legacy
