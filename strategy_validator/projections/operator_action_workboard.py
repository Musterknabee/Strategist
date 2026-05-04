from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Iterable

from strategy_validator.contracts.operator_action_journal import OperatorActionEvent
from strategy_validator.contracts.operator_queue import OracleOperatorWorkItem
from strategy_validator.ledger.operator_actions import read_operator_action_events

if TYPE_CHECKING:
    from strategy_validator.control_plane.operator_queue_service import OracleGovernanceWorkQueueState


_ACTION_OPERABILITY = {
    'claim-item': (
        'JOURNALED_CLAIM_PENDING',
        'Journaled claim request is awaiting projection-backed governed materialization.',
    ),
    'acknowledge-reentry': (
        'JOURNALED_REENTRY_PENDING',
        'Journaled re-entry acknowledgement is awaiting projection-backed governed materialization.',
    ),
    'renew-lease': (
        'JOURNALED_LEASE_PENDING',
        'Journaled lease renewal is awaiting projection-backed governed materialization.',
    ),
}


@dataclass(frozen=True)
class OperatorActionProjectionStatus:
    enabled: bool
    state: str
    reason: str
    source_label: str = 'operator_action_journal'
    trust_status: str = 'TRUST_RESTRICTED'
    ledger_db_path_configured: bool = False

    def to_payload(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class OperatorActionWorkboardProjection:
    review_target: str
    source_event_count: int
    projected_work_item_count: int
    work_items: tuple[OracleOperatorWorkItem, ...]
    latest_action_created_at_utc: datetime | None = None
    operator_ids: tuple[str, ...] = ()
    action_names: tuple[str, ...] = ()
    operator_count: int = 0
    action_count: int = 0
    current_work_item_count: int = 0
    aging_work_item_count: int = 0
    stale_work_item_count: int = 0
    primary_merge_pending_count: int = 0
    auxiliary_merge_pending_count: int = 0
    post_merge_ready_count: int = 0
    post_merge_review_required_count: int = 0
    post_merge_stale_count: int = 0
    downstream_closure_ready_count: int = 0
    downstream_closure_review_required_count: int = 0
    downstream_closure_blocked_count: int = 0
    summary_line: str = 'No journaled operator actions were materialized.'
    recommended_next_actions: tuple[str, ...] = ()
    projection_enabled: bool = False
    projection_status_state: str = 'DISABLED'
    projection_status_reason: str = 'STRATEGY_VALIDATOR_LEDGER_DB_PATH is not configured.'
    projection_trust_status: str = 'TRUST_RESTRICTED'
    projection_source_label: str = 'operator_action_journal'
    projection_ledger_db_path_configured: bool = False


def get_operator_action_projection_status() -> OperatorActionProjectionStatus:
    ledger_db_path = os.environ.get('STRATEGY_VALIDATOR_LEDGER_DB_PATH')
    if not ledger_db_path:
        return OperatorActionProjectionStatus(
            enabled=False,
            state='DISABLED',
            reason='STRATEGY_VALIDATOR_LEDGER_DB_PATH is not configured; journaled operator actions are not projected.',
            trust_status='TRUST_RESTRICTED',
            ledger_db_path_configured=False,
        )
    return OperatorActionProjectionStatus(
        enabled=True,
        state='ENABLED',
        reason='STRATEGY_VALIDATOR_LEDGER_DB_PATH is configured; journaled operator actions can be projected from the operator action journal.',
        trust_status='PROJECTION_ENABLED',
        ledger_db_path_configured=True,
    )


def operator_action_projection_enabled() -> bool:
    return get_operator_action_projection_status().enabled


def _ordered_unique(items: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(item for item in items if str(item).strip()))


def _latest_accepted_operator_action_events(queue_state: 'OracleGovernanceWorkQueueState') -> tuple[OperatorActionEvent, ...]:
    if not get_operator_action_projection_status().enabled:
        return ()

    claim = queue_state.governance_claim_envelope
    rows = read_operator_action_events(
        review_target=claim.governance_plane_claim_review_target,
    )
    latest_by_key: dict[str, OperatorActionEvent] = {}
    for row in rows:
        if not row.accepted or row.status != 'accepted':
            continue
        item_key = row.target_payload.get('work_item_key') or row.action_event_id
        latest_by_key[item_key] = row
    return tuple(
        latest_by_key[key]
        for key in sorted(
            latest_by_key,
            key=lambda value: (latest_by_key[value].created_at_utc, latest_by_key[value].action_event_id),
        )
    )


def _projection_age_seconds(created_at_utc: datetime, *, as_of_utc: datetime) -> int:
    return max(0, int((as_of_utc - created_at_utc).total_seconds()))


def _projection_freshness_state(*, age_seconds: int) -> str:
    if age_seconds <= 24 * 60 * 60:
        return 'CURRENT'
    if age_seconds <= 72 * 60 * 60:
        return 'AGING'
    return 'STALE'


def _projection_recommended_actions(
    *,
    action_name: str,
    operator_id: str,
    freshness_state: str,
    merge_state: str,
    post_merge_recommendation: str,
    downstream_closure_recommendation: str,
) -> tuple[str, ...]:
    actions = [
        f'review journaled action {action_name}',
        f'confirm operator handoff for {operator_id}',
    ]
    if merge_state == 'PRIMARY_GOVERNED_MERGE_PENDING':
        actions.append('reconcile journaled action with primary governed work item')
    else:
        actions.append('materialize auxiliary governed queue item')
    if freshness_state != 'CURRENT':
        actions.append('refresh projection state')
    actions.append(post_merge_recommendation)
    actions.append(downstream_closure_recommendation)
    return _ordered_unique(actions)



def _projection_downstream_closure_fields(
    *,
    freshness_state: str,
    merge_state: str,
    post_merge_state: str,
) -> tuple[str, str, str]:
    if freshness_state == 'STALE' or post_merge_state == 'POST_MERGE_STALE':
        return (
            'DOWNSTREAM_CLOSURE_BLOCKED',
            'Downstream closure is blocked until the journal projection is refreshed and the governed queue state can be trusted again.',
            'block downstream closure until projection refresh completes',
        )
    if freshness_state == 'AGING' or post_merge_state == 'POST_MERGE_REVIEW_REQUIRED':
        return (
            'DOWNSTREAM_CLOSURE_REVIEW_REQUIRED',
            'Downstream closure requires explicit operator review because the journal projection is aging relative to governed materialization.',
            'review downstream closure readiness',
        )
    if merge_state == 'PRIMARY_GOVERNED_MERGE_PENDING':
        return (
            'PRIMARY_DOWNSTREAM_CLOSURE_READY',
            'Downstream closure is ready on the current governed primary item because the journal projection is current and aligned with the governed queue.',
            'close the primary governed work item',
        )
    return (
        'AUXILIARY_DOWNSTREAM_CLOSURE_READY',
        'Downstream closure is ready for the auxiliary governed queue item because the journal projection is current and aligned with governed materialization.',
        'close the auxiliary governed queue item',
    )


def _projection_post_merge_lifecycle_fields(*, freshness_state: str, merge_state: str) -> tuple[str, str, str]:
    if freshness_state == 'STALE':
        return (
            'POST_MERGE_STALE',
            'Projected journal state is stale relative to downstream governed materialization and requires explicit operator refresh before merge closure.',
            'refresh projection state before merge closure',
        )
    if freshness_state == 'AGING':
        return (
            'POST_MERGE_REVIEW_REQUIRED',
            'Projected journal state is aging and should be rechecked against governed state before post-merge closure is assumed.',
            'review post-merge governed alignment',
        )
    if merge_state == 'PRIMARY_GOVERNED_MERGE_PENDING':
        return (
            'PRIMARY_POST_MERGE_READY',
            'Projected journal state is current and ready for primary governed merge closure.',
            'complete primary governed merge closure',
        )
    return (
        'AUXILIARY_POST_MERGE_READY',
        'Projected journal state is current and ready for auxiliary governed queue materialization.',
        'complete auxiliary governed materialization',
    )

def _projection_governed_merge_fields(*, item_key: str, queue_state: 'OracleGovernanceWorkQueueState') -> tuple[str, str, bool]:
    claim = queue_state.governance_claim_envelope
    if item_key == claim.governance_plane_claim_sha256:
        return (
            'PRIMARY_GOVERNED_MERGE_PENDING',
            'Journaled operator action targets the current governed primary work item and awaits downstream governed merge materialization.',
            True,
        )
    return (
        'AUXILIARY_GOVERNED_MERGE_PENDING',
        'Journaled operator action targets an auxiliary governed queue item and awaits downstream merge materialization.',
        False,
    )


def _build_projection_summary(
    *,
    rows: tuple[OperatorActionEvent, ...],
    review_target: str,
    current_count: int,
    aging_count: int,
    stale_count: int,
    primary_merge_pending_count: int,
    auxiliary_merge_pending_count: int,
    post_merge_ready_count: int,
    post_merge_review_required_count: int,
    post_merge_stale_count: int,
    downstream_closure_ready_count: int,
    downstream_closure_review_required_count: int,
    downstream_closure_blocked_count: int,
) -> tuple[datetime | None, tuple[str, ...], tuple[str, ...], str, tuple[str, ...]]:
    latest_action_at = max((row.created_at_utc for row in rows), default=None)
    operator_ids = _ordered_unique(row.operator_id for row in rows)
    action_names = _ordered_unique(row.action for row in rows)
    if not rows:
        return (
            None,
            operator_ids,
            action_names,
            f'No accepted journaled operator actions are currently projected for {review_target}.',
            (),
        )

    latest_text = latest_action_at.isoformat() if latest_action_at is not None else 'unknown time'
    summary_line = (
        f'Projected {len(rows)} accepted journaled operator work item(s) for {review_target}; '
        f'latest action at {latest_text}; operators={len(operator_ids)}; action_families={len(action_names)}; '
        f'freshness(current={current_count},aging={aging_count},stale={stale_count}); '
        f'governed_merge(primary={primary_merge_pending_count},auxiliary={auxiliary_merge_pending_count}); '
        f'post_merge(ready={post_merge_ready_count},review_required={post_merge_review_required_count},stale={post_merge_stale_count}); '
        f'downstream_closure(ready={downstream_closure_ready_count},review_required={downstream_closure_review_required_count},blocked={downstream_closure_blocked_count}).'
    )
    recommended = _ordered_unique(
        [
            'refresh projection state',
            'reconcile governed queue state',
            *(action.replace('-', ' ') for action in action_names),
        ]
    )
    return latest_action_at, operator_ids, action_names, summary_line, recommended


def materialize_operator_action_workboard_projection(
    queue_state: 'OracleGovernanceWorkQueueState',
) -> OperatorActionWorkboardProjection:
    claim = queue_state.governance_claim_envelope
    dispatch = queue_state.governance_dispatch_envelope
    projection_status = get_operator_action_projection_status()
    rows = _latest_accepted_operator_action_events(queue_state)
    items: list[OracleOperatorWorkItem] = []
    current_count = 0
    aging_count = 0
    stale_count = 0
    primary_merge_pending_count = 0
    auxiliary_merge_pending_count = 0
    post_merge_ready_count = 0
    post_merge_review_required_count = 0
    post_merge_stale_count = 0
    downstream_closure_ready_count = 0
    downstream_closure_review_required_count = 0
    downstream_closure_blocked_count = 0
    as_of_utc = datetime.now(UTC)
    for row in rows:
        item_key = row.target_payload.get('work_item_key') or row.action_event_id
        review_target = row.target_payload.get('review_target') or claim.governance_plane_claim_review_target
        review_due_by_utc = row.created_at_utc
        review_sort_key = f"journal:{review_due_by_utc.isoformat()}:{row.action_event_id}"
        summary_line = f"{row.summary_line} [journaled by {row.operator_id}]"
        claim_operability, claim_operability_summary_line = _ACTION_OPERABILITY.get(
            row.action,
            (
                'JOURNALED_ACTION_PENDING',
                'Journaled operator action is awaiting projection-backed materialization.',
            ),
        )
        projection_age_seconds = _projection_age_seconds(row.created_at_utc, as_of_utc=as_of_utc)
        projection_freshness_state = _projection_freshness_state(age_seconds=projection_age_seconds)
        if projection_freshness_state == 'CURRENT':
            current_count += 1
        elif projection_freshness_state == 'AGING':
            aging_count += 1
        else:
            stale_count += 1
        projection_governed_merge_state, projection_governed_summary_line, is_primary_merge = _projection_governed_merge_fields(
            item_key=item_key,
            queue_state=queue_state,
        )
        if is_primary_merge:
            primary_merge_pending_count += 1
        else:
            auxiliary_merge_pending_count += 1
        projection_post_merge_lifecycle_state, projection_post_merge_summary_line, post_merge_recommendation = _projection_post_merge_lifecycle_fields(
            freshness_state=projection_freshness_state,
            merge_state=projection_governed_merge_state,
        )
        if projection_post_merge_lifecycle_state.endswith('READY'):
            post_merge_ready_count += 1
        elif projection_post_merge_lifecycle_state == 'POST_MERGE_REVIEW_REQUIRED':
            post_merge_review_required_count += 1
        else:
            post_merge_stale_count += 1
        projection_downstream_closure_state, projection_downstream_closure_summary_line, downstream_closure_recommendation = _projection_downstream_closure_fields(
            freshness_state=projection_freshness_state,
            merge_state=projection_governed_merge_state,
            post_merge_state=projection_post_merge_lifecycle_state,
        )
        if projection_downstream_closure_state.endswith('READY'):
            downstream_closure_ready_count += 1
        elif projection_downstream_closure_state == 'DOWNSTREAM_CLOSURE_REVIEW_REQUIRED':
            downstream_closure_review_required_count += 1
        else:
            downstream_closure_blocked_count += 1
        projection_recommended_actions = _projection_recommended_actions(
            action_name=row.action,
            operator_id=row.operator_id,
            freshness_state=projection_freshness_state,
            merge_state=projection_governed_merge_state,
            post_merge_recommendation=post_merge_recommendation,
            downstream_closure_recommendation=downstream_closure_recommendation,
        )
        items.append(
            OracleOperatorWorkItem(
                work_item_key=item_key,
                queue_key=claim.governance_plane_claim_queue_key,
                review_target=review_target,
                priority_band=claim.governance_plane_claim_priority_band,
                review_due_by_utc=review_due_by_utc,
                review_sort_key=review_sort_key,
                source_kind='JOURNALED_PENDING',
                source_event_id=row.action_event_id,
                source_created_at_utc=row.created_at_utc,
                claim_summary_line=summary_line,
                claim_primary_action_text=row.action,
                claim_worker_lane=claim.governance_plane_claim_worker_lane,
                claim_worker_summary_line=f"Operator {row.operator_id} journaled `{row.action}` for governed queue follow-up.",
                claim_worker_sort_key=f"journal-worker:{row.operator_id}:{row.action_event_id}",
                claim_operability=claim_operability,
                claim_operability_summary_line=claim_operability_summary_line,
                dispatch_posture=dispatch.governance_plane_dispatch_posture,
                dispatch_permitted=dispatch.governance_plane_dispatch_permitted,
                dispatch_claim_permitted_now=dispatch.governance_plane_dispatch_claim_permitted_now,
                dispatch_claim_key=dispatch.governance_plane_dispatch_claim_key,
                dispatch_claim_urgency='JOURNALED',
                dispatch_claim_score=dispatch.governance_plane_dispatch_claim_score,
                dispatch_claim_summary_line=dispatch.governance_plane_dispatch_claim_summary_line,
                lease_key=f"journal:{row.action_event_id}",
                lease_active_now=row.action == 'renew-lease',
                lease_summary_line='Operator action projection is active until downstream state materialization confirms the governed queue view.',
                lease_action=row.action,
                lease_action_summary_line='Refresh the operator workboard projection to materialize journal-backed state.',
                projected_operator_id=row.operator_id,
                projected_action_name=row.action,
                projection_generated_at_utc=row.created_at_utc,
                projection_age_seconds=projection_age_seconds,
                projection_freshness_state=projection_freshness_state,
                projection_summary_line=summary_line,
                projection_recommended_actions=projection_recommended_actions,
                projection_governed_merge_state=projection_governed_merge_state,
                projection_governed_queue_key=claim.governance_plane_claim_queue_key,
                projection_governed_priority_band=claim.governance_plane_claim_priority_band,
                projection_governed_dispatch_posture=dispatch.governance_plane_dispatch_posture,
                projection_governed_summary_line=projection_governed_summary_line,
                projection_post_merge_lifecycle_state=projection_post_merge_lifecycle_state,
                projection_post_merge_summary_line=projection_post_merge_summary_line,
                projection_downstream_closure_state=projection_downstream_closure_state,
                projection_downstream_closure_summary_line=projection_downstream_closure_summary_line,
            )
        )
    latest_action_at, operator_ids, action_names, summary_line, recommended = _build_projection_summary(
        rows=rows,
        review_target=claim.governance_plane_claim_review_target,
        current_count=current_count,
        aging_count=aging_count,
        stale_count=stale_count,
        primary_merge_pending_count=primary_merge_pending_count,
        auxiliary_merge_pending_count=auxiliary_merge_pending_count,
        post_merge_ready_count=post_merge_ready_count,
        post_merge_review_required_count=post_merge_review_required_count,
        post_merge_stale_count=post_merge_stale_count,
        downstream_closure_ready_count=downstream_closure_ready_count,
        downstream_closure_review_required_count=downstream_closure_review_required_count,
        downstream_closure_blocked_count=downstream_closure_blocked_count,
    )
    return OperatorActionWorkboardProjection(
        review_target=claim.governance_plane_claim_review_target,
        source_event_count=len(rows),
        projected_work_item_count=len(items),
        work_items=tuple(items),
        latest_action_created_at_utc=latest_action_at,
        operator_ids=operator_ids,
        action_names=action_names,
        operator_count=len(operator_ids),
        action_count=len(action_names),
        current_work_item_count=current_count,
        aging_work_item_count=aging_count,
        stale_work_item_count=stale_count,
        primary_merge_pending_count=primary_merge_pending_count,
        auxiliary_merge_pending_count=auxiliary_merge_pending_count,
        post_merge_ready_count=post_merge_ready_count,
        post_merge_review_required_count=post_merge_review_required_count,
        post_merge_stale_count=post_merge_stale_count,
        downstream_closure_ready_count=downstream_closure_ready_count,
        downstream_closure_review_required_count=downstream_closure_review_required_count,
        downstream_closure_blocked_count=downstream_closure_blocked_count,
        summary_line=summary_line,
        recommended_next_actions=recommended,
        projection_enabled=projection_status.enabled,
        projection_status_state=projection_status.state,
        projection_status_reason=projection_status.reason,
        projection_trust_status=projection_status.trust_status,
        projection_source_label=projection_status.source_label,
        projection_ledger_db_path_configured=projection_status.ledger_db_path_configured,
    )


def materialize_journaled_operator_work_items(queue_state: 'OracleGovernanceWorkQueueState') -> tuple[OracleOperatorWorkItem, ...]:
    return materialize_operator_action_workboard_projection(queue_state).work_items


__all__ = [
    'OperatorActionProjectionStatus',
    'OperatorActionWorkboardProjection',
    'materialize_journaled_operator_work_items',
    'materialize_operator_action_workboard_projection',
    'get_operator_action_projection_status',
    'operator_action_projection_enabled',
]
