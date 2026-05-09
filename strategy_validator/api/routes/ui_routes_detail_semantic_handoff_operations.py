from __future__ import annotations

from fastapi import APIRouter, Query

from strategy_validator.api.routes._ui_detail_legacy import legacy_callable


build_ui_semantic_validator_handoff_action_queue_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_action_queue_latest_payload')
build_ui_semantic_validator_handoff_action_queue_payload = legacy_callable('build_ui_semantic_validator_handoff_action_queue_payload')
build_ui_semantic_validator_handoff_audit_packet_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_audit_packet_latest_payload')
build_ui_semantic_validator_handoff_audit_packet_payload = legacy_callable('build_ui_semantic_validator_handoff_audit_packet_payload')
build_ui_semantic_validator_handoff_escalation_board_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_escalation_board_latest_payload')
build_ui_semantic_validator_handoff_escalation_board_payload = legacy_callable('build_ui_semantic_validator_handoff_escalation_board_payload')
build_ui_semantic_validator_handoff_evidence_gaps_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_evidence_gaps_latest_payload')
build_ui_semantic_validator_handoff_evidence_gaps_payload = legacy_callable('build_ui_semantic_validator_handoff_evidence_gaps_payload')
build_ui_semantic_validator_handoff_exceptions_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_exceptions_latest_payload')
build_ui_semantic_validator_handoff_exceptions_payload = legacy_callable('build_ui_semantic_validator_handoff_exceptions_payload')
build_ui_semantic_validator_handoff_resolution_plan_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_resolution_plan_latest_payload')
build_ui_semantic_validator_handoff_resolution_plan_payload = legacy_callable('build_ui_semantic_validator_handoff_resolution_plan_payload')
build_ui_semantic_validator_handoff_timeline_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_timeline_latest_payload')
build_ui_semantic_validator_handoff_timeline_payload = legacy_callable('build_ui_semantic_validator_handoff_timeline_payload')

router = APIRouter()

@router.get('/semantic-validator-handoff/exceptions')
def get_semantic_validator_handoff_exceptions(
    repo_root: str | None = None,
    search_root: str | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    exception_state: list[str] = Query(default=[]),
    exception_kind: list[str] = Query(default=[]),
    priority: list[str] = Query(default=[]),
    severity: list[str] = Query(default=[]),
    include_resolved: bool = False,
    limit: int = Query(default=200, ge=1, le=1000),
) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_exceptions_payload(
        repo_root=repo_root,
        search_root=search_root,
        experiment_id_contains=experiment_id_contains,
        issue_contains=issue_contains,
        exception_state=tuple(exception_state or ()),
        exception_kind=tuple(exception_kind or ()),
        priority=tuple(priority or ()),
        severity=tuple(severity or ()),
        include_resolved=include_resolved,
        limit=limit,
    )

@router.get('/semantic-validator-handoff/exceptions/latest')
def get_semantic_validator_handoff_exceptions_latest(
    repo_root: str | None = None,
    search_root: str | None = None,
) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_exceptions_latest_payload(repo_root=repo_root, search_root=search_root)

@router.get('/semantic-validator-handoff/timeline')
def get_semantic_validator_handoff_timeline(
    repo_root: str | None = None,
    search_root: str | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    stage: list[str] = Query(default=[]),
    event_state: list[str] = Query(default=[]),
    severity: list[str] = Query(default=[]),
    include_ready: bool = True,
    limit: int = Query(default=200, ge=1, le=1000),
) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_timeline_payload(
        repo_root=repo_root,
        search_root=search_root,
        experiment_id_contains=experiment_id_contains,
        issue_contains=issue_contains,
        stage=tuple(stage or ()),
        event_state=tuple(event_state or ()),
        severity=tuple(severity or ()),
        include_ready=include_ready,
        limit=limit,
    )

@router.get('/semantic-validator-handoff/timeline/latest')
def get_semantic_validator_handoff_timeline_latest(
    repo_root: str | None = None,
    search_root: str | None = None,
) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_timeline_latest_payload(repo_root=repo_root, search_root=search_root)

@router.get('/semantic-validator-handoff/evidence-gaps')
def get_semantic_validator_handoff_evidence_gaps(
    repo_root: str | None = None,
    search_root: str | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    gap_kind: list[str] = Query(default=[]),
    gap_state: list[str] = Query(default=[]),
    priority: list[str] = Query(default=[]),
    severity: list[str] = Query(default=[]),
    stage: list[str] = Query(default=[]),
    include_resolved: bool = False,
    limit: int = Query(default=200, ge=1, le=1000),
) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_evidence_gaps_payload(repo_root=repo_root, search_root=search_root, experiment_id_contains=experiment_id_contains, issue_contains=issue_contains, gap_kind=tuple(gap_kind or ()), gap_state=tuple(gap_state or ()), priority=tuple(priority or ()), severity=tuple(severity or ()), stage=tuple(stage or ()), include_resolved=include_resolved, limit=limit)

