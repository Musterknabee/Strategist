from __future__ import annotations

from typing import Any, Mapping

from strategy_validator.application.readiness import get_readiness_health_payload
from strategy_validator.application.ui_view_helpers import utc_now_iso
from strategy_validator.contracts.ui_workboard_dashboard import (
    UiOperatorWorkboardPayload,
    UiWorkboardDashboardPayload,
    UiWorkboardDashboardStats,
)
from strategy_validator.contracts.ui_workboard_export import (
    UiWorkboardExportPayload,
    UiWorkboardOperationalTruth,
    UiWorkboardQueueProvenance,
)

_utc_now = utc_now_iso


def build_ui_workboard_dashboard_payload_model(*, dashboard_context: Mapping[str, Any]) -> UiWorkboardDashboardPayload:
    board_label = str(dashboard_context.get("board_label") or "operator")
    workboard = UiOperatorWorkboardPayload.from_mapping(dashboard_context.get("workboard", {}) or {}).to_payload()
    workbench = dict(dashboard_context.get("workbench", {}) or {})
    intelligence = dict(dashboard_context.get("intelligence", {}) or {})
    transition_policy = dict(dashboard_context.get("transition_policy", {}) or {})
    escalation_count = sum(
        1
        for entry in workboard.get("entries", [])
        if "ESCAL" in str(entry.get("priority_band", "")).upper() or "HIGH" in str(entry.get("urgency", "")).upper()
    )
    materialization = dict(intelligence.get("board_materialization_status", {}) or {})
    stats = UiWorkboardDashboardStats.from_mapping({
        "active_count": int(workboard.get("work_item_count", 0)),
        "governed_count": int(workboard.get("governed_work_item_count", 0)),
        "journaled_count": int(workboard.get("journaled_work_item_count", 0)),
        "escalated_count": escalation_count,
        "blocked_count": int(intelligence.get("summary", {}).get("blocked_count", 0)),
        "linked_count": int(intelligence.get("summary", {}).get("linked_count", 0)),
        "stale_link_count": int(intelligence.get("summary", {}).get("stale_link_count", 0)),
        "pack_item_count": int(workbench.get("total_item_count", 0)),
        "pack_column_count": int(workbench.get("column_count", 0)),
        "freshness_state": str(materialization.get("freshness_state") or "UNKNOWN"),
    })
    return UiWorkboardDashboardPayload.from_mapping({
        "schema_version": "ui_workboard_dashboard/v1",
        "generated_at_utc": _utc_now(),
        "board_label": board_label,
        "queue": workboard,
        "pack_workbench": workbench,
        "transition_policy": transition_policy,
        "intelligence": intelligence,
        "materialization": materialization,
        "stats": stats.to_payload(),
    })


def build_ui_workboard_export_payload_model(*, export_context: Mapping[str, Any]) -> UiWorkboardExportPayload:
    board_label = str(export_context.get("board_label") or "operator")
    workboard = dict(export_context.get("workboard", {}) or {})
    workbench = dict(export_context.get("workbench", {}) or {})
    intelligence = dict(export_context.get("intelligence", {}) or {})
    base_payload = dict(intelligence.get("board_export_payload", {}))
    base_payload.setdefault("schema_version", "oracle_operator_board_export_payload/v1")
    base_payload["board_label"] = board_label
    base_payload["generated_at_utc"] = _utc_now()
    base_payload["queue_work_item_count"] = int(workboard.get("work_item_count", 0))
    base_payload["pack_item_count"] = int(workbench.get("total_item_count", 0))
    base_payload["pack_column_count"] = int(workbench.get("column_count", 0))
    materialization = dict(intelligence.get("board_materialization_status", {}) or {})
    mutation_safety = dict(get_readiness_health_payload().get("mutation_safety", {}) or {})
    queue_provenance = UiWorkboardQueueProvenance(
        governed_work_item_count=int(workboard.get("governed_work_item_count", 0)),
        journaled_work_item_count=int(workboard.get("journaled_work_item_count", 0)),
        queue_key=workboard.get("queue_key"),
        review_target=workboard.get("review_target"),
        materialization_state=materialization.get("materialization_state"),
        freshness_state=materialization.get("freshness_state"),
        latest_journaled_action_at_utc=materialization.get("latest_journaled_action_at_utc"),
        latest_projection_generated_at_utc=materialization.get("latest_projection_generated_at_utc"),
    )
    operational_truth = UiWorkboardOperationalTruth(
        mutation_safety=mutation_safety,
        materialization=materialization,
        queue_provenance=queue_provenance,
    )
    return UiWorkboardExportPayload.from_mapping({
        **base_payload,
        "materialization": materialization,
        "queue_provenance": queue_provenance.to_payload(),
        "mutation_safety": mutation_safety,
        "operational_truth": operational_truth.to_payload(),
    })


__all__ = [
    "build_ui_workboard_dashboard_payload_model",
    "build_ui_workboard_export_payload_model",
]
