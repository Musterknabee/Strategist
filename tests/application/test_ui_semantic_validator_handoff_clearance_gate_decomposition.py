from __future__ import annotations

import ast
from pathlib import Path

APP = Path("strategy_validator/application")


def _source(path: str) -> str:
    return (APP / path).read_text(encoding="utf-8")


def _function_names(path: str) -> set[str]:
    tree = ast.parse(_source(path))
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def test_clearance_gate_facade_remains_thin() -> None:
    source = _source("ui_semantic_validator_handoff_clearance_gate.py")

    assert len(source.splitlines()) <= 90
    assert "def build_ui_semantic_validator_handoff_clearance_gate_payload(" not in source
    assert "def _gate_from_steps(" not in source
    assert "def _matches(" not in source
    assert "ui_semantic_validator_handoff_clearance_gate_common" in source
    assert "ui_semantic_validator_handoff_clearance_gate_rows" in source
    assert "ui_semantic_validator_handoff_clearance_gate_payload" in source


def test_clearance_gate_subphase_ownership() -> None:
    common = _function_names("ui_semantic_validator_handoff_clearance_gate_common.py")
    rows = _function_names("ui_semantic_validator_handoff_clearance_gate_rows.py")
    payload = _function_names("ui_semantic_validator_handoff_clearance_gate_payload.py")

    assert {"_utc_now", "_s", "_norm", "_as_list", "_norm_set", "_contains", "_digest", "_counts", "_authority"} <= common
    assert rows == {
        "_highest_priority",
        "_highest_severity",
        "_status",
        "_gate_instruction",
        "_completion_condition",
        "_gate_from_steps",
        "_group_steps",
        "_sort_gate",
        "_haystack",
        "_matches",
    }
    assert payload == {
        "_source_builder",
        "build_ui_semantic_validator_handoff_clearance_gate_payload",
        "build_ui_semantic_validator_handoff_clearance_gate_latest_payload",
    }


def test_clearance_gate_facade_exports_public_builders() -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_gate as facade
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_gate_payload as payload

    assert facade.__all__ == payload.__all__
    for name in facade.__all__:
        assert getattr(facade, name) is getattr(payload, name)


def test_clearance_gate_legacy_private_imports_remain_available() -> None:
    from strategy_validator.application.ui_semantic_validator_handoff_clearance_gate import (
        _gate_from_steps,
        _group_steps,
        _matches,
        _sort_gate,
        _status,
    )

    assert callable(_status)
    assert callable(_gate_from_steps)
    assert callable(_group_steps)
    assert callable(_sort_gate)
    assert callable(_matches)


def test_clearance_gate_facade_source_monkeypatch_surface_is_preserved(monkeypatch) -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_gate as facade

    monkeypatch.setattr(
        facade,
        "build_ui_semantic_validator_handoff_resolution_plan_payload",
        lambda **_: {
            "schema_version": "synthetic-resolution-plan/v1",
            "search_root": "synthetic-root",
            "degraded": [],
            "resolution_steps": [
                {
                    "resolution_step_id": "step-monkeypatch",
                    "phase": "EXTERNAL_ARTIFACT_COLLECTION",
                    "experiment_id": "EXP-MONKEY",
                    "continuity_id": "cont-monkeypatch",
                    "audit_packet_id": "packet-monkeypatch",
                    "audit_packet_digest": "digest-monkeypatch",
                    "priority": "P1",
                    "severity": "WARN",
                    "trust_banner": "TRUST_RESTRICTED",
                    "owner_hint": "human_operator_clearance_owner",
                    "resolution_route": "/ui/semantic-validator-handoff/resolution-plan",
                    "issue_codes": ["EXTERNAL_ARTIFACT_REQUIRED"],
                    "requires_external_artifact": True,
                    "requires_human_review": True,
                    "blocks_handoff_clearance": True,
                }
            ],
        },
    )

    payload = facade.build_ui_semantic_validator_handoff_clearance_gate_payload()

    assert payload["source_schema_version"] == "synthetic-resolution-plan/v1"
    assert payload["summary"]["clearance_gate_count_returned"] == 1
    assert payload["clearance_gates"][0]["clearance_status"] == "WAITING_EXTERNAL_ARTIFACT"
    assert payload["clearance_gates"][0]["external_artifact_write_authority"] == "none_read_plane"
