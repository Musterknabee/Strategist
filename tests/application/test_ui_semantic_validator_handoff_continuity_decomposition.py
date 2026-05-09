from __future__ import annotations

import ast
from pathlib import Path

APP = Path("strategy_validator/application")


def _source(path: str) -> str:
    return (APP / path).read_text(encoding="utf-8")


def _function_names(path: str) -> set[str]:
    tree = ast.parse(_source(path))
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def test_semantic_validator_handoff_continuity_facade_remains_thin() -> None:
    source = _source("ui_semantic_validator_handoff_continuity.py")

    assert len(source.splitlines()) <= 100
    assert "def build_ui_semantic_validator_handoff_continuity_payload(" not in source
    assert "def _continuity_row(" not in source
    assert "def _stage_record(" not in source
    assert "ui_semantic_validator_handoff_continuity_common" in source
    assert "ui_semantic_validator_handoff_continuity_rows" in source
    assert "ui_semantic_validator_handoff_continuity_payload" in source


def test_semantic_validator_handoff_continuity_subphase_ownership() -> None:
    common = _function_names("ui_semantic_validator_handoff_continuity_common.py")
    rows = _function_names("ui_semantic_validator_handoff_continuity_rows.py")
    payload = _function_names("ui_semantic_validator_handoff_continuity_payload.py")

    assert {
        "_utc_now",
        "_s",
        "_norm",
        "_norm_set",
        "_as_list",
        "_counts",
        "_contains",
        "_authority",
    } <= common
    assert rows == {
        "_stage_record",
        "_terminal_status",
        "_current_stage",
        "_continuity_row",
        "_haystack",
        "_matches",
    }
    assert payload == {
        "_source_builder",
        "build_ui_semantic_validator_handoff_continuity_payload",
        "build_ui_semantic_validator_handoff_continuity_latest_payload",
    }


def test_semantic_validator_handoff_continuity_facade_exports_public_builders() -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_continuity as facade
    from strategy_validator.application import ui_semantic_validator_handoff_continuity_payload as payload

    assert facade.__all__ == payload.__all__
    for name in facade.__all__:
        assert getattr(facade, name) is getattr(payload, name)


def test_semantic_validator_handoff_continuity_legacy_private_imports_remain_available() -> None:
    from strategy_validator.application.ui_semantic_validator_handoff_continuity import (
        _continuity_row,
        _current_stage,
        _haystack,
        _matches,
        _stage_record,
        _terminal_status,
    )

    assert callable(_stage_record)
    assert callable(_terminal_status)
    assert callable(_current_stage)
    assert callable(_continuity_row)
    assert callable(_haystack)
    assert callable(_matches)


def test_semantic_validator_handoff_continuity_facade_source_monkeypatch_surface_is_preserved(monkeypatch) -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_continuity as facade

    monkeypatch.setattr(
        facade,
        "build_ui_semantic_validator_handoff_closure_payload",
        lambda **_: {
            "schema_version": "synthetic-closure/v1",
            "search_root": "synthetic-root",
            "degraded": [],
            "closure_gates": [
                {
                    "closure_gate_id": "closure-1",
                    "closure_status": "READY_FOR_EXTERNAL_CLOSURE_ATTESTATION",
                    "closure_attestation_recorded": False,
                    "closure_attestation_required": True,
                    "trust_banner": "TRUSTED",
                    "archive_gate_id": "archive-1",
                    "archive_manifest_id": "manifest-1",
                    "archive_status": "ARCHIVE_MANIFEST_VERIFIED",
                    "custody_gate_id": "custody-1",
                    "signoff_gate_id": "signoff-1",
                    "decision_id": "decision-1",
                    "chain_id": "chain-1",
                    "chain_digest": "chain-digest",
                    "experiment_id": "EXP-CONTINUITY",
                    "decision_packet_digest": "decision-digest",
                    "custody_packet_digest": "custody-digest",
                    "archive_packet_digest": "archive-digest",
                    "closure_packet_digest": "closure-digest",
                    "issue_codes": ["EXTERNAL_CLOSURE_ATTESTATION_MISSING"],
                    "closure_template": {"schema_version": "semantic_validator_handoff_closure_attestation/v1"},
                    "recommended_action": "CREATE_EXTERNAL_CLOSURE_ATTESTATION",
                }
            ],
        },
    )

    payload = facade.build_ui_semantic_validator_handoff_continuity_payload()

    assert payload["source_schema_version"] == "synthetic-closure/v1"
    assert payload["search_root"] == "synthetic-root"
    assert payload["summary"]["continuity_count_returned"] == 1
    row = payload["continuity_rows"][0]
    assert row["experiment_id"] == "EXP-CONTINUITY"
    assert row["terminal_status"] == "AWAITING_EXTERNAL_CLOSURE_ATTESTATION"
    assert row["authority"]["execution_allowed"] is False
