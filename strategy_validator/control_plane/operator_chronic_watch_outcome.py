from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from strategy_validator.control_plane.materialization import write_json_markdown_artifacts

from strategy_validator.control_plane.operator_chronic_watch_handoff import (
    OracleOperatorChronicWatchHandoff,
    build_operator_chronic_watch_handoff_request,
    materialize_operator_chronic_watch_handoff,
)


@dataclass(frozen=True)
class OracleOperatorChronicWatchOutcomeRequest:
    outcome_root: Path
    board_label: str = 'default'
    evaluator_label: str = 'chronic-watch-evaluator'
    evaluated_at_utc: datetime | None = None
    drift_signal_mode: str = 'AUTO'


@dataclass(frozen=True)
class OracleOperatorChronicWatchOutcomeItem:
    outcome_key: str
    handoff_key: str
    activation_key: str
    policy_key: str
    work_item_key: str
    handoff_state: str
    watch_authority: str
    watch_window_minutes: int
    watch_due_by_utc: str
    drift_signal_mode: str
    watch_status: str
    outcome_state: str
    outcome_reason_code: str
    normalization_eligible: bool
    reopen_required: bool
    next_queue_lane: str
    evaluator_label: str
    evaluated_at_utc: str

    def to_payload(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class OracleOperatorChronicWatchOutcome:
    schema_version: str
    board_label: str
    outcome_root: str
    evaluator_label: str
    evaluated_at_utc: str
    outcome_count: int
    stable_count: int
    active_watch_count: int
    breached_count: int
    blocked_count: int
    normalization_ready_count: int
    reopen_required_count: int
    summary_output_path: str
    markdown_output_path: str
    items: tuple[OracleOperatorChronicWatchOutcomeItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'board_label': self.board_label,
            'outcome_root': self.outcome_root,
            'evaluator_label': self.evaluator_label,
            'evaluated_at_utc': self.evaluated_at_utc,
            'outcome_count': self.outcome_count,
            'stable_count': self.stable_count,
            'active_watch_count': self.active_watch_count,
            'breached_count': self.breached_count,
            'blocked_count': self.blocked_count,
            'normalization_ready_count': self.normalization_ready_count,
            'reopen_required_count': self.reopen_required_count,
            'summary_output_path': self.summary_output_path,
            'markdown_output_path': self.markdown_output_path,
            'items': [item.to_payload() for item in self.items],
        }


def build_operator_chronic_watch_outcome_request(**kwargs: Any) -> OracleOperatorChronicWatchOutcomeRequest:
    kwargs['outcome_root'] = Path(kwargs['outcome_root']).resolve()
    return OracleOperatorChronicWatchOutcomeRequest(**kwargs)


def _normalize(ts: datetime | None) -> datetime:
    if ts is None:
        return datetime.now(tz=UTC).replace(microsecond=0)
    if ts.tzinfo is None:
        return ts.replace(tzinfo=UTC)
    return ts.astimezone(UTC).replace(microsecond=0)


def _derive_item(item: Any, request: OracleOperatorChronicWatchOutcomeRequest, evaluated_at_utc: datetime) -> OracleOperatorChronicWatchOutcomeItem:
    due_by = datetime.fromisoformat(item.watch_due_by_utc)
    if due_by.tzinfo is None:
        due_by = due_by.replace(tzinfo=UTC)

    watch_status = 'WATCH_ACTIVE'
    outcome_state = 'CHRONIC_WATCH_UNDER_OBSERVATION'
    reason = 'CHRONIC_REJOIN_STILL_WITHIN_WATCH_WINDOW'
    normalization_eligible = False
    reopen_required = False
    next_lane = 'SUPERVISOR_MONITORED_RETURN_QUEUE' if item.watch_authority == 'SUPERVISOR_MONITORING_AUTHORITY' else 'RETURN_AUTHORIZATION_REENTRY_QUEUE'

    if item.handoff_state == 'WATCH_HANDOFF_BLOCKED':
        watch_status = 'WATCH_BLOCKED'
        outcome_state = 'CHRONIC_WATCH_OUTCOME_BLOCKED'
        reason = 'WATCH_HANDOFF_DID_NOT_AUTHORIZE_MONITORED_REJOIN_OBSERVATION'
        next_lane = 'CHRONIC_REMEDIATION_QUEUE'
    elif request.drift_signal_mode == 'DETECTED':
        watch_status = 'WATCH_BREACHED'
        outcome_state = 'CHRONIC_WATCH_BREACH_REOPEN_REQUIRED'
        reason = 'CHRONIC_REJOIN_DRIFT_SIGNAL_DETECTED_DURING_WATCH_WINDOW'
        reopen_required = True
        next_lane = 'REENTRY_QUEUE'
    elif evaluated_at_utc >= due_by:
        watch_status = 'WATCH_WINDOW_COMPLETE'
        outcome_state = 'CHRONIC_WATCH_STABLE_NORMALIZATION_READY'
        reason = 'CHRONIC_REJOIN_STAYED_STABLE_THROUGH_WATCH_WINDOW'
        normalization_eligible = True
        next_lane = 'RETURN_NORMALIZATION_BRIDGE'

    return OracleOperatorChronicWatchOutcomeItem(
        outcome_key=f'chronic_watch_outcome:{item.handoff_key}',
        handoff_key=item.handoff_key,
        activation_key=item.activation_key,
        policy_key=item.policy_key,
        work_item_key=item.work_item_key,
        handoff_state=item.handoff_state,
        watch_authority=item.watch_authority,
        watch_window_minutes=item.watch_window_minutes,
        watch_due_by_utc=item.watch_due_by_utc,
        drift_signal_mode=request.drift_signal_mode,
        watch_status=watch_status,
        outcome_state=outcome_state,
        outcome_reason_code=reason,
        normalization_eligible=normalization_eligible,
        reopen_required=reopen_required,
        next_queue_lane=next_lane,
        evaluator_label=request.evaluator_label,
        evaluated_at_utc=evaluated_at_utc.isoformat(),
    )


def materialize_operator_chronic_watch_outcome(
    request: OracleOperatorChronicWatchOutcomeRequest,
    *,
    chronic_watch_handoff: OracleOperatorChronicWatchHandoff | None = None,
    operator_queue_query_result=None,
    board_label: str = 'default',
) -> OracleOperatorChronicWatchOutcome:
    if chronic_watch_handoff is None:
        chronic_watch_handoff = materialize_operator_chronic_watch_handoff(
            build_operator_chronic_watch_handoff_request(
                handoff_root=request.outcome_root / 'chronic_watch_handoff',
                board_label=board_label,
                handoff_label='chronic-watch-handoff',
                handed_off_at_utc=request.evaluated_at_utc,
            ),
            operator_queue_query_result=operator_queue_query_result,
            board_label=board_label,
        )
    evaluated_at_utc = _normalize(request.evaluated_at_utc)
    items = tuple(_derive_item(item, request, evaluated_at_utc) for item in chronic_watch_handoff.items)
    request.outcome_root.mkdir(parents=True, exist_ok=True)
    summary_output_path = request.outcome_root / 'ORACLE_OPERATOR_CHRONIC_WATCH_OUTCOME.json'
    markdown_output_path = request.outcome_root / 'ORACLE_OPERATOR_CHRONIC_WATCH_OUTCOME.md'
    report = OracleOperatorChronicWatchOutcome(
        schema_version='oracle_operator_chronic_watch_outcome/v1',
        board_label=chronic_watch_handoff.board_label,
        outcome_root=str(request.outcome_root),
        evaluator_label=request.evaluator_label,
        evaluated_at_utc=evaluated_at_utc.isoformat(),
        outcome_count=len(items),
        stable_count=len([item for item in items if item.outcome_state == 'CHRONIC_WATCH_STABLE_NORMALIZATION_READY']),
        active_watch_count=len([item for item in items if item.outcome_state == 'CHRONIC_WATCH_UNDER_OBSERVATION']),
        breached_count=len([item for item in items if item.outcome_state == 'CHRONIC_WATCH_BREACH_REOPEN_REQUIRED']),
        blocked_count=len([item for item in items if item.outcome_state == 'CHRONIC_WATCH_OUTCOME_BLOCKED']),
        normalization_ready_count=len([item for item in items if item.normalization_eligible]),
        reopen_required_count=len([item for item in items if item.reopen_required]),
        summary_output_path=str(summary_output_path),
        markdown_output_path=str(markdown_output_path),
        items=items,
    )
    write_json_markdown_artifacts(
        summary_output_path=summary_output_path,
        markdown_output_path=markdown_output_path,
        payload=report.to_payload(),
        markdown=[
        '## Operator Chronic Watch Outcome',
        f"- Board label: `{report.board_label}`",
        f"- Evaluator label: `{report.evaluator_label}`",
        f"- Stable count: `{report.stable_count}`",
        f"- Active watch count: `{report.active_watch_count}`",
        f"- Breached count: `{report.breached_count}`",
        *[f"- {item.work_item_key}: {item.outcome_state} -> {item.next_queue_lane}" for item in report.items],
        '',
    ],
    )
    return report


__all__ = [
    'OracleOperatorChronicWatchOutcome',
    'OracleOperatorChronicWatchOutcomeItem',
    'OracleOperatorChronicWatchOutcomeRequest',
    'build_operator_chronic_watch_outcome_request',
    'materialize_operator_chronic_watch_outcome',
]
