from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from strategy_validator.control_plane.operator_queue_service import OracleGovernanceWorkQueueState


@dataclass(frozen=True)
class OracleOperatorWorkItem:
    work_item_key: str
    queue_key: str
    review_target: str
    priority_band: str
    review_due_by_utc: datetime
    review_sort_key: str
    source_kind: str
    source_event_id: str | None
    source_created_at_utc: datetime | None
    claim_summary_line: str
    claim_primary_action_text: str
    claim_worker_lane: str
    claim_worker_summary_line: str
    claim_worker_sort_key: str
    claim_operability: str
    claim_operability_summary_line: str
    dispatch_posture: str
    dispatch_permitted: bool
    dispatch_claim_permitted_now: bool
    dispatch_claim_key: str
    dispatch_claim_urgency: str
    dispatch_claim_score: int
    dispatch_claim_summary_line: str
    lease_key: str
    lease_active_now: bool
    lease_summary_line: str
    lease_action: str
    lease_action_summary_line: str
    projected_operator_id: str | None = None
    projected_action_name: str | None = None
    projection_generated_at_utc: datetime | None = None
    projection_age_seconds: int | None = None
    projection_freshness_state: str | None = None
    projection_summary_line: str | None = None
    projection_recommended_actions: tuple[str, ...] = ()
    projection_governed_merge_state: str | None = None
    projection_governed_queue_key: str | None = None
    projection_governed_priority_band: str | None = None
    projection_governed_dispatch_posture: str | None = None
    projection_governed_summary_line: str | None = None
    projection_post_merge_lifecycle_state: str | None = None
    projection_post_merge_summary_line: str | None = None
    projection_downstream_closure_state: str | None = None
    projection_downstream_closure_summary_line: str | None = None


@dataclass(frozen=True)
class OracleOperatorQueueSnapshot:
    queue_key: str
    review_target: str
    priority_band: str
    review_due_by_utc: datetime
    review_sort_key: str
    queue_summary_line: str
    queue_state: 'OracleGovernanceWorkQueueState'
    primary_work_item: OracleOperatorWorkItem
    work_items: tuple[OracleOperatorWorkItem, ...]
    recommended_next_actions: tuple[str, ...]
    latest_journaled_action_at_utc: datetime | None = None
    journal_operator_count: int = 0
    journal_action_count: int = 0
    journal_projection_summary_line: str | None = None
    journal_primary_merge_pending_count: int = 0
    journal_auxiliary_merge_pending_count: int = 0
    journal_post_merge_ready_count: int = 0
    journal_post_merge_review_required_count: int = 0
    journal_post_merge_stale_count: int = 0
    journal_downstream_closure_ready_count: int = 0
    journal_downstream_closure_review_required_count: int = 0
    journal_downstream_closure_blocked_count: int = 0
    journal_projection_enabled: bool = False
    journal_projection_status_state: str = 'DISABLED'
    journal_projection_status_reason: str = 'STRATEGY_VALIDATOR_LEDGER_DB_PATH is not configured.'
    journal_projection_trust_status: str = 'TRUST_RESTRICTED'
    journal_projection_source_label: str = 'operator_action_journal'
    journal_projection_ledger_db_path_configured: bool = False


@dataclass(frozen=True)
class OracleOperatorQueueSnapshotRequest:
    governance_work_queue: 'OracleGovernanceWorkQueueState'


@dataclass(frozen=True)
class OracleOperatorQueueQueryRequest:
    operator_queue_snapshot: OracleOperatorQueueSnapshot


