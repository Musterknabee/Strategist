from __future__ import annotations

from typing import Any, Mapping

from strategy_validator.application.ui_workboard_intelligence_foundations import _unique_nonempty_paths


def _build_board_governance_snapshot(*, ranked_items: list[Mapping[str, Any]]) -> dict[str, Any]:
    contradiction_count = sum(len(list(item.get('policy_recommendation', {}).get('contradictions', []) or [])) for item in ranked_items)
    drift_count = sum(len(list(item.get('policy_recommendation', {}).get('drift_flags', []) or [])) for item in ranked_items)
    anomaly_count = sum(len(list(item.get('policy_recommendation', {}).get('anomaly_flags', []) or [])) for item in ranked_items)
    high_severity_count = 0
    medium_severity_count = 0
    drift_frequency: dict[str, int] = {}
    anomaly_frequency: dict[str, int] = {}
    for item in ranked_items:
        policy = item.get('policy_recommendation', {}) or {}
        for signal in [
            *(policy.get('contradictions', []) or []),
            *(policy.get('drift_signals', []) or []),
            *(policy.get('anomaly_details', []) or []),
        ]:
            severity = str(signal.get('severity') or '').upper()
            if severity == 'HIGH':
                high_severity_count += 1
            elif severity == 'MEDIUM':
                medium_severity_count += 1
        for signal in policy.get('drift_signals', []) or []:
            kind = str(signal.get('kind') or '')
            if kind:
                drift_frequency[kind] = drift_frequency.get(kind, 0) + 1
        for signal in policy.get('anomaly_details', []) or []:
            kind = str(signal.get('kind') or '')
            if kind:
                anomaly_frequency[kind] = anomaly_frequency.get(kind, 0) + 1

    focus = ranked_items[0] if ranked_items else None
    focus_policy = (focus or {}).get('policy_recommendation', {}) or {}
    top_drift_flags = [kind for kind, _ in sorted(drift_frequency.items(), key=lambda item: (-item[1], item[0]))[:3]]
    top_anomaly_flags = [kind for kind, _ in sorted(anomaly_frequency.items(), key=lambda item: (-item[1], item[0]))[:3]]
    if focus is None:
        summary_line = 'No governance recommendation pressure is present because the queue is empty.'
        focus_line = 'No contradictions or anomalies require operator review yet.'
        severity_line = 'No high- or medium-severity governance signals are currently present.'
    else:
        summary_line = (
            f"Governance snapshot: {contradiction_count} contradiction(s), {drift_count} drift signal(s), and {anomaly_count} anomaly flag(s) across {len(ranked_items)} ranked item(s)."
        )
        focus_line = (
            f"Highest-pressure policy lane is {focus.get('work_item_key')} with "
            f"{len(list(focus_policy.get('contradictions', []) or []))} contradiction(s), "
            f"{len(list(focus_policy.get('drift_signals', []) or []))} drift detail(s), and "
            f"{len(list(focus_policy.get('anomaly_details', []) or []))} anomaly detail(s)."
        )
        severity_line = (
            f"Severity pressure: {high_severity_count} high and {medium_severity_count} medium governance signal(s) are currently active across the board."
        )
    return {
        'summary_line': summary_line,
        'focus_line': focus_line,
        'severity_line': severity_line,
        'contradiction_count': contradiction_count,
        'drift_count': drift_count,
        'anomaly_count': anomaly_count,
        'high_severity_count': high_severity_count,
        'medium_severity_count': medium_severity_count,
        'top_drift_flags': top_drift_flags,
        'top_anomaly_flags': top_anomaly_flags,
    }


