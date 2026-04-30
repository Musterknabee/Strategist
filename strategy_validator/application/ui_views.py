from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from strategy_validator.application.operator_queue_commands import (
    build_transition_policy_payload,
    build_workboard_payload as _build_operator_queue_workboard_payload,
)
from strategy_validator.application.ui_command_actions import build_ui_operator_command_receipt_payload
from strategy_validator.application.ui_detail_views import (
    build_ui_burnin_payload,
    build_ui_evidence_payload,
    build_ui_pack_detail_payload,
    build_ui_runtime_status_payload,
    build_ui_tribunal_payload,
)
from strategy_validator.application.operator_pack_queries import build_operator_pack_workbench_payload as _build_operator_pack_workbench_payload
from strategy_validator.application.ui_workboard_intelligence import build_workboard_intelligence
from strategy_validator.application.ui_workboard_views import (
    build_ui_workboard_export_allow_headers,
    build_ui_workboard_export_disposition_headers,
    build_ui_workboard_export_document_headers,
    build_ui_workboard_export_freshness_headers,
    build_ui_workboard_export_index_from_payload,
    build_ui_workboard_export_index_headers,
    build_ui_workboard_export_location_headers,
    build_ui_workboard_export_profile_headers,
    build_ui_workboard_export_representation_headers,
    build_ui_workboard_export_response_class_headers,
    build_ui_workboard_export_payload_from_context,
    build_ui_workboard_payload_from_context,
    canonicalize_ui_workboard_export_payload as _canonicalize_ui_workboard_export_payload,
    default_export_filename as _default_export_filename,
    export_etag_matches,
    export_last_modified_matches,
    serialize_ui_workboard_export_document,
)


def _build_ui_workboard_context(
    *,
    board_label: str = 'operator',
    search_root: str | Path | None = None,
    pack_kinds: Iterable[str] = (),
    trust_statuses: Iterable[str] = (),
) -> dict[str, Any]:
    workboard = build_workboard_payload(board_label=board_label)
    workbench = build_operator_pack_workbench_payload(
        search_root=search_root,
        pack_kinds=list(pack_kinds),
        trust_statuses=list(trust_statuses),
    )
    if "read_model_surface" not in workbench:
        workbench["read_model_surface"] = "application.ui_projection_surfaces"
    if "source_projection_family" not in workbench:
        workbench["source_projection_family"] = "operator_pack_projection"
    now_utc = None
    generated_at_raw = workboard.get("generated_at_utc")
    if isinstance(generated_at_raw, str) and generated_at_raw.strip():
        try:
            now_utc = datetime.fromisoformat(generated_at_raw.replace("Z", "+00:00"))
        except ValueError:
            now_utc = None
    if now_utc is None:
        workbench_generated_raw = workbench.get("generated_at_utc")
        if isinstance(workbench_generated_raw, str) and workbench_generated_raw.strip():
            try:
                now_utc = datetime.fromisoformat(workbench_generated_raw.replace("Z", "+00:00"))
            except ValueError:
                now_utc = None
    if now_utc is None:
        generated_values: list[datetime] = []
        for column in workbench.get("columns", []) or []:
            for item in column.get("items", []) or []:
                generated_raw = item.get("generated_at_utc")
                if not isinstance(generated_raw, str) or not generated_raw.strip():
                    continue
                try:
                    generated_values.append(datetime.fromisoformat(generated_raw.replace("Z", "+00:00")))
                except ValueError:
                    continue
        if generated_values:
            now_utc = max(generated_values)
    intelligence = build_workboard_intelligence(
        workboard=workboard,
        workbench=workbench,
        now_utc=now_utc,
    )
    return {
        "workboard": workboard,
        "workbench": workbench,
        "intelligence": intelligence,
    }