@router.get('/semantic-validator-handoff/evidence-gaps/latest')
def get_semantic_validator_handoff_evidence_gaps_latest(
    repo_root: str | None = None,
    search_root: str | None = None,
) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_evidence_gaps_latest_payload(repo_root=repo_root, search_root=search_root)

@router.get('/semantic-validator-handoff/audit-packet')
def get_semantic_validator_handoff_audit_packet(
    repo_root: str | None = None,
    search_root: str | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    packet_status: list[str] = Query(default=[]),
    trust_banner: list[str] = Query(default=[]),
    audit_ready: bool | None = None,
    operator_attention_required: bool | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_audit_packet_payload(
        repo_root=repo_root,
        search_root=search_root,
        experiment_id_contains=experiment_id_contains,
        issue_contains=issue_contains,
        packet_status=tuple(packet_status or ()),
        trust_banner=tuple(trust_banner or ()),
        audit_ready=audit_ready,
        operator_attention_required=operator_attention_required,
        limit=limit,
    )

@router.get('/semantic-validator-handoff/audit-packet/latest')
def get_semantic_validator_handoff_audit_packet_latest(
    repo_root: str | None = None,
    search_root: str | None = None,
) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_audit_packet_latest_payload(repo_root=repo_root, search_root=search_root)

@router.get('/semantic-validator-handoff/action-queue')
def get_semantic_validator_handoff_action_queue(
    repo_root: str | None = None,
    search_root: str | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    queue_state: list[str] = Query(default=[]),
    priority: list[str] = Query(default=[]),
    severity: list[str] = Query(default=[]),
    trust_banner: list[str] = Query(default=[]),
    source: list[str] = Query(default=[]),
    external_artifact_required: bool | None = None,
    blocked: bool | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_action_queue_payload(repo_root=repo_root, search_root=search_root, experiment_id_contains=experiment_id_contains, issue_contains=issue_contains, queue_state=tuple(queue_state or ()), priority=tuple(priority or ()), severity=tuple(severity or ()), trust_banner=tuple(trust_banner or ()), source=tuple(source or ()), external_artifact_required=external_artifact_required, blocked=blocked, limit=limit)

@router.get('/semantic-validator-handoff/action-queue/latest')
def get_semantic_validator_handoff_action_queue_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_action_queue_latest_payload(repo_root=repo_root, search_root=search_root)

@router.get('/semantic-validator-handoff/escalation-board')
def get_semantic_validator_handoff_escalation_board(
    repo_root: str | None = None,
    search_root: str | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    escalation_lane: list[str] = Query(default=[]),
    priority: list[str] = Query(default=[]),
    severity: list[str] = Query(default=[]),
    trust_banner: list[str] = Query(default=[]),
    source: list[str] = Query(default=[]),
    external_artifact_required: bool | None = None,
    blocked: bool | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_escalation_board_payload(repo_root=repo_root, search_root=search_root, experiment_id_contains=experiment_id_contains, issue_contains=issue_contains, escalation_lane=tuple(escalation_lane or ()), priority=tuple(priority or ()), severity=tuple(severity or ()), trust_banner=tuple(trust_banner or ()), source=tuple(source or ()), external_artifact_required=external_artifact_required, blocked=blocked, limit=limit)

@router.get('/semantic-validator-handoff/escalation-board/latest')
def get_semantic_validator_handoff_escalation_board_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_escalation_board_latest_payload(repo_root=repo_root, search_root=search_root)

@router.get('/semantic-validator-handoff/resolution-plan')
def get_semantic_validator_handoff_resolution_plan(
    repo_root: str | None = None,
    search_root: str | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    phase: list[str] = Query(default=[]),
    step_state: list[str] = Query(default=[]),
    priority: list[str] = Query(default=[]),
    severity: list[str] = Query(default=[]),
    trust_banner: list[str] = Query(default=[]),
    owner_hint: list[str] = Query(default=[]),
    requires_external_artifact: bool | None = None,
    blocks_handoff_clearance: bool | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_resolution_plan_payload(repo_root=repo_root, search_root=search_root, experiment_id_contains=experiment_id_contains, issue_contains=issue_contains, phase=tuple(phase or ()), step_state=tuple(step_state or ()), priority=tuple(priority or ()), severity=tuple(severity or ()), trust_banner=tuple(trust_banner or ()), owner_hint=tuple(owner_hint or ()), requires_external_artifact=requires_external_artifact, blocks_handoff_clearance=blocks_handoff_clearance, limit=limit)

@router.get('/semantic-validator-handoff/resolution-plan/latest')
def get_semantic_validator_handoff_resolution_plan_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_resolution_plan_latest_payload(repo_root=repo_root, search_root=search_root)

__all__ = (
    'router',
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