def _build_board_governance_clusters(*, ranked_items: list[Mapping[str, Any]]) -> dict[str, Any]:
    severity_rank = {
        'HIGH': 3,
        'MEDIUM': 2,
        'LOW': 1,
    }
    clusters: dict[tuple[str, str], dict[str, Any]] = {}

    for item in ranked_items:
        work_item_key = str(item.get('work_item_key') or '')
        review_target = str(item.get('review_target') or work_item_key or 'unknown item')
        evidence_briefing = item.get('evidence_backed_briefing') or {}
        policy = item.get('policy_recommendation') or {}
        for category, signals in (
            ('CONTRADICTION', policy.get('contradictions', []) or []),
            ('DRIFT', policy.get('drift_signals', []) or []),
            ('ANOMALY', policy.get('anomaly_details', []) or []),
        ):
            for signal in signals:
                kind = str(signal.get('kind') or '').upper()
                if not kind:
                    continue
                cluster = clusters.setdefault(
                    (category, kind),
                    {
                        'category': category,
                        'signal_kind': kind,
                        'dominant_severity': 'LOW',
                        'summary_examples': [],
                        'affected_work_item_keys': [],
                        'affected_review_targets': [],
                        'source_paths': [],
                    },
                )
                severity = str(signal.get('severity') or '').upper() or 'LOW'
                current_severity = str(cluster.get('dominant_severity') or 'LOW').upper()
                if severity_rank.get(severity, 0) > severity_rank.get(current_severity, 0):
                    cluster['dominant_severity'] = severity
                summary_line = str(signal.get('summary_line') or '')
                if summary_line and summary_line not in cluster['summary_examples']:
                    cluster['summary_examples'].append(summary_line)
                if work_item_key and work_item_key not in cluster['affected_work_item_keys']:
                    cluster['affected_work_item_keys'].append(work_item_key)
                if review_target and review_target not in cluster['affected_review_targets']:
                    cluster['affected_review_targets'].append(review_target)
                for source_path in evidence_briefing.get('source_paths', []) or []:
                    source_path = str(source_path or '')
                    if source_path and source_path not in cluster['source_paths']:
                        cluster['source_paths'].append(source_path)

    cluster_entries: list[dict[str, Any]] = []
    for cluster in clusters.values():
        affected_review_targets = list(cluster.get('affected_review_targets', []) or [])
        affected_work_item_keys = list(cluster.get('affected_work_item_keys', []) or [])
        summary_examples = list(cluster.get('summary_examples', []) or [])
        affected_item_count = len(affected_work_item_keys)
        summary_line = (
            f"{cluster['signal_kind']} pressure is affecting {affected_item_count} ranked item(s): "
            f"{', '.join(affected_review_targets) or ', '.join(affected_work_item_keys) or 'unknown items'}."
        )
        if affected_item_count > 1:
            operator_line = (
                f"Review these items together because {cluster['signal_kind']} is recurring across the board at "
                f"{cluster['dominant_severity']} severity."
            )
        else:
            operator_line = (
                f"Keep this item in the focused governance lane because {cluster['signal_kind']} is isolated but still "
                f"{cluster['dominant_severity']} severity."
            )
        cluster_entries.append({
            'category': cluster['category'],
            'signal_kind': cluster['signal_kind'],
            'dominant_severity': cluster['dominant_severity'],
            'affected_item_count': affected_item_count,
            'affected_work_item_keys': affected_work_item_keys,
            'affected_review_targets': affected_review_targets,
            'summary_line': summary_line,
            'operator_line': operator_line,
            'sample_summary_line': summary_examples[0] if summary_examples else None,
            'source_paths': list(cluster.get('source_paths', []) or []),
        })

    cluster_entries.sort(
        key=lambda item: (
            -int(item.get('affected_item_count') or 0),
            -severity_rank.get(str(item.get('dominant_severity') or '').upper(), 0),
            str(item.get('category') or ''),
            str(item.get('signal_kind') or ''),
        )
    )

    if not cluster_entries:
        return {
            'summary_line': 'No board governance clusters are currently present.',
            'pressure_line': 'No recurring contradiction, drift, or anomaly classes are currently active.',
            'cluster_count': 0,
            'clusters': [],
        }

    top_cluster = cluster_entries[0]
    return {
        'summary_line': (
            f"Board governance clusters group {len(cluster_entries)} pressure class(es) across "
            f"{len(ranked_items)} ranked item(s)."
        ),
        'pressure_line': (
            f"Most repeated cluster is {top_cluster['signal_kind']} "
            f"({top_cluster['affected_item_count']} item(s), {top_cluster['dominant_severity']} severity)."
        ),
        'cluster_count': len(cluster_entries),
        'clusters': cluster_entries,
    }


