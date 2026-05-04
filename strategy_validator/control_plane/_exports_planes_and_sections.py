from __future__ import annotations

"""Control-plane assessments, section composition, and posture surfaces."""

EXPORTS_PLANES_AND_SECTIONS = {
    'OracleOperatorSectionComposition': 'strategy_validator.control_plane.operator_section_registry',
    'OracleOperatorSectionEntry': 'strategy_validator.control_plane.operator_section_registry',
    'compose_briefing_pack_sections': 'strategy_validator.control_plane.operator_section_registry',
    'compose_incident_pack_sections': 'strategy_validator.control_plane.operator_section_registry',
    'compose_status_pack_sections': 'strategy_validator.control_plane.operator_section_registry',
    'OracleControlPlaneAssessment': 'strategy_validator.control_plane.control_plane',
    'OracleGovernancePlaneAssessment': 'strategy_validator.control_plane.governance_plane',
    'OracleTrustPlaneAssessment': 'strategy_validator.control_plane.trust_plane',
    'assess_automation_posture': 'strategy_validator.control_plane.automation_posture',
    'assess_control_plane': 'strategy_validator.control_plane.control_plane',
    'assess_governance_plane': 'strategy_validator.control_plane.governance_plane',
    'assess_operator_escalation_lane': 'strategy_validator.control_plane.escalation',
    'assess_operator_propagation_posture': 'strategy_validator.control_plane.propagation_posture',
    'assess_operator_reliance_posture': 'strategy_validator.control_plane.reliance_posture',
    'assess_trust_plane': 'strategy_validator.control_plane.trust_plane',
    'build_operator_queue_briefing_section': 'strategy_validator.control_plane.operator_board_sections',
    'build_operator_workboard_report': 'strategy_validator.control_plane.operator_board_sections',
    'render_operator_workboard_markdown_lines': 'strategy_validator.control_plane.operator_board_sections',
}
