from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from strategy_validator.projections.operator_pack_discovery import (
    OperatorPackDiscoveryMatch,
    build_operator_pack_query,
    discover_operator_pack_matches,
)

_TRUST_RANK = {
    'TRUSTED': 0,
    'TRUST_RESTRICTED': 1,
    'UNTRUSTED': 2,
}


@dataclass(frozen=True)
class OracleOperatorPackDriftRequest:
    search_root: Path
    repo_root: Path | None = None
    current_pack_kind: str | None = None
    pack_kinds: tuple[str, ...] = ()
    trust_statuses: tuple[str, ...] = ()
    summary_line_contains: str | None = None
    output_artifact_label_contains: str | None = None
    max_items: int = 4
    sustained_degraded_threshold: int = 2


@dataclass(frozen=True)
class OracleOperatorPackDriftItem:
    pack_kind: str
    drift_state: str
    severity: str
    latest_generated_at_utc: str | None
    previous_generated_at_utc: str | None
    latest_trust_status: str | None
    previous_trust_status: str | None
    degraded_streak_count: int
    latest_summary_line: str | None
    previous_summary_line: str | None
    latest_manifest_path: Path
    previous_manifest_path: Path | None
    changed_fields: tuple[str, ...]
    recommended_actions: tuple[str, ...]
    is_current_pack_kind: bool


@dataclass(frozen=True)
class OracleOperatorPackDrift:
    schema_version: str
    search_root: str
    current_pack_kind: str | None
    pack_kinds: tuple[str, ...]
    trust_statuses: tuple[str, ...]
    summary_line_contains: str | None
    output_artifact_label_contains: str | None
    total_alert_count: int
    items: tuple[OracleOperatorPackDriftItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'search_root': self.search_root,
            'current_pack_kind': self.current_pack_kind,
            'pack_kinds': list(self.pack_kinds),
            'trust_statuses': list(self.trust_statuses),
            'summary_line_contains': self.summary_line_contains,
            'output_artifact_label_contains': self.output_artifact_label_contains,
            'total_alert_count': self.total_alert_count,
            'item_count': len(self.items),
            'items': [
                {
                    'pack_kind': item.pack_kind,
                    'drift_state': item.drift_state,
                    'severity': item.severity,
                    'latest_generated_at_utc': item.latest_generated_at_utc,
                    'previous_generated_at_utc': item.previous_generated_at_utc,
                    'latest_trust_status': item.latest_trust_status,
                    'previous_trust_status': item.previous_trust_status,
                    'degraded_streak_count': item.degraded_streak_count,
                    'latest_summary_line': item.latest_summary_line,
                    'previous_summary_line': item.previous_summary_line,
                    'latest_manifest_path': str(item.latest_manifest_path),
                    'previous_manifest_path': str(item.previous_manifest_path) if item.previous_manifest_path else None,
                    'changed_fields': list(item.changed_fields),
                    'recommended_actions': list(item.recommended_actions),
                    'is_current_pack_kind': item.is_current_pack_kind,
                }
                for item in self.items
            ],
        }


def build_operator_pack_drift_request(
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
) -> OracleOperatorPackDriftRequest:
    return OracleOperatorPackDriftRequest(
        search_root=search_root.resolve(),
        repo_root=repo_root.resolve() if repo_root is not None else None,
        current_pack_kind=current_pack_kind or None,
        pack_kinds=tuple(item for item in pack_kinds if item),
        trust_statuses=tuple(item for item in trust_statuses if item),
        summary_line_contains=summary_line_contains or None,
        output_artifact_label_contains=output_artifact_label_contains or None,
        max_items=max(1, int(max_items)),
        sustained_degraded_threshold=max(2, int(sustained_degraded_threshold)),
    )


def _trust_rank(status: str | None) -> int:
    return _TRUST_RANK.get(status or '', 1)


def _degraded_streak(matches: Sequence[OperatorPackDiscoveryMatch]) -> int:
    streak = 0
    for match in matches:
        if _trust_rank(match.trust_status) > 0:
            streak += 1
        else:
            break
    return streak


def _changed_fields(*, latest: OperatorPackDiscoveryMatch, previous: OperatorPackDiscoveryMatch | None) -> tuple[str, ...]:
    if previous is None:
        return ('trust_status', 'summary_line') if _trust_rank(latest.trust_status) > 0 else ()
    fields: list[str] = []
    if latest.trust_status != previous.trust_status:
        fields.append('trust_status')
    if (latest.summary_line or '') != (previous.summary_line or ''):
        fields.append('summary_line')
    if (latest.generated_at_utc or '') != (previous.generated_at_utc or ''):
        fields.append('generated_at_utc')
    return tuple(fields)


def _recommended_actions(*, pack_kind: str, drift_state: str, latest_status: str | None, degraded_streak_count: int) -> tuple[str, ...]:
    actions = [f'Prioritize operator review for `{pack_kind}` before relying on the latest pack generation.']
    if latest_status == 'UNTRUSTED':
        actions.append('Treat the latest pack as blocked for downstream operator reliance until constitutional repair is complete.')
    elif latest_status == 'TRUST_RESTRICTED':
        actions.append('Keep the pack in review-only circulation and regenerate after addressing the degraded trust inputs.')
    if drift_state == 'SUSTAINED_DEGRADED':
        actions.append(f'Investigate why `{pack_kind}` has remained degraded for `{degraded_streak_count}` consecutive indexed generations.')
    else:
        actions.append(f'Compare the latest and previous `{pack_kind}` pack manifests to isolate the worsening change drivers.')
    return tuple(actions)


