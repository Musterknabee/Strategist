from __future__ import annotations

import ast
from pathlib import Path

APP = Path("strategy_validator/application")


def _source(path: str) -> str:
    return (APP / path).read_text(encoding="utf-8")


def _function_names(path: str) -> set[str]:
    tree = ast.parse(_source(path))
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def test_semantic_validator_handoff_action_queue_facade_remains_thin() -> None:
    source = _source("ui_semantic_validator_handoff_action_queue.py")

    assert len(source.splitlines()) <= 80
    assert "def build_ui_semantic_validator_handoff_action_queue_payload(" not in source
    assert "def _queue_state(" not in source
    assert "def _row(" not in source
    assert "ui_semantic_validator_handoff_action_queue_common" in source
    assert "ui_semantic_validator_handoff_action_queue_rows" in source
    assert "ui_semantic_validator_handoff_action_queue_payload" in source


def test_semantic_validator_handoff_action_queue_subphase_ownership() -> None:
    common = _function_names("ui_semantic_validator_handoff_action_queue_common.py")
    rows = _function_names("ui_semantic_validator_handoff_action_queue_rows.py")
    payload = _function_names("ui_semantic_validator_handoff_action_queue_payload.py")

    assert {"_utc_now", "_s", "_norm", "_as_list", "_norm_set", "_contains", "_digest", "_counts", "_authority"} <= common
    assert rows == {"_queue_state", "_action_id", "_row", "_sort_key", "_hay", "_matches"}
    assert payload == {"_source_builder", "build_ui_semantic_validator_handoff_action_queue_payload", "build_ui_semantic_validator_handoff_action_queue_latest_payload"}


def test_semantic_validator_handoff_action_queue_facade_exports_public_builders() -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_action_queue as facade
    from strategy_validator.application import ui_semantic_validator_handoff_action_queue_payload as payload

    assert facade.__all__ == payload.__all__
    for name in facade.__all__:
        assert getattr(facade, name) is getattr(payload, name)


def test_semantic_validator_handoff_action_queue_legacy_private_imports_remain_available() -> None:
    from strategy_validator.application.ui_semantic_validator_handoff_action_queue import (
        _action_id,
        _matches,
        _queue_state,
        _row,
        _sort_key,
    )

    assert callable(_queue_state)
    assert callable(_action_id)
    assert callable(_row)
    assert callable(_sort_key)
    assert callable(_matches)


def test_semantic_validator_handoff_action_queue_facade_source_monkeypatch_surface_is_preserved(monkeypatch) -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_action_queue as facade

    monkeypatch.setattr(
        facade,
        "build_ui_semantic_validator_handoff_audit_packet_payload",
        lambda **_: {
            "schema_version": "synthetic-audit-packet/v1",
            "search_root": "synthetic-root",
            "degraded": [],
            "audit_packets": [
                {
                    "audit_packet_id": "packet-monkeypatch",
                    "audit_packet_digest": "digest-monkeypatch",
                    "experiment_id": "EXP-ACTION-MONKEYPATCH",
                    "packet_status": "AWAITING_EXTERNAL_ARTIFACT",
                    "packet_lane": "external_artifact",
                    "trust_banner": "TRUST_RESTRICTED",
                    "operator_attention_required": True,
                    "required_actions": [
                        {
                            "source": "evidence_gap",
                            "source_id": "gap-monkeypatch",
                            "priority": "P1",
                            "severity": "WARN",
                            "operator_action": "CREATE_EXTERNAL_ARTIFACT_EXTERNALLY",
                            "issue_codes": ["EXTERNAL_CLOSURE_ATTESTATION_MISSING"],
                        }
                    ],
                }
            ],
        },
    )

    payload = facade.build_ui_semantic_validator_handoff_action_queue_payload()

    assert payload["source_schema_version"] == "synthetic-audit-packet/v1"
    assert payload["summary"]["action_count_returned"] == 1
    assert payload["action_rows"][0]["experiment_id"] == "EXP-ACTION-MONKEYPATCH"
    assert payload["action_rows"][0]["queue_state"] == "EXTERNAL_ARTIFACT_REQUIRED"
