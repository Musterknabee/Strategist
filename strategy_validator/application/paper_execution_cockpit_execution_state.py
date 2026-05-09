"""Paper execution cockpit execution-state assembly facade."""
from __future__ import annotations

from strategy_validator.application.paper_execution_cockpit_execution_common import _as_dict, _safe_read_json
from strategy_validator.application.paper_execution_cockpit_execution_freshness import (
    _freshness_gate,
    _selected_dry_run_replay_status,
)
from strategy_validator.application.paper_execution_cockpit_execution_intent import (
    _broker_status,
    _build_intent_preview,
    _dry_run,
    _intent_selection_count,
    _selected_artifact_to_preview,
    _selection_artifact,
)
from strategy_validator.application.paper_execution_cockpit_execution_journal import (
    _journal_entries,
    _submission_receipts,
)
from strategy_validator.application.paper_execution_cockpit_execution_timeline import _execution_timeline

__all__ = [
    "_as_dict",
    "_broker_status",
    "_build_intent_preview",
    "_dry_run",
    "_execution_timeline",
    "_freshness_gate",
    "_intent_selection_count",
    "_journal_entries",
    "_safe_read_json",
    "_selected_artifact_to_preview",
    "_selected_dry_run_replay_status",
    "_selection_artifact",
    "_submission_receipts",
]