@dataclass(frozen=True)
class OracleOperatorQueueQueryWorkItem:
    work_item_key: str
    queue_key: str
    review_target: str
    priority_band: str
    review_due_by_utc: datetime
    review_sort_key: str
    source_kind: str
    source_event_id: str | None
    source_created_at_utc: datetime | None
    claim_summary_line: str
    claim_primary_action_text: str
    claim_worker_lane: str
    claim_operability: str
    dispatch_posture: str
    dispatch_permitted: bool
    dispatch_claim_permitted_now: bool
    dispatch_claim_key: str
    dispatch_claim_urgency: str
    dispatch_claim_score: int
    lease_key: str
    lease_active_now: bool
    projected_operator_id: str | None = None
    projected_action_name: str | None = None
    projection_generated_at_utc: datetime | None = None
    projection_age_seconds: int | None = None
    projection_freshness_state: str | None = None
    projection_summary_line: str | None = None
    projection_governed_merge_state: str | None = None
    projection_governed_queue_key: str | None = None
    projection_governed_priority_band: str | None = None
    projection_governed_dispatch_posture: str | None = None
    projection_governed_summary_line: str | None = None
    projection_post_merge_lifecycle_state: str | None = None
    projection_post_merge_summary_line: str | None = None
    projection_downstream_closure_state: str | None = None
    projection_downstream_closure_summary_line: str | None = None
    recommended_actions: tuple[str, ...] = ()


@dataclass(frozen=True)
class OracleOperatorQueueQueryResult:
    queue_key: str
    review_target: str
    priority_band: str
    review_due_by_utc: datetime
    review_sort_key: str
    work_item_count: int
    governed_work_item_count: int
    journaled_work_item_count: int
    summary_line: str
    queue_summary_line: str
    recommended_next_actions: tuple[str, ...]
    work_items: tuple[OracleOperatorQueueQueryWorkItem, ...]
    latest_journaled_action_at_utc: datetime | None = None
    journal_operator_count: int = 0
    journal_action_count: int = 0
    journal_projection_summary_line: str | None = None
    journal_primary_merge_pending_count: int = 0
    journal_auxiliary_merge_pending_count: int = 0
    journal_post_merge_ready_count: int = 0
    journal_post_merge_review_required_count: int = 0
    journal_post_merge_stale_count: int = 0
    journal_downstream_closure_ready_count: int = 0
    journal_downstream_closure_review_required_count: int = 0
    journal_downstream_closure_blocked_count: int = 0
    journal_projection_enabled: bool = False
    journal_projection_status_state: str = 'DISABLED'
    journal_projection_status_reason: str = 'STRATEGY_VALIDATOR_LEDGER_DB_PATH is not configured.'
    journal_projection_trust_status: str = 'TRUST_RESTRICTED'
    journal_projection_source_label: str = 'operator_action_journal'
    journal_projection_ledger_db_path_configured: bool = False

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': 'oracle_operator_queue_query_report/v1',
            'queue_key': self.queue_key,
            'review_target': self.review_target,
            'priority_band': self.priority_band,
            'review_due_by_utc': self.review_due_by_utc.isoformat(),
            'review_sort_key': self.review_sort_key,
            'work_item_count': self.work_item_count,
            'governed_work_item_count': self.governed_work_item_count,
            'journaled_work_item_count': self.journaled_work_item_count,
            'summary_line': self.summary_line,
            'queue_summary_line': self.queue_summary_line,
            'recommended_next_actions': list(self.recommended_next_actions),
            'latest_journaled_action_at_utc': self.latest_journaled_action_at_utc.isoformat() if self.latest_journaled_action_at_utc else None,
            'journal_operator_count': self.journal_operator_count,
            'journal_action_count': self.journal_action_count,
            'journal_projection_summary_line': self.journal_projection_summary_line,
            'journal_primary_merge_pending_count': self.journal_primary_merge_pending_count,
            'journal_auxiliary_merge_pending_count': self.journal_auxiliary_merge_pending_count,
            'journal_post_merge_ready_count': self.journal_post_merge_ready_count,
            'journal_post_merge_review_required_count': self.journal_post_merge_review_required_count,
            'journal_post_merge_stale_count': self.journal_post_merge_stale_count,
            'journal_downstream_closure_ready_count': self.journal_downstream_closure_ready_count,
            'journal_downstream_closure_review_required_count': self.journal_downstream_closure_review_required_count,
            'journal_downstream_closure_blocked_count': self.journal_downstream_closure_blocked_count,
            'journal_projection_enabled': self.journal_projection_enabled,
            'journal_projection_status_state': self.journal_projection_status_state,
            'journal_projection_status_reason': self.journal_projection_status_reason,
            'journal_projection_trust_status': self.journal_projection_trust_status,
            'journal_projection_source_label': self.journal_projection_source_label,
            'journal_projection_ledger_db_path_configured': self.journal_projection_ledger_db_path_configured,
            'work_items': [
                {
                    **asdict(item),
                    'review_due_by_utc': item.review_due_by_utc.isoformat(),
                    'source_created_at_utc': item.source_created_at_utc.isoformat() if item.source_created_at_utc else None,
                    'projection_generated_at_utc': item.projection_generated_at_utc.isoformat() if item.projection_generated_at_utc else None,
                    'recommended_actions': list(item.recommended_actions),
                }
                for item in self.work_items
            ],
        }


