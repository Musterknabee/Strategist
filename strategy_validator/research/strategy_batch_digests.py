from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json_sha256(obj: Any) -> str:
    """Deterministic SHA-256 of *obj* using sorted JSON keys."""

    body = json.dumps(obj, sort_keys=True, separators=(",", ":"), default=_json_default)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _json_default(o: Any) -> str:
    if hasattr(o, "isoformat"):
        return o.isoformat()
    raise TypeError(f"not JSON serializable: {type(o)!r}")


__all__ = ["canonical_json_sha256"]
