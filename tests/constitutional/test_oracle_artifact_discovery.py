from __future__ import annotations

import json
from pathlib import Path

import pytest

from strategy_validator.contracts.oracle import OracleDoctrineAdaptationReport
from strategy_validator.validator.oracle_cadence_feedback import summarize_exact_cadence_feedback
from strategy_validator.validator.oracle_schema_registry import iter_registered_artifacts, load_registered_artifact


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def _doctrine_payload(*, run_id: str) -> dict:
    return {
        "schema_version": "oracle_doctrine_adaptation_report/v1",
        "generated_at_utc": "2026-04-14T10:00:00Z",
        "input_timestamp_utc": "2026-04-14T10:00:00Z",
        "oracle_run_id": run_id,
        "universe_label": "US_EQ_FACTORS",
        "dominant_regime": "TRANSITION",
        "strategic_posture": "CAUTION_BIASED",
        "transition_classification": "DRIFTING",
        "history_integrity_status": "SEALED_HISTORY",
        "sealed_history_observation_count": 2,
        "unsealed_history_excluded_count": 0,
        "preferred_strategic_backing_source": "SEALED_STRATEGIC_STACK",
        "preferred_strategic_backing_classification": "SEALED_STRATEGIC_STACK_BACKED",
        "exact_evidence_support_score": 0.91,
        "summary_line": "ok",
        "top_review_clause_ids": ["doctrine:stress-window"],
        "freeze_recommended": False,
        "operator_actions": [],
        "items": [
            {
                "clause_id": "doctrine:stress-window",
                "clause_label": "Stress window",
                "adaptation_state": "ADAPT",
                "stress_score": 0.74,
                "review_priority_score": 0.71,
                "exact_evidence_support_score": 0.91,
                "weakening_assumptions": [],
                "pressure_sources": ["queue_pressure"],
                "recommended_adaptation": "review now",
                "summary_line": "pressure persists",
            }
        ],
    }


@pytest.mark.constitutional
def test_load_registered_artifact_validates_and_materializes_model(tmp_path: Path) -> None:
    path = tmp_path / "ORACLE_DOCTRINE_ADAPTATION_REPORT.json"
    _write_json(path, _doctrine_payload(run_id="run-1"))

    registration, payload, model = load_registered_artifact(path, expected_families={"oracle"})

    assert registration.schema_version == "oracle_doctrine_adaptation_report/v1"
    assert payload["oracle_run_id"] == "run-1"
    assert isinstance(model, OracleDoctrineAdaptationReport)


@pytest.mark.constitutional
def test_iter_registered_artifacts_ignores_unknown_json_and_filters_to_expected_schema(tmp_path: Path) -> None:
    _write_json(tmp_path / "junk.json", {"schema_version": "oracle_unknown_report/v999", "hello": "world"})

    report = tmp_path / "nested" / "ORACLE_DOCTRINE_ADAPTATION_REPORT.json"
    _write_json(report, _doctrine_payload(run_id="run-2"))

    discovered = list(
        iter_registered_artifacts(
            roots=[tmp_path],
            expected_schemas={"oracle_doctrine_adaptation_report/v1"},
            expected_families={"oracle"},
        )
    )

    assert len(discovered) == 1
    discovered_path, registration, _, model = discovered[0]
    assert discovered_path == report.resolve()
    assert registration.schema_version == "oracle_doctrine_adaptation_report/v1"
    assert isinstance(model, OracleDoctrineAdaptationReport)


@pytest.mark.constitutional
def test_cadence_feedback_uses_only_registered_doctrine_reports(tmp_path: Path) -> None:
    _write_json(tmp_path / "noise.json", {"schema_version": "oracle_unknown_report/v999"})
    _write_json(tmp_path / "invalid.json", {"schema_version": "oracle_doctrine_adaptation_report/v1", "oops": True})
    _write_json(tmp_path / "ORACLE_DOCTRINE_ADAPTATION_REPORT.json", _doctrine_payload(run_id="run-3"))

    summary = summarize_exact_cadence_feedback(search_root=tmp_path)

    assert summary.exact_evidence_support_score == 0.91
    assert summary.exact_feedback_confirmation_count == 1
    assert summary.exact_feedback_relief_count == 0
