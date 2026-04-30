from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from strategy_validator.control_plane.operator_pack_drift import (
    OracleOperatorPackDrift,
    OracleOperatorPackDriftItem,
    OracleOperatorPackDriftRequest,
    build_operator_pack_drift_request,
    materialize_operator_pack_drift,
)


@dataclass(frozen=True)
class OracleOperatorPackEscalationRequest:
    search_root: Path
    repo_root: Path | None = None
    current_pack_kind: str | None = None
    pack_kinds: tuple[str, ...] = ()
    trust_statuses: tuple[str, ...] = ()
    summary_line_contains: str | None = None
    output_artifact_label_contains: str | None = None
    max_items: int = 4
    sustained_degraded_threshold: int = 2
    queue_key: str | None = None
    review_target: str | None = None
    priority_band: str | None = None
    action_owner_lane: str | None = None
    board_label: str | None = None


@dataclass(frozen=True)
class OracleOperatorPackEscalationItem:
    pack_kind: str
    drift_state: str
    severity: str
    escalation_posture: str
    routing_lane: str
    routing_target: str
    priority_band: str
    queue_key: str | None
    board_label: str | None
    latest_trust_status: str | None
    previous_trust_status: str | None
    latest_summary_line: str | None
    previous_summary_line: str | None
    latest_manifest_path: Path
    previous_manifest_path: Path | None
    recommended_actions: tuple[str, ...]
    is_current_pack_kind: bool


@dataclass(frozen=True)
class OracleOperatorPackEscalation:
    schema_version: str
    search_root: str
    current_pack_kind: str | None
    queue_key: str | None
    review_target: str | None
    priority_band: str | None
    action_owner_lane: str | None
    board_label: str | None
    total_escalation_count: int
    items: tuple[OracleOperatorPackEscalationItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'search_root': self.search_root,
            'current_pack_kind': self.current_pack_kind,
            'queue_key': self.queue_key,
            'review_target': self.review_target,
            'priority_band': self.priority_band,
            'action_owner_lane': self.action_owner_lane,
            'board_label': self.board_label,
            'total_escalation_count': self.total_escalation_count,
            'item_count': len(self.items),
            'items': [
                {
                    'pack_kind': item.pack_kind,
                    'drift_state': item.drift_state,
                    'severity': item.severity,
                    'escalation_posture': item.escalation_posture,
                    'routing_lane': item.routing_lane,
                    'routing_target': item.routing_target,
                    'priority_band': item.priority_band,
                    'queue_key': item.queue_key,
                    'board_label': item.board_label,
                    'latest_trust_status': item.latest_trust_status,
                    'previous_trust_status': item.previous_trust_status,
                    'latest_summary_line': item.latest_summary_line,
                    'previous_summary_line': item.previous_summary_line,
                    'latest_manifest_path': str(item.latest_manifest_path),
                    'previous_manifest_path': str(item.previous_manifest_path) if item.previous_manifest_path else None,
                    'recommended_actions': list(item.recommended_actions),
                    'is_current_pack_kind': item.is_current_pack_kind,
                }
                for item in self.items
            ],
        }


def build_operator_pack_escalation_request(
    *,
    search_root: Path,
    repo_root: Path | None = None,
    current_pack_kind: str | None = None,
    pack_kinds: Sequence[str] = (),
    trust_statuses: Sequence[str] = (),
    summary_line_contains: str | None = None,
    output_artifact_label_contains: str | None = None,
    max_items: int = 4,
    sustained_degraded_threshold: int = 2,
    queue_key: str | None = None,
    review_target: str | None = None,
    priority_band: str | None = None,
    action_owner_lane: str | None = None,
    board_label: str | None = None,
) -> OracleOperatorPackEscalationRequest:
    return OracleOperatorPackEscalationRequest(
        search_root=search_root.resolve(),
        repo_root=repo_root.resolve() if repo_root is not None else None,
        current_pack_kind=current_pack_kind or None,
        pack_kinds=tuple(item for item in pack_kinds if item),
        trust_statuses=tuple(item for item in trust_statuses if item),
        summary_line_contains=summary_line_contains or None,
        output_artifact_label_contains=output_artifact_label_contains or None,
        max_items=max(1, int(max_items)),
        sustained_degraded_threshold=max(2, int(sustained_degraded_threshold)),
        queue_key=queue_key or None,
        review_target=review_target or None,
        priority_band=priority_band or None,
        action_owner_lane=action_owner_lane or None,
        board_label=board_label or None,
    )


def _infer_routing_lane(pack_kind: str, severity: str, action_owner_lane: str | None) -> str:
    if action_owner_lane:
        return action_owner_lane
    if pack_kind == 'incident_pack' or severity == 'ELEVATED':
        return 'incident_response'
    if pack_kind == 'status_pack':
        return 'governance_ops'
    return 'research_ops'


def _infer_routing_target(pack_kind: str, review_target: str | None) -> str:
    if review_target:
        return review_target
    return {
        'incident_pack': 'incident_triage',
        'status_pack': 'governance_review',
        'briefing_pack': 'operator_briefing_review',
    }.get(pack_kind, 'operator_review')


def _infer_priority_band(drift: OracleOperatorPackDriftItem, explicit: str | None) -> str:
    if explicit:
        return explicit
    if drift.severity == 'ELEVATED' and drift.latest_trust_status == 'UNTRUSTED':
        return 'CRITICAL'
    if drift.severity == 'ELEVATED':
        return 'HIGH'
    return 'NORMAL'


