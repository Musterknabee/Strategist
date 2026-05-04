from __future__ import annotations

import hashlib
import json
from typing import Any


def derive_idempotency_key(*, command_name: str, payload: dict[str, Any]) -> str:
    stable = json.dumps({'command_name': command_name, 'payload': payload}, sort_keys=True, default=str)
    return hashlib.sha256(stable.encode('utf-8')).hexdigest()
