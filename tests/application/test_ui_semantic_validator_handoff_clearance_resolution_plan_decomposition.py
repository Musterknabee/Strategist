from __future__ import annotations

import ast
from pathlib import Path

APP = Path("strategy_validator/application")


def _source(path: str) -> str:
    return (APP / path).read_text(encoding="utf-8")


def _function_names(path: str) -> set[str]:
    tree = ast.parse(_source(path))
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def test_clearance_resolution_plan_facade_remains_thin() -> None:
    source = _source("ui_semantic_validator_handoff_clearance_resolution_plan.py")

    assert len(source.splitlines()) <= 90
    assert "def build_ui_semantic_validator_handoff_clearance_resolution_plan_payload(" not in source
    assert "def _resolution_step(" not in source
    assert "def _matches(" not in source
    assert "ui_semantic_validator_handoff_clearance_resolution_plan_common" in source
    assert "ui_semantic_validator_handoff_clearance_resolution_plan_rows" in source
    assert "ui_semantic_validator_handoff_clearance_resolution_plan_payload" in source


def test_clearance_resolution_plan_subphase_ownership() -> None:
    common = _function_names("ui_semantic_validator_handoff_clearance_resolution_plan_common.py")
    rows = _function_names("ui_semantic_validator_handoff_clearance_resolution_plan_rows.py")
    payload = _function_names("ui_semantic_validator_handoff_clearance_resolution_plan_payload.py")

    assert {"_utc_now", "_s", "_norm", "_as_list", "_norm_set", "_contains", "_digest", "_counts", "_authority"} <= common
    assert rows == {
        "_phase",
        "_step_state",
        "_safe_instruction",
        "_completion_gate",
        "_verification_hint",
        "_resolution_step",
        "_sort_step",
        "_haystack",
        "_matches",
        "_degraded",
    }
    assert payload == {
        "_source_builder",
        "build_ui_semantic_validator_handoff_clearance_resolution_plan_payload",
        "build_ui_semantic_validator_handoff_clearance_resolution_plan_latest_payload",
    }


def test_clearance_resolution_plan_facade_exports_public_builders() -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_resolution_plan as facade
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_resolution_plan_payload as payload

    assert facade.__all__ == payload.__all__
    for name in facade.__all__:
        assert getattr(facade, name) is getattr(payload, name)


def test_clearance_resolution_plan_legacy_private_imports_remain_available() -> None:
    from strategy_validator.application.ui_semantic_validator_handoff_clearance_resolution_plan import (
        _matches,
        _phase,
        _resolution_step,
        _safe_instruction,
        _sort_step,
        _step_state,
    )

    assert callable(_phase)
    assert callable(_step_state)
    assert callable(_safe_instruction)
    assert callable(_resolution_step)
    assert callable(_sort_step)
    assert callable(_matches)


def test_clearance_resolution_plan_facade_source_monkeypatch_surface_is_preserved(monkeypatch) -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_resolution_plan as facade

    monkeypatch.setattr(
        facade,
        "build_ui_semantic_validator_handoff_clearance_action_register_payload",
        lambda **_: {
            "schema_version": "synthetic-action-register/v1",
            "search_root": "synthetic-root",
            "degraded": [],
            "action_rows": [
                {
                    "action_id": "action-monkeypatch",
                    "action_state": "WAITING_EXTERNAL_ARTIFACT",
                    "action_type": "COLLECT_EXTERNAL_ARTIFACT",
                    "evidence_lane": "EXTERNAL_ARTIFACT",
                    "operation_state": "WAITING_EXTERNAL_ARTIFACT_OPERATION",
                    "action_group": "EXTERNAL_ARTIFACT_COLLECTION",
                    "coverage_status": "NEEDS_EXTERNAL_ARTIFACT",
                    "priority": "P1",
                    "severity": "WARN",
                    "trust_banner": "TRUST_RESTRICTED",
                    "owner_hint": "human_operator_clearance_owner",
                    "owner_hints": ["human_operator_clearance_owner"],
                    "issue_codes": ["EXTERNAL_ARTIFACT_REQUIRED"],
                    "requires_external_artifact": True,
                    "requires_human_review": True,
                    "blocked": True,
                }
            ],
        },
    )

    payload = facade.build_ui_semantic_validator_handoff_clearance_resolution_plan_payload()

    assert payload["source_schema_version"] == "synthetic-action-register/v1"
    assert payload["summary"]["resolution_step_count_returned"] == 1
    assert payload["resolution_steps"][0]["phase"] == "EXTERNAL_ARTIFACT_COLLECTION"
    assert payload["resolution_steps"][0]["external_artifact_write_authority"] == "none_read_plane"
