from __future__ import annotations

from pathlib import Path
from typing import Any

from strategy_validator.application.operator_pack_assembly import (
    build_pack_assignment_payload,
    build_pack_claim_lease_payload,
    build_pack_claim_lifecycle_payload,
    build_pack_escalation_payload,
)
from strategy_validator.application.operator_pack_queries import (
    build_operator_pack_navigation_payload,
    build_operator_pack_timeline_payload,
    build_operator_pack_workbench_payload,
)
from strategy_validator.application.operator_queue_read_models import build_workboard_payload
from strategy_validator.application.ui_view_helpers import utc_now_iso

_utc_now = utc_now_iso

def _select_pack_item(*, search_root: Path, pack_kind: str | None = None, manifest_path: str | None = None) -> dict[str, Any] | None:
    workbench = build_operator_pack_workbench_payload(search_root=search_root)
    all_items = [item for column in workbench.get('columns', []) for item in column.get('items', [])]
    if manifest_path:
        for item in all_items:
            if item.get('manifest_path') == manifest_path:
                return item
    if pack_kind:
        for item in all_items:
            if item.get('pack_kind') == pack_kind:
                return item
    return all_items[0] if all_items else None

def build_ui_pack_detail_payload(
    *,
    search_root: str | Path | None = None,
    board_label: str = 'operator',
    pack_kind: str | None = None,
    manifest_path: str | None = None,
) -> dict[str, Any]:
    root = Path(search_root) if search_root is not None else Path.cwd()
    selected = _select_pack_item(search_root=root, pack_kind=pack_kind, manifest_path=manifest_path)
    if selected is None:
        return {
            'schema_version': 'ui_pack_detail/v1',
            'generated_at_utc': _utc_now(),
            'pack': None,
            'navigation': {'item_count': 0, 'items': []},
            'timeline': {'item_count': 0, 'items': []},
            'assignment': {'item_count': 0, 'items': []},
            'claim_lease': {'item_count': 0, 'items': []},
            'claim_lifecycle': {'item_count': 0, 'items': []},
            'escalation': {'item_count': 0, 'items': []},
            'command_hints': [],
        }

    current_pack_kind = selected.get('pack_kind')
    workboard = build_workboard_payload(board_label=board_label)
    first_entry = (workboard.get('entries') or [{}])[0]
    common = {
        'search_root': root,
        'current_pack_kind': current_pack_kind,
        'queue_key': first_entry.get('queue_key'),
        'review_target': first_entry.get('review_target'),
        'priority_band': first_entry.get('priority_band'),
        'action_owner_lane': first_entry.get('action_owner_lane'),
        'board_label': board_label,
    }
    navigation = build_operator_pack_navigation_payload(search_root=root, current_pack_kind=current_pack_kind, max_items=4)
    timeline = build_operator_pack_timeline_payload(search_root=root, current_pack_kind=current_pack_kind, max_items=8)
    assignment = build_pack_assignment_payload(**common)
    claim_lease = build_pack_claim_lease_payload(**common)
    claim_lifecycle = build_pack_claim_lifecycle_payload(**common)
    escalation = build_pack_escalation_payload(**common)

    command_hints: list[str] = []
    lease_items = claim_lease.get('items', [])
    if lease_items:
        command_hints.extend(lease_items[0].get('recommended_actions', []))
    lifecycle_items = claim_lifecycle.get('items', [])
    if lifecycle_items:
        command_hints.extend(lifecycle_items[0].get('recommended_actions', []))
    escalation_items = escalation.get('items', [])
    if escalation_items:
        command_hints.extend(escalation_items[0].get('recommended_actions', []))

    return {
        'schema_version': 'ui_pack_detail/v1',
        'generated_at_utc': _utc_now(),
        'pack': selected,
        'navigation': navigation,
        'timeline': timeline,
        'assignment': assignment,
        'claim_lease': claim_lease,
        'claim_lifecycle': claim_lifecycle,
        'escalation': escalation,
        'command_hints': command_hints[:8],
    }
