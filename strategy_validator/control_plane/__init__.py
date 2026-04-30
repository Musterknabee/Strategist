"""Lazy public export surface for control-plane workflows and governance.

This package intentionally avoids eager importing of the full control-plane
tree. Consumers should prefer ``public_api`` and ``pack_api`` for bounded
access, while this root package remains a compatibility surface with lazy
attribute resolution.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from ._exports import _EXPORT_MAP

__all__ = list(_EXPORT_MAP)


def __getattr__(name: str) -> Any:
    module_name = _EXPORT_MAP.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(module_name)
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(_EXPORT_MAP))
