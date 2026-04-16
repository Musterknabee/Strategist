from strategy_validator.validator.oracle_governance_plane import assess_governance_plane


def test_governance_review_target_blocked_surface_routes_to_constitutional_repair_queue():
    assessment = assess_governance_plane(
        evidence_freshness_status='STALE',
        evidence_integrity_status='UNVERIFIED',
        evidence_coverage_status='MISSING',
        support_verification_status='UNVERIFIED',
        support_chain_trust_status='UNTRUSTED',
        support_chain_remediation_status='REMEDIATION_REQUIRED',
        operator_readiness='HOLD_FOR_REFRESH',
        surface_label='fusion surface',
    )
    assert assessment.governance_plane_status == 'GOVERNANCE_BLOCKED'
    assert assessment.governance_plane_priority_band == 'CRITICAL_PRIORITY'
    assert assessment.governance_plane_review_target == 'CONSTITUTIONAL_REPAIR_QUEUE'
    assert assessment.governance_plane_review_sla_hours == 4


def test_governance_review_target_restricted_surface_routes_to_heightened_queue():
    assessment = assess_governance_plane(
        evidence_freshness_status='AGING',
        evidence_integrity_status='MIXED',
        evidence_coverage_status='PARTIAL',
        support_verification_status='ABSENT',
        support_chain_trust_status='TRUST_RESTRICTED',
        support_chain_remediation_status='REMEDIATION_RECOMMENDED',
        operator_readiness='REVIEW_WITH_CAUTION',
        surface_label='briefing surface',
    )
    assert assessment.governance_plane_status == 'GOVERNANCE_RESTRICTED'
    assert assessment.governance_plane_review_target == 'HEIGHTENED_REVIEW_QUEUE'
    assert assessment.governance_plane_review_sla_hours == 24


def test_governance_review_target_ready_surface_routes_to_routine_queue():
    assessment = assess_governance_plane(
        evidence_freshness_status='FRESH',
        evidence_integrity_status='VERIFIED',
        evidence_coverage_status='COMPLETE',
        support_verification_status='VERIFIED',
        support_chain_trust_status='TRUSTED',
        support_chain_remediation_status='NO_REMEDIATION',
        operator_readiness='READY_FOR_REVIEW',
        surface_label='attestation',
    )
    assert assessment.governance_plane_status == 'GOVERNANCE_READY'
    assert assessment.governance_plane_review_target == 'ROUTINE_REVIEW_QUEUE'
    assert assessment.governance_plane_review_sla_hours == 72
