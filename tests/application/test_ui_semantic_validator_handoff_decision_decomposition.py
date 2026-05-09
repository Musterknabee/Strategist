from __future__ import annotations

import ast
from pathlib import Path

APP = Path("strategy_validator/application")


def _source(path: str) -> str:
    return (APP / path).read_text(encoding="utf-8")


def _function_names(path: str) -> set[str]:
    tree = ast.parse(_source(path))
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def test_semantic_validator_handoff_decision_facade_remains_thin() -> None:
    source = _source("ui_semantic_validator_handoff_decision.py")

    assert len(source.splitlines()) <= 100
    assert "def build_ui_semantic_validator_handoff_decision_payload(" not in source
    assert "def _decision_row(" not in source
    assert "def _preconditions(" not in source
    assert "ui_semantic_validator_handoff_decision_common" in source
    assert "ui_semantic_validator_handoff_decision_rows" in source
    assert "ui_semantic_validator_handoff_decision_payload" in source


def test_semantic_validator_handoff_decision_subphase_ownership() -> None:
    common = _function_names("ui_semantic_validator_handoff_decision_common.py")
    rows = _function_names("ui_semantic_validator_handoff_decision_rows.py")
    payload = _function_names("ui_semantic_validator_handoff_decision_payload.py")

    assert {
        "_utc_now",
        "_s",
        "_as_list",
        "_norm_set",
        "_contains",
        "_counts",
        "_digest",
        "_authority",
    } <= common
    assert rows == {
        "_decision_status",
        "_preconditions",
        "_decision_options",
        "_decision_packet",
        "_decision_row",
        "_haystack",
        "_matches",
    }
    assert payload == {
        "_source_builder",
        "build_ui_semantic_validator_handoff_decision_payload",
        "build_ui_semantic_validator_handoff_decision_latest_payload",
    }


def test_semantic_validator_handoff_decision_facade_exports_public_builders() -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_decision as facade
    from strategy_validator.application import ui_semantic_validator_handoff_decision_payload as payload

    assert facade.__all__ == payload.__all__
    for name in facade.__all__:
        assert getattr(facade, name) is getattr(payload, name)


def test_semantic_validator_handoff_decision_legacy_private_imports_remain_available() -> None:
    from strategy_validator.application.ui_semantic_validator_handoff_decision import (
        _decision_options,
        _decision_packet,
        _decision_row,
        _decision_status,
        _haystack,
        _matches,
        _preconditions,
    )

    assert callable(_decision_status)
    assert callable(_preconditions)
    assert callable(_decision_options)
    assert callable(_decision_packet)
    assert callable(_decision_row)
    assert callable(_haystack)
    assert callable(_matches)


def test_semantic_validator_handoff_decision_facade_source_monkeypatch_surface_is_preserved(monkeypatch) -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_decision as facade

    monkeypatch.setattr(
        facade,
        "build_ui_semantic_validator_handoff_review_payload",
        lambda **_: {
            "schema_version": "synthetic-review/v1",
            "search_root": "synthetic-root",
            "degraded": [],
            "summary": {"review_count_total": 1, "ready_for_operator_review_count": 1},
            "reviews": [
                {
                    "review_id": "review-1",
                    "review_status": "READY_FOR_OPERATOR_REVIEW",
                    "operator_review_allowed": True,
                    "trust_banner": "TRUSTED",
                    "review_check_count": 2,
                    "review_pass_count": 2,
                    "review_block_count": 0,
                    "review_blocker_codes": [],
                    "remediation_step_count": 0,
                    "remediation_steps": [],
                    "validator_submission_allowed": False,
                    "promotion_allowed": False,
                    "execution_allowed": False,
                    "chain_id": "chain-1",
                    "chain_digest": "chain-digest-1",
                    "remediation_id": "remediation-1",
                    "experiment_id": "EXP-DECISION",
                }
            ],
        },
    )

    payload = facade.build_ui_semantic_validator_handoff_decision_payload(issue_contains="preconditions")

    assert payload["source_schema_version"] == "synthetic-review/v1"
    assert payload["search_root"] == "synthetic-root"
    assert payload["summary"]["decision_count_returned"] == 1
    assert payload["summary"]["ready_decision_count"] == 1
    row = payload["decisions"][0]
    assert row["decision_status"] == "READY_FOR_OPERATOR_DECISION_DRAFT"
    assert row["manual_operator_signoff_preparable"] is True
    assert row["validator_submission_allowed"] is False
    assert row["promotion_allowed"] is False
    assert row["execution_allowed"] is False
    assert row["decision_packet"]["human_reviewer_id"] == "<REQUIRED_EXTERNALLY>"
    assert payload["validator_submission_authority"] == "none_read_plane"
