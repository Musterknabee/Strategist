"""Root contract exports resolved lazily."""
from __future__ import annotations

from importlib import import_module

from strategy_validator.contracts._exports import _EXPORT_MAP

__all__ = sorted(_EXPORT_MAP)

def __getattr__(name: str):
    module_name = _EXPORT_MAP.get(name)
    if module_name is None:
        raise AttributeError(name)
    module = import_module(module_name)
    value = getattr(module, name)
    globals()[name] = value
    return value

def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
