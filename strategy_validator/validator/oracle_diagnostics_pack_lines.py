from __future__ import annotations

from pathlib import Path

from strategy_validator.contracts.operational import (
    ClosureReleaseAttestation,
    ClosureSnapshotVerification,
)
from strategy_validator.contracts.oracle_operator_reports import OracleStatusPackSection
from strategy_validator.control_plane.operator_pack_assignment import (
    build_operator_pack_assignment_request,
    materialize_operator_pack_assignment,
    render_operator_pack_assignment_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_approval_disposition import (
    build_operator_pack_approval_disposition_request,
    materialize_operator_pack_approval_disposition,
    render_operator_pack_approval_disposition_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_approval_needed import (
    build_operator_pack_approval_needed_request,
    materialize_operator_pack_approval_needed,
    render_operator_pack_approval_needed_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_claim_lease import (
    build_operator_pack_claim_lease_request,
    materialize_operator_pack_claim_lease,
    render_operator_pack_claim_lease_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_claim_lifecycle import (
    build_operator_pack_claim_lifecycle_request,
    materialize_operator_pack_claim_lifecycle,
    render_operator_pack_claim_lifecycle_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_claim_operability import (
    build_operator_pack_claim_operability_request,
    materialize_operator_pack_claim_operability,
    render_operator_pack_claim_operability_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_comparison import (
    build_operator_pack_comparison_request,
    materialize_operator_pack_comparison,
    render_operator_pack_comparison_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_dashboard import (
    build_operator_pack_dashboard_request,
    materialize_operator_pack_dashboard,
    render_operator_pack_dashboard_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_dispatch_outcome import (
    build_operator_pack_dispatch_outcome_request,
    materialize_operator_pack_dispatch_outcome,
    render_operator_pack_dispatch_outcome_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_dispatch_permission import (
    build_operator_pack_dispatch_permission_request,
    materialize_operator_pack_dispatch_permission,
    render_operator_pack_dispatch_permission_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_drift import (
    build_operator_pack_drift_request,
    materialize_operator_pack_drift,
    render_operator_pack_drift_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_escalation import (
    build_operator_pack_escalation_request,
    materialize_operator_pack_escalation,
    render_operator_pack_escalation_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_execution_authorization import (
    build_operator_pack_execution_authorization_request,
    materialize_operator_pack_execution_authorization,
    render_operator_pack_execution_authorization_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_execution_exception import (
    build_operator_pack_execution_exception_request,
    materialize_operator_pack_execution_exception,
    render_operator_pack_execution_exception_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_execution_finality import (
    build_operator_pack_execution_finality_request,
    materialize_operator_pack_execution_finality,
    render_operator_pack_execution_finality_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_execution_force import (
    build_operator_pack_execution_force_request,
    materialize_operator_pack_execution_force,
    render_operator_pack_execution_force_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_execution_readiness import (
    build_operator_pack_execution_readiness_request,
    materialize_operator_pack_execution_readiness,
    render_operator_pack_execution_readiness_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_handoff import (
    build_operator_pack_handoff_request,
    materialize_operator_pack_handoff,
    render_operator_pack_handoff_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_lease_governance import (
    build_operator_pack_lease_governance_request,
    materialize_operator_pack_lease_governance,
    render_operator_pack_lease_governance_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_terminal_archive import (
    build_operator_pack_terminal_archive_request,
    materialize_operator_pack_terminal_archive,
    render_operator_pack_terminal_archive_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_terminal_closure import (
    build_operator_pack_terminal_closure_request,
    materialize_operator_pack_terminal_closure,
    render_operator_pack_terminal_closure_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_terminal_record import (
    build_operator_pack_terminal_record_request,
    materialize_operator_pack_terminal_record,
    render_operator_pack_terminal_record_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_terminal_resolution import (
    build_operator_pack_terminal_resolution_request,
    materialize_operator_pack_terminal_resolution,
    render_operator_pack_terminal_resolution_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_timeline import (
    build_operator_pack_timeline_request,
    materialize_operator_pack_timeline,
    render_operator_pack_timeline_markdown_lines,
)


def _unique(items):
    seen = set()
    out = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out

def _operator_pack_dashboard_lines(*, report_search_root: str, report_repo_root: str, current_pack_kind: str, preferred_pack_kinds: tuple[str, ...]) -> list[str]:
    search_root = Path(report_search_root)
    repo_root = Path(report_repo_root)
    if not search_root.exists():
        return []
    dashboard = materialize_operator_pack_dashboard(
        build_operator_pack_dashboard_request(
            search_root=search_root,
            repo_root=repo_root,
            current_pack_kind=current_pack_kind,
            preferred_pack_kinds=preferred_pack_kinds,
            max_navigation_items=max(1, len(preferred_pack_kinds)),
            max_column_items=max(1, len(preferred_pack_kinds)),
        )
    )
    if not dashboard.columns and not dashboard.navigation.items:
        return []
    return render_operator_pack_dashboard_markdown_lines(dashboard)


def _operator_pack_comparison_lines(*, report_search_root: str, report_repo_root: str, current_pack_kind: str, pack_kinds: tuple[str, ...]) -> list[str]:
    search_root = Path(report_search_root)
    if not search_root.exists():
        return []
    comparison = materialize_operator_pack_comparison(
        build_operator_pack_comparison_request(
            search_root=search_root,
            repo_root=Path(report_repo_root),
            current_pack_kind=current_pack_kind,
            pack_kinds=pack_kinds,
            max_items=3,
        )
    )
    if not comparison.items:
        return []
    return render_operator_pack_comparison_markdown_lines(comparison)


def _operator_pack_timeline_lines(*, report_search_root: str, report_repo_root: str, current_pack_kind: str, preferred_pack_kinds: tuple[str, ...]) -> list[str]:
    search_root = Path(report_search_root)
    repo_root = Path(report_repo_root)
    if not search_root.exists():
        return []
    timeline = materialize_operator_pack_timeline(
        build_operator_pack_timeline_request(
            search_root=search_root,
            repo_root=repo_root,
            current_pack_kind=current_pack_kind,
            pack_kinds=preferred_pack_kinds,
            max_items=max(3, len(preferred_pack_kinds) * 2),
        )
    )
    if not timeline.items:
        return []
    return render_operator_pack_timeline_markdown_lines(timeline)


def _operator_pack_drift_lines(*, report_search_root: str, report_repo_root: str, current_pack_kind: str, pack_kinds: tuple[str, ...]) -> list[str]:
    search_root = Path(report_search_root)
    if not search_root.exists():
        return []
    drift = materialize_operator_pack_drift(
        build_operator_pack_drift_request(
            search_root=search_root,
            repo_root=Path(report_repo_root),
            current_pack_kind=current_pack_kind,
            pack_kinds=pack_kinds,
            max_items=3,
        )
    )
    if not drift.items:
        return []
    return render_operator_pack_drift_markdown_lines(drift)


def _operator_pack_escalation_lines(*, report_search_root: str, report_repo_root: str, current_pack_kind: str, pack_kinds: tuple[str, ...], operator_workboard=None) -> list[str]:
    search_root = Path(report_search_root)
    if not search_root.exists():
        return []
    escalation = materialize_operator_pack_escalation(
        build_operator_pack_escalation_request(
            search_root=search_root,
            repo_root=Path(report_repo_root),
            current_pack_kind=current_pack_kind,
            pack_kinds=pack_kinds,
            max_items=3,
            queue_key=getattr(operator_workboard, 'queue_key', None),
            review_target=getattr(operator_workboard, 'review_target', None),
            priority_band=getattr(operator_workboard, 'priority_band', None),
            action_owner_lane=(operator_workboard.entries[0].action_owner_lane if getattr(operator_workboard, 'entries', None) else None),
            board_label=getattr(operator_workboard, 'board_label', None),
        )
    )
    if not escalation.items:
        return []
    return render_operator_pack_escalation_markdown_lines(escalation)


def _operator_pack_assignment_lines(*, report_search_root: str, report_repo_root: str, current_pack_kind: str, pack_kinds: tuple[str, ...], operator_workboard=None) -> list[str]:
    search_root = Path(report_search_root)
    if not search_root.exists():
        return []
    assignment = materialize_operator_pack_assignment(
        build_operator_pack_assignment_request(
            search_root=search_root,
            repo_root=Path(report_repo_root),
            current_pack_kind=current_pack_kind,
            pack_kinds=pack_kinds,
            max_items=3,
            queue_key=getattr(operator_workboard, 'queue_key', None),
            review_target=getattr(operator_workboard, 'review_target', None),
            priority_band=getattr(operator_workboard, 'priority_band', None),
            action_owner_lane=(operator_workboard.entries[0].action_owner_lane if getattr(operator_workboard, 'entries', None) else None),
            board_label=getattr(operator_workboard, 'board_label', None),
        ),
        operator_workboard=operator_workboard,
    )
    if not assignment.items:
        return []
    return render_operator_pack_assignment_markdown_lines(assignment)


def _operator_pack_handoff_lines(*, report_search_root: str, report_repo_root: str, current_pack_kind: str, pack_kinds: tuple[str, ...], operator_workboard=None) -> list[str]:
    search_root = Path(report_search_root)
    if not search_root.exists():
        return []
    handoff = materialize_operator_pack_handoff(
        build_operator_pack_handoff_request(
            search_root=search_root,
            repo_root=Path(report_repo_root),
            current_pack_kind=current_pack_kind,
            pack_kinds=pack_kinds,
            max_items=3,
            queue_key=getattr(operator_workboard, 'queue_key', None),
            review_target=getattr(operator_workboard, 'review_target', None),
            priority_band=getattr(operator_workboard, 'priority_band', None),
            action_owner_lane=(operator_workboard.entries[0].action_owner_lane if getattr(operator_workboard, 'entries', None) else None),
            board_label=getattr(operator_workboard, 'board_label', None),
        ),
        operator_workboard=operator_workboard,
    )
    if not handoff.items:
        return []
    return render_operator_pack_handoff_markdown_lines(handoff)


def _operator_pack_claim_lease_lines(*, report_search_root: str, report_repo_root: str, current_pack_kind: str, pack_kinds: tuple[str, ...], operator_workboard=None) -> list[str]:
    search_root = Path(report_search_root)
    if not search_root.exists():
        return []
    claim_lease = materialize_operator_pack_claim_lease(
        build_operator_pack_claim_lease_request(
            search_root=search_root,
            repo_root=Path(report_repo_root),
            current_pack_kind=current_pack_kind,
            pack_kinds=pack_kinds,
            max_items=3,
            queue_key=getattr(operator_workboard, 'queue_key', None),
            review_target=getattr(operator_workboard, 'review_target', None),
            priority_band=getattr(operator_workboard, 'priority_band', None),
            action_owner_lane=(operator_workboard.entries[0].action_owner_lane if getattr(operator_workboard, 'entries', None) else None),
            board_label=getattr(operator_workboard, 'board_label', None),
        ),
        operator_workboard=operator_workboard,
    )
    if not claim_lease.items:
        return []
    return render_operator_pack_claim_lease_markdown_lines(claim_lease)


def _operator_pack_claim_lifecycle_lines(*, report_search_root: str, report_repo_root: str, current_pack_kind: str, pack_kinds: tuple[str, ...], operator_workboard=None) -> list[str]:
    search_root = Path(report_search_root)
    if not search_root.exists():
        return []
    claim_lifecycle = materialize_operator_pack_claim_lifecycle(
        build_operator_pack_claim_lifecycle_request(
            search_root=search_root,
            repo_root=Path(report_repo_root),
            current_pack_kind=current_pack_kind,
            pack_kinds=pack_kinds,
            max_items=3,
            queue_key=getattr(operator_workboard, 'queue_key', None),
            review_target=getattr(operator_workboard, 'review_target', None),
            priority_band=getattr(operator_workboard, 'priority_band', None),
            action_owner_lane=(operator_workboard.entries[0].action_owner_lane if getattr(operator_workboard, 'entries', None) else None),
            board_label=getattr(operator_workboard, 'board_label', None),
        ),
        operator_workboard=operator_workboard,
    )
    if not claim_lifecycle.items:
        return []
    return render_operator_pack_claim_lifecycle_markdown_lines(claim_lifecycle)


def _operator_pack_lease_governance_lines(*, report_search_root: str, report_repo_root: str, current_pack_kind: str, pack_kinds: tuple[str, ...], operator_workboard=None) -> list[str]:
    search_root = Path(report_search_root)
    if not search_root.exists():
        return []
    lease_governance = materialize_operator_pack_lease_governance(
        build_operator_pack_lease_governance_request(
            search_root=search_root,
            repo_root=Path(report_repo_root),
            current_pack_kind=current_pack_kind,
            pack_kinds=pack_kinds,
            max_items=3,
            queue_key=getattr(operator_workboard, 'queue_key', None),
            review_target=getattr(operator_workboard, 'review_target', None),
            priority_band=getattr(operator_workboard, 'priority_band', None),
            action_owner_lane=(operator_workboard.entries[0].action_owner_lane if getattr(operator_workboard, 'entries', None) else None),
            board_label=getattr(operator_workboard, 'board_label', None),
        ),
        operator_workboard=operator_workboard,
    )
    if not lease_governance.items:
        return []
    return render_operator_pack_lease_governance_markdown_lines(lease_governance)


def _operator_pack_dispatch_permission_lines(*, report_search_root: str, report_repo_root: str, current_pack_kind: str, pack_kinds: tuple[str, ...], operator_workboard=None) -> list[str]:
    search_root = Path(report_search_root)
    if not search_root.exists():
        return []
    dispatch_permission = materialize_operator_pack_dispatch_permission(
        build_operator_pack_dispatch_permission_request(
            search_root=search_root,
            repo_root=Path(report_repo_root),
            current_pack_kind=current_pack_kind,
            pack_kinds=pack_kinds,
            max_items=3,
            queue_key=getattr(operator_workboard, 'queue_key', None),
            review_target=getattr(operator_workboard, 'review_target', None),
            priority_band=getattr(operator_workboard, 'priority_band', None),
            action_owner_lane=(operator_workboard.entries[0].action_owner_lane if getattr(operator_workboard, 'entries', None) else None),
            board_label=getattr(operator_workboard, 'board_label', None),
        ),
        operator_workboard=operator_workboard,
    )
    if not dispatch_permission.items:
        return []
    return render_operator_pack_dispatch_permission_markdown_lines(dispatch_permission)


def _operator_pack_dispatch_outcome_lines(*, report_search_root: str, report_repo_root: str, current_pack_kind: str, pack_kinds: tuple[str, ...], operator_workboard=None) -> list[str]:
    search_root = Path(report_search_root)
    if not search_root.exists():
        return []
    dispatch_outcome = materialize_operator_pack_dispatch_outcome(
        build_operator_pack_dispatch_outcome_request(
            search_root=search_root,
            repo_root=Path(report_repo_root),
            current_pack_kind=current_pack_kind,
            pack_kinds=pack_kinds,
            max_items=3,
            queue_key=getattr(operator_workboard, 'queue_key', None),
            review_target=getattr(operator_workboard, 'review_target', None),
            priority_band=getattr(operator_workboard, 'priority_band', None),
            action_owner_lane=(operator_workboard.entries[0].action_owner_lane if getattr(operator_workboard, 'entries', None) else None),
            board_label=getattr(operator_workboard, 'board_label', None),
        ),
        operator_workboard=operator_workboard,
    )
    if not dispatch_outcome.items:
        return []
    return render_operator_pack_dispatch_outcome_markdown_lines(dispatch_outcome)


def _operator_pack_execution_exception_lines(*, report_search_root: str, report_repo_root: str, current_pack_kind: str, pack_kinds: tuple[str, ...], operator_workboard=None) -> list[str]:
    search_root = Path(report_search_root)
    if not search_root.exists():
        return []
    execution_exception = materialize_operator_pack_execution_exception(
        build_operator_pack_execution_exception_request(
            search_root=search_root,
            repo_root=Path(report_repo_root),
            current_pack_kind=current_pack_kind,
            pack_kinds=pack_kinds,
            max_items=3,
            queue_key=getattr(operator_workboard, 'queue_key', None),
            review_target=getattr(operator_workboard, 'review_target', None),
            priority_band=getattr(operator_workboard, 'priority_band', None),
            action_owner_lane=(operator_workboard.entries[0].action_owner_lane if getattr(operator_workboard, 'entries', None) else None),
            board_label=getattr(operator_workboard, 'board_label', None),
        ),
        operator_workboard=operator_workboard,
    )
    if not execution_exception.items:
        return []
    return render_operator_pack_execution_exception_markdown_lines(execution_exception)


def _operator_pack_approval_needed_lines(*, report_search_root: str, report_repo_root: str, current_pack_kind: str, pack_kinds: tuple[str, ...], operator_workboard=None) -> list[str]:
    search_root = Path(report_search_root)
    if not search_root.exists():
        return []
    approval_needed = materialize_operator_pack_approval_needed(
        build_operator_pack_approval_needed_request(
            search_root=search_root,
            repo_root=Path(report_repo_root),
            current_pack_kind=current_pack_kind,
            pack_kinds=pack_kinds,
            max_items=3,
            queue_key=getattr(operator_workboard, 'queue_key', None),
            review_target=getattr(operator_workboard, 'review_target', None),
            priority_band=getattr(operator_workboard, 'priority_band', None),
            action_owner_lane=(operator_workboard.entries[0].action_owner_lane if getattr(operator_workboard, 'entries', None) else None),
            board_label=getattr(operator_workboard, 'board_label', None),
        ),
        operator_workboard=operator_workboard,
    )
    if not approval_needed.items:
        return []
    return render_operator_pack_approval_needed_markdown_lines(approval_needed)


def _operator_pack_approval_disposition_lines(*, report_search_root: str, report_repo_root: str, current_pack_kind: str, pack_kinds: tuple[str, ...], operator_workboard=None) -> list[str]:
    search_root = Path(report_search_root)
    if not search_root.exists():
        return []
    approval_disposition = materialize_operator_pack_approval_disposition(
        build_operator_pack_approval_disposition_request(
            search_root=search_root,
            repo_root=Path(report_repo_root),
            current_pack_kind=current_pack_kind,
            pack_kinds=pack_kinds,
            max_items=3,
            queue_key=getattr(operator_workboard, 'queue_key', None),
            review_target=getattr(operator_workboard, 'review_target', None),
            priority_band=getattr(operator_workboard, 'priority_band', None),
            action_owner_lane=(operator_workboard.entries[0].action_owner_lane if getattr(operator_workboard, 'entries', None) else None),
            board_label=getattr(operator_workboard, 'board_label', None),
        ),
        operator_workboard=operator_workboard,
    )
    if not approval_disposition.items:
        return []
    return render_operator_pack_approval_disposition_markdown_lines(approval_disposition)


def _operator_pack_execution_authorization_lines(*, report_search_root: str, report_repo_root: str, current_pack_kind: str, pack_kinds: tuple[str, ...], operator_workboard=None) -> list[str]:
    search_root = Path(report_search_root)
    if not search_root.exists():
        return []
    execution_authorization = materialize_operator_pack_execution_authorization(
        build_operator_pack_execution_authorization_request(
            search_root=search_root,
            repo_root=Path(report_repo_root),
            current_pack_kind=current_pack_kind,
            pack_kinds=pack_kinds,
            max_items=3,
            queue_key=getattr(operator_workboard, 'queue_key', None),
            review_target=getattr(operator_workboard, 'review_target', None),
            priority_band=getattr(operator_workboard, 'priority_band', None),
            action_owner_lane=(operator_workboard.entries[0].action_owner_lane if getattr(operator_workboard, 'entries', None) else None),
            board_label=getattr(operator_workboard, 'board_label', None),
        ),
        operator_workboard=operator_workboard,
    )
    if not execution_authorization.items:
        return []
    return render_operator_pack_execution_authorization_markdown_lines(execution_authorization)


def _operator_pack_terminal_resolution_lines(*, report_search_root: str, report_repo_root: str, current_pack_kind: str, pack_kinds: tuple[str, ...], operator_workboard=None) -> list[str]:
    report_root = Path(report_search_root)
    repo_root = Path(report_repo_root)
    if not report_root.exists():
        return []
    terminal_resolution = materialize_operator_pack_terminal_resolution(
        build_operator_pack_terminal_resolution_request(
            search_root=report_root,
            repo_root=repo_root,
            current_pack_kind=current_pack_kind,
            pack_kinds=pack_kinds,
            max_items=3,
        ),
        operator_workboard=operator_workboard,
    )
    if not terminal_resolution.items:
        return []
    return render_operator_pack_terminal_resolution_markdown_lines(terminal_resolution)


def _operator_pack_terminal_closure_lines(*, report_search_root: str, report_repo_root: str, current_pack_kind: str, pack_kinds: tuple[str, ...], operator_workboard=None) -> list[str]:
    report_root = Path(report_search_root)
    repo_root = Path(report_repo_root)
    if not report_root.exists():
        return []
    terminal_closure = materialize_operator_pack_terminal_closure(
        build_operator_pack_terminal_closure_request(
            search_root=report_root,
            repo_root=repo_root,
            current_pack_kind=current_pack_kind,
            pack_kinds=pack_kinds,
            max_items=3,
        ),
        operator_workboard=operator_workboard,
    )
    if not terminal_closure.items:
        return []
    return render_operator_pack_terminal_closure_markdown_lines(terminal_closure)


def _operator_pack_terminal_archive_lines(*, report_search_root: str, report_repo_root: str, current_pack_kind: str, pack_kinds: tuple[str, ...], operator_workboard=None) -> list[str]:
    report_root = Path(report_search_root)
    repo_root = Path(report_repo_root)
    if not report_root.exists():
        return []
    terminal_archive = materialize_operator_pack_terminal_archive(
        build_operator_pack_terminal_archive_request(
            search_root=report_root,
            repo_root=repo_root,
            current_pack_kind=current_pack_kind,
            pack_kinds=pack_kinds,
            max_items=3,
        )
    )
    if not terminal_archive.items:
        return []
    return render_operator_pack_terminal_archive_markdown_lines(terminal_archive)


def _operator_pack_terminal_record_lines(*, report_search_root: str, report_repo_root: str, current_pack_kind: str, pack_kinds: tuple[str, ...], operator_workboard=None) -> list[str]:
    report_root = Path(report_search_root)
    repo_root = Path(report_repo_root)
    if not report_root.exists():
        return []
    terminal_record = materialize_operator_pack_terminal_record(
        build_operator_pack_terminal_record_request(
            search_root=report_root,
            repo_root=repo_root,
            current_pack_kind=current_pack_kind,
            pack_kinds=pack_kinds,
            max_items=3,
        )
    )
    if not terminal_record.items:
        return []
    return render_operator_pack_terminal_record_markdown_lines(terminal_record)


def _operator_pack_execution_finality_lines(*, report_search_root: str, report_repo_root: str, current_pack_kind: str, pack_kinds: tuple[str, ...], operator_workboard=None) -> list[str]:
    if not Path(report_search_root).exists():
        return []
    execution_finality = materialize_operator_pack_execution_finality(
        build_operator_pack_execution_finality_request(
            search_root=Path(report_search_root),
            repo_root=Path(report_repo_root),
            current_pack_kind=current_pack_kind,
            pack_kinds=pack_kinds,
            max_items=3,
        ),
        operator_workboard=operator_workboard,
    )
    if not execution_finality.items:
        return []
    return render_operator_pack_execution_finality_markdown_lines(execution_finality)


def _operator_pack_execution_force_lines(*, report_search_root: str, report_repo_root: str, current_pack_kind: str, pack_kinds: tuple[str, ...], operator_workboard=None) -> list[str]:
    search_root = Path(report_search_root)
    if not search_root.exists():
        return []
    execution_force = materialize_operator_pack_execution_force(
        build_operator_pack_execution_force_request(
            search_root=search_root,
            repo_root=Path(report_repo_root),
            current_pack_kind=current_pack_kind,
            pack_kinds=pack_kinds,
            max_items=3,
            queue_key=getattr(operator_workboard, 'queue_key', None),
            review_target=getattr(operator_workboard, 'review_target', None),
            priority_band=getattr(operator_workboard, 'priority_band', None),
            action_owner_lane=(operator_workboard.entries[0].action_owner_lane if getattr(operator_workboard, 'entries', None) else None),
            board_label=getattr(operator_workboard, 'board_label', None),
        ),
        operator_workboard=operator_workboard,
    )
    if not execution_force.items:
        return []
    return render_operator_pack_execution_force_markdown_lines(execution_force)


def _operator_pack_claim_operability_lines(*, report_search_root: str, report_repo_root: str, current_pack_kind: str, pack_kinds: tuple[str, ...], operator_workboard=None) -> list[str]:
    if not Path(report_search_root).exists():
        return []
    claim_operability = materialize_operator_pack_claim_operability(
        build_operator_pack_claim_operability_request(
            search_root=Path(report_search_root),
            repo_root=Path(report_repo_root),
            current_pack_kind=current_pack_kind,
            pack_kinds=pack_kinds,
            max_items=3,
        ),
        operator_workboard=operator_workboard,
    )
    if not claim_operability.items:
        return []
    return render_operator_pack_claim_operability_markdown_lines(claim_operability)


def _operator_pack_execution_readiness_lines(*, report_search_root: str, report_repo_root: str, current_pack_kind: str, pack_kinds: tuple[str, ...], operator_workboard=None) -> list[str]:
    search_root = Path(report_search_root)
    if not search_root.exists():
        return []
    execution_readiness = materialize_operator_pack_execution_readiness(
        build_operator_pack_execution_readiness_request(
            search_root=search_root,
            repo_root=Path(report_repo_root),
            current_pack_kind=current_pack_kind,
            pack_kinds=pack_kinds,
            max_items=3,
            queue_key=getattr(operator_workboard, 'queue_key', None),
            review_target=getattr(operator_workboard, 'review_target', None),
            priority_band=getattr(operator_workboard, 'priority_band', None),
            action_owner_lane=(operator_workboard.entries[0].action_owner_lane if getattr(operator_workboard, 'entries', None) else None),
            board_label=getattr(operator_workboard, 'board_label', None),
        ),
        operator_workboard=operator_workboard,
    )
    if not execution_readiness.items:
        return []
    return render_operator_pack_execution_readiness_markdown_lines(execution_readiness)


def _closure_section(
    *,
    snapshot_path: Path,
    verification: ClosureSnapshotVerification,
    attestation: ClosureReleaseAttestation,
) -> OracleStatusPackSection:
    return OracleStatusPackSection(
        section_id="closure_attestation",
        status=attestation.signoff_status,
        summary_line=attestation.summary_line,
        facts=_unique([
            f"closure_id={attestation.closure_id}",
            f"verification_status={verification.status}",
            f"machine_decision={attestation.machine_decision}",
            f"primary_classification={attestation.primary_classification}",
            f"final_release_stance={attestation.final_release_stance}",
            f"snapshot_path={snapshot_path}",
        ] + [f"reason={item}" for item in attestation.reasons]),
        operator_actions=list(attestation.required_operator_actions),
    )
