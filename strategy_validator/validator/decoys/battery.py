from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from strategy_validator.contracts.evidence import Evidence

REQUIRED_DECOY_TYPES = {
    "randomized_labels",
    "timestamp_jitter",
    "shuffled_cross_section",
    "regime_mismatch",
}


@dataclass(frozen=True)
class DecoyEvaluation:
    passed: bool | None
    suite_version: str | None
    coverage: float | None


def _coerce_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _evaluate_structured_battery(payload: dict[str, Any]) -> DecoyEvaluation:
    rows = payload.get("decoy_battery_results")
    suite_version = str(payload.get("decoy_suite_version", "")) or None
    if not isinstance(rows, list) or not rows:
        return DecoyEvaluation(False, suite_version, 0.0)

    seen: set[str] = set()
    passed = True
    valid_rows = 0
    for row in rows:
        if not isinstance(row, dict):
            passed = False
            continue

        decoy_type = str(row.get("decoy_type", "")).strip()
        if decoy_type:
            seen.add(decoy_type)
        else:
            passed = False
            continue

        if decoy_type not in REQUIRED_DECOY_TYPES:
            # Unknown decoys are tolerated for future suite growth, but they do
            # not contribute toward required constitutional coverage.
            continue

        valid_rows += 1
        row_pass: bool | None = None
        if "passed" in row:
            row_pass = bool(row["passed"])
        else:
            strategy_metric = _coerce_float(row.get("strategy_metric"))
            decoy_metric = _coerce_float(row.get("decoy_metric"))
            margin = _coerce_float(row.get("required_margin", 0.0))
            if strategy_metric is None or decoy_metric is None:
                row_pass = False
            else:
                # The strategy must beat its decoy by at least the configured
                # margin; equality is not enough to claim survival.
                row_pass = (strategy_metric - decoy_metric) > (margin or 0.0)

        if row_pass is not True:
            passed = False

    coverage = len(seen.intersection(REQUIRED_DECOY_TYPES)) / len(REQUIRED_DECOY_TYPES)
    if valid_rows < len(REQUIRED_DECOY_TYPES):
        passed = False
    if not REQUIRED_DECOY_TYPES.issubset(seen):
        passed = False
    if not suite_version:
        passed = False
    return DecoyEvaluation(passed=passed, suite_version=suite_version, coverage=coverage)


def evaluate_decoy_survival_hook(evidence: Iterable[Evidence]) -> DecoyEvaluation:
    for ev in evidence:
        if "decoy_battery_results" in ev.payload:
            return _evaluate_structured_battery(ev.payload)

        if "decoy_survival_passed" in ev.payload:
            coverage = float(ev.payload["decoy_coverage"]) if "decoy_coverage" in ev.payload else None
            passed = bool(ev.payload["decoy_survival_passed"])
            suite_version = str(ev.payload.get("decoy_suite_version", "")) or None
            if coverage is not None and not (0.0 <= coverage <= 1.0):
                passed = False
            return DecoyEvaluation(
                passed=passed,
                suite_version=suite_version,
                coverage=coverage,
            )
    return DecoyEvaluation(None, None, None)
