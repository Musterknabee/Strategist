"""Read-plane payload for paper broker policy (env-derived; no live calls from API)."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

from strategy_validator.brokers.alpaca_paper import evaluate_alpaca_paper_policy

_SCHEMA = "ui_paper_broker/v1"


def build_ui_paper_broker_status_payload() -> dict[str, Any]:
    env = {k: str(v) for k, v in os.environ.items()}
    pol, warns, blocks = evaluate_alpaca_paper_policy(env)
    return {
        "schema_version": _SCHEMA,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "read_plane_only": True,
        "no_live_trading": True,
        "broker_id": "alpaca_paper",
        "policy_status": pol.value,
        "warnings": warns,
        "blockers": blocks,
        "note": "API surfaces env policy only; use CLI for authenticated paper evidence.",
    }


__all__ = ["build_ui_paper_broker_status_payload"]
