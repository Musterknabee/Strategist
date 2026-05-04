"""Shared API token and scope policy for single-tenant deployments.

This module intentionally has no FastAPI/Pydantic imports so it can be reused by
CLI env checks, startup/readiness checks, and tests without pulling the full app.
"""
from __future__ import annotations

import re

REQUIRED_MUTATION_SCOPES = frozenset({"operator:command:write", "operator:projection:read"})
DEFAULT_TOKEN_SCOPES = tuple(sorted(REQUIRED_MUTATION_SCOPES))
PLACEHOLDER_TOKEN_VALUES = frozenset(
    {
        "",
        "replace-me",
        "changeme",
        "change-me",
        "secret-token",
        "test-token",
        "ci-smoke-token",
        "password",
        "token",
    }
)
PLACEHOLDER_TOKEN_MARKERS = (
    "changeme",
    "change-me",
    "replace-me",
    "placeholder",
    "example",
    "dummy",
    "secret-token",
    "test-token",
    "password",
    "minimum-32-random-characters",
)


def split_token_scopes(raw: str | None, *, default_when_empty: bool = False) -> tuple[str, ...]:
    """Return normalized token scopes from comma/whitespace-separated env text."""

    scopes = tuple(sorted({item.strip() for item in re.split(r"[,\s]+", raw or "") if item.strip()}))
    if scopes:
        return scopes
    return DEFAULT_TOKEN_SCOPES if default_when_empty else ()


def missing_required_mutation_scopes(scopes: tuple[str, ...] | list[str] | set[str]) -> tuple[str, ...]:
    """Return required mutation scopes not present in the provided scope set."""

    return tuple(sorted(REQUIRED_MUTATION_SCOPES.difference(set(scopes))))


def is_placeholder_token(value: str | None) -> bool:
    """Return True for missing, low-quality, or template-like API tokens."""

    normalized = (value or "").strip().lower()
    if normalized in PLACEHOLDER_TOKEN_VALUES:
        return True
    if len(normalized) < 32:
        return True
    if any(marker in normalized for marker in PLACEHOLDER_TOKEN_MARKERS):
        return True
    if len(set(normalized)) <= 3:
        return True
    return False


__all__ = [
    "DEFAULT_TOKEN_SCOPES",
    "PLACEHOLDER_TOKEN_MARKERS",
    "PLACEHOLDER_TOKEN_VALUES",
    "REQUIRED_MUTATION_SCOPES",
    "is_placeholder_token",
    "missing_required_mutation_scopes",
    "split_token_scopes",
]