@dataclass(frozen=True)
class OracleOperatorWorkboardRequest:
    operator_queue_query_result: OracleOperatorQueueQueryResult
    board_label: str = 'default'


@dataclass(frozen=True)
class OracleOperatorWorkboardEntry:
    work_item_key: str
    queue_key: str
    review_target: str
    priority_band: str
    review_due_by_utc: datetime
    review_sort_key: str
    source_kind: str
    source_event_id: str | None
    source_created_at_utc: datetime | None
    action_owner_lane: str
    claim_operability: str
    dispatch_posture: str
    urgency: str
    score: int
    summary_line: str
    projected_operator_id: str | None = None
    projected_action_name: str | None = None
    projection_generated_at_utc: datetime | None = None
    projection_age_seconds: int | None = None
    projection_freshness_state: str | None = None
    projection_summary_line: str | None = None
    projection_governed_merge_state: str | None = None
    projection_governed_queue_key: str | None = None
    projection_governed_priority_band: str | None = None
    projection_governed_dispatch_posture: str | None = None
    projection_governed_summary_line: str | None = None
    projection_post_merge_lifecycle_state: str | None = None
    projection_post_merge_summary_line: str | None = None
    projection_downstream_closure_state: str | None = None
    projection_downstream_closure_summary_line: str | None = None
    recommended_actions: tuple[str, ...] = ()

    def to_payload(self) -> dict[str, Any]:
        return {
            'work_item_key': self.work_item_key,
            'queue_key': self.queue_key,
            'review_target': self.review_target,
            'priority_band': self.priority_band,
            'review_due_by_utc': self.review_due_by_utc.isoformat(),
            'review_sort_key': self.review_sort_key,
            'source_kind': self.source_kind,
            'source_event_id': self.source_event_id,
            'source_created_at_utc': self.source_created_at_utc.isoformat() if self.source_created_at_utc else None,
            'action_owner_lane': self.action_owner_lane,
            'claim_operability': self.claim_operability,
            'dispatch_posture': self.dispatch_posture,
            'urgency': self.urgency,
            'score': self.score,
            'summary_line': self.summary_line,
            'projected_operator_id': self.projected_operator_id,
            'projected_action_name': self.projected_action_name,
            'projection_generated_at_utc': self.projection_generated_at_utc.isoformat() if self.projection_generated_at_utc else None,
            'projection_age_seconds': self.projection_age_seconds,
            'projection_freshness_state': self.projection_freshness_state,
            'projection_summary_line': self.projection_summary_line,
            'projection_governed_merge_state': self.projection_governed_merge_state,
            'projection_governed_queue_key': self.projection_governed_queue_key,
            'projection_governed_priority_band': self.projection_governed_priority_band,
            'projection_governed_dispatch_posture': self.projection_governed_dispatch_posture,
            'projection_governed_summary_line': self.projection_governed_summary_line,
            'projection_post_merge_lifecycle_state': self.projection_post_merge_lifecycle_state,
            'projection_post_merge_summary_line': self.projection_post_merge_summary_line,
            'projection_downstream_closure_state': self.projection_downstream_closure_state,
            'projection_downstream_closure_summary_line': self.projection_downstream_closure_summary_line,
            'recommended_actions': list(self.recommended_actions),
        }


