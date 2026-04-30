from __future__ import annotations

from strategy_validator.contracts.ui_detail_queries import UiEvidenceQuery, UiPackDetailQuery


def build_ui_evidence_query(
    *,
    repo_root: str | None,
    search_root: str | None,
) -> UiEvidenceQuery:
    return UiEvidenceQuery(
        repo_root=repo_root,
        search_root=search_root,
    )


def build_ui_pack_detail_query(
    *,
    search_root: str | None,
    board_label: str,
    pack_kind: str | None,
    manifest_path: str | None,
) -> UiPackDetailQuery:
    return UiPackDetailQuery(
        search_root=search_root,
        board_label=board_label,
        pack_kind=pack_kind,
        manifest_path=manifest_path,
    )


__all__ = ['build_ui_evidence_query', 'build_ui_pack_detail_query']
