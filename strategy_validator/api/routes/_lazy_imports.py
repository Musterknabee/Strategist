from __future__ import annotations

from collections.abc import Callable
from functools import lru_cache
from importlib import import_module
from typing import Any, TypeVar, cast

_ReturnT = TypeVar("_ReturnT")


@lru_cache(maxsize=None)
def load_callable(module_name: str, attribute_name: str) -> Callable[..., Any]:
    """Load a route dependency on first use instead of API import time.

    UI/read-plane route modules intentionally expose many endpoints.  Importing
    every backing application builder during ``strategy_validator.api.app``
    creation pulls in heavy optional surfaces such as pandas-backed paper
    execution contracts.  This helper preserves the existing monkeypatchable
    route globals while deferring those imports until an endpoint is actually
    called.
    """

    value = load_attribute(module_name, attribute_name)
    if not callable(value):
        raise TypeError(f"{module_name}.{attribute_name} is not callable")
    return cast(Callable[..., Any], value)


def lazy_callable(module_name: str, attribute_name: str) -> Callable[..., Any]:
    """Return a small proxy function for a lazily loaded callable."""

    def _proxy(*args: Any, **kwargs: Any) -> Any:
        return load_callable(module_name, attribute_name)(*args, **kwargs)

    _proxy.__name__ = attribute_name
    _proxy.__qualname__ = attribute_name
    _proxy.__module__ = __name__
    _proxy.__doc__ = f"Lazy proxy for {module_name}.{attribute_name}."
    return _proxy


class _LazyModel:
    """Tiny proxy exposing ``model_validate`` without importing a model at route import time.

    Research routes receive raw JSON dictionaries at the HTTP boundary.  The
    canonical Pydantic contract is still enforced inside the endpoint, but the
    expensive semantic contract graph is loaded only when the endpoint is
    executed instead of during FastAPI app creation.
    """

    def __init__(self, module_name: str, attribute_name: str) -> None:
        self._module_name = module_name
        self._attribute_name = attribute_name
        self.__name__ = attribute_name
        self.__qualname__ = attribute_name
        self.__module__ = __name__

    def _model(self) -> Any:
        return load_attribute(self._module_name, self._attribute_name)

    def model_validate(self, value: Any, *args: Any, **kwargs: Any) -> Any:
        return self._model().model_validate(value, *args, **kwargs)

    def __repr__(self) -> str:
        return f"<lazy model {self._module_name}.{self._attribute_name}>"


@lru_cache(maxsize=None)
def load_attribute(module_name: str, attribute_name: str) -> Any:
    """Load any route dependency on first use instead of API import time."""

    module = import_module(module_name)
    return getattr(module, attribute_name)


def lazy_model(module_name: str, attribute_name: str) -> _LazyModel:
    """Return a proxy for a Pydantic model class loaded on first validation."""

    return _LazyModel(module_name, attribute_name)