@dataclass(frozen=True)
class OracleOperatorWorkboard:
    board_label: str
    queue_key: str
    review_target: str
    priority_band: str
    review_due_by_utc: datetime
    review_sort_key: str
    work_item_count: int
    governed_work_item_count: int
    journaled_work_item_count: int
    summary_line: str
    queue_summary_line: str
    recommended_next_actions: tuple[str, ...]
    entries: tuple[OracleOperatorWorkboardEntry, ...]
    latest_journaled_action_at_utc: datetime | None = None
    journal_operator_count: int = 0
    journal_action_count: int = 0
    journal_projection_summary_line: str | None = None
    journal_primary_merge_pending_count: int = 0
    journal_auxiliary_merge_pending_count: int = 0
    journal_post_merge_ready_count: int = 0
    journal_post_merge_review_required_count: int = 0
    journal_post_merge_stale_count: int = 0
    journal_downstream_closure_ready_count: int = 0
    journal_downstream_closure_review_required_count: int = 0
    journal_downstream_closure_blocked_count: int = 0
    journal_projection_enabled: bool = False
    journal_projection_status_state: str = 'DISABLED'
    journal_projection_status_reason: str = 'STRATEGY_VALIDATOR_LEDGER_DB_PATH is not configured.'
    journal_projection_trust_status: str = 'TRUST_RESTRICTED'
    journal_projection_source_label: str = 'operator_action_journal'
    journal_projection_ledger_db_path_configured: bool = False

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': 'oracle_operator_workboard/v1',
            'board_label': self.board_label,
            'queue_key': self.queue_key,
            'review_target': self.review_target,
            'priority_band': self.priority_band,
            'review_due_by_utc': self.review_due_by_utc.isoformat(),
            'review_sort_key': self.review_sort_key,
            'work_item_count': self.work_item_count,
            'governed_work_item_count': self.governed_work_item_count,
            'journaled_work_item_count': self.journaled_work_item_count,
            'summary_line': self.summary_line,
            'queue_summary_line': self.queue_summary_line,
            'recommended_next_actions': list(self.recommended_next_actions),
            'latest_journaled_action_at_utc': self.latest_journaled_action_at_utc.isoformat() if self.latest_journaled_action_at_utc else None,
            'journal_operator_count': self.journal_operator_count,
            'journal_action_count': self.journal_action_count,
            'journal_projection_summary_line': self.journal_projection_summary_line,
            'journal_primary_merge_pending_count': self.journal_primary_merge_pending_count,
            'journal_auxiliary_merge_pending_count': self.journal_auxiliary_merge_pending_count,
            'journal_post_merge_ready_count': self.journal_post_merge_ready_count,
            'journal_post_merge_review_required_count': self.journal_post_merge_review_required_count,
            'journal_post_merge_stale_count': self.journal_post_merge_stale_count,
            'journal_downstream_closure_ready_count': self.journal_downstream_closure_ready_count,
            'journal_downstream_closure_review_required_count': self.journal_downstream_closure_review_required_count,
            'journal_downstream_closure_blocked_count': self.journal_downstream_closure_blocked_count,
            'journal_projection_enabled': self.journal_projection_enabled,
            'journal_projection_status_state': self.journal_projection_status_state,
            'journal_projection_status_reason': self.journal_projection_status_reason,
            'journal_projection_trust_status': self.journal_projection_trust_status,
            'journal_projection_source_label': self.journal_projection_source_label,
            'journal_projection_ledger_db_path_configured': self.journal_projection_ledger_db_path_configured,
            'entries': [entry.to_payload() for entry in self.entries],
        }


__all__ = [
    'OracleOperatorQueueQueryRequest',
    'OracleOperatorQueueQueryResult',
    'OracleOperatorQueueQueryWorkItem',
    'OracleOperatorQueueSnapshot',
    'OracleOperatorQueueSnapshotRequest',
    'OracleOperatorWorkItem',
    'OracleOperatorWorkboard',
    'OracleOperatorWorkboardEntry',
    'OracleOperatorWorkboardRequest',
]
