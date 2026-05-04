from __future__ import annotations

from strategy_validator.contracts.ui_runtime_queries import UiBurninQuery, UiRuntimeQuery, UiTribunalQuery


def build_ui_burnin_query(*, artifact_path: list[str]) -> UiBurninQuery:
    return UiBurninQuery(artifact_paths=list(artifact_path))


def build_ui_runtime_query(*, role: str) -> UiRuntimeQuery:
    return UiRuntimeQuery(role=role)


def build_ui_tribunal_query() -> UiTribunalQuery:
    return UiTribunalQuery()


__all__ = ["build_ui_burnin_query", "build_ui_runtime_query", "build_ui_tribunal_query"]
