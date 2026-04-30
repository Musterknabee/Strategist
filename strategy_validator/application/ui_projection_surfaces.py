from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from strategy_validator.application.operator_pack_queries import build_operator_pack_workbench_payload


def build_ui_projection_read_model(
    *,
    search_root: str | Path | None = None,
    pack_kinds: Iterable[str] = (),
    trust_statuses: Iterable[str] = (),
) -> dict[str, Any]:
    """Materialize the UI workbench through the projection/read-model seam.

    UI routes should consume this application surface instead of importing
    ledger/control-plane discovery code directly. The payload preserves an
    explicit provenance marker so regressions back to direct state assembly are
    visible in tests and operator exports.
    """
    root = Path(search_root) if search_root is not None else Path.cwd()
    workbench = build_operator_pack_workbench_payload(
        search_root=root,
        pack_kinds=list(pack_kinds),
        trust_statuses=list(trust_statuses),
    )
    workbench['read_model_surface'] = 'application.ui_projection_surfaces'
    workbench['source_projection_family'] = 'operator_pack_projection'
    return workbench


__all__ = ['build_ui_projection_read_model']
