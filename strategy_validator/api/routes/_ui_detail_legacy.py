from __future__ import annotations

from importlib import import_module
from typing import Any, Callable

_LEGACY_MODULE = "strategy_validator.api.routes.ui_routes_detail_runtime"


def legacy_callable(name: str) -> Callable[..., Any]:
    """Resolve a legacy detail-runtime builder at endpoint execution time.

    Route-family modules call through this proxy so existing tests/operator
    monkeypatches against ``ui_routes_detail_runtime.<builder>`` still affect
    the registered endpoint after route definitions move out of the legacy
    aggregate module.
    """

    def _call(*args: Any, **kwargs: Any) -> Any:
        return getattr(import_module(_LEGACY_MODULE), name)(*args, **kwargs)

    _call.__name__ = name
    return _call
