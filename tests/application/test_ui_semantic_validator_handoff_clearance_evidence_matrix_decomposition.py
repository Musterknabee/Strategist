from __future__ import annotations

import ast
from pathlib import Path

APP = Path("strategy_validator/application")


def _source(path: str) -> str:
    return (APP / path).read_text(encoding="utf-8")


def _function_names(path: str) -> set[str]:
    tree = ast.parse(_source(path))
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def test_clearance_evidence_matrix_facade_remains_thin() -> None:
    source = _source("ui_semantic_validator_handoff_clearance_evidence_matrix.py")

    assert len(source.splitlines()) <= 90
    assert "def build_ui_semantic_validator_handoff_clearance_evidence_matrix_payload(" not in source
    assert "def _matrix_row(" not in source
    assert "def _matches(" not in source
    assert "ui_semantic_validator_handoff_clearance_evidence_matrix_common" in source
    assert "ui_semantic_validator_handoff_clearance_evidence_matrix_rows" in source
    assert "ui_semantic_validator_handoff_clearance_evidence_matrix_payload" in source


def test_clearance_evidence_matrix_subphase_ownership() -> None:
    common = _function_names("ui_semantic_validator_handoff_clearance_evidence_matrix_common.py")
    rows = _function_names("ui_semantic_validator_handoff_clearance_evidence_matrix_rows.py")
    payload = _function_names("ui_semantic_validator_handoff_clearance_evidence_matrix_payload.py")

    assert {"_utc_now", "_s", "_norm", "_as_list", "_norm_set", "_contains", "_digest", "_counts", "_authority"} <= common
    assert rows == {"_evidence_lane", "_evidence_state", "_coverage_state", "_instruction", "_matrix_row", "_sort_row", "_haystack", "_matches", "_matrix_cells", "_degraded"}
    assert payload == {"_source_builder", "build_ui_semantic_validator_handoff_clearance_evidence_matrix_payload", "build_ui_semantic_validator_handoff_clearance_evidence_matrix_latest_payload"}


def test_clearance_evidence_matrix_facade_exports_public_builders() -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_evidence_matrix as facade
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_evidence_matrix_payload as payload

    assert facade.__all__ == payload.__all__
    for name in facade.__all__:
        assert getattr(facade, name) is getattr(payload, name)


def test_clearance_evidence_matrix_legacy_private_imports_remain_available() -> None:
    from strategy_validator.application.ui_semantic_validator_handoff_clearance_evidence_matrix import _evidence_lane, _evidence_state, _matches, _matrix_cells, _matrix_row, _sort_row

    assert callable(_evidence_lane)
    assert callable(_evidence_state)
    assert callable(_matrix_row)
    assert callable(_sort_row)
    assert callable(_matches)
    assert callable(_matrix_cells)


def test_clearance_evidence_matrix_facade_source_monkeypatch_surface_is_preserved(monkeypatch) -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_evidence_matrix as facade

    monkeypatch.setattr(
        facade,
        "build_ui_semantic_validator_handoff_clearance_checklist_payload",
        lambda **_: {
            "schema_version": "synthetic-clearance-checklist/v1",
            "search_root": "synthetic-root",
            "degraded": [],
            "checklist_items": [
                {
                    "checklist_item_id": "item-monkeypatch",
                    "check_id": "external_artifact_gap_absent",
                    "check_state": "WAITING_EXTERNAL_ARTIFACT",
                    "attention_required": True,
                    "blocks_clearance": False,
                    "requires_external_artifact": True,
                    "route": "/ui/semantic-validator-handoff/clearance-gate",
                    "experiment_id": "EXP-MONKEY",
                    "scope_key": "EXP-MONKEY",
                    "priority": "P1",
                    "severity": "WARN",
                    "trust_banner": "TRUST_RESTRICTED",
                    "owner_hint": "human_operator_clearance_owner",
                    "issue_codes": ["EXTERNAL_ARTIFACT_REQUIRED"],
                    "phase_set": ["EXTERNAL_ARTIFACT_COLLECTION"],
                }
            ],
        },
    )

    payload = facade.build_ui_semantic_validator_handoff_clearance_evidence_matrix_payload()

    assert payload["source_schema_version"] == "synthetic-clearance-checklist/v1"
    assert payload["summary"]["evidence_matrix_row_count_returned"] == 1
    assert payload["evidence_rows"][0]["evidence_lane"] == "EXTERNAL_ARTIFACT"
    assert payload["evidence_rows"][0]["evidence_state"] == "WAITING_EXTERNAL_ARTIFACT"
    assert payload["evidence_rows"][0]["external_artifact_write_authority"] == "none_read_plane"