def build_ui_workboard_payload(
    *,
    board_label: str = 'operator',
    search_root: str | Path | None = None,
    pack_kinds: Iterable[str] = (),
    trust_statuses: Iterable[str] = (),
) -> dict[str, Any]:
    context = _build_ui_workboard_context(
        board_label=board_label,
        search_root=search_root,
        pack_kinds=pack_kinds,
        trust_statuses=trust_statuses,
    )
    transition_policy = build_transition_policy_payload(board_label=board_label)
    return build_ui_workboard_payload_from_context(board_label=board_label, context=context, transition_policy=transition_policy)


def build_workboard_payload(
    *,
    board_label: str = 'operator',
    search_root: str | Path | None = None,
    pack_kinds: Iterable[str] = (),
    trust_statuses: Iterable[str] = (),
) -> dict[str, Any]:
    return _build_operator_queue_workboard_payload(
        board_label=board_label,
    )


def build_operator_pack_workbench_payload(
    *,
    board_label: str = 'operator',
    search_root: str | Path | None = None,
    pack_kinds: Iterable[str] = (),
    trust_statuses: Iterable[str] = (),
) -> dict[str, Any]:
    """Compatibility alias expected by UI workboard intelligence tests."""
    return _build_operator_pack_workbench_payload(
        search_root=search_root,
        pack_kinds=list(pack_kinds),
        trust_statuses=list(trust_statuses),
    )


def build_ui_workboard_export_payload(
    *,
    board_label: str = 'operator',
    search_root: str | Path | None = None,
    pack_kinds: Iterable[str] = (),
    trust_statuses: Iterable[str] = (),
) -> dict[str, Any]:
    context = _build_ui_workboard_context(
        board_label=board_label,
        search_root=search_root,
        pack_kinds=pack_kinds,
        trust_statuses=trust_statuses,
    )
    return build_ui_workboard_export_payload_from_context(board_label=board_label, context=context)


def build_ui_workboard_export_document(
    *,
    board_label: str = 'operator',
    search_root: str | Path | None = None,
    pack_kinds: Iterable[str] = (),
    trust_statuses: Iterable[str] = (),
) -> dict[str, Any]:
    export_payload = build_ui_workboard_export_payload(
        board_label=board_label,
        search_root=search_root,
        pack_kinds=pack_kinds,
        trust_statuses=trust_statuses,
    )
    return serialize_ui_workboard_export_document(export_payload)


def build_ui_workboard_export_index(
    *,
    board_label: str = 'operator',
    search_root: str | Path | None = None,
    pack_kinds: Iterable[str] = (),
    trust_statuses: Iterable[str] = (),
) -> dict[str, Any]:
    export_payload = build_ui_workboard_export_payload(
        board_label=board_label,
        search_root=search_root,
        pack_kinds=pack_kinds,
        trust_statuses=trust_statuses,
    )
    return build_ui_workboard_export_index_from_payload(board_label=board_label, export_payload=export_payload)


__all__ = [
    'build_ui_runtime_status_payload',
    'build_ui_workboard_payload',
    'build_workboard_payload',
    'build_operator_pack_workbench_payload',
    'build_ui_workboard_export_payload',
    'serialize_ui_workboard_export_document',
    'build_ui_workboard_export_document',
    'build_ui_workboard_export_document_headers',
    'build_ui_workboard_export_allow_headers',
    'build_ui_workboard_export_freshness_headers',
    'build_ui_workboard_export_representation_headers',
    'build_ui_workboard_export_profile_headers',
    'build_ui_workboard_export_location_headers',
    'build_ui_workboard_export_disposition_headers',
    'build_ui_workboard_export_response_class_headers',
    'build_ui_workboard_export_index_headers',
    'build_ui_workboard_export_index',
    'export_etag_matches',
    'export_last_modified_matches',
    'build_ui_burnin_payload',
    'build_ui_pack_detail_payload',
    'build_ui_tribunal_payload',
    'build_ui_evidence_payload',
    'build_ui_operator_command_receipt_payload',
    '_canonicalize_ui_workboard_export_payload',
    '_default_export_filename',
]
