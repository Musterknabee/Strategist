from __future__ import annotations

from strategy_validator.contracts.oracle import (
    OracleBriefingSection,
    OracleOperatorWorkboardItemReport,
    OracleOperatorWorkboardReport,
)
from strategy_validator.control_plane.operator_queue_snapshot import OracleOperatorQueueSnapshot
from strategy_validator.control_plane.operator_workboard import OracleOperatorWorkboard


def build_operator_workboard_report(*, workboard: OracleOperatorWorkboard) -> OracleOperatorWorkboardReport:
    return OracleOperatorWorkboardReport(
        board_label=workboard.board_label,
        queue_key=workboard.queue_key,
        review_target=workboard.review_target,
        priority_band=workboard.priority_band,
        review_due_by_utc=workboard.review_due_by_utc,
        review_sort_key=workboard.review_sort_key,
        work_item_count=workboard.work_item_count,
        summary_line=workboard.summary_line,
        queue_summary_line=workboard.queue_summary_line,
        recommended_next_actions=list(workboard.recommended_next_actions),
        entries=[
            OracleOperatorWorkboardItemReport(
                work_item_key=item.work_item_key,
                queue_key=item.queue_key,
                review_target=item.review_target,
                priority_band=item.priority_band,
                review_due_by_utc=item.review_due_by_utc,
                review_sort_key=item.review_sort_key,
                action_owner_lane=item.action_owner_lane,
                claim_operability=item.claim_operability,
                dispatch_posture=item.dispatch_posture,
                urgency=item.urgency,
                score=item.score,
                summary_line=item.summary_line,
                recommended_actions=list(item.recommended_actions),
            )
            for item in workboard.entries
        ],
    )



def render_operator_workboard_markdown_lines(*, workboard: OracleOperatorWorkboardReport | None) -> list[str]:
    if workboard is None:
        return []
    lines = [
        "## Operator Workboard",
        f"- Board label: `{workboard.board_label}`",
        f"- Queue key: `{workboard.queue_key}`",
        f"- Review target: `{workboard.review_target}`",
        f"- Priority band: `{workboard.priority_band}`",
        f"- Work item count: `{workboard.work_item_count}`",
        f"- Summary: {workboard.summary_line}",
    ]
    if workboard.recommended_next_actions:
        lines.append("- Recommended next actions:")
        lines.extend([f"  - {item}" for item in workboard.recommended_next_actions])
    for entry in workboard.entries:
        lines.extend(
            [
                (
                    f"  - Work item `{entry.work_item_key}` ({entry.action_owner_lane}, {entry.urgency}) "
                    f"— {entry.summary_line}"
                )
            ]
        )
        if entry.recommended_actions:
            lines.append("    - Recommended actions:")
            lines.extend([f"      - {item}" for item in entry.recommended_actions])
    lines.append("")
    return lines



def build_operator_queue_briefing_section(
    *,
    operator_queue_snapshot: OracleOperatorQueueSnapshot,
    governance_plane_status: str,
    governance_claim_sha256: str,
    governance_dispatch_sha256: str,
    status_pack_provenance_digest_sha256: str,
) -> OracleBriefingSection:
    primary_work_item = operator_queue_snapshot.primary_work_item
    return OracleBriefingSection(
        section_id="operator_queue",
        title="Operator Queue",
        status=governance_plane_status,
        summary_line=operator_queue_snapshot.queue_summary_line,
        facts=[
            f"queue_key={operator_queue_snapshot.queue_key}",
            f"review_target={operator_queue_snapshot.review_target}",
            f"priority_band={operator_queue_snapshot.priority_band}",
            f"review_due_by_utc={operator_queue_snapshot.review_due_by_utc.isoformat()}",
            f"review_sort_key={operator_queue_snapshot.review_sort_key}",
            f"primary_work_item_key={primary_work_item.work_item_key}",
            f"dispatch_posture={primary_work_item.dispatch_posture}",
            f"dispatch_claim_key={primary_work_item.dispatch_claim_key}",
            f"dispatch_claim_urgency={primary_work_item.dispatch_claim_urgency}",
            f"claim_operability={primary_work_item.claim_operability}",
            f"claim_worker_lane={primary_work_item.claim_worker_lane}",
            f"lease_key={primary_work_item.lease_key}",
            f"lease_active_now={primary_work_item.lease_active_now}",
            f"claim_summary={primary_work_item.claim_summary_line}",
            *[f"recommended_action={item}" for item in operator_queue_snapshot.recommended_next_actions[:4]],
        ],
        operator_actions=list(operator_queue_snapshot.recommended_next_actions[:4]) or [primary_work_item.claim_primary_action_text],
        provenance_refs=[
            f"governance_claim:{governance_claim_sha256}",
            f"governance_dispatch:{governance_dispatch_sha256}",
            f"status_pack:{status_pack_provenance_digest_sha256}",
        ],
    )


__all__ = [
    'build_operator_queue_briefing_section',
    'build_operator_workboard_report',
    'render_operator_workboard_markdown_lines',
]
