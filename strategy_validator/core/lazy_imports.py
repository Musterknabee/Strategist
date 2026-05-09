"""Small dependency-free lazy import helpers for hot import surfaces.

These helpers live under ``core`` so API, application, and CLI code can defer
expensive optional dependency graphs without depending on route-only utilities.
"""
from __future__ import annotations

from collections.abc import Callable
from functools import lru_cache
from importlib import import_module
from typing import Any, cast


@lru_cache(maxsize=None)
def load_attribute(module_name: str, attribute_name: str) -> Any:
    """Load an attribute once and cache it for subsequent calls."""

    module = import_module(module_name)
    return getattr(module, attribute_name)


@lru_cache(maxsize=None)
def load_callable(module_name: str, attribute_name: str) -> Callable[..., Any]:
    """Load a callable lazily and fail loudly when the target is invalid."""

    value = load_attribute(module_name, attribute_name)
    if not callable(value):
        raise TypeError(f"{module_name}.{attribute_name} is not callable")
    return cast(Callable[..., Any], value)


def lazy_callable(module_name: str, attribute_name: str) -> Callable[..., Any]:
    """Return a proxy that imports and calls the target only on first use."""

    def _proxy(*args: Any, **kwargs: Any) -> Any:
        return load_callable(module_name, attribute_name)(*args, **kwargs)

    _proxy.__name__ = attribute_name
    _proxy.__qualname__ = attribute_name
    _proxy.__module__ = __name__
    _proxy.__doc__ = f"Lazy proxy for {module_name}.{attribute_name}."
    return _proxy


class LazyAttribute:
    """Proxy for class-like/model-like attributes loaded on first use."""

    def __init__(self, module_name: str, attribute_name: str) -> None:
        self._module_name = module_name
        self._attribute_name = attribute_name
        self.__name__ = attribute_name
        self.__qualname__ = attribute_name
        self.__module__ = __name__

    def _target(self) -> Any:
        return load_attribute(self._module_name, self._attribute_name)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self._target()(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._target(), name)

    def __repr__(self) -> str:
        return f"<lazy attribute {self._module_name}.{self._attribute_name}>"


def lazy_model(module_name: str, attribute_name: str) -> LazyAttribute:
    """Return a class/model proxy imported on first constructor or attribute use."""

    return LazyAttribute(module_name, attribute_name)
