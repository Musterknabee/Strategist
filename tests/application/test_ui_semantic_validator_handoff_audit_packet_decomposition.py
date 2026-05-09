from __future__ import annotations

import ast
from pathlib import Path

APP = Path("strategy_validator/application")


def _source(path: str) -> str:
    return (APP / path).read_text(encoding="utf-8")


def _function_names(path: str) -> set[str]:
    tree = ast.parse(_source(path))
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def test_semantic_validator_handoff_audit_packet_facade_remains_thin() -> None:
    source = _source("ui_semantic_validator_handoff_audit_packet.py")

    assert len(source.splitlines()) <= 95
    assert "def build_ui_semantic_validator_handoff_audit_packet_payload(" not in source
    assert "def _audit_packet_row(" not in source
    assert "def _packet_status(" not in source
    assert "def _index_rows(" not in source
    assert "ui_semantic_validator_handoff_audit_packet_common" in source
    assert "ui_semantic_validator_handoff_audit_packet_indexing" in source
    assert "ui_semantic_validator_handoff_audit_packet_rows" in source
    assert "ui_semantic_validator_handoff_audit_packet_payload" in source


def test_semantic_validator_handoff_audit_packet_subphase_ownership() -> None:
    common = _function_names("ui_semantic_validator_handoff_audit_packet_common.py")
    indexing = _function_names("ui_semantic_validator_handoff_audit_packet_indexing.py")
    rows = _function_names("ui_semantic_validator_handoff_audit_packet_rows.py")
    payload = _function_names("ui_semantic_validator_handoff_audit_packet_payload.py")

    assert {"_utc_now", "_s", "_norm", "_as_list", "_norm_set", "_contains", "_counts", "_digest", "_authority"} <= common
    assert indexing == {"_row_key", "_index_rows", "_related"}
    assert rows == {"_packet_status", "_packet_lane", "_trust_banner", "_required_actions", "_timeline_tail", "_audit_packet_row", "_haystack", "_matches"}
    assert payload == {"_source_builders", "build_ui_semantic_validator_handoff_audit_packet_payload", "build_ui_semantic_validator_handoff_audit_packet_latest_payload"}


def test_semantic_validator_handoff_audit_packet_facade_exports_public_builders() -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_audit_packet as facade
    from strategy_validator.application import ui_semantic_validator_handoff_audit_packet_payload as payload

    assert facade.__all__ == payload.__all__
    for name in facade.__all__:
        assert getattr(facade, name) is getattr(payload, name)


def test_semantic_validator_handoff_audit_packet_legacy_private_imports_remain_available() -> None:
    from strategy_validator.application.ui_semantic_validator_handoff_audit_packet import (
        _audit_packet_row,
        _index_rows,
        _packet_status,
        _related,
        _trust_banner,
    )

    assert callable(_audit_packet_row)
    assert callable(_index_rows)
    assert callable(_packet_status)
    assert callable(_related)
    assert callable(_trust_banner)


def test_semantic_validator_handoff_audit_packet_facade_source_monkeypatch_surface_is_preserved(monkeypatch) -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_audit_packet as facade

    monkeypatch.setattr(
        facade,
        "build_ui_semantic_validator_handoff_continuity_payload",
        lambda **_: {
            "schema_version": "synthetic-continuity/v1",
            "search_root": "synthetic-root",
            "degraded": [],
            "continuity_rows": [
                {
                    "continuity_id": "continuity-monkeypatch",
                    "experiment_id": "EXP-MONKEYPATCH",
                    "chain_id": "chain-monkeypatch",
                    "chain_digest": "digest-monkeypatch",
                    "terminal_status": "CLOSED_WITH_RECORDED_CLOSURE_ATTESTATION",
                    "current_stage": "closure",
                    "closure_status": "RECORDED",
                    "trust_banner": "TRUSTED",
                    "stage_path": [],
                }
            ],
        },
    )
    monkeypatch.setattr(
        facade,
        "build_ui_semantic_validator_handoff_evidence_gaps_payload",
        lambda **_: {"schema_version": "synthetic-gaps/v1", "degraded": [], "gap_rows": []},
    )
    monkeypatch.setattr(
        facade,
        "build_ui_semantic_validator_handoff_exceptions_payload",
        lambda **_: {"schema_version": "synthetic-exceptions/v1", "degraded": [], "exception_rows": []},
    )
    monkeypatch.setattr(
        facade,
        "build_ui_semantic_validator_handoff_timeline_payload",
        lambda **_: {"schema_version": "synthetic-timeline/v1", "degraded": [], "timeline_events": []},
    )

    payload = facade.build_ui_semantic_validator_handoff_audit_packet_payload()

    assert payload["source_schema_versions"] == {
        "continuity": "synthetic-continuity/v1",
        "timeline": "synthetic-timeline/v1",
        "exceptions": "synthetic-exceptions/v1",
        "evidence_gaps": "synthetic-gaps/v1",
    }
    assert payload["audit_packets"][0]["experiment_id"] == "EXP-MONKEYPATCH"
    assert payload["audit_packets"][0]["packet_status"] == "CLOSED_AUDIT_READY"
