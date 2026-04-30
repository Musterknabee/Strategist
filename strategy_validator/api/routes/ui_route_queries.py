from __future__ import annotations

from strategy_validator.application.api_ui_surfaces import (
    build_ui_burnin_query,
    build_ui_evidence_query,
    build_ui_pack_detail_query,
    build_ui_runtime_query,
    build_ui_tribunal_query,
    build_ui_workboard_query,
)


def build_ui_evidence_query_kwargs(
    *,
    repo_root: str | None,
    search_root: str | None,
) -> dict[str, object]:
    return build_ui_evidence_query(
        repo_root=repo_root,
        search_root=search_root,
    ).to_payload()



def build_ui_pack_detail_query_kwargs(
    *,
    search_root: str | None,
    board_label: str,
    pack_kind: str | None,
    manifest_path: str | None,
) -> dict[str, object]:
    return build_ui_pack_detail_query(
        search_root=search_root,
        board_label=board_label,
        pack_kind=pack_kind,
        manifest_path=manifest_path,
    ).to_payload()



def build_ui_burnin_query_kwargs(*, artifact_path: list[str]) -> dict[str, object]:
    return build_ui_burnin_query(artifact_path=artifact_path).to_payload()



def build_ui_runtime_query_kwargs(*, role: str) -> dict[str, object]:
    return build_ui_runtime_query(role=role).to_payload()



def build_ui_tribunal_query_kwargs() -> dict[str, object]:
    return build_ui_tribunal_query().to_payload()



def build_ui_workboard_query_kwargs(
    *,
    board_label: str,
    search_root: str | None,
    pack_kind: list[str],
    trust_status: list[str],
) -> dict[str, object]:
    return build_ui_workboard_query(
        board_label=board_label,
        search_root=search_root,
        pack_kind=pack_kind,
        trust_status=trust_status,
    ).to_payload()
