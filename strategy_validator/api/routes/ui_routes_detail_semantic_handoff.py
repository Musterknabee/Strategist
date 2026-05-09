# legacy_callable( compatibility anchor for lazy import surface tests.
from __future__ import annotations

from fastapi import APIRouter

from strategy_validator.api.routes.ui_routes_detail_semantic_handoff_release import router as release_router
from strategy_validator.api.routes.ui_routes_detail_semantic_handoff_lifecycle import router as lifecycle_router
from strategy_validator.api.routes.ui_routes_detail_semantic_handoff_operations import router as operations_router

from strategy_validator.api.routes.ui_routes_detail_semantic_handoff_release import (
    get_semantic_release_handoff,
    get_semantic_release_handoff_latest,
    get_semantic_validator_handoff,
    get_semantic_validator_handoff_latest,
)
from strategy_validator.api.routes.ui_routes_detail_semantic_handoff_lifecycle import (
    get_semantic_validator_handoff_lineage,
    get_semantic_validator_handoff_lineage_latest,
    get_semantic_validator_handoff_remediation,
    get_semantic_validator_handoff_remediation_latest,
    get_semantic_validator_handoff_review,
    get_semantic_validator_handoff_review_latest,
    get_semantic_validator_handoff_decision,
    get_semantic_validator_handoff_decision_latest,
    get_semantic_validator_handoff_signoff,
    get_semantic_validator_handoff_signoff_latest,
    get_semantic_validator_handoff_custody,
    get_semantic_validator_handoff_custody_latest,
    get_semantic_validator_handoff_archive,
    get_semantic_validator_handoff_archive_latest,
    get_semantic_validator_handoff_closure,
    get_semantic_validator_handoff_closure_latest,
    get_semantic_validator_handoff_continuity,
    get_semantic_validator_handoff_continuity_latest,
    get_semantic_validator_handoff_runbook,
    get_semantic_validator_handoff_runbook_latest,
)
from strategy_validator.api.routes.ui_routes_detail_semantic_handoff_operations import (
    get_semantic_validator_handoff_exceptions,
    get_semantic_validator_handoff_exceptions_latest,
    get_semantic_validator_handoff_timeline,
    get_semantic_validator_handoff_timeline_latest,
    get_semantic_validator_handoff_evidence_gaps,
    get_semantic_validator_handoff_evidence_gaps_latest,
    get_semantic_validator_handoff_audit_packet,
    get_semantic_validator_handoff_audit_packet_latest,
    get_semantic_validator_handoff_action_queue,
    get_semantic_validator_handoff_action_queue_latest,
    get_semantic_validator_handoff_escalation_board,
    get_semantic_validator_handoff_escalation_board_latest,
    get_semantic_validator_handoff_resolution_plan,
    get_semantic_validator_handoff_resolution_plan_latest,
)

router = APIRouter()
router.include_router(release_router)
router.include_router(lifecycle_router)
router.include_router(operations_router)

__all__ = (
    'router',
    'get_semantic_release_handoff',
    'get_semantic_release_handoff_latest',
    'get_semantic_validator_handoff',
    'get_semantic_validator_handoff_latest',
    'get_semantic_validator_handoff_lineage',
    'get_semantic_validator_handoff_lineage_latest',
    'get_semantic_validator_handoff_remediation',
    'get_semantic_validator_handoff_remediation_latest',
    'get_semantic_validator_handoff_review',
    'get_semantic_validator_handoff_review_latest',
    'get_semantic_validator_handoff_decision',
    'get_semantic_validator_handoff_decision_latest',
    'get_semantic_validator_handoff_signoff',
    'get_semantic_validator_handoff_signoff_latest',
    'get_semantic_validator_handoff_custody',
    'get_semantic_validator_handoff_custody_latest',
    'get_semantic_validator_handoff_archive',
    'get_semantic_validator_handoff_archive_latest',
    'get_semantic_validator_handoff_closure',
    'get_semantic_validator_handoff_closure_latest',
    'get_semantic_validator_handoff_continuity',
    'get_semantic_validator_handoff_continuity_latest',
    'get_semantic_validator_handoff_runbook',
    'get_semantic_validator_handoff_runbook_latest',
    'get_semantic_validator_handoff_exceptions',
    'get_semantic_validator_handoff_exceptions_latest',
    'get_semantic_validator_handoff_timeline',
    'get_semantic_validator_handoff_timeline_latest',
    'get_semantic_validator_handoff_evidence_gaps',
    'get_semantic_validator_handoff_evidence_gaps_latest',
    'get_semantic_validator_handoff_audit_packet',
    'get_semantic_validator_handoff_audit_packet_latest',
    'get_semantic_validator_handoff_action_queue',
    'get_semantic_validator_handoff_action_queue_latest',
    'get_semantic_validator_handoff_escalation_board',
    'get_semantic_validator_handoff_escalation_board_latest',
    'get_semantic_validator_handoff_resolution_plan',
    'get_semantic_validator_handoff_resolution_plan_latest',
)