def _escalation_posture(drift: OracleOperatorPackDriftItem) -> str:
    if drift.latest_trust_status == 'UNTRUSTED':
        return 'IMMEDIATE_OPERATOR_REVIEW'
    if drift.drift_state == 'WORSENING' or drift.severity == 'ELEVATED':
        return 'EXPEDITED_QUEUE_REVIEW'
    return 'WATCH_QUEUE_REVIEW'


def _compose_actions(
    drift: OracleOperatorPackDriftItem,
    *,
    routing_lane: str,
    routing_target: str,
    priority_band: str,
    queue_key: str | None,
) -> tuple[str, ...]:
    actions = [
        f'Route `{drift.pack_kind}` drift into `{routing_lane}` for `{routing_target}` at priority `{priority_band}`.',
    ]
    if queue_key:
        actions.append(f'Attach the escalation to operator queue `{queue_key}` for the next review cycle.')
    actions.extend(drift.recommended_actions)
    return tuple(actions)


def materialize_operator_pack_escalation(
    request: OracleOperatorPackEscalationRequest,
    *,
    drift: OracleOperatorPackDrift | None = None,
    drift_request: OracleOperatorPackDriftRequest | None = None,
) -> OracleOperatorPackEscalation:
    if drift is None:
        drift = materialize_operator_pack_drift(
            drift_request
            or build_operator_pack_drift_request(
                search_root=request.search_root,
                repo_root=request.repo_root,
                current_pack_kind=request.current_pack_kind,
                pack_kinds=request.pack_kinds,
                trust_statuses=request.trust_statuses,
                summary_line_contains=request.summary_line_contains,
                output_artifact_label_contains=request.output_artifact_label_contains,
                max_items=request.max_items,
                sustained_degraded_threshold=request.sustained_degraded_threshold,
            )
        )
    items: list[OracleOperatorPackEscalationItem] = []
    for drift_item in drift.items[: request.max_items]:
        routing_lane = _infer_routing_lane(drift_item.pack_kind, drift_item.severity, request.action_owner_lane)
        routing_target = _infer_routing_target(drift_item.pack_kind, request.review_target)
        priority_band = _infer_priority_band(drift_item, request.priority_band)
        items.append(
            OracleOperatorPackEscalationItem(
                pack_kind=drift_item.pack_kind,
                drift_state=drift_item.drift_state,
                severity=drift_item.severity,
                escalation_posture=_escalation_posture(drift_item),
                routing_lane=routing_lane,
                routing_target=routing_target,
                priority_band=priority_band,
                queue_key=request.queue_key,
                board_label=request.board_label,
                latest_trust_status=drift_item.latest_trust_status,
                previous_trust_status=drift_item.previous_trust_status,
                latest_summary_line=drift_item.latest_summary_line,
                previous_summary_line=drift_item.previous_summary_line,
                latest_manifest_path=drift_item.latest_manifest_path,
                previous_manifest_path=drift_item.previous_manifest_path,
                recommended_actions=_compose_actions(
                    drift_item,
                    routing_lane=routing_lane,
                    routing_target=routing_target,
                    priority_band=priority_band,
                    queue_key=request.queue_key,
                ),
                is_current_pack_kind=drift_item.is_current_pack_kind,
            )
        )
    return OracleOperatorPackEscalation(
        schema_version='oracle_operator_pack_escalation/v1',
        search_root=str(request.search_root),
        current_pack_kind=request.current_pack_kind,
        queue_key=request.queue_key,
        review_target=request.review_target,
        priority_band=request.priority_band,
        action_owner_lane=request.action_owner_lane,
        board_label=request.board_label,
        total_escalation_count=len(items),
        items=tuple(items),
    )


def render_operator_pack_escalation_markdown_lines(escalation: OracleOperatorPackEscalation) -> list[str]:
    lines = ['## Operator Pack Escalations']
    lines.extend([
        f"- Escalations in scope: `{escalation.total_escalation_count}`",
        f"- Queue context: `{escalation.queue_key or 'none'}` / target `{escalation.review_target or 'operator_review'}`",
    ])
    if not escalation.items:
        lines.append('- No escalating operator pack drift detected for the current filters.')
        return lines
    for item in escalation.items:
        current = ' (current kind)' if item.is_current_pack_kind else ''
        lines.extend([
            f"- `{item.pack_kind}`{current} — `{item.escalation_posture}` via `{item.routing_lane}` -> `{item.routing_target}`",
            f"  - Severity: `{item.severity}` / drift state: `{item.drift_state}` / priority: `{item.priority_band}`",
            f"  - Latest trust: `{item.latest_trust_status or 'unknown'}` / previous: `{item.previous_trust_status or 'unknown'}`",
            f"  - Latest summary: {item.latest_summary_line or 'No summary recorded.'}",
        ])
        for action in item.recommended_actions[:4]:
            lines.append(f"  - Action: {action}")
    return lines


__all__ = [
    'OracleOperatorPackEscalationRequest',
    'OracleOperatorPackEscalationItem',
    'OracleOperatorPackEscalation',
    'build_operator_pack_escalation_request',
    'materialize_operator_pack_escalation',
    'render_operator_pack_escalation_markdown_lines',
]