def _build_board_governance_digest(
    *,
    ranked_items: list[Mapping[str, Any]],
    board_operator_brief: Mapping[str, Any],
    board_governance_snapshot: Mapping[str, Any],
    board_governance_clusters: Mapping[str, Any],
    board_evidence_briefing: Mapping[str, Any],
) -> dict[str, Any]:
    if not ranked_items:
        return {
            'summary_line': 'No board governance digest is available because the ranked queue is empty.',
            'action_line': 'No lawful board action is currently surfaced.',
            'focus_line': 'No focus item is currently accumulating governance pressure.',
            'cluster_line': 'No clustered governance pressure is currently active.',
            'watch_line': 'No board-level governance watch items are currently active.',
            'watch_items': [],
            'source_paths': [],
            'focus_work_item_key': None,
            'focus_action': None,
            'top_cluster_signal_kind': None,
            'high_severity_count': 0,
            'cluster_count': 0,
            'focus_projection_post_merge_lifecycle_state': None,
            'focus_projection_downstream_closure_state': None,
            'journal_downstream_closure_ready_count': 0,
            'journal_downstream_closure_review_required_count': 0,
            'journal_downstream_closure_blocked_count': 0,
            'closure_line': 'No downstream closure posture is currently active.',
        }

    focus = ranked_items[0]
    focus_key = str(focus.get('work_item_key') or '') or None
    focus_policy = focus.get('policy_recommendation') or {}
    focus_action = str(focus_policy.get('lawful_next_action') or board_operator_brief.get('focus_action') or '') or None
    focus_action_state = str(focus_policy.get('lawful_next_action_state') or '') or None
    top_cluster = ((board_governance_clusters.get('clusters') or [])[:1] or [None])[0]
    top_cluster_signal = str((top_cluster or {}).get('signal_kind') or '') or None
    blocked_count = sum(1 for item in ranked_items if item.get('attention_state') == 'BLOCKED')
    stale_count = sum(1 for item in ranked_items if (item.get('projection_recency') or {}).get('state') == 'STALE')
    contradiction_count = int(board_governance_snapshot.get('contradiction_count') or 0)
    drift_count = int(board_governance_snapshot.get('drift_count') or 0)
    anomaly_count = int(board_governance_snapshot.get('anomaly_count') or 0)
    high_severity_count = int(board_governance_snapshot.get('high_severity_count') or 0)
    cluster_count = int(board_governance_clusters.get('cluster_count') or 0)
    closure_ready_count = sum(1 for item in ranked_items if str(item.get('projection_downstream_closure_state') or '').endswith('READY'))
    closure_review_required_count = sum(1 for item in ranked_items if str(item.get('projection_downstream_closure_state') or '') == 'DOWNSTREAM_CLOSURE_REVIEW_REQUIRED')
    closure_blocked_count = sum(1 for item in ranked_items if str(item.get('projection_downstream_closure_state') or '') == 'DOWNSTREAM_CLOSURE_BLOCKED')
    focus_projection_post_merge_lifecycle_state = str(focus.get('projection_post_merge_lifecycle_state') or '') or None
    focus_projection_downstream_closure_state = str(focus.get('projection_downstream_closure_state') or '') or None

    closure_phrase = ''
    if focus_projection_downstream_closure_state == 'DOWNSTREAM_CLOSURE_BLOCKED':
        closure_phrase = ' Downstream closure is currently blocked for the focus item.'
    elif focus_projection_downstream_closure_state == 'DOWNSTREAM_CLOSURE_REVIEW_REQUIRED':
        closure_phrase = ' Downstream closure requires explicit review for the focus item.'
    elif focus_projection_downstream_closure_state == 'PRIMARY_DOWNSTREAM_CLOSURE_READY':
        closure_phrase = ' Downstream closure is ready on the primary governed item.'
    elif focus_projection_downstream_closure_state == 'AUXILIARY_DOWNSTREAM_CLOSURE_READY':
        closure_phrase = ' Downstream closure is ready on an auxiliary governed item.'

    closure_counts_phrase = ''
    if closure_ready_count or closure_review_required_count or closure_blocked_count:
        closure_counts_phrase = (
            f"; downstream closure counts ready={closure_ready_count}, review_required={closure_review_required_count}, blocked={closure_blocked_count} still need follow-up"
        )

    if focus_action and focus_action_state:
        summary_line = (
            f"Board governance digest: keep {focus_key} on {focus_action.replace('-', ' ')} "
            f"({focus_action_state}) while {top_cluster_signal or 'the focus lane'} remains the top governance pressure.{closure_phrase}"
        )
        action_line = (
            f"Action posture: {focus_key} is the current lawful focus on {focus_action.replace('-', ' ')} "
            f"({focus_action_state}); {blocked_count} blocked lane(s) and {stale_count} stale linkage(s) still need follow-up{closure_counts_phrase}."
        )
    else:
        summary_line = (
            f"Board governance digest: keep {focus_key} in evidence review while "
            f"{top_cluster_signal or 'the focus lane'} remains the top governance pressure.{closure_phrase}"
        )
        action_line = (
            f"Action posture: no direct lawful command is currently surfaced for {focus_key}; "
            f"{blocked_count} blocked lane(s) and {stale_count} stale linkage(s) still need follow-up{closure_counts_phrase}."
        )

    focus_line = str(board_evidence_briefing.get('focus_line') or board_operator_brief.get('summary_line') or '')
    if top_cluster is None:
        cluster_line = 'Cluster pressure: no recurring governance cluster is currently active beyond the focus lane.'
    else:
        cluster_line = (
            f"Cluster pressure: {top_cluster.get('summary_line')} "
            f"{top_cluster.get('operator_line')}"
        )
    watch_line = (
        f"Governance watch: {contradiction_count} contradiction(s), {drift_count} drift detail(s), "
        f"{anomaly_count} anomaly detail(s), and {cluster_count} clustered pressure class(es) are active across "
        f"{len(ranked_items)} ranked item(s)."
    )
    closure_line = (
        f"Downstream closure watch: ready={closure_ready_count}, review_required={closure_review_required_count}, "
        f"blocked={closure_blocked_count}; focus post-merge state is {focus_projection_post_merge_lifecycle_state or 'none'} and closure state is {focus_projection_downstream_closure_state or 'none'}."
    )

    watch_items: list[str] = []
    for item in [
        *((board_evidence_briefing.get('watch_items') or [])[:2]),
        str((top_cluster or {}).get('sample_summary_line') or ''),
        str(board_operator_brief.get('blocked_follow_up_line') or ''),
        closure_line,
        str(board_governance_snapshot.get('severity_line') or ''),
    ]:
        if item and item not in watch_items:
            watch_items.append(item)

    return {
        'summary_line': summary_line,
        'action_line': action_line,
        'focus_line': focus_line,
        'cluster_line': cluster_line,
        'watch_line': watch_line,
        'closure_line': closure_line,
        'watch_items': watch_items[:5],
        'source_paths': _unique_nonempty_paths(
            *[str(path) for path in board_evidence_briefing.get('source_paths', []) or []],
            extra_paths=[str(path) for path in ((top_cluster or {}).get('source_paths') or [])],
        ),
        'focus_work_item_key': focus_key,
        'focus_action': focus_action,
        'top_cluster_signal_kind': top_cluster_signal,
        'high_severity_count': high_severity_count,
        'cluster_count': cluster_count,
        'focus_projection_post_merge_lifecycle_state': focus_projection_post_merge_lifecycle_state,
        'focus_projection_downstream_closure_state': focus_projection_downstream_closure_state,
        'journal_downstream_closure_ready_count': closure_ready_count,
        'journal_downstream_closure_review_required_count': closure_review_required_count,
        'journal_downstream_closure_blocked_count': closure_blocked_count,
    }


__all__ = [
    '_build_board_governance_snapshot',
    '_build_board_governance_clusters',
    '_build_board_governance_digest',
]
