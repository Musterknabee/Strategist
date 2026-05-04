from __future__ import annotations

from typing import Any


def summarize_execution_realism(decision: Any) -> dict[str, Any]:
    report = getattr(decision, 'execution_report', None)
    if report is None:
        return {}
    if hasattr(report, 'model_dump'):
        return report.model_dump(mode='json')
    if isinstance(report, dict):
        return dict(report)
    return {'repr': repr(report)}
