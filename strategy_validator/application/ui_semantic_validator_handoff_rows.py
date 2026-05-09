"""Filtering helpers for semantic validator handoff read-plane rows."""
from __future__ import annotations

from typing import Any

from strategy_validator.application.ui_semantic_validator_handoff_common import _as_list, _contains, _issue_haystack


def _matches(
    entry: dict[str, Any],
    *,
    artifact_kinds: set[str],
    recommended_actions: set[str],
    experiment_id_contains: str | None,
    certificate_id_contains: str | None,
    packet_id_contains: str | None,
    issue_contains: str | None,
    handoff_allowed: bool | None,
    verified: bool | None,
    ready_for_validator_ingress: bool | None,
    require_blockers: bool | None,
) -> bool:
    if artifact_kinds and str(entry.get("artifact_kind") or "").upper() not in artifact_kinds:
        return False
    if recommended_actions and str(entry.get("recommended_action") or "").upper() not in recommended_actions:
        return False
    if not _contains(entry.get("experiment_id"), experiment_id_contains):
        return False
    if not _contains(entry.get("certificate_id"), certificate_id_contains):
        return False
    if not _contains(entry.get("packet_id"), packet_id_contains):
        return False
    if issue_contains and not _contains(_issue_haystack(entry), issue_contains):
        return False
    if handoff_allowed is not None and bool(entry.get("handoff_allowed")) is not handoff_allowed:
        return False
    if verified is not None and bool(entry.get("verified")) is not verified:
        return False
    if ready_for_validator_ingress is not None and bool(entry.get("ready_for_validator_ingress")) is not ready_for_validator_ingress:
        return False
    blocker_count = len(_as_list(entry.get("blocker_codes")))
    if require_blockers is True and blocker_count <= 0:
        return False
    if require_blockers is False and blocker_count > 0:
        return False
    return True