def materialize_operator_pack_drift(request: OracleOperatorPackDriftRequest) -> OracleOperatorPackDrift:
    query = build_operator_pack_query(
        search_root=request.search_root,
        repo_root=request.repo_root,
        pack_kinds=request.pack_kinds,
        trust_statuses=request.trust_statuses,
        summary_line_contains=request.summary_line_contains,
        output_artifact_label_contains=request.output_artifact_label_contains,
    )
    matches = list(discover_operator_pack_matches(query))
    grouped: dict[str, list[OperatorPackDiscoveryMatch]] = {}
    for match in matches:
        grouped.setdefault(match.pack_kind, []).append(match)
    alerts: list[OracleOperatorPackDriftItem] = []
    for pack_kind, pack_matches in grouped.items():
        pack_matches.sort(key=lambda item: ((item.generated_at_utc or ''), str(item.manifest_path)), reverse=True)
        latest = pack_matches[0]
        previous = pack_matches[1] if len(pack_matches) > 1 else None
        latest_rank = _trust_rank(latest.trust_status)
        previous_rank = _trust_rank(previous.trust_status) if previous is not None else 0
        degraded_streak_count = _degraded_streak(pack_matches)
        drift_state: str | None = None
        if latest_rank == 0:
            continue
        if previous is None:
            drift_state = 'NEW_DEGRADATION'
        elif latest_rank > previous_rank:
            drift_state = 'WORSENING'
        elif degraded_streak_count >= request.sustained_degraded_threshold:
            drift_state = 'SUSTAINED_DEGRADED'
        if drift_state is None:
            continue
        severity = 'ELEVATED' if latest_rank >= 2 or degraded_streak_count >= 3 or drift_state == 'WORSENING' else 'WATCH'
        alerts.append(
            OracleOperatorPackDriftItem(
                pack_kind=pack_kind,
                drift_state=drift_state,
                severity=severity,
                latest_generated_at_utc=latest.generated_at_utc,
                previous_generated_at_utc=previous.generated_at_utc if previous is not None else None,
                latest_trust_status=latest.trust_status,
                previous_trust_status=previous.trust_status if previous is not None else None,
                degraded_streak_count=degraded_streak_count,
                latest_summary_line=latest.summary_line,
                previous_summary_line=previous.summary_line if previous is not None else None,
                latest_manifest_path=latest.manifest_path,
                previous_manifest_path=previous.manifest_path if previous is not None else None,
                changed_fields=_changed_fields(latest=latest, previous=previous),
                recommended_actions=_recommended_actions(
                    pack_kind=pack_kind,
                    drift_state=drift_state,
                    latest_status=latest.trust_status,
                    degraded_streak_count=degraded_streak_count,
                ),
                is_current_pack_kind=bool(request.current_pack_kind and pack_kind == request.current_pack_kind),
            )
        )
    alerts.sort(key=lambda item: (item.severity == 'ELEVATED', item.latest_generated_at_utc or '', item.pack_kind), reverse=True)
    selected = tuple(alerts[:request.max_items])
    return OracleOperatorPackDrift(
        schema_version='oracle_operator_pack_drift/v1',
        search_root=str(request.search_root),
        current_pack_kind=request.current_pack_kind,
        pack_kinds=request.pack_kinds,
        trust_statuses=request.trust_statuses,
        summary_line_contains=request.summary_line_contains,
        output_artifact_label_contains=request.output_artifact_label_contains,
        total_alert_count=len(alerts),
        items=selected,
    )


def render_operator_pack_drift_markdown_lines(drift: OracleOperatorPackDrift) -> list[str]:
    lines = ['## Operator Pack Drift Alerts']
    lines.extend([
        f"- Drift alerts in scope: `{drift.total_alert_count}`",
        f"- Drift items shown: `{len(drift.items)}`",
    ])
    if not drift.items:
        lines.append('- No worsening or sustained degraded operator pack drift detected for the current filters.')
        return lines
    for item in drift.items:
        current = ' (current kind)' if item.is_current_pack_kind else ''
        changes = ', '.join(item.changed_fields) if item.changed_fields else 'no tracked field changes'
        lines.extend([
            f"- `{item.pack_kind}`{current} — `{item.drift_state}` / `{item.severity}`",
            f"  - Latest: `{item.latest_generated_at_utc or 'unknown'}` / `{item.latest_trust_status or 'unknown'}` / {item.latest_summary_line or 'No summary recorded.'}",
            f"  - Previous: `{item.previous_generated_at_utc or 'n/a'}` / `{item.previous_trust_status or 'n/a'}` / {item.previous_summary_line or 'No summary recorded.'}",
            f"  - Degraded streak: `{item.degraded_streak_count}` generations",
            f"  - Changed fields: `{changes}`",
            f"  - Latest manifest: `{item.latest_manifest_path}`",
        ])
        for action in item.recommended_actions:
            lines.append(f"  - Action: {action}")
    return lines


__all__ = [
    'OracleOperatorPackDriftRequest',
    'OracleOperatorPackDriftItem',
    'OracleOperatorPackDrift',
    'build_operator_pack_drift_request',
    'materialize_operator_pack_drift',
    'render_operator_pack_drift_markdown_lines',
]
