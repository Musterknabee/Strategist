from __future__ import annotations

import ast
from pathlib import Path

APP = Path("strategy_validator/application")


def _source(path: str) -> str:
    return (APP / path).read_text(encoding="utf-8")


def _function_names(path: str) -> set[str]:
    tree = ast.parse(_source(path))
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def test_clearance_checklist_facade_remains_thin() -> None:
    source = _source("ui_semantic_validator_handoff_clearance_checklist.py")

    assert len(source.splitlines()) <= 90
    assert "def build_ui_semantic_validator_handoff_clearance_checklist_payload(" not in source
    assert "def _checklist_item(" not in source
    assert "def _matches(" not in source
    assert "ui_semantic_validator_handoff_clearance_checklist_common" in source
    assert "ui_semantic_validator_handoff_clearance_checklist_rows" in source
    assert "ui_semantic_validator_handoff_clearance_checklist_payload" in source


def test_clearance_checklist_subphase_ownership() -> None:
    common = _function_names("ui_semantic_validator_handoff_clearance_checklist_common.py")
    rows = _function_names("ui_semantic_validator_handoff_clearance_checklist_rows.py")
    payload = _function_names("ui_semantic_validator_handoff_clearance_checklist_payload.py")

    assert {"_utc_now", "_s", "_norm", "_as_list", "_norm_set", "_contains", "_digest", "_counts", "_authority"} <= common
    assert rows == {"_instruction", "_checklist_item", "_items_from_dossiers", "_sort_item", "_haystack", "_matches", "_degraded"}
    assert payload == {"_source_builder", "build_ui_semantic_validator_handoff_clearance_checklist_payload", "build_ui_semantic_validator_handoff_clearance_checklist_latest_payload"}


def test_clearance_checklist_facade_exports_public_builders() -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_checklist as facade
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_checklist_payload as payload

    assert facade.__all__ == payload.__all__
    for name in facade.__all__:
        assert getattr(facade, name) is getattr(payload, name)


def test_clearance_checklist_legacy_private_imports_remain_available() -> None:
    from strategy_validator.application.ui_semantic_validator_handoff_clearance_checklist import _checklist_item, _items_from_dossiers, _matches, _sort_item

    assert callable(_checklist_item)
    assert callable(_items_from_dossiers)
    assert callable(_sort_item)
    assert callable(_matches)


def test_clearance_checklist_facade_source_monkeypatch_surface_is_preserved(monkeypatch) -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_checklist as facade

    monkeypatch.setattr(
        facade,
        "build_ui_semantic_validator_handoff_clearance_dossier_payload",
        lambda **_: {
            "schema_version": "synthetic-clearance-dossier/v1",
            "search_root": "synthetic-root",
            "degraded": [],
            "clearance_dossiers": [
                {
                    "clearance_dossier_id": "dossier-monkeypatch",
                    "schema_version": "synthetic-clearance-dossier/v1",
                    "ordinal": 1,
                    "review_posture": "WAITING_EXTERNAL_ARTIFACT",
                    "clearance_status": "WAITING_EXTERNAL_ARTIFACT",
                    "clearance_gate_id": "gate-monkeypatch",
                    "scope_key": "EXP-MONKEY",
                    "experiment_id": "EXP-MONKEY",
                    "priority": "P1",
                    "severity": "WARN",
                    "trust_banner": "TRUST_RESTRICTED",
                    "owner_hint": "human_operator_clearance_owner",
                    "handoff_clearance_blocked": True,
                    "requires_external_artifact": True,
                    "issue_codes": ["EXTERNAL_ARTIFACT_REQUIRED"],
                    "issue_count": 1,
                    "phase_set": ["EXTERNAL_ARTIFACT_COLLECTION"],
                    "routes": {"clearance_dossier": "/ui/semantic-validator-handoff/clearance-dossier"},
                    "review_checks": [
                        {
                            "check_id": "external_artifact_gap_absent",
                            "check_state": "WAITING_EXTERNAL_ARTIFACT",
                            "evidence": "requires_external_artifact=True",
                            "route": "/ui/semantic-validator-handoff/clearance-gate",
                            "write_allowed": False,
                        }
                    ],
                }
            ],
        },
    )

    payload = facade.build_ui_semantic_validator_handoff_clearance_checklist_payload()

    assert payload["source_schema_version"] == "synthetic-clearance-dossier/v1"
    assert payload["summary"]["checklist_item_count_returned"] == 1
    assert payload["checklist_items"][0]["check_id"] == "external_artifact_gap_absent"
    assert payload["checklist_items"][0]["check_state"] == "WAITING_EXTERNAL_ARTIFACT"
    assert payload["checklist_items"][0]["external_artifact_write_authority"] == "none_read_plane"
